package com.example.iot_nha_thong_minh.data.local

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey
import com.example.iot_nha_thong_minh.data.model.ChatMessage
import com.example.iot_nha_thong_minh.data.model.ChatRole

@Entity(tableName = "chat_messages")
data class ChatMessageEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    @ColumnInfo(name = "role")
    val role: String,
    @ColumnInfo(name = "content")
    val content: String,
    @ColumnInfo(name = "timestamp_millis")
    val timestampMillis: Long,
    @ColumnInfo(name = "is_streaming")
    val isStreaming: Boolean = false,
    @ColumnInfo(name = "image_data", typeAffinity = ColumnInfo.BLOB)
    val imageData: ByteArray? = null,
    @ColumnInfo(name = "image_mime_type")
    val imageMimeType: String? = null,
) {
    fun toDomain(): ChatMessage = ChatMessage(
        id = id,
        role = ChatRole.valueOf(role),
        content = content,
        timestampMillis = timestampMillis,
        isStreaming = isStreaming,
        imageData = imageData,
        imageMimeType = imageMimeType,
    )

    companion object {
        fun fromDomain(message: ChatMessage): ChatMessageEntity = ChatMessageEntity(
            id = if (message.id > 0) message.id else 0,
            role = message.role.name,
            content = message.content,
            timestampMillis = message.timestampMillis,
            isStreaming = message.isStreaming,
            imageData = message.imageData,
            imageMimeType = message.imageMimeType,
        )
    }
}
