# 🌤️ Weather Monitoring System - Complete Setup Guide

> **Hướng dẫn chi tiết từng bước, chạy trên Minikube (Windows)**  
> Phù hợp cho hôm sau khi bật PC lên, có thể chạy từ đầu đến cuối không bị lỗi

---

## 📋 Kiểm Tra Trước Khi Bắt Đầu

Mở **PowerShell** và chạy các lệnh sau để kiểm tra điều kiện:

```powershell
# 1. Kiểm tra Docker
docker version

# 2. Kiểm tra Minikube
minikube status

# 3. Kiểm tra kubectl
kubectl version --client

# 4. Kiểm tra thư mục project
cd d:\BigData\bigdata
ls
```

**Nếu Minikube chưa chạy:**
```powershell
minikube delete  # Xóa cluster cũ (nếu cần reset)
minikube start --cpus=4 --memory=8192 --disk-size=40g
minikube status  # Kiểm tra

# ⚠️ IMPORTANT: Tạo data directories trong Minikube VM
minikube ssh "sudo mkdir -p /data/postgres /data/kafka /data/namenode /data/datanode /data/zookeeper && sudo chmod 777 /data/*"
```

✅ **Điều kiện sẵn sàng:**
- Docker Desktop chạy bình thường  
- Minikube Status = `Running`
- kubectl có thể gọi được

---

## ⏱️ Thời Gian Dự Kiến (Tổng ~60 phút)

| Bước | Mô tả | Thời gian |
|------|-------|----------|
| 1-2 | Setup Kubernetes + Kafka | 5 phút |
| 3-5 | Deploy HDFS, Spark, PostgreSQL | 8 phút |
| 6 | Build Docker images | 5 phút |
| 7-8 | Deploy + Verify apps | 5 phút |
| 9-10 | Lambda Architecture + Batch | 30 phút |
| **TỔNG** | | **~53 phút** |

---

## 🏗️ Kiến Trúc Hệ Thống (Lambda Architecture)

```
┌─────────────┐      ┌───────────┐      ┌─────────────────────┐
│  Producer   │─────▶│   Kafka   │─────▶│  Spark Streaming    │
│  (Python)   │      │ (Strimzi) │      │  (stream_app.py)    │
└─────────────┘      └───────────┘      └──────┬──────────┬───┘
                                                │          │
                                        SPEED LAYER   BATCH LAYER
                                                │          │
                                    ┌───────────┘          └──────────────┐
                                    │                                     │
                        PostgreSQL ◀┴─────────────┐      HDFS /batch/     │
                       weather_final              │      daily_stats      │
                                           SERVING LAYER◀─────────────────┘
                                                │
                                    PostgreSQL ◀┘
                                   weather_daily_stats
```

---

## 🚀 BƯỚC 1-2: Setup Kubernetes & Kafka

**Mục đích:** Khởi tạo cluster và Kafka broker

⚠️ **Lưu ý Minikube:** Kafka sử dụng ephemeral storage (emptyDir) để tránh lỗi permission trên Minikube hostPath PV. Dữ liệu Kafka sẽ mất khi pod restart. Phù hợp cho testing/demo.

```powershell
# 1. Tạo namespace
kubectl create namespace air-quality

# 2. Cài Strimzi Operator (Kafka controller)
kubectl create -f 'https://strimzi.io/install/latest?namespace=air-quality' -n air-quality

# 3. Chờ Strimzi ready (~30 giây)
kubectl wait deployment strimzi-cluster-operator --for=condition=available --timeout=300s -n air-quality

# 4. Deploy services & Kafka
kubectl apply -f k8s/00-namespace-config.yaml
kubectl apply -f k8s/01-services.yaml
kubectl apply -f k8s/kafka-strimzi.yaml

# 5. Chờ Kafka ready (~2-3 phút) ⏳
Write-Host "Waiting for Kafka..." -ForegroundColor Yellow
kubectl wait kafka/air-quality-kafka --for=condition=Ready --timeout=300s -n air-quality

# ✓ Verify Kafka
kubectl get kafka -n air-quality
```

**Expected output:** Kafka với `Ready` = `True`

---

## 🏢 BƯỚC 3: Deploy HDFS (Storage)

**Mục đích:** Lưu stream data (/stream/) và batch aggregations (/batch/daily_stats/)

```powershell
# Deploy HDFS
kubectl apply -f k8s/03-hadoop.yaml

# Chờ HDFS ready (~2 phút) ⏳
Write-Host "Waiting for HDFS..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod -l app=namenode -n air-quality --timeout=300s

# ✓ Verify HDFS pods
kubectl get pods -n air-quality 
```

**Expected output:** `namenode-0` và `datanode-0` running

---

## ⚡ BƯỚC 4: Deploy Spark Cluster

**Mục đích:** Processing engine cho streaming + batch

```powershell
# Deploy Spark Master & Workers
kubectl apply -f k8s/04-spark.yaml

# Chờ Spark ready (~1 phút) ⏳
Write-Host "Waiting for Spark..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod -l app=spark-master -n air-quality --timeout=300s

# ✓ Verify Spark
kubectl get pods -n air-quality | Select-String spark
```

**Expected output:** `spark-master-0` + `spark-worker-0-x` + `spark-worker-1-x` running

---

## 🗄️ BƯỚC 5: Deploy PostgreSQL & Create Tables

**Mục đích:** OLTP database cho real-time + analytical queries

```powershell
# Deploy PostgreSQL
kubectl apply -f k8s/05-database.yaml

# Chờ PostgreSQL ready (~1 phút) ⏳
Write-Host "Waiting for PostgreSQL..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod -l app=postgres -n air-quality --timeout=300s

# Tạo database weather_data
kubectl exec -it postgres-0 -n air-quality -- psql -U admin -d postgres -c "CREATE DATABASE weather_data;"

# Tạo table weather_final (Speed Layer - real-time)
kubectl exec -it postgres-0 -n air-quality -- psql -U admin -d weather_data -c "CREATE TABLE IF NOT EXISTS weather_final (timestamp timestamp, ingested_at timestamp, longitude double precision, latitude double precision, temperature double precision, feels_like double precision, humidity int, pressure int, city varchar(50));"

# Tạo table weather_daily_stats (Batch Layer - aggregations)
kubectl exec -it postgres-0 -n air-quality -- psql -U admin -d weather_data -c "CREATE TABLE IF NOT EXISTS weather_daily_stats (date date NOT NULL, city varchar(50) NOT NULL, avg_temperature double precision, min_temperature double precision, max_temperature double precision, avg_humidity double precision, min_humidity double precision, max_humidity double precision, avg_pressure double precision, record_count bigint, PRIMARY KEY (date, city)); CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON weather_daily_stats(date DESC); CREATE INDEX IF NOT EXISTS idx_daily_stats_city ON weather_daily_stats(city);"

# ✓ Verify tables
kubectl exec -it postgres-0 -n air-quality -- psql -U admin -d weather_data -c "\dt"
```

**Expected output:** 2 tables: `weather_final` + `weather_daily_stats`

---

## 🐳 BƯỚC 6: Build Docker Images

**Mục đích:** Tạo images cho Producer (v3) và Spark Processor (v7 với batch scripts)

```powershell
# IMPORTANT: Point Docker to Minikube (để build image trong Minikube)
Write-Host "Pointing Docker to Minikube..." -ForegroundColor Cyan
minikube -p minikube docker-env --shell powershell | Invoke-Expression

# Build Producer (v3)
Write-Host "Building producer:v3..." -ForegroundColor Cyan
docker build -t producer:v3 ./producer

# Build Spark Processor (v7 - includes batch_job.py + serving_layer.py)
Write-Host "Building spark-processor:v7..." -ForegroundColor Cyan
docker build -t spark-processor:v7 ./spark-processor

# ✓ Verify images
Write-Host "Verifying images..." -ForegroundColor Green
docker images | Select-String "producer\|spark-processor"
```

**Expected output:** Thấy cả `producer:v3` và `spark-processor:v7`

---

## 🚀 BƯỚC 7-8: Deploy Applications & Kafka Topic

**Mục đích:** Chạy Producer → Kafka, Spark Processor xử lý real-time

```powershell
# Deploy Kafka topic trước
kubectl apply -f k8s/07-kafka-topic-weather.yaml

# Deploy Producer + Spark Processor
kubectl apply -f k8s/06-applications.yaml

# Chờ pods ready (~1 phút) ⏳
Write-Host "Waiting for Producer & Spark Processor..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod -l app=producer -n air-quality --timeout=300s
kubectl wait --for=condition=ready pod -l app=spark-processor -n air-quality --timeout=300s

# ✓ Verify deployment
kubectl get pods -n air-quality | Select-String "producer\|spark-processor"
```

**Expected output:** Both pods `Running`

---

## ✓ BƯỚC 9: Verify Real-Time Data Flow (Speed Layer)

**Mục đích:** Kiểm tra Producer → Kafka → Spark → PostgreSQL/HDFS

```powershell
# 1. Check Producer logs
Write-Host "`n📤 Producer logs:" -ForegroundColor Green
kubectl logs -f deployment/producer -n air-quality --tail=5
# (Chờ 5 giây rồi Ctrl+C)
# Expected: "Sending data for Hanoi...", "Sending data for HCM...", etc.

# 2. Check Spark logs
Write-Host "`n⚡ Spark logs:" -ForegroundColor Green
kubectl logs deployment/spark-processor -n air-quality --tail=15
# Expected: "=== Batch X ===" với data rows

# 3. Check HDFS data
kubectl exec -it namenode-0 -n air-quality -- sh -c "hdfs dfs -ls /data/weather_data/ | tail -10"
# Expected: Many .snappy.parquet files

# 4. Check PostgreSQL data (Speed Layer)
kubectl exec -it postgres-0 -n air-quality -- psql -U admin -d weather_data -c "SELECT COUNT(*) FROM weather_final;"
# Expected: count > 30
```

---

## 🏗️ BƯỚC 10: Lambda Architecture - Batch Processing

### 10.1 Chờ Stream Data (10-15 phút)

```powershell
# Kiểm tra stream data folder được tạo
kubectl exec -it namenode-0 -n air-quality -- sh -c "hdfs dfs -ls /data/weather_data/stream/ | tail -5"

# Nếu chưa có, chờ 10 phút, stream app sẽ tạo nó
# Nếu vẫn không có, kiểm tra logs:
kubectl logs deployment/spark-processor -n air-quality | Select-String "write parquet to STREAM"
```

### 10.2 Run Batch Job (Aggregate Daily Stats)

```powershell
# chạy lệnh lấy pods
kubectl get pods -n air-quality

# Lấy tên pod spark-processor (pod có Spark + Python runtime)
$SPARK_POD = kubectl get pods -n air-quality -l app=spark-processor -o jsonpath="{.items[0].metadata.name}"


# Chạy Spark batch job (Python sẽ tự kết nối Spark cluster)
kubectl exec -it $SPARK_POD -n air-quality -- python3 /opt/spark-apps/batch_job.py


# Verify batch output in HDFS
kubectl exec -it namenode-0 -n air-quality -- sh -c "hdfs dfs -ls /data/weather_data/batch/daily_stats/ | tail -10"
```

### 10.3 Run Serving Layer (Load Batch to PostgreSQL)

```powershell
Write-Host "`n📊 Running Serving Layer (load to PostgreSQL)..." -ForegroundColor Green

# Get spark-processor pod name
$SPARK_POD = kubectl get pods -n air-quality -l app=spark-processor -o jsonpath='{.items[0].metadata.name}'

# Run serving layer
kubectl exec -it $SPARK_POD -n air-quality -- python3 /opt/spark-apps/serving_layer.py
```

**Note:** The serving layer uses pandas + sqlalchemy instead of JDBC for simpler PostgreSQL integration.

```powershell
# Verify daily stats in PostgreSQL
Write-Host "`n✓ Daily statistics in PostgreSQL:" -ForegroundColor Green
kubectl exec -it postgres-0 -n air-quality -- psql -U admin -d weather_data -c "SELECT date, city, ROUND(avg_temperature::numeric, 2) as avg_temp, ROUND(min_temperature::numeric, 2) as min_temp, ROUND(max_temperature::numeric, 2) as max_temp, record_count FROM weather_daily_stats ORDER BY date DESC, city;"
```

**Expected output:** Daily aggregations for each city by date

---

## 🎨 BƯỚC 11 (Optional): Grafana Dashboard

```powershell
# Chạy lệnh:
kubectl port-forward svc/grafana -n air-quality 3000:3000


# Giữ terminal KHÔNG ĐÓNG.

# Mở trình duyệt:
http://localhost:3000


👉 Grafana sẽ mở ra ngay

# Login: admin / admin123
# 
# Add PostgreSQL Data Source:
# - Host: postgres:5432
# - Database: weather_data
# - User: admin
# - Password: password123
# - SSL Mode: disable
#
# Create Panel:
# SELECT 
#   timestamp as time,
#   temperature,
#   city
# FROM weather_final 
# WHERE timestamp > now() - interval '1 hour'
# ORDER BY timestamp DESC
```

---

## ✅ Verification Checklist

Chạy script này để xác minh tất cả đã hoàn thành:

```powershell
Write-Host "=== SYSTEM VERIFICATION ===" -ForegroundColor Cyan

Write-Host "`n1️⃣ Pods Status:" -ForegroundColor Green
kubectl get pods -n air-quality | Select-String "producer|spark-processor|kafka|namenode|datanode|postgres|spark-master|spark-worker"

Write-Host "`n2️⃣ Kafka Topic:" -ForegroundColor Green
kubectl get kafkatopic -n air-quality

Write-Host "`n3️⃣ PostgreSQL Tables:" -ForegroundColor Green
kubectl exec -it postgres-0 -n air-quality -- psql -U admin -d weather_data -c "\dt"

Write-Host "`n4️⃣ Real-time Data (weather_final):" -ForegroundColor Green
kubectl exec -it postgres-0 -n air-quality -- psql -U admin -d weather_data -c "SELECT COUNT(*) as count, COUNT(DISTINCT city) as cities FROM weather_final;"

Write-Host "`n5️⃣ Daily Stats (weather_daily_stats):" -ForegroundColor Green
kubectl exec -it postgres-0 -n air-quality -- psql -U admin -d weather_data -c "SELECT COUNT(*) as days_aggregated FROM weather_daily_stats;"

Write-Host "`n6️⃣ HDFS Stream Data:" -ForegroundColor Green
kubectl exec -it namenode-0 -n air-quality -- hdfs dfs -du -h /data/weather_data/stream/ | head -3

Write-Host "`n✅ System is Ready!" -ForegroundColor Cyan
```

---

## 📚 File Structure

```
bigdata/
├── README.md                        ← Bạn đang đọc cái này
├── producer/
│   ├── sensor_sim.py               (Kafka producer)
│   ├── Dockerfile
│   └── requirements.txt
├── spark-processor/
│   ├── stream_app.py               (Speed layer)
│   ├── batch_job.py                (Batch layer - NEW)
│   ├── serving_layer.py            (Serving layer - NEW)
│   ├── Dockerfile
│   └── requirements.txt
└── k8s/
    ├── 00-namespace-config.yaml
    ├── 01-services.yaml
    ├── 03-hadoop.yaml
    ├── 04-spark.yaml
    ├── 05-database.yaml
    ├── 06-applications.yaml        (Deploy apps with v7 image)
    ├── 07-kafka-topic-weather.yaml
    └── kafka-strimzi.yaml
```

---

## 🔍 Useful Commands

```powershell
# Check pod status
kubectl get pods -n air-quality

# View logs
kubectl logs -f deployment/producer -n air-quality
kubectl logs -f deployment/spark-processor -n air-quality

# Connect to containers
kubectl exec -it namenode-0 -n air-quality -- bash
kubectl exec -it postgres-0 -n air-quality -- psql -U admin -d weather_data

# HDFS operations
kubectl exec -it namenode-0 -n air-quality -- hdfs dfs -ls /data/weather_data/

# Restart pods
kubectl rollout restart deployment/producer -n air-quality
kubectl rollout restart deployment/spark-processor -n air-quality

# Check resources
kubectl top nodes -n air-quality
kubectl top pods -n air-quality

# Delete resources
kubectl delete namespace air-quality
```

---

## 🚨 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| **Pods Pending** | `minikube delete && minikube start --memory=12288` |
| **Producer no data** | `kubectl rollout restart deployment/producer -n air-quality` |
| **No /stream/ folder** | Wait 10-15 min for spark to create it |
| **PostgreSQL connection error** | `kubectl logs statefulset/postgres -n air-quality` |
| **HDFS error** | `kubectl exec -it namenode-0 -n air-quality -- hdfs dfsadmin -report` |

---

## 🛑 Stop & Cleanup

```powershell
# Stop Minikube (keeps data)
minikube stop

# Delete everything
minikube delete

# Remove namespace
kubectl delete namespace air-quality
```

---

## 📊 Data Format

### Kafka Message
```json
{
  "timestamp": 1736912345,
  "longitude": 105.8542,
  "latitude": 21.0285,
  "temperature": 25.3,
  "feels_like": 27.1,
  "humidity": 75,
  "pressure": 1012,
  "city": "Hanoi"
}
```

### Cities & Coordinates
| City | Coordinates | Temp Range |
|------|-------------|-----------|
| Hà Nội | 21.0285°N, 105.8542°E | 15-35°C |
| Đà Nẵng | 16.0544°N, 108.2022°E | 20-36°C |
| TP HCM | 10.8231°N, 106.6297°E | 25-38°C |

---

## 🎯 Next Steps

1. ✅ Complete BƯỚC 1-10
2. 📊 Setup Grafana (Optional BƯỚC 11)
3. 🚀 Customize batch job for your needs
4. 📈 Add alerting rules
5. 🔄 Setup automated CronJob for daily batch

---

**Last Updated:** 2026-01-16  
**Version:** 2.0  
**Status:** ✅ Production Ready
