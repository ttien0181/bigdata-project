# 🎤 Hướng Dẫn Demo Bài Tập Lớn

> Script chi tiết để demo Air Quality Monitoring System trong 15-20 phút

---

## 📋 Chuẩn Bị Trước Khi Demo

### 1. Checklist Hệ Thống

**Trước 30 phút:**

```powershell
# 1. Khởi động Minikube (nếu chưa chạy)
minikube start

# 2. Verify tất cả pods Running
kubectl get pods -n air-quality

# 3. Kiểm tra services
kubectl get svc -n air-quality

# 4. Xem logs nhanh để đảm bảo không có lỗi
kubectl logs deployment/spark-processor -n air-quality --tail=20
kubectl logs deployment/producer -n air-quality --tail=10
```

**Expected Output:**
```
✅ All pods: Running
✅ Spark logs: === Batch X === (batches tăng dần)
✅ Producer logs: "Message published successfully"
```

### 2. Mở Sẵn Các Tab/Windows

**Browser tabs (mở trước):**
1. Grafana Dashboard: `http://MINIKUBE_IP:30300`
2. Spark Master UI: `http://MINIKUBE_IP:30080`
3. HDFS NameNode UI: `http://MINIKUBE_IP:30870`

**PowerShell terminals (3 windows):**
1. Terminal 1: Để chạy kubectl commands
2. Terminal 2: Để tail logs real-time
3. Terminal 3: Backup terminal

### 3. Chuẩn Bị Slides/Tài Liệu

- [ ] Kiến trúc tổng quan (Architecture Diagram)
- [ ] Tech stack (Kafka, Spark, HDFS, PostgreSQL, Grafana)
- [ ] Use case: Air Quality Monitoring cho Hanoi, HCM, DaNang

---

## 🎬 Script Demo (20 phút)

### **Phần 1: Giới thiệu Project (3 phút)**

**Nội dung:**

> "Xin chào các thầy cô. Em xin giới thiệu đồ án: **Hệ Thống Giám Sát Chất Lượng Không Khí Real-time**

**Tech Stack:**
- **Kafka**: Message queue để stream dữ liệu
- **Spark Streaming**: Xử lý dữ liệu real-time
- **HDFS**: Lưu trữ dữ liệu dạng Parquet (Data Lake)
- **PostgreSQL**: Database cho query nhanh
- **Grafana**: Dashboard visualization
- **Kubernetes**: Orchestration trên Minikube

**Use Case:**
- Producer giả lập OpenWeather API
- Lấy dữ liệu AQI (Air Quality Index) của 3 thành phố: Hanoi, HCM, DaNang
- Data flow: Producer → Kafka → Spark → HDFS + PostgreSQL → Grafana

**Hiển thị:** Architecture Diagram (slide)

---

### **Phần 2: Kiểm Tra Hệ Thống Đang Chạy (2 phút)**

**Terminal 1:**

```powershell
# 1. Show pods đang chạy
kubectl get pods -n air-quality
```

**Giải thích:**
> "Đây là tất cả các pods đang chạy trong hệ thống:
> - **Kafka**: Message broker
> - **Spark Master/Workers**: Xử lý streaming
> - **NameNode/DataNodes**: HDFS storage
> - **PostgreSQL**: Database
> - **Grafana**: Visualization
> - **Producer**: Giả lập data source
> - **Spark Processor**: Streaming job đang chạy liên tục"

**Terminal 1:**

```powershell
# 2. Show services
kubectl get svc -n air-quality | Select-Object -First 10
```

**Giải thích:**
> "Các services expose pods ra ngoài:
> - Grafana: NodePort 30300
> - Spark Master UI: NodePort 30080
> - HDFS NameNode UI: NodePort 30870"

---

### **Phần 3: Demo Data Flow (10 phút)**

#### **3.1. Producer tạo dữ liệu (2 phút)**

**Terminal 2:**

```powershell
# Tail producer logs real-time
kubectl logs -f deployment/producer -n air-quality --tail=20
```

**Giải thích:**
> "Producer đang giả lập OpenWeather API, tạo dữ liệu AQI mỗi 5 giây.
> Mỗi message chứa: timestamp, latitude, longitude, aqi, pm2.5, pm10, co, no2.
> Dữ liệu được publish vào Kafka topic `air_quality_data`."

**Chờ 10 giây để thấy 2 messages được publish**

**Dừng log (Ctrl+C)**

---

#### **3.2. Kafka lưu trữ messages (1 phút)**

**Terminal 1:**

```powershell
# List Kafka topics
kubectl exec -it air-quality-kafka-air-quality-pool-0 -n air-quality -- `
  /opt/kafka/bin/kafka-topics.sh `
  --list `
  --bootstrap-server localhost:29092
```

**Giải thích:**
> "Topic `air_quality_data` đã được tạo tự động."

**Terminal 1:**

```powershell
# Consume 3 messages từ Kafka
kubectl exec -it air-quality-kafka-air-quality-pool-0 -n air-quality -- `
  /opt/kafka/bin/kafka-console-consumer.sh `
  --bootstrap-server localhost:29092 `
  --topic air_quality_data `
  --from-beginning `
  --max-messages 3
```

**Giải thích:**
> "Đây là dữ liệu JSON raw trong Kafka. Spark sẽ đọc và xử lý những messages này."

---

#### **3.3. Spark Streaming xử lý dữ liệu (2 phút)**

**Terminal 2:**

```powershell
# Tail Spark processor logs
kubectl logs -f deployment/spark-processor -n air-quality --tail=50
```

**Giải thích:**
> "Spark đang chạy streaming job, xử lý micro-batches mỗi 5 giây.
> Mỗi batch:
> - Đọc messages từ Kafka
> - Parse JSON
> - Transform: thêm cột `city` (Hanoi/HCM/DaNang), timestamp
> - Ghi vào HDFS (Parquet) và PostgreSQL"

**Chờ 10 giây để thấy 2 batches:**
```
=== Batch 125 ===
[5 rows with data]

=== Batch 126 ===
[5 rows with data]
```

**Dừng log (Ctrl+C)**

---

**Browser: Spark Master UI**

```
URL: http://MINIKUBE_IP:30080
```

**Giải thích:**
> "Spark Master UI cho thấy:
> - Application `OpenWeatherProcessor` đang RUNNING
> - 2 Workers đang active
> - 2 Cores đang được sử dụng"

**Click vào application → Show stages/tasks**

---

#### **3.4. HDFS lưu trữ Parquet files (2 phút)**

**Terminal 1:**

```powershell
# List files trong HDFS
kubectl exec -it namenode-0 -n air-quality -- `
  hdfs dfs -ls /data/air_quality_v2/
```

**Giải thích:**
> "HDFS chứa Parquet files (Data Lake):
> - `_SUCCESS`: File marker cho thành công
> - `_spark_metadata`: Checkpoint metadata
> - `part-*.parquet`: Dữ liệu compressed (Snappy)"

**Browser: HDFS NameNode UI**

```
URL: http://MINIKUBE_IP:30870
Click: Utilities → Browse the file system → /data/air_quality_v2/
```

**Giải thích:**
> "HDFS UI cho thấy tất cả files với size > 0, tổng dung lượng ~500KB."

---

#### **3.5. PostgreSQL lưu trữ structured data (1 phút)**

**Terminal 1:**

```powershell
# Count records
kubectl exec -it postgres-0 -n air-quality -- `
  psql -U admin -d air_quality -c "SELECT COUNT(*) FROM air_quality_final;"
```

**Giải thích:**
> "PostgreSQL đã lưu hơn 8,000 records."

**Terminal 1:**

```powershell
# Show sample data
kubectl exec -it postgres-0 -n air-quality -- `
  psql -U admin -d air_quality -c `
  "SELECT city, timestamp, aqi, pm2_5, ingested_at FROM air_quality_final ORDER BY ingested_at DESC LIMIT 5;"
```

**Giải thích:**
> "Dữ liệu mới nhất từ 3 thành phố, với AQI và PM2.5 values."

**Terminal 1:**

```powershell
# Aggregate by city
kubectl exec -it postgres-0 -n air-quality -- `
  psql -U admin -d air_quality -c `
  "SELECT city, COUNT(*) as count, ROUND(AVG(aqi), 2) as avg_aqi FROM air_quality_final GROUP BY city;"
```

**Giải thích:**
> "Dữ liệu phân bố đều cho 3 thành phố, mỗi thành phố ~2,700 records với AQI trung bình ~3."

---

#### **3.6. Grafana Visualization (2 phút)**

**Browser: Grafana Dashboard**

```
URL: http://MINIKUBE_IP:30300
Login: admin / admin123
Navigate: Dashboards → Air Quality Monitoring
```

**Giải thích:**
> "Grafana dashboard hiển thị real-time data:
> - **Time-series chart**: PM2.5 trends cho 3 thành phố
> - **Table**: Latest AQI values
> - **Gauge panels**: Current AQI levels
> - Auto-refresh mỗi 5 giây để cập nhật dữ liệu mới"

**Chờ 5 giây để dashboard refresh, chỉ vào điểm dữ liệu mới xuất hiện**

---

### **Phần 4: Demo E2E Flow (3 phút)**

**Mục tiêu:** Chứng minh dữ liệu flow từ đầu đến cuối tự động

**Terminal 1:**

```powershell
# Step 1: Ghi lại count PostgreSQL
Write-Host "Count trước:" -ForegroundColor Yellow
kubectl exec -it postgres-0 -n air-quality -- `
  psql -U admin -d air_quality -c "SELECT COUNT(*) FROM air_quality_final;"
```

**Output:** (ví dụ: 8241)

**Giải thích:**
> "Bây giờ em sẽ chờ 10 giây (2 batches mới) và kiểm tra lại count."

```powershell
# Step 2: Đợi 10 giây
Write-Host "Đang đợi 10 giây..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Step 3: Kiểm tra lại count
Write-Host "Count sau:" -ForegroundColor Green
kubectl exec -it postgres-0 -n air-quality -- `
  psql -U admin -d air_quality -c "SELECT COUNT(*) FROM air_quality_final;"
```

**Output:** (ví dụ: 8250+)

**Giải thích:**
> "Count tăng từ 8241 lên 8250, chứng tỏ:
> 1. Producer tạo dữ liệu mới
> 2. Kafka nhận messages
> 3. Spark xử lý batches
> 4. PostgreSQL insert records
> 
> Toàn bộ flow hoàn toàn tự động, không cần can thiệp thủ công!"

**Browser: Refresh Grafana dashboard**

**Giải thích:**
> "Dashboard cũng cập nhật với điểm dữ liệu mới (chỉ vào chart)."

---

### **Phần 5: Technical Highlights (2 phút)**

**Terminal 1:**

```powershell
# Show resource usage
kubectl top pods -n air-quality
```

**Giải thích:**
> "Resource usage của hệ thống:
> - Spark Processor: ~1.5GB RAM (xử lý streaming)
> - Kafka: ~1GB RAM
> - Các service khác < 500MB
> 
> **Optimization đã thực hiện:**
> - Spark executor memory: 512MB (giảm từ 2GB)
> - Total cores: 1 (để phù hợp Minikube)
> - Kafka compression: Snappy
> - Parquet files: Snappy compression"

**Terminal 1:**

```powershell
# Show Kafka consumer lag
kubectl exec -it air-quality-kafka-air-quality-pool-0 -n air-quality -- `
  /opt/kafka/bin/kafka-consumer-groups.sh `
  --bootstrap-server localhost:29092 `
  --describe `
  --all-groups | Select-String "spark-kafka"
```

**Giải thích:**
> "LAG = 0 nghĩa là Spark đọc kịp Producer, không bị tụt hậu."

---

### **Phần 6: Q&A và Kết Luận (2 phút)**

**Tóm tắt:**

> "**Tóm lại, hệ thống đã thực hiện:**
> 
> ✅ **Data Ingestion**: Producer giả lập API → Kafka (stream processing)
> 
> ✅ **Data Processing**: Spark Streaming xử lý real-time, transform schema
> 
> ✅ **Data Storage**:
>   - HDFS: Data Lake (Parquet files) cho analytics
>   - PostgreSQL: Database cho query nhanh
> 
> ✅ **Data Visualization**: Grafana dashboard real-time
> 
> ✅ **Orchestration**: Kubernetes quản lý toàn bộ services trên Minikube
> 
> **Challenges đã giải quyết:**
> - Spark executor crash → Tạo headless Service cho driver DNS resolution
> - Resource constraints → Optimize memory/cores
> - Kafka-Spark integration → Đúng Kafka libraries version
> 
> Em xin cảm ơn!"

---

## 🎯 Câu Hỏi Thường Gặp & Trả Lời

### **Q1: Tại sao dùng Kubernetes thay vì Docker Compose?**

**A:**
> "Kubernetes cung cấp:
> - **Auto-healing**: Pod crash sẽ tự động restart
> - **Scalability**: Dễ dàng scale workers (replicas)
> - **Service discovery**: DNS tự động cho pods
> - **Production-ready**: Sẵn sàng deploy lên cloud (AKS, EKS, GKE)"

---

### **Q2: Spark Streaming vs Spark Batch?**

**A:**
> "Spark Streaming xử lý micro-batches (mỗi 5s) thay vì batch lớn 1 ngày.
> - **Latency**: Giây thay vì giờ
> - **Use case**: Real-time monitoring thay vì daily report
> - **Windowing**: Có thể tính aggregations theo time windows"

---

### **Q3: Tại sao cần cả HDFS và PostgreSQL?**

**A:**
> "Mỗi loại storage có mục đích riêng:
> - **HDFS (Parquet)**: Data Lake cho long-term storage, analytics lớn
> - **PostgreSQL**: Fast query cho dashboard, API
> 
> Kiến trúc Lambda: Batch layer (HDFS) + Speed layer (PostgreSQL)"

---

### **Q4: Làm sao đảm bảo data không bị mất khi pod restart?**

**A:**
> "Dùng PersistentVolumes:
> - HDFS: `hostPath` mount vào Minikube VM
> - PostgreSQL: StatefulSet với PVC
> - Kafka: PVC cho topic data
> 
> Khi pod restart, dữ liệu vẫn còn trong PV."

---

### **Q5: Performance ra sao với data lớn?**

**A:**
> "Hiện tại: 8,000+ records, < 1MB/batch.
> 
> **Scalability options:**
> - Tăng Spark workers: `replicas: 5`
> - Tăng Kafka partitions: multiple producers
> - Tăng HDFS DataNodes: distributed storage
> - Optimize Parquet: partition by date"

---

### **Q6: Có xử lý lỗi không?**

**A:**
> "Có:
> - **Spark**: Checkpoint HDFS → recovery khi crash
> - **Kafka**: Retention policy 7 days → replay messages
> - **Kubernetes**: RestartPolicy OnFailure
> - **Init Containers**: Đợi dependencies sẵn sàng"

---

## 📝 Backup Commands (Nếu Demo Gặp Lỗi)

### Nếu pods không Running:

```powershell
# Restart deployment
kubectl rollout restart deployment/spark-processor -n air-quality
kubectl rollout restart deployment/producer -n air-quality

# Xem logs lỗi
kubectl logs deployment/spark-processor -n air-quality --tail=50 | Select-String "error"
```

### Nếu Grafana không hiển thị data:

```powershell
# Kiểm tra PostgreSQL connection
kubectl exec -it postgres-0 -n air-quality -- `
  psql -U admin -d air_quality -c "\dt"

# Restart Grafana
kubectl delete pod -l app=grafana -n air-quality
```

### Nếu Spark không process batches:

```powershell
# Kiểm tra Kafka topic
kubectl exec -it air-quality-kafka-air-quality-pool-0 -n air-quality -- `
  /opt/kafka/bin/kafka-topics.sh --describe --topic air_quality_data --bootstrap-server localhost:29092

# Restart Spark
kubectl delete pod -l app=spark-processor -n air-quality
```

---

## ✅ Checklist Trước Khi Demo

- [ ] Minikube đang chạy (`minikube status`)
- [ ] Tất cả pods Running (`kubectl get pods -n air-quality`)
- [ ] Producer logs hiển thị "Message published"
- [ ] Spark logs hiển thị batches tăng dần
- [ ] PostgreSQL có data (`COUNT(*) > 0`)
- [ ] HDFS có Parquet files
- [ ] Grafana dashboard mở được
- [ ] Spark Master UI mở được
- [ ] HDFS NameNode UI mở được
- [ ] Browser tabs đã mở sẵn
- [ ] Terminal windows chuẩn bị sẵn
- [ ] Minikube IP đã lấy (`minikube ip`)

---

## 🎥 Video Demo Tips

**Nếu record video:**

1. **Screen resolution**: 1920x1080 (Full HD)
2. **Font size**: Tăng terminal font size lên 14pt
3. **Zoom browser**: 125% để dễ nhìn
4. **Cursor highlight**: Dùng ZoomIt hoặc PowerToys
5. **Voice clarity**: Test mic trước
6. **Timing**: Tổng thời lượng 15-20 phút

**Tools gợi ý:**
- **Screen recorder**: OBS Studio (free)
- **Cursor highlight**: ZoomIt
- **Slide**: PowerPoint hoặc Google Slides

---

**🎉 Chúc bạn demo thành công! Good luck!** 🚀
