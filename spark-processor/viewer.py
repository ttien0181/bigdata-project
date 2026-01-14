# -*- coding: utf-8 -*-
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, max, min, count, col, from_unixtime, desc, round

spark = SparkSession.builder \
    .appName("AirQualityViewer") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

hdfs_path = "hdfs://namenode:9000/data/air_quality_v2/"

print("\n" + "="*60)
print("   BÁO CÁO CHẤT LƯỢNG KHÔNG KHÍ (DATA REPORT)")
print("="*60)

try:
    df = spark.read.parquet(hdfs_path)
    
    df.cache()
    
    total_records = df.count()
    print(f"\n[INFO] Tổng số bản ghi đã thu thập: {total_records}")

    if total_records > 0:
        print("\n>>> 1. 5 Bản ghi mới nhất:")
        df.select(
            from_unixtime(col("timestamp_unix")).alias("thoi_gian"),
            "latitude", "longitude", "aqi", "pm2_5", "co"
        ).orderBy(desc("timestamp_unix")).show(5, truncate=False)

        print("\n>>> 2. Bảng xếp hạng ô nhiễm theo địa điểm (Group By):")
        stats_df = df.groupBy("latitude", "longitude") \
            .agg(
                count("*").alias("so_lan_do"),
                round(avg("pm2_5"), 2).alias("tb_pm2.5"),
                round(avg("co"), 2).alias("tb_CO"),
                max("aqi").alias("max_AQI")
            ) \
            .orderBy(desc("tb_pm2.5"))
        
        stats_df.show(truncate=False)

        print("\n>>> 3. Cảnh báo các điểm nóng (AQI >= 3):")
        bad_air = df.filter(col("aqi") >= 3)
        print(f"Số lượng bản ghi mức cảnh báo: {bad_air.count()}")
        if bad_air.count() > 0:
            bad_air.select("latitude", "longitude", "aqi", "pm2_5").show(5)
    else:
        print("!!! Chưa có dữ liệu nào trong kho.")

except Exception as e:
    print(f"Lỗi đọc dữ liệu (Có thể Producer chưa chạy đủ lâu): {e}")

print("="*60 + "\n")
spark.stop()