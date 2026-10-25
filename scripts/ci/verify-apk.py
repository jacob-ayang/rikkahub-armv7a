#!/usr/bin/env python3
"""Check installability, native dependency closure and signing continuity before upload."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SYSTEM_LIBS = {"libc.so", "libm.so", "libdl.so", "liblog.so", "libandroid.so", "libz.so",
               "libjnigraphics.so", "libGLESv2.so", "libGLESv3.so", "libEGL.so", "libOpenSLES.so",
               "libmediandk.so", "libvulkan.so", "libaaudio.so", "libstdc++.so"}


def run(*args):
    return subprocess.check_output([str(a) for a in args], text=True, stderr=subprocess.STDOUT).strip()


def certificate(apksigner, apk):
    result = run(apksigner, "verify", "--verbose", "--print-certs", apk)
    signer_count = re.search(r"(?m)^Number of signers:\s*(\d+)\s*$", result)
    if signer_count and int(signer_count[1]) != 1:
        raise RuntimeError("APK must have exactly one verified signing certificate")
    # Build-tools 37 labels signing schemes (V2 Signer, V3.1 Signer) instead
    # of Signer #1. The same identity can be listed once per signing scheme.
    certs = {value.lower() for value in re.findall(
        r"(?m)^(?:Signer #\d+|V[\d.]+ Signer(?: #\d+)?):? certificate SHA-256 digest: ([0-9a-fA-F]{64})\s*$",
        result,
    )}
    if len(certs) != 1:
        raise RuntimeError("APK must have exactly one verified signing certificate")
    return certs.pop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default="")
    parser.add_argument("--output", default="build-output")
    args = parser.parse_args()
    cfg = json.loads((ROOT / "fork/config.json").read_text())
    sdk = Path(os.environ["ANDROID_HOME"])
    tools = sdk / "build-tools" / cfg["build_tools"]
    readelf = sdk / "ndk" / cfg["ndk"] / "toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf"
    apks = list((ROOT / "app/build/outputs/apk/github/release").glob("*.apk"))
    if len(apks) != 1:
        raise RuntimeError(f"Expected one GitHub ARMv7 APK, found {len(apks)}")
    apk = apks[0]
    badging = run(tools / "aapt", "dump", "badging", apk)
    package = re.search(r"package: name='([^']+)' versionCode='([0-9]+)' versionName='([^']+)'", badging)
    if not package or package[1] != "me.rerere.rikkahub":
        raise RuntimeError("Unexpected APK package metadata")
    version_code, version_name = int(package[2]), package[3]
    if args.tag and args.tag.removeprefix("v") != version_name:
        raise RuntimeError("APK versionName differs from the exact upstream release tag")
    min_sdk = int(re.search(r"sdkVersion:'([0-9]+)'", badging)[1])
    expected_min = int(re.search(r"minSdk\s*=\s*(\d+)", (ROOT / "app/build.gradle.kts").read_text())[1])
    if min_sdk != expected_min:
        raise RuntimeError("APK minimum SDK differs from upstream")
    with zipfile.ZipFile(apk) as archive, tempfile.TemporaryDirectory() as temporary:
        entries = [name for name in archive.namelist() if name.startswith("lib/") and name.endswith(".so")]
        if not entries or any(not name.startswith("lib/armeabi-v7a/") for name in entries):
            raise RuntimeError("APK contains missing or non-ARMv7 native code")
        names = {Path(name).name for name in entries}
        for required in ("libsimple.so", "libtermux.so", "libworkspace.so", "libproot_exec.so", "libproot_loader.so"):
            if required not in names:
                raise RuntimeError(f"Required native library missing: {required}")
        for pattern in ("sqlite", "quickjs"):
            if not any(pattern in name.lower() for name in names):
                raise RuntimeError(f"Required native dependency missing: {pattern}")
        for name in entries:
            path = Path(archive.extract(name, temporary))
            header = run(readelf, "-h", path)
            if not re.search(r"Class:\s+ELF32", header) or not re.search(r"Machine:\s+ARM", header):
                raise RuntimeError(f"Incorrect ELF architecture: {name}")
            dynamic = run(readelf, "-d", path)
            needed = set(re.findall(r"Shared library: \[([^]]+)\]", dynamic))
            missing = needed - names - SYSTEM_LIBS
            if missing:
                raise RuntimeError(f"Unresolved native dependencies in {name}: {sorted(missing)}")
            if "RUNPATH" in dynamic or "RPATH" in dynamic:
                raise RuntimeError(f"Unexpected native search path in {name}")
            if name.endswith("/libsimple.so"):
                symbols = run(readelf, "--dyn-syms", "--wide", path)
                if "sqlite3_simple_init" not in symbols or "fts5_simple_xCreate" not in symbols:
                    raise RuntimeError("libsimple tokenizer exports are missing")
    cert = certificate(tools / "apksigner", apk)
    with tempfile.TemporaryDirectory() as temporary:
        previous = Path(temporary) / "previous.apk"
        # gh strips credentials on CDN redirects and also supports draft releases.
        releases = json.loads(run("gh", "api", f"repos/{cfg['repository']}/releases/tags/{cfg['previous_signed_release']}"))
        asset = next(a for a in releases["assets"] if "armv7a" in a["name"] and a["name"].endswith(".apk"))
        with previous.open("wb") as stream:
            subprocess.run(["gh", "api", f"repos/{cfg['repository']}/releases/assets/{asset['id']}",
                            "-H", "Accept: application/octet-stream"], stdout=stream, check=True)
        if certificate(tools / "apksigner", previous) != cert:
            raise RuntimeError("Signing certificate changed: existing installations cannot be upgraded")
        old_badging = run(tools / "aapt", "dump", "badging", previous)
        old_code = int(re.search(r"versionCode='([0-9]+)'", old_badging)[1])
        if version_code <= old_code:
            raise RuntimeError("versionCode must increase from the previous signed release")
    state = json.loads((ROOT / ".fork-state.json").read_text())
    sha = run("git", "rev-parse", "HEAD")
    output = ROOT / args.output
    output.mkdir(exist_ok=True)
    name = f"rikkahub-{version_name}-armv7a-{sha[:12]}.apk"
    shutil.copyfile(apk, output / name)
    apk_hash = hashlib.sha256(apk.read_bytes()).hexdigest()
    manifest = {"schema": 1, "tag": args.tag, "version_name": version_name, "version_code": version_code,
                "min_sdk": min_sdk, "abi": "armeabi-v7a", "upstream_sha": state["upstream_sha"],
                "source_sha": sha, "control_sha": state["control_sha"], "overlay_sha256": state["overlay_sha256"],
                "build_overlay_sha256": state["build_overlay_sha256"],
                "apk": name, "apk_size": apk.stat().st_size, "apk_sha256": apk_hash,
                "certificate_sha256": cert,
                "native": json.loads((ROOT / "native-build-info.json").read_text())}
    info = output / "build-info.json"
    info.write_text(json.dumps(manifest, indent=2) + "\n")
    info_hash = hashlib.sha256(info.read_bytes()).hexdigest()
    (output / "SHA256SUMS").write_text(f"{apk_hash}  {name}\n{info_hash}  build-info.json\n")
    print(json.dumps({"apk": name, "apk_sha256": apk_hash, "certificate_sha256": cert}))


if __name__ == "__main__":
    main()
