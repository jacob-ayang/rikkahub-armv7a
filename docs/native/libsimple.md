# libsimple.so provenance

This project uses `libsimple.so` from `wangfenjin/simple` `v0.6.0`.

## Source baseline

- Upstream repo: `https://github.com/wangfenjin/simple`
- Tag: `v0.6.0`
- Commit: `da0fd57cfac0194e2f949c975d535383c635919f`
- Android NDK: `r29` (`android-ndk-r29-linux.zip`, package `ndk;29.0.14206865`)

## Build command (armeabi-v7a)

```bash
python3 -m venv /tmp/cmake-venv
/tmp/cmake-venv/bin/pip install cmake ninja

curl -L --fail -o /path/android-ndk-r29-linux.zip \
  https://dl.google.com/android/repository/android-ndk-r29-linux.zip
unzip -q /path/android-ndk-r29-linux.zip -d /path

git clone --branch v0.6.0 --depth 1 https://github.com/wangfenjin/simple.git
cd simple

export PATH="/tmp/cmake-venv/bin:$PATH"
NDK=/path/android-ndk-r29

cmake -S . -B build-android-armeabi-v7a -G Ninja \
  -DCMAKE_MAKE_PROGRAM=ninja \
  -DCMAKE_TOOLCHAIN_FILE="$NDK/build/cmake/android.toolchain.cmake" \
  -DANDROID_ABI=armeabi-v7a \
  -DANDROID_PLATFORM=android-21 \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PWD/output-android-armeabi-v7a" \
  -DBUILD_TEST_EXAMPLE=OFF \
  -DBUILD_SHELL=OFF

cmake --build build-android-armeabi-v7a --config Release --parallel
cmake --install build-android-armeabi-v7a --config Release
```

Copy output:

```bash
cp output-android-armeabi-v7a/bin/libsimple.so \
  app/src/main/jniLibs/armeabi-v7a/libsimple.so
```

## SHA-256

- `app/src/main/jniLibs/arm64-v8a/libsimple.so`
  - `c6f8944d9dfed48caef04a342fcab87c5ebb7ab7bdeb7b5a8bb5e38689ccb5b8`
- `app/src/main/jniLibs/x86_64/libsimple.so`
  - `c14959df728630ae391c081106056b5c2ee2dead3abe0a98ec794e9fa7c778e9`
- `app/src/main/jniLibs/armeabi-v7a/libsimple.so`
  - `253692506d8788f09b941d64f5a92ea8befe9e178acc8c8e23df25ea4a18cf62`
