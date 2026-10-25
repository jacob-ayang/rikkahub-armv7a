# ARMv7a native provenance

Native build inputs are pinned by immutable source URLs and SHA-256 in
`fork/native/sources.json`. `scripts/ci/build-native.py` verifies each archive before extraction,
compiles with Android NDK 29.0.14206865 and records binary hashes in native-build-info.json.
That record is included in every APK's build-info.json.

## SQLite tokenizer

- Source: wangfenjin/simple v0.6.1, commit ea854b0a727e9f15f4878ad0ae9f1b738a92afe4.
- armeabi-v7a, android-21, Release, static libc++, SIMPLE_WITH_JIEBA=OFF,
  BUILD_SQLITE3=OFF, BUILD_SHELL=OFF, BUILD_TEST_EXAMPLE=OFF.
- Matches the current upstream tokenizer configuration and SQLite extension API; database schema,
  migrations and search SQL follow upstream. No old unicode61 fallback patch is carried forward.
- Output: app/src/main/jniLibs/armeabi-v7a/libsimple.so.

## PRoot and dependencies

- Termux PRoot v5.1.107.101, commit b27d81a68d765f3462e807f4a14e01a03f8e89ea.
- talloc 2.4.3, statically linked; cross-configuration answers are versioned under fork/native.
- termux/libandroid-shmem commit 7f0bd7e25dbdd146265aff7c6a890029e374622d, statically linked.
- PRoot and the separate freestanding loader are built for ARMv7a, Android API 26. The app supplies
  PROOT_LOADER and PROOT_TMP_DIR; there is no Termux prefix dependency. The shmem key-file path
  uses PROOT_TMP_DIR instead of a hardcoded Termux path.
- Outputs: workspace/src/main/jniLibs/armeabi-v7a/libproot_exec.so and libproot_loader.so.
- PRoot sources carry GPL-2.0 licensing, talloc LGPL-3.0-or-later, and libandroid-shmem its upstream
  license. Locked source archives contain the corresponding license and source; preserve provenance
  and license notices when redistributing these components.

Terminal/workspace JNI libraries are built by their existing CMake projects. SQLite and QuickJS
native libraries are resolved with the app dependencies. Publication fails if any required ARMv7a
library is absent or has an unresolved dynamic dependency. Existing upstream 64-bit binaries are
retained as source but excluded from the ARMv7a APK.

```bash
ANDROID_HOME=/path/to/android-sdk python3 scripts/ci/build-native.py
```

Generated binaries are ignored by Git. Native source archives and tool versions must be reviewed
and their hashes updated deliberately, rather than following a moving native dependency tag.
