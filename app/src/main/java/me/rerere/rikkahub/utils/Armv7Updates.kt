package me.rerere.rikkahub.utils

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull

/** Only public, complete ARMv7a releases from this fork are installable updates. */
internal object Armv7Updates {
    fun decode(payload: String): UpdateInfo {
        val releases = Json.parseToJsonElement(payload) as? JsonArray
            ?: error("Invalid GitHub releases response")
        return releases.mapNotNull { it as? JsonObject }
            .filter { !it.flag("draft") && !it.flag("prerelease") }
            .sortedByDescending { it.text("published_at") }
            .firstNotNullOfOrNull { release ->
                val assets = release["assets"] as? JsonArray ?: return@firstNotNullOfOrNull null
                val files = assets.mapNotNull { it as? JsonObject }
                val apk = files.singleOrNull {
                    it.text("name").matches(Regex("rikkahub-.+-armv7a-[0-9a-f]{7,40}\\.apk")) &&
                        it["size"]?.jsonPrimitive?.longOrNull?.let { size -> size > 0 } == true
                } ?: return@firstNotNullOfOrNull null
                if (files.none { it.text("name") == "SHA256SUMS" } ||
                    files.none { it.text("name") == "build-info.json" }
                ) return@firstNotNullOfOrNull null
                val url = apk.text("browser_download_url")
                if (!url.startsWith("https://github.com/jacob-ayang/rikkahub-armv7a/releases/download/")) {
                    return@firstNotNullOfOrNull null
                }
                UpdateInfo(
                    version = release.text("tag_name").removePrefix("v"),
                    publishedAt = release.text("published_at"),
                    changelog = release.text("body"),
                    downloads = listOf(
                        UpdateDownload(
                            name = apk.text("name"),
                            url = url,
                            size = "${apk["size"]!!.jsonPrimitive.longOrNull!! / 1024 / 1024} MB",
                        )
                    ),
                )
            } ?: error("No complete ARMv7a release is available")
    }

    private fun JsonObject.text(key: String) = this[key]?.jsonPrimitive?.contentOrNull.orEmpty()
    private fun JsonObject.flag(key: String) = this[key]?.jsonPrimitive?.booleanOrNull != false
}
