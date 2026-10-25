package me.rerere.workspace

import java.io.DataInputStream
import java.io.File

/** Validate the extracted guest, before replacing an existing working rootfs. */
internal object Armv7Rootfs {
    fun validate(root: File) {
        val candidates = listOf(
            "usr/bin/bash", "bin/bash", "usr/bin/dash", "bin/dash", "bin/busybox", "usr/bin/busybox",
        )
        val binary = candidates.map { File(root, it) }
            .firstOrNull { it.isFile && !java.nio.file.Files.isSymbolicLink(it.toPath()) }
            ?: error("Rootfs has no supported shell executable")
        val header = ByteArray(20)
        DataInputStream(binary.inputStream()).use { it.readFully(header) }
        require(
            header[0] == 0x7f.toByte() && header[1] == 'E'.code.toByte() &&
                header[2] == 'L'.code.toByte() && header[3] == 'F'.code.toByte() &&
                header[4] == 1.toByte() && header[5] == 1.toByte() &&
                header[18] == 40.toByte() && header[19] == 0.toByte()
        ) { "This ARMv7a build requires a 32-bit ARM (armhf) rootfs" }
    }
}
