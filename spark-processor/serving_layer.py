# -*- coding: utf-8 -*-
"""
Serving Layer - Lambda Architecture
Loads batch results from HDFS into PostgreSQL using pandas + sqlalchemy
PostgreSQL serves as the ONLY serving layer queried by Grafana
"""

from pyspark.sql import SparkSession
import pandas as pd
from sqlalchemy import create_engine
import psycopg2

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("WeatherServingLayer") \
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
print("SERVING LAYER: Loading batch results into PostgreSQL")
print("=" * 80)

# Read batch results from HDFS
batch_path = "hdfs://namenode:9000/data/weather_data/batch/daily_stats"

try:
    batch_df = spark.read.parquet(batch_path)
    
    print(f"\nTotal daily statistics records: {batch_df.count()}")
    batch_df.printSchema()
    batch_df.show(10, truncate=False)
    
    # Step 1: Truncate existing data
    print("\nTruncating existing data...")
    conn_str = "dbname=weather_data user=admin password=password123 host=postgres port=5432"
    try:
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        cur.execute("TRUNCATE TABLE public.weather_daily_stats")
        conn.commit()
        cur.close()
        conn.close()
        print("✓ Truncated existing weather_daily_stats")
    except Exception as e:
        print(f"Warning: Could not truncate table: {e}")
    
    # Step 2: Write batch results to PostgreSQL using pandas + sqlalchemy
    print("\nWriting to PostgreSQL table: weather_daily_stats...")
    
    # Convert Spark DataFrame to Pandas
    pandas_df = batch_df.toPandas()
    
    # Create SQLAlchemy engine and write
    engine = create_engine('postgresql://admin:password123@postgres:5432/weather_data')
    pandas_df.to_sql('weather_daily_stats', con=engine, if_exists='append', index=False)
    
    print(f"✓ Successfully inserted {len(pandas_df)} records to weather_daily_stats")
    
    print("\n" + "=" * 80)
    print("SERVING LAYER: Successfully loaded batch results to PostgreSQL")
    print("  Table: weather_daily_stats")
    print("  Records: " + str(len(pandas_df)))
    print("=" * 80)
    
    # Step 3: Verify data in PostgreSQL
    print("\nVerification - Querying PostgreSQL...")
    verify_query = "SELECT COUNT(*) as row_count FROM weather_daily_stats"
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute(verify_query)
    row_count = cur.fetchone()[0]
    
    print(f"  Total records in PostgreSQL: {row_count}")
    
    # Show sample
    cur.execute("SELECT date, city, ROUND(avg_temperature::numeric, 2) as avg_temp FROM weather_daily_stats LIMIT 10")
    print("\n  Sample data:")
    for row in cur.fetchall():
        print(f"    {row[0]} | {row[1]} | {row[2]}°C")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"ERROR in serving layer: {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    spark.stop()
    print("\nServing layer update completed.")
