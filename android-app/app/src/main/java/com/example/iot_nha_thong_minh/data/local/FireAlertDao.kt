package com.example.iot_nha_thong_minh.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

@Dao
interface FireAlertDao {
    @Query("SELECT * FROM fire_alerts ORDER BY timestamp_millis DESC LIMIT :limit")
    fun getRecentAlerts(limit: Int = 100): Flow<List<FireAlertEntity>>

    @Query("SELECT * FROM fire_alerts ORDER BY timestamp_millis DESC")
    suspend fun getAllAlerts(): List<FireAlertEntity>

    @Query("SELECT COUNT(*) FROM fire_alerts WHERE is_acknowledged = 0")
    fun getUnacknowledgedCount(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAlert(alert: FireAlertEntity): Long

    @Update
    suspend fun updateAlert(alert: FireAlertEntity)

    @Query("UPDATE fire_alerts SET is_acknowledged = 1 WHERE id = :alertId")
    suspend fun acknowledgeAlert(alertId: Long)

    @Query("UPDATE fire_alerts SET is_acknowledged = 1")
    suspend fun acknowledgeAllAlerts()

    @Query("DELETE FROM fire_alerts WHERE id = :alertId")
    suspend fun deleteAlert(alertId: Long)

    @Query("DELETE FROM fire_alerts")
    suspend fun clearAllAlerts()
}
