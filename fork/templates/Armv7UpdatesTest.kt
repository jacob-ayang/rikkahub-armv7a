package me.rerere.rikkahub.utils

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class Armv7UpdatesTest {
    private fun release(tag: String, extra: String = "", assets: String = "") = """
        {"tag_name":"$tag","published_at":"2026-10-24T12:00:00Z","body":"Changes",
        "draft":false,"prerelease":false$extra,"assets":[
        {"name":"rikkahub-$tag-armv7a-123abcd.apk","size":123,
        "browser_download_url":"https://github.com/jacob-ayang/rikkahub-armv7a/releases/download/$tag/app.apk"},
        {"name":"SHA256SUMS"},{"name":"build-info.json"}$assets]}
    """.trimIndent()

    @Test fun selectsOnlyCompatibleFormalRelease() {
        val draft = release("3.2.0").replace("\"draft\":false", "\"draft\":true")
        val preview = release("3.3.0").replace("\"prerelease\":false", "\"prerelease\":true")
        val info = Armv7Updates.decode("[$draft,$preview,${release("3.1.1")}]")
        assertEquals("3.1.1", info.version)
        assertEquals(1, info.downloads.size)
    }

    @Test fun rejectsMissingOrAmbiguousAssets() {
        val incomplete = release("3.1.1").replace("SHA256SUMS", "unrelated.txt")
        assertThrows(IllegalStateException::class.java) { Armv7Updates.decode("[$incomplete]") }
        val ambiguous = release("3.1.1", assets = "," + """
            {"name":"rikkahub-3.1.1-armv7a-7654321.apk","size":20}
        """.trimIndent())
        assertThrows(IllegalStateException::class.java) { Armv7Updates.decode("[$ambiguous]") }
    }

    @Test fun rejectsUpstreamAndNonArmApks() {
        val foreign = release("3.1.1").replace("jacob-ayang/rikkahub-armv7a", "rikkahub/rikkahub")
        val arm64 = release("3.1.1").replace("-armv7a-", "-arm64-")
        assertThrows(IllegalStateException::class.java) { Armv7Updates.decode("[$foreign,$arm64]") }
    }
}
