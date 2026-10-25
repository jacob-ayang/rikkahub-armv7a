#!/usr/bin/env python3
"""Build the ARMv7a native overlay from checksum-locked source archives."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def run(*args, cwd=None, env=None):
    subprocess.run([str(arg) for arg in args], cwd=cwd, env=env, check=True)


def fetch(name, entry, cache):
    archive = cache / (name + ".tar.gz")
    if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest() != entry["sha256"]:
        for attempt in range(4):
            try:
                with urllib.request.urlopen(entry["url"], timeout=120) as response:
                    archive.write_bytes(response.read())
                break
            except (OSError, TimeoutError):
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != entry["sha256"]:
        raise RuntimeError(f"Source checksum mismatch: {name}")
    target = cache / name
    if target.exists():
        shutil.rmtree(target)
    target.mkdir()
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            parts = member.name.split("/", 1)
            if len(parts) != 2 or not parts[1]:
                continue
            member.name = parts[1]
            tar.extract(member, target, filter="data")
    return target


def main():
    cfg = json.loads((ROOT / "fork/config.json").read_text())
    lock = json.loads((ROOT / "fork/native/sources.json").read_text())
    page = ROOT / "app/src/main/java/me/rerere/rikkahub/ui/pages/extensions/workspace/WorkspaceDetailPage.kt"
    rootfs_url = re.search(r'https://cdimage\.ubuntu\.com/ubuntu-base/[^"\s]+-armhf\.tar\.gz', page.read_text())[0]
    # Do not publish a default Linux installer URL that has no 32-bit image.
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(rootfs_url, method="HEAD"), timeout=60):
                break
        except (OSError, TimeoutError):
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    sdk = Path(os.environ["ANDROID_HOME"])
    ndk = sdk / "ndk" / cfg["ndk"]
    tools = ndk / "toolchains/llvm/prebuilt/linux-x86_64/bin"
    cc = tools / "armv7a-linux-androideabi26-clang"
    ar = tools / "llvm-ar"
    cmake = sdk / "cmake" / cfg["cmake"] / "bin/cmake"
    cache = Path(os.getenv("ARMV7_NATIVE_CACHE", str(ROOT / ".native-build")))
    cache.mkdir(parents=True, exist_ok=True)
    sources = {name: fetch(name, entry, cache) for name, entry in lock.items()}
    prefix = cache / "prefix"
    (prefix / "lib").mkdir(parents=True, exist_ok=True)
    (prefix / "include").mkdir(exist_ok=True)
    env = dict(os.environ, CC=str(cc), AR=str(ar), RANLIB=str(tools / "llvm-ranlib"),
               CFLAGS=f"-O2 -fPIC -ffile-prefix-map={cache}=native", LDFLAGS="")
    talloc = sources["talloc"]
    shutil.copyfile(ROOT / "fork/native/talloc-cross-answers.txt", talloc / "cross-answers.txt")
    run("./configure", f"--prefix={prefix}", "--disable-rpath", "--disable-python",
        "--cross-compile", "--cross-answers=cross-answers.txt", cwd=talloc, env=env)
    run("make", "-j2", cwd=talloc, env=env)
    objects = list((talloc / "bin/default").glob("talloc*.o"))
    if not objects:
        raise RuntimeError("No talloc objects were built")
    run(ar, "rcs", prefix / "lib/libtalloc.a", *objects)
    shutil.copyfile(talloc / "talloc.h", prefix / "include/talloc.h")

    shmem = sources["android-shmem"]
    # Termux normally supplies _PATH_TMP at build time. Use the caller's private
    # PRoot temporary directory instead of a hardcoded Termux installation path.
    shmem_source = shmem / "shmem.c"
    text = shmem_source.read_text()
    text = text.replace('_PATH_TMP "ashv_key_%d"', '"%s/ashv_key_%d"')
    text = text.replace('sprintf(symlink_path, ASHV_KEY_SYMLINK_PATH, key);',
                        'snprintf(symlink_path, sizeof(symlink_path), ASHV_KEY_SYMLINK_PATH, '
                        'getenv("PROOT_TMP_DIR") ? getenv("PROOT_TMP_DIR") : ".", key);')
    shmem_source.write_text(text)
    run(cc, "-O2", "-fPIC", "-I" + str(shmem), "-c", shmem / "shmem.c", "-o", shmem / "shmem.o")
    run(ar, "rcs", prefix / "lib/libandroid-shmem.a", shmem / "shmem.o")
    (prefix / "include/sys").mkdir(exist_ok=True)
    shutil.copyfile(shmem / "shm.h", prefix / "include/sys/shm.h")

    proot = sources["proot"] / "src"
    # NDK r29 no longer supplies these declarations through transitive includes.
    ashmem = proot / "extension/ashmem_memfd/ashmem_memfd.c"
    ashmem.write_text('#include <string.h>\n' + ashmem.read_text())
    run("make", "-j2", "V=1", f"CC={cc}", f"LD={cc}", f"STRIP={tools / 'llvm-strip'}",
        f"OBJCOPY={tools / 'llvm-objcopy'}", f"OBJDUMP={tools / 'llvm-objdump'}",
        "PROOT_WITH_LIBANDROID_SHMEM=true", "PROOT_UNBUNDLE_LOADER=/unused",
        f"CPPFLAGS=-D_GNU_SOURCE -D_FILE_OFFSET_BITS=64 -DWITH_LIBANDROID_SHMEM -DARG_MAX=131072 -DVERSION=\\\"5.1.107.101\\\" -I{prefix / 'include'} -I. -I{proot}",
        'CFLAGS=-O2 -fPIE -DPROOT_UNBUNDLE_LOADER=\\\"/unused\\\"',
        f"LDFLAGS=-L{prefix / 'lib'} -Wl,-Bstatic -ltalloc -landroid-shmem -Wl,-Bdynamic -llog -landroid -pie",
        cwd=proot, env=env)
    workspace = ROOT / "workspace/src/main/jniLibs/armeabi-v7a"
    workspace.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(proot / "proot", workspace / "libproot_exec.so")
    shutil.copyfile(proot / "loader/loader", workspace / "libproot_loader.so")

    simple_build = cache / "simple-build"
    run(cmake, "-S", sources["simple"], "-B", simple_build,
        f"-DCMAKE_TOOLCHAIN_FILE={ndk / 'build/cmake/android.toolchain.cmake'}",
        "-DANDROID_ABI=armeabi-v7a", "-DANDROID_PLATFORM=android-21", "-DANDROID_STL=c++_static",
        "-DCMAKE_BUILD_TYPE=Release", "-DSIMPLE_WITH_JIEBA=OFF", "-DBUILD_TEST_EXAMPLE=OFF",
        "-DBUILD_SHELL=OFF", "-DBUILD_SQLITE3=OFF", f"-DCMAKE_CXX_FLAGS=-ffile-prefix-map={cache}=native")
    run(cmake, "--build", simple_build, "--parallel", "2")
    libraries = list(simple_build.rglob("libsimple.so"))
    if len(libraries) != 1:
        raise RuntimeError("Expected exactly one libsimple.so")
    app = ROOT / "app/src/main/jniLibs/armeabi-v7a"
    app.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(libraries[0], app / "libsimple.so")
    for path in (*workspace.glob("*.so"), app / "libsimple.so"):
        run(tools / "llvm-strip", "--strip-unneeded", path)
        path.chmod(0o755)
    manifest = {"ndk": cfg["ndk"], "sources": lock, "rootfs_url": rootfs_url,
                "outputs": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in (*workspace.glob("*.so"), app / "libsimple.so")}}
    (ROOT / "native-build-info.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
