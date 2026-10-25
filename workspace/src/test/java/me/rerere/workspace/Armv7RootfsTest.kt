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
            val elf = ByteArray(20)
            elf[0] = 0x7f
            elf[1] = 'E'.code.toByte()
            elf[2] = 'L'.code.toByte()
            elf[3] = 'F'.code.toByte()
            elf[4] = 1
            elf[5] = 1
            elf[18] = 40
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
