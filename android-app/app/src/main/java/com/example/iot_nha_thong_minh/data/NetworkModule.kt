package com.example.iot_nha_thong_minh.data

import android.content.Context
import com.example.iot_nha_thong_minh.data.local.ChatDatabase
import com.example.iot_nha_thong_minh.data.remote.SmartHomeApi
import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit

object NetworkModule {
    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BASIC
    }

    val json: Json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        coerceInputValues = true
    }

    val okHttpClient: OkHttpClient = OkHttpClient.Builder()
        .pingInterval(15, TimeUnit.SECONDS)
        .addInterceptor(loggingInterceptor)
        .build()

    @OptIn(ExperimentalSerializationApi::class)
    private val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl(EnvironmentConfig.apiBaseUrl)
        .client(okHttpClient)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()

    val api: SmartHomeApi = retrofit.create(SmartHomeApi::class.java)

    private var database: ChatDatabase? = null

    fun initialize(context: Context) {
        if (database == null) {
            database = ChatDatabase.getInstance(context)
        }
    }

    val repository: SmartHomeRepository by lazy {
        val db = database
        SmartHomeRepository(
            api = api,
            okHttpClient = okHttpClient,
            json = json,
            chatMessageDao = db?.chatMessageDao(),
            fireAlertDao = db?.fireAlertDao(),
        )
    }
}
