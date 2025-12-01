package com.example.iot_nha_thong_minh.data.local

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey
import com.example.iot_nha_thong_minh.data.model.FireAlert

@Entity(tableName = "fire_alerts")
data class FireAlertEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    @ColumnInfo(name = "message")
    val message: String,
    @ColumnInfo(name = "confidence")
    val confidence: Double?,
    @ColumnInfo(name = "fire_regions")
    val fireRegions: Int?,
    @ColumnInfo(name = "fire_percentage")
    val firePercentage: Double?,
    @ColumnInfo(name = "total_fire_area")
    val totalFireArea: Int?,
    @ColumnInfo(name = "triggered_at")
    val triggeredAt: String?,
    @ColumnInfo(name = "timestamp_millis")
    val timestampMillis: Long,
    @ColumnInfo(name = "is_acknowledged")
    val isAcknowledged: Boolean = false,
) {
    fun toDomain(): FireAlert = FireAlert(
        id = id,
        message = message,
        confidence = confidence,
        fireRegions = fireRegions,
        firePercentage = firePercentage,
        totalFireArea = totalFireArea,
        triggeredAt = triggeredAt,
        timestampMillis = timestampMillis,
        isAcknowledged = isAcknowledged,
    )

    companion object {
        fun fromDomain(alert: FireAlert): FireAlertEntity = FireAlertEntity(
            id = if (alert.id > 0) alert.id else 0,
            message = alert.message,
            confidence = alert.confidence,
            fireRegions = alert.fireRegions,
            firePercentage = alert.firePercentage,
            totalFireArea = alert.totalFireArea,
            triggeredAt = alert.triggeredAt,
            timestampMillis = alert.timestampMillis,
            isAcknowledged = alert.isAcknowledged,
        )
    }
}
