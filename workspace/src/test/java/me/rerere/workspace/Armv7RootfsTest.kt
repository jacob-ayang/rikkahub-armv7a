package me.rerere.workspace

import java.nio.file.Files
import org.junit.Assert.assertThrows
import org.junit.Test

class Armv7RootfsTest {
    @Test fun acceptsArmAndRejectsArm64BeforeReplacingRootfs() {
        val root = Files.createTempDirectory("rootfs-abi").toFile()
        try {
            val binary = root.resolve("usr/bin/bash")
            binary.parentFile.mkdirs()
            val elf = armv7TestShellElf()
            binary.writeBytes(elf)
            Armv7Rootfs.validate(root)
            elf[4] = 2
            elf[18] = 183.toByte()
            binary.writeBytes(elf)
            assertThrows(IllegalArgumentException::class.java) { Armv7Rootfs.validate(root) }
        } finally {
            root.deleteRecursively()
        }
    }
}

internal fun armv7TestShellElf() = ByteArray(20).apply {
    this[0] = 0x7f
    this[1] = 'E'.code.toByte()
    this[2] = 'L'.code.toByte()
    this[3] = 'F'.code.toByte()
    this[4] = 1
    this[5] = 1
    this[18] = 40
}
