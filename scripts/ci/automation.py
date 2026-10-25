#!/usr/bin/env python3
"""Upstream synchronization and recoverable, provenance-checked ARMv7a releases."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OWNED = (".github", "fork", "scripts/ci", "docs/CI_CD.md", "docs/BRANCH_POLICY.md",
         "docs/native/libsimple.md", "AGENTS.md")
STATE = ".fork-state.json"


def git(*args, cwd=ROOT, input=None):
    return subprocess.check_output(["git", *args], cwd=cwd, input=input, text=True).strip()


def digest(path):
    with open(path, "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def config():
    return json.loads((ROOT / "fork/config.json").read_text())


def output(name, value):
    value = value if isinstance(value, str) else json.dumps(value, separators=(",", ":"))
    if "\n" in value:
        raise ValueError("Actions outputs must be single line")
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
            stream.write(f"{name}={value}\n")
    print(f"{name}={value}")


class GitHub:
    def __init__(self, repository=None):
        self.repository = repository or config()["repository"]

    def request(self, path, method="GET", data=None, raw=False, content_type=None):
        url = path if path.startswith("https://") else f"https://api.github.com/repos/{self.repository}/{path}"
        # Send credentials only to GitHub API/upload hosts. urllib drops no headers on
        # redirects, so asset downloads below use public URLs without authentication.
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "rikkahub-armv7a-ci",
                   "X-GitHub-Api-Version": "2022-11-28"}
        token = os.getenv("GH_TOKEN", "")
        if token and urllib.parse.urlparse(url).hostname in ("api.github.com", "uploads.github.com"):
            headers["Authorization"] = f"Bearer {token}"
        if data is not None and not isinstance(data, bytes):
            data = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
        if content_type:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    body = response.read()
                    return body if raw else json.loads(body) if body else None
            except urllib.error.HTTPError as error:
                if error.code == 404:
                    return None
                # Only reads are retried here. Retrying a mutation blindly can create
                # duplicate releases/assets; the next scheduled run reconciles them.
                if method != "GET" or error.code not in (429, 500, 502, 503, 504) or attempt == 3:
                    raise RuntimeError(f"GitHub {method} {path}: HTTP {error.code}") from error
            except (TimeoutError, urllib.error.URLError):
                if method != "GET" or attempt == 3:
                    raise
            time.sleep(2 ** attempt)

    def pages(self, path):
        page = 1
        while True:
            items = self.request(f"{path}{'&' if '?' in path else '?'}per_page=100&page={page}")
            if not isinstance(items, list):
                raise RuntimeError(f"Expected paginated list: {path}")
            yield from items
            if len(items) < 100:
                break
            page += 1

    def release(self, tag):
        return self.request("releases/tags/" + urllib.parse.quote(tag, safe=""))

    def sha(self, ref):
        commit = self.request("commits/" + urllib.parse.quote(ref, safe=""))
        if not commit:
            raise RuntimeError(f"Missing upstream ref: {ref}")
        return commit["sha"]


def asset_bytes(api, asset):
    # API asset endpoint redirects to a public/CDN host. Use gh for the authenticated
    # draft download so its HTTP client strips credentials on cross-host redirects.
    return subprocess.check_output(["gh", "api", f"repos/{api.repository}/releases/assets/{asset['id']}",
                                    "-H", "Accept: application/octet-stream"])


def release_manifest(api, release, upstream_sha):
    if not release or release.get("prerelease"):
        return None
    assets = {a["name"]: a for a in release["assets"]}
    if "build-info.json" not in assets or "SHA256SUMS" not in assets:
        return None
    info_bytes = asset_bytes(api, assets["build-info.json"])
    manifest = json.loads(info_bytes)
    if manifest.get("upstream_sha") != upstream_sha or manifest.get("tag") != release["tag_name"]:
        raise RuntimeError("Existing release provenance does not match the upstream tag")
    apk = assets.get(manifest["apk"])
    if not apk or apk["size"] != manifest["apk_size"] or not manifest.get("certificate_sha256"):
        return None
    checksums = asset_bytes(api, assets["SHA256SUMS"]).decode()
    if f"{manifest['apk_sha256']}  {manifest['apk']}" not in checksums.splitlines():
        raise RuntimeError("Existing release has inconsistent checksums")
    if f"{hashlib.sha256(info_bytes).hexdigest()}  build-info.json" not in checksums.splitlines():
        raise RuntimeError("Existing release metadata checksum mismatch")
    remote_digest = apk.get("digest")
    if remote_digest and remote_digest != "sha256:" + manifest["apk_sha256"]:
        raise RuntimeError("GitHub APK digest does not match the manifest")
    # Older GitHub assets may not expose a digest; still verify their bytes.
    if not remote_digest and hashlib.sha256(asset_bytes(api, apk)).hexdigest() != manifest["apk_sha256"]:
        raise RuntimeError("Existing release APK checksum mismatch")
    return manifest


def select_releases(upstream_releases, local_releases, baseline):
    local = {r["tag_name"]: r for r in local_releases}
    formal = [r for r in upstream_releases if not r["draft"] and not r["prerelease"] and
              r["published_at"] >= baseline["published_at"]]
    return [(r, local.get(r["tag_name"])) for r in sorted(formal, key=lambda r: r["published_at"])]


def overlay_hash(root=ROOT, owned_paths=OWNED):
    result = hashlib.sha256()
    for owned in owned_paths:
        base = root / owned
        paths = sorted(base.rglob("*")) if base.is_dir() else [base]
        for path in paths:
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                data = path.read_bytes()
                if path.relative_to(root).as_posix() == "fork/config.json":
                    cfg = json.loads(data)
                    # Approving the exact tested APK must not force its rebuild.
                    cfg.pop("device_validation", None)
                    data = json.dumps(cfg, sort_keys=True).encode()
                result.update(str(path.relative_to(root)).encode() + b"\0" + data)
    return result.hexdigest()


def build_hash(root=ROOT):
    # Controller/notification/documentation changes do not invalidate a tested APK.
    # Every input that changes app sources, signing preparation, or native/toolchain
    # output is included; the upstream source SHA is validated separately.
    return overlay_hash(root, ("fork", "scripts/ci/apply-overlay.py", "scripts/ci/build-native.py",
                               "scripts/ci/setup-android.py", "scripts/ci/prepare-build-secrets.py"))


def plan(args):
    cfg = config()
    api, upstream = GitHub(), GitHub(cfg["upstream"])
    upstream_sha = upstream.sha(cfg["branch"])
    base_sha = api.sha(cfg["branch"])
    state_response = api.request(f"contents/{STATE}?ref={base_sha}")
    state = {}
    if state_response:
        import base64
        state = json.loads(base64.b64decode(state_response["content"]))
    now = dt.datetime.now(dt.timezone.utc)
    checked = dt.datetime.fromisoformat(state.get("checked_at", "1970-01-01T00:00:00+00:00"))
    sync = (state.get("upstream_sha") != upstream_sha or state.get("overlay_sha256") != overlay_hash() or
            (now - checked).days >= 45)
    releases = []
    for remote, local in select_releases(list(upstream.pages("releases")), list(api.pages("releases")),
                                          cfg["release_baseline"]):
        sha = upstream.sha(remote["tag_name"])
        manifest = release_manifest(api, local, sha)
        if not manifest or local["draft"]:
            releases.append({"tag": remote["tag_name"], "sha": sha})
    output("sync", str(sync).lower())
    output("upstream_sha", upstream_sha)
    output("base_sha", base_sha)
    output("releases", {"include": releases})
    output("has_releases", str(bool(releases)).lower())


def copy_owned(source, target):
    for owned in OWNED:
        src, dst = source / owned, target / owned
        if dst.is_dir():
            shutil.rmtree(dst)
        elif dst.exists():
            dst.unlink()
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        elif src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)


def prepare(args):
    cfg = config()
    if not re.fullmatch(r"[0-9a-f]{40}", args.upstream_sha):
        raise ValueError("An immutable upstream SHA is required")
    target = Path(args.target).resolve()
    if target.exists():
        raise ValueError(f"Candidate directory already exists: {target}")
    base = args.base_sha or GitHub().sha(cfg["branch"])
    git("fetch", "origin", base, "--no-tags")
    git("fetch", "https://github.com/" + cfg["upstream"] + ".git", args.upstream_sha, "--no-tags")
    subprocess.run(["git", "clone", "--shared", "--no-checkout", str(ROOT), str(target)], check=True)
    git("read-tree", "--reset", "-u", args.upstream_sha, cwd=target)
    copy_owned(ROOT, target)
    subprocess.run([sys.executable, str(target / "scripts/ci/apply-overlay.py"), str(target)], check=True)
    state = {"schema": 1, "upstream_sha": args.upstream_sha, "overlay_sha256": overlay_hash(),
             "build_overlay_sha256": build_hash(),
             "control_sha": git("rev-parse", "HEAD"), "checked_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    (target / STATE).write_text(json.dumps(state, indent=2) + "\n")
    git("add", "-A", cwd=target)
    tree = git("write-tree", cwd=target)
    git("config", "user.name", "github-actions[bot]", cwd=target)
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com", cwd=target)
    sha = git("commit-tree", tree, "-p", base, "-p", args.upstream_sha,
              "-m", f"chore: adapt upstream {args.tag or args.upstream_sha[:12]} for ARMv7a", cwd=target)
    # The disposable clone can contain upstream directory-to-symlink transitions
    # (e.g. .claude/skills). Force checkout only inside this newly-created clone.
    git("checkout", "--force", "--detach", sha, cwd=target)
    git("remote", "set-url", "origin", git("remote", "get-url", "origin"), cwd=target)
    git("submodule", "update", "--init", "--recursive", cwd=target)
    output("source_sha", sha)
    output("base_sha", base)


def advance(args):
    cfg = config()
    sha = git("rev-parse", "HEAD", cwd=Path(args.target))
    git("fetch", str(Path(args.target).resolve()), sha, "--no-tags")
    # A normal push enforces ancestry. Also compare the exact expected base, so a
    # racing maintainer commit is never silently incorporated or overwritten.
    actual = git("ls-remote", "origin", f"refs/heads/{cfg['branch']}").split()[0]
    if actual != args.base_sha:
        raise RuntimeError("master changed while validating; the next run will prepare a fresh candidate")
    git("push", "origin", f"{sha}:refs/heads/{cfg['branch']}")


def persist(args):
    sha = git("rev-parse", "HEAD", cwd=Path(args.target))
    git("fetch", str(Path(args.target).resolve()), sha, "--no-tags")
    # Each attempt has an immutable branch; partial releases keep their original
    # commit reachable even when a later attempt builds a replacement draft.
    git("push", "origin", f"{sha}:refs/heads/build/armv7/{sha}")


def status(args):
    release = GitHub().release(args.tag)
    manifest = release_manifest(GitHub(), release, args.upstream_sha)
    ready = bool(manifest) and (not release["draft"] or manifest.get("build_overlay_sha256") == build_hash())
    output("ready", str(ready).lower())


def upload(args):
    api = GitHub()
    root = Path(args.directory)
    manifest = json.loads((root / "build-info.json").read_text())
    if manifest["tag"] != args.tag or manifest["upstream_sha"] != args.upstream_sha:
        raise RuntimeError("Build provenance mismatch")
    release = api.release(args.tag)
    if release and not release["draft"] and release_manifest(api, release, args.upstream_sha):
        print("Complete published release already exists")
        return
    if not release:
        release = api.request("releases", "POST", {
            "tag_name": args.tag, "target_commitish": manifest["source_sha"],
            "name": f"RikkaHub {manifest['version_name']} ARMv7a", "draft": True, "prerelease": False,
            "body": f"ARMv7a build of [{args.tag}](https://github.com/{config()['upstream']}/releases/tag/{urllib.parse.quote(args.tag, safe='')}).\n\n"
                    f"Upstream: `{args.upstream_sha}`\nSource: `{manifest['source_sha']}`\n"
                    f"Adapter: `{manifest['control_sha']}`\n\n"
                    "Requires Android 8.0 or newer. SHA256SUMS and build-info.json document the exact APK and signing certificate."
        })
    elif release["draft"]:
        # Drafts can be retried with a newly prepared source commit. Keep their
        # target aligned with the replacement build; never relabel an existing tag.
        tag_ref = api.request("git/ref/tags/" + urllib.parse.quote(args.tag, safe=""))
        if tag_ref and api.sha(args.tag) != manifest["source_sha"]:
            raise RuntimeError("Existing tag points at a different source; refusing to relabel it")
        api.request(f"releases/{release['id']}", "PATCH", {"target_commitish": manifest["source_sha"]})
    assets = {a["name"]: a for a in release["assets"]}
    # Upload the manifest last: it is the completion marker after the APK/checksums.
    for name in (manifest["apk"], "SHA256SUMS", "build-info.json"):
        path = root / name
        data = path.read_bytes()
        existing = assets.get(name)
        if existing:
            if hashlib.sha256(asset_bytes(api, existing)).hexdigest() == hashlib.sha256(data).hexdigest():
                continue
            if not release["draft"]:
                raise RuntimeError(f"Refusing to replace published asset: {name}")
            # Partial/unverified draft assets may be replaced safely.
            api.request(f"releases/assets/{existing['id']}", "DELETE")
        url = release["upload_url"].split("{")[0] + "?name=" + urllib.parse.quote(name, safe="")
        api.request(url, "POST", data, content_type="application/octet-stream")
    if not release_manifest(api, api.release(args.tag), args.upstream_sha):
        raise RuntimeError("Release assets were not completely verified")


def publish(args):
    cfg, api = config(), GitHub()
    release = api.release(args.tag)
    manifest = release_manifest(api, release, args.upstream_sha)
    if not manifest:
        raise RuntimeError("Release assets are incomplete")
    if not release["draft"]:
        print("Already published and verified")
        return
    validation = cfg["device_validation"]
    if not validation["approved"]:
        print("Draft ready. First-device validation is required before public releases are enabled.")
        output("awaiting_device", "true")
        return
    baseline = validation["baseline_apk_sha256"]
    if not re.fullmatch(r"[0-9a-f]{64}", baseline):
        raise RuntimeError("Device approval must record the tested baseline APK SHA-256")
    baseline_release = api.release(cfg["release_baseline"]["tag"])
    baseline_info = release_manifest(api, baseline_release,
                                    GitHub(cfg["upstream"]).sha(cfg["release_baseline"]["tag"]))
    if not baseline_info or baseline_info["apk_sha256"] != baseline:
        raise RuntimeError("The tested baseline APK does not match the stored release")
    api.request(f"releases/{release['id']}", "PATCH", {"draft": False, "make_latest": "legacy"})
    output("awaiting_device", "false")


def report(args):
    """Best effort notification; never change the result of the original CI stage."""
    try:
        api = GitHub()
        title = f"ARMv7 automation: {args.stage} failure"
        issues = list(api.pages("issues?state=open&labels=upstream-sync"))
        issue = next((i for i in issues if not i.get("pull_request") and i["title"] == title), None)
        if args.result == "success":
            if issue:
                api.request(f"issues/{issue['number']}", "PATCH", {"state": "closed"})
            return
        # REST endpoint corresponds to github.rest.issues.createLabel, not repos.createLabel.
        if not api.request("labels/upstream-sync"):
            api.request("labels", "POST", {"name": "upstream-sync", "color": "b60205"})
        run = f"https://github.com/{api.repository}/actions/runs/{os.getenv('GITHUB_RUN_ID', '')}"
        body = f"Stage: {args.stage}\nResult: {args.result}\nRun: {run}\n\nThe previous working version is retained. The next scheduled run retries unfinished work."
        if issue:
            api.request(f"issues/{issue['number']}", "PATCH", {"body": body})
        else:
            api.request("issues", "POST", {"title": title, "body": body, "labels": ["upstream-sync"]})
    except Exception as error:
        print(f"::warning::Could not update automation issue: {error}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan")
    p = commands.add_parser("prepare")
    p.add_argument("--upstream-sha", required=True)
    p.add_argument("--base-sha")
    p.add_argument("--tag", default="")
    p.add_argument("--target", required=True)
    p = commands.add_parser("advance")
    p.add_argument("--target", required=True)
    p.add_argument("--base-sha", required=True)
    p = commands.add_parser("persist")
    p.add_argument("--target", required=True)
    for command in ("status", "upload", "publish"):
        p = commands.add_parser(command)
        p.add_argument("--tag", required=True)
        p.add_argument("--upstream-sha", required=True)
        if command == "upload":
            p.add_argument("--directory", required=True)
    p = commands.add_parser("report")
    p.add_argument("--stage", required=True)
    p.add_argument("--result", required=True)
    args = parser.parse_args()
    globals()[args.command](args)


if __name__ == "__main__":
    main()
