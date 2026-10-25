#!/usr/bin/env python3
"""Deterministic, fail-closed adaptations of an otherwise pristine upstream tree."""
import argparse
import json
from pathlib import Path
import shutil


def replace_once(path, old, new):
    text = path.read_text()
    if new in text and old not in text:
        return
    if text.count(old) != 1:
        raise RuntimeError(f"Upstream structure changed: {path}: expected exactly one {old!r}")
    path.write_text(text.replace(old, new, 1))


def apply(root):
    config = json.loads((root / "fork/config.json").read_text())
    ignores = (root / "fork/gitignore").read_text()
    ignore_file = root / ".gitignore"
    if ignores.strip() not in ignore_file.read_text():
        ignore_file.write_text(ignore_file.read_text().rstrip() + "\n" + ignores)
    properties = root / "gradle.properties"
    test_setting = "android.onlyEnableUnitTestForTheTestedBuildType=false"
    if test_setting not in properties.read_text():
        if "android.onlyEnableUnitTestForTheTestedBuildType=" in properties.read_text():
            raise RuntimeError("Upstream unit-test variant policy changed")
        properties.write_text(properties.read_text().rstrip() + "\n\n# Validate the signed release variant, too.\n" + test_setting + "\n")
    app = root / "app/build.gradle.kts"
    source = app.read_text()
    if 'create("armv7")' in source or 'create("universal")' in source:
        raise RuntimeError("Expected pristine upstream Gradle configuration, not the old fork flavors")
    marker = 'apply(from = rootProject.file("fork/armv7.gradle"))'
    if marker not in source:
        app.write_text(source.rstrip() + "\n\n" + marker + "\n")
    root_build = root / "build.gradle.kts"
    marker = 'apply(from = rootProject.file("fork/armv7-libraries.gradle"))'
    if marker not in root_build.read_text():
        root_build.write_text(root_build.read_text().rstrip() + "\n\n" + marker + "\n")

    updater = root / "app/src/main/java/me/rerere/rikkahub/utils/UpdateChecker.kt"
    replace_once(updater, 'https://updates.rikka-ai.com/',
                 f'https://api.github.com/repos/{config["repository"]}/releases?per_page=100')
    # Release responses must be closed on both the success and error paths.
    replace_once(updater, 'if (response.isSuccessful) {\n                        json.decodeFromString<UpdateInfo>(response.body.string())\n                    } else {\n                        throw Exception("Failed to fetch update info")\n                    }',
                 'response.use {\n                        if (it.isSuccessful) {\n                            Armv7Updates.decode(it.body.string())\n                        } else {\n                            throw Exception("Failed to fetch update info: HTTP ${it.code}")\n                        }\n                    }')

    page = root / "app/src/main/java/me/rerere/rikkahub/ui/pages/extensions/workspace/WorkspaceDetailPage.kt"
    replace_once(page, 'ubuntu-base-24.04.3-base-arm64.tar.gz', 'ubuntu-base-24.04.3-base-armhf.tar.gz')
    installer = root / "workspace/src/main/java/me/rerere/workspace/RootfsInstaller.kt"
    replace_once(installer, 'extractTar(archive, stagingDir, format, onProgress)\n            linuxDir.deleteRecursively()',
                 'extractTar(archive, stagingDir, format, onProgress)\n            Armv7Rootfs.validate(stagingDir)\n            linuxDir.deleteRecursively()')
    templates = {
        "Armv7Updates.kt": "app/src/main/java/me/rerere/rikkahub/utils/Armv7Updates.kt",
        "Armv7Rootfs.kt": "workspace/src/main/java/me/rerere/workspace/Armv7Rootfs.kt",
        "Armv7UpdatesTest.kt": "app/src/test/java/me/rerere/rikkahub/utils/Armv7UpdatesTest.kt",
        "Armv7RootfsTest.kt": "workspace/src/test/java/me/rerere/workspace/Armv7RootfsTest.kt",
    }
    for template, destination in templates.items():
        target = root / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / "fork/templates" / template, target)
    # Never carry upstream schedules or issue-management automation into this fork.
    allowed = {"sync-upstream.yml", "release.yml"}
    for path in (root / ".github/workflows").glob("*"):
        if path.name not in allowed:
            path.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path.cwd())
    apply(parser.parse_args().root.resolve())
