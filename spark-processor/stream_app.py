# -*- coding: utf-8 -*-
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, when, col, explode, current_timestamp, to_timestamp,from_unixtime
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType, IntegerType, ArrayType


spark = SparkSession.builder \
    .appName("OpenWeatherProcessor") \
    .config("spark.master", "spark://spark-master:7077") \
    .config("spark.executor.memory", "1g") \
    .config("spark.executor.cores", "1") \
    .config("spark.cores.max", "2") \
    .config("spark.executor.memoryOverhead", "512m") \
    .config("spark.driver.memory", "1g") \
    .config("spark.driver.memoryOverhead", "512m") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

component_schema = StructType([
    StructField("co", DoubleType()),
    StructField("no", DoubleType()),
    StructField("no2", DoubleType()),
    StructField("o3", DoubleType()),
    StructField("so2", DoubleType()),
    StructField("pm2_5", DoubleType()),
    StructField("pm10", DoubleType()),
    StructField("nh3", DoubleType())
])

main_info_schema = StructType([
    StructField("aqi", IntegerType())
])

list_item_schema = StructType([
    StructField("dt", LongType()),
    StructField("main", main_info_schema),
    StructField("components", component_schema)
])

api_schema = StructType([
    StructField("coord", ArrayType(DoubleType())), # [lon, lat]
    StructField("list", ArrayType(list_item_schema))
])

kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribe", "air_quality_data") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false")\
    .load()

json_df = kafka_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), api_schema).alias("data"))

exploded_df = json_df.select(
    col("data.coord").getItem(0).alias("longitude"),
    col("data.coord").getItem(1).alias("latitude"),
    explode(col("data.list")).alias("measure")
)

final_df = exploded_df.select(
    col("measure.dt").alias("timestamp_unix"),
    current_timestamp().alias("processed_time"),
    col("longitude"),
    col("latitude"),
    col("measure.main.aqi").alias("aqi"),
    col("measure.components.pm2_5").alias("pm2_5"),
    col("measure.components.pm10").alias("pm10"),
    col("measure.components.co").alias("co"),
    col("measure.components.no2").alias("no2")
)

# query = final_df.writeStream \
#     .outputMode("append") \
#     .format("parquet") \
#     .option("path", "hdfs://namenode:9000/data/air_quality_v2/") \
#     .option("checkpointLocation", "hdfs://namenode:9000/checkpoint/air_quality_v2/") \
#     .trigger(processingTime='1 minute') \
#     .start()
    #  .option("path", "hdfs://namenode-service:9000/data/air_quality_v2/") \
    # .option("checkpointLocation", "hdfs://namenode-service:9000/checkpoint/air_quality_v2/") \
db_properties = {
    "user": "admin",
    "password": "password123",
    "driver": "org.postgresql.Driver"
}
jdbc_url = "jdbc:postgresql://postgres:5432/air_quality" # 'postgres' là tên service trong docker

# def write_to_postgres(batch_df, batch_id):

#     print(f"=== Batch {batch_id} ===")
#     batch_df.printSchema()
#     batch_df.show(5, False)
#     final_df = (
#         batch_df
#         .withColumn(
#             "city",
#             when(
#                 (col("latitude").between(20.9, 21.2)) &
#                 (col("longitude").between(105.7, 106.1)),
#                 "Hanoi"
#             )
#             .when(
#                 (col("latitude").between(10.7, 11.0)) &
#                 (col("longitude").between(106.4, 106.8)),
#                 "HCM"
#             )
#             .when(
#                 (col("latitude").between(15.9, 16.2)) &
#                 (col("longitude").between(108.0, 108.4)),
#                 "DaNang"
#             )
#             .otherwise("Unknown")
#         )
#         .withColumn(
#             "timestamp",
#             to_timestamp(from_unixtime(col("timestamp_unix")))
#         )
#         .withColumnRenamed("processed_time", "ingested_at")
#         .drop("timestamp_unix")
#     )

#     final_df.write \
#         .jdbc(
#             url=jdbc_url,
#             table="public.air_quality_final",
#             mode="append",
#             properties=db_properties
#         )


def write_to_postgres_and_parquet(batch_df, batch_id):
    print(f"=== Batch {batch_id} ===")
    batch_df.show(5, False)

    enriched = (
        batch_df
        .withColumn(
            "city",
            when(
                (col("latitude").between(20.9, 21.2)) &
                (col("longitude").between(105.7, 106.1)),
                "Hanoi"
            )
            .when(
                (col("latitude").between(10.7, 11.0)) &
                (col("longitude").between(106.4, 106.8)),
                "HCM"
            )
            .when(
                (col("latitude").between(15.9, 16.2)) &
                (col("longitude").between(108.0, 108.4)),
                "DaNang"
            )
            .otherwise("Unknown")
        )
        .withColumn(
            "timestamp",
            to_timestamp(from_unixtime(col("timestamp_unix")))
        )
        .withColumnRenamed("processed_time", "ingested_at")
        .drop("timestamp_unix")
    )

    # write parquet
    enriched.write.parquet(
        "hdfs://namenode:9000/data/air_quality_v2/",
        mode="append"
    )

    # write postgres
    enriched.write.jdbc(
        url=jdbc_url,
        table="public.air_quality_final",
        mode="append",
        properties=db_properties
    )


# Áp dụng cho Stream
# query = final_df.writeStream \
#     .foreachBatch(write_to_postgres) \
#     .start()



query = final_df.writeStream \
    .outputMode("append") \
    .foreachBatch(write_to_postgres_and_parquet) \
    .option("checkpointLocation", "hdfs://namenode:9000/checkpoint/air_quality_v2/") \
    .start()

print(">>> Đang xử lý dữ liệu từ OpenWeatherMap API giả lập...")
query.awaitTermination()