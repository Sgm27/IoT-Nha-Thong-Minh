package com.example.iot_nha_thong_minh.data

import com.example.iot_nha_thong_minh.BuildConfig

object EnvironmentConfig {
    val apiBaseUrl: String
        get() = ensureTrailingSlash(BuildConfig.API_BASE_URL)

    val wsBaseUrl: String
        get() = BuildConfig.WS_BASE_URL.trimEnd('/')

    val geminiWsUrl: String
        get() = BuildConfig.GEMINI_WS_URL.ifBlank { "${wsBaseUrl}/ws/gemini" }

    private fun ensureTrailingSlash(value: String): String =
        if (value.endsWith('/')) value else "$value/"
}
