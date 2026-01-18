# -*- coding: utf-8 -*-
"""
Batch Layer - Lambda Architecture
Reads historical weather data from HDFS stream layer
Aggregates by date and city
Computes daily statistics
Writes to HDFS batch layer
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, min as spark_min, max as spark_max, count, to_date

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("WeatherBatchProcessor") \
    .config("spark.master", "spark://spark-master:7077") \
    .config("spark.executor.memory", "1g") \
    .config("spark.executor.cores", "1") \
    .config("spark.cores.max", "2") \
    .config("spark.executor.memoryOverhead", "512m") \
    .config("spark.driver.memory", "1g") \
    .config("spark.driver.memoryOverhead", "512m") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

print("=" * 80)
print("BATCH LAYER: Reading historical weather data from HDFS stream layer")
print("=" * 80)

# Read all historical Parquet files from stream layer
stream_path = "hdfs://namenode:9000/data/weather_data/stream/"

try:
    df = spark.read.parquet(stream_path)
    
    print(f"Total records read from stream layer: {df.count()}")
    df.printSchema()
    df.show(5, truncate=False)
    
    # Extract date from timestamp and aggregate
    daily_stats = df \
        .withColumn("date", to_date(col("timestamp"))) \
        .groupBy("date", "city") \
        .agg(
            avg("temperature").alias("avg_temperature"),
            spark_min("temperature").alias("min_temperature"),
            spark_max("temperature").alias("max_temperature"),
            avg("humidity").alias("avg_humidity"),
            spark_min("humidity").alias("min_humidity"),
            spark_max("humidity").alias("max_humidity"),
            avg("pressure").alias("avg_pressure"),
            count("*").alias("record_count")
        ) \
        .orderBy("date", "city")
    
    print("\n" + "=" * 80)
    print("BATCH LAYER: Daily aggregated statistics")
    print("=" * 80)
    daily_stats.show(20, truncate=False)
    
    # Write to batch layer (overwrite mode - recomputable)
    batch_output_path = "hdfs://namenode:9000/data/weather_data/batch/daily_stats"
    
    daily_stats.write \
        .mode("overwrite") \
        .parquet(batch_output_path)
    
    print("\n" + "=" * 80)
    print(f"BATCH LAYER: Successfully wrote {daily_stats.count()} daily statistics to:")
    print(f"  {batch_output_path}")
    print("=" * 80)
    
except Exception as e:
    print(f"ERROR in batch processing: {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    spark.stop()
    print("\nBatch processing completed.")
