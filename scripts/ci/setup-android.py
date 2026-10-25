#!/usr/bin/env python3
"""Install pinned modern Android command-line tools, avoiding the retired tools package."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def main():
    cfg = json.loads((ROOT / "fork/config.json").read_text())
    sdk = Path(os.environ["RUNNER_TEMP"]) / "armv7-android-sdk"
    cli = sdk / "cmdline-tools/latest"
    if not cli.exists():
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "cmdline-tools.zip"
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(cfg["cmdline_tools"]["url"], timeout=120) as response, archive.open("wb") as out:
                        shutil.copyfileobj(response, out)
                    break
                except (OSError, TimeoutError):
                    if attempt == 3:
                        raise
                    time.sleep(2 ** attempt)
            with archive.open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != cfg["cmdline_tools"]["sha256"]:
                    raise RuntimeError("Android command-line tools checksum mismatch")
            cli.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["unzip", "-q", str(archive), "-d", str(cli.parent)], check=True)
            (cli.parent / "cmdline-tools").rename(cli)
    packages = ["platform-tools", "platforms;" + cfg["sdk_platform"], "platforms;android-37.0",
                "build-tools;" + cfg["build_tools"], "ndk;" + cfg["ndk"], "cmake;" + cfg["cmake"]]
    env = dict(os.environ, ANDROID_HOME=str(sdk), ANDROID_SDK_ROOT=str(sdk))
    manager = str(cli / "bin/sdkmanager")
    subprocess.run([manager, f"--sdk_root={sdk}", "--licenses"], input=b"y\n" * 100, env=env, check=True)
    subprocess.run([manager, f"--sdk_root={sdk}", *packages], input=b"y\n" * 100, env=env, check=True)
    with open(os.environ["GITHUB_ENV"], "a") as stream:
        stream.write(f"ANDROID_HOME={sdk}\nANDROID_SDK_ROOT={sdk}\n")
    with open(os.environ["GITHUB_PATH"], "a") as stream:
        stream.write(f"{cli / 'bin'}\n{sdk / 'platform-tools'}\n")


if __name__ == "__main__":
    main()
