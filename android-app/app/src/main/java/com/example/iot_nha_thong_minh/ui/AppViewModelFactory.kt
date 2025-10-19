package com.example.iot_nha_thong_minh.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.example.iot_nha_thong_minh.data.SmartHomeRepository
import com.example.iot_nha_thong_minh.ui.chat.ChatViewModel
import com.example.iot_nha_thong_minh.ui.lights.LightsViewModel
import com.example.iot_nha_thong_minh.ui.music.MusicViewModel

class AppViewModelFactory(private val repository: SmartHomeRepository) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T = when {
        modelClass.isAssignableFrom(ChatViewModel::class.java) -> ChatViewModel(repository) as T
        modelClass.isAssignableFrom(LightsViewModel::class.java) -> LightsViewModel(repository) as T
        modelClass.isAssignableFrom(MusicViewModel::class.java) -> MusicViewModel(repository) as T
        else -> throw IllegalArgumentException("Unknown ViewModel class ${modelClass.simpleName}")
    }
}
