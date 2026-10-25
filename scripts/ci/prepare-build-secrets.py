#!/usr/bin/env python3
"""Decode existing CI secrets without interpolating their contents into shell code."""
import base64
import json
import os
from pathlib import Path


def prepare(root):
    names = ("KEY_BASE64", "SIGNING_CONFIG_B64", "GOOGLE_SERVICES_JSON_B64")
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Missing required secrets: " + ", ".join(missing))
    key, signing, firebase = (base64.b64decode(os.environ[name], validate=True) for name in names)
    properties = signing.decode().rstrip() + "\n"
    values = dict(line.split("=", 1) for line in properties.splitlines()
                  if "=" in line and not line.lstrip().startswith(("#", "!")))
    if not all(values.get(name) for name in ("storePassword", "keyAlias", "keyPassword")):
        raise RuntimeError("Signing configuration lacks storePassword, keyAlias or keyPassword")
    # Always use the decoded key at a predictable root-relative path. Old secret
    # configurations sometimes point at app/app.key or an absolute local path.
    properties = "\n".join(line for line in properties.splitlines()
                           if line.split("=", 1)[0].strip() not in ("storeFile", "sdk.dir", "ndk.dir"))
    properties += "\nstoreFile=rikkahub.keystore\n"
    services = json.loads(firebase)
    if not any(c.get("client_info", {}).get("android_client_info", {}).get("package_name") ==
               "me.rerere.rikkahub" for c in services.get("client", [])):
        raise RuntimeError("Firebase configuration has no client for me.rerere.rikkahub")
    for path, content in ((root / "rikkahub.keystore", key), (root / "local.properties", properties.encode()),
                          (root / "app/google-services.json", firebase)):
        path.write_bytes(content)
        path.chmod(0o600)


if __name__ == "__main__":
    prepare(Path.cwd())
