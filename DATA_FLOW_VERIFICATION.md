# 🔍 Luồng Hoạt Động & Minh Chứng từng Step

> Tài liệu mô tả chi tiết data flow của hệ thống Air Quality Monitoring và cách kiểm tra minh chứng từng bước.

---

## 📊 Sơ đồ Luồng Dữ Liệu

```
┌──────────────┐
│   Producer   │  Simulates OpenWeather API
│ (sensor_sim) │  Every 5 seconds
└──────┬───────┘
       │ Publish JSON messages
       │ Topic: air_quality_data
       ▼
┌──────────────┐
│    Kafka     │  Message Queue
│  (Strimzi)   │  Stores messages temporarily
└──────┬───────┘
       │ Subscribe & Stream
       │
       ▼
┌──────────────┐
│    Spark     │  Stream Processing
│  Streaming   │  - Parse JSON
│              │  - Add city mapping
│              │  - Transform schema
└──────┬───────┘
       │
       ├─────────────────┬─────────────────┐
       │                 │                 │
       ▼                 ▼                 ▼
┌──────────┐      ┌──────────┐     ┌──────────┐
│   HDFS   │      │PostgreSQL│     │ Console  │
│ Parquet  │      │  Table   │     │  Logs    │
│  Files   │      │          │     │          │
└──────────┘      └────┬─────┘     └──────────┘
                       │
                       ▼
                 ┌──────────┐
                 │ Grafana  │  Visualization
                 │Dashboard │
                 └──────────┘
```

---

## 🔄 Chi Tiết từng Step

### **Step 1: Producer tạo dữ liệu giả lập**

**Chức năng:**
- Giả lập OpenWeather API
- Tạo dữ liệu AQI cho 3 thành phố: Hanoi, HCM, DaNang
- Publish vào Kafka topic `air_quality_data` mỗi 5 giây

**Minh chứng:**

```powershell
# Xem logs producer để thấy messages được tạo
kubectl logs -f deployment/producer -n air-quality --tail=20
```

**Output mẫu:**
```
Publishing message to Kafka topic: air_quality_data
{
  "timestamp_unix": 1768328352,
  "latitude": 21.0285,
  "longitude": 105.8542,
  "aqi": 3,
  "pm2_5": 74.17,
  "pm10": 35.92,
  "co": 203.18,
  "no2": 1.28
}
Message published successfully
Sleeping for 5 seconds...
```

**Xác nhận:** Producer publish JSON messages mỗi 5 giây ✅

---

### **Step 2: Kafka nhận và lưu trữ messages**

**Chức năng:**
- Nhận messages từ Producer
- Lưu trữ tạm thời trong topic
- Cung cấp cho Spark consumer

**Minh chứng 1: Xem Kafka topics**

```powershell
kubectl exec -it air-quality-kafka-air-quality-pool-0 -n air-quality -- \
  /opt/kafka/bin/kafka-topics.sh \
  --list \
  --bootstrap-server localhost:29092
```

**Output mẫu:**
```
air_quality_data
__consumer_offsets
```

**Minh chứng 2: Consume messages từ topic**

```powershell
kubectl exec -it air-quality-kafka-air-quality-pool-0 -n air-quality -- \
  /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:29092 \
  --topic air_quality_data \
  --from-beginning \
  --max-messages 5
```

**Output mẫu:**
```
{"timestamp_unix":1768328352,"latitude":21.0285,"longitude":105.8542,"aqi":3,"pm2_5":74.17,...}
{"timestamp_unix":1768328357,"latitude":10.8231,"longitude":106.6297,"aqi":5,"pm2_5":150.66,...}
{"timestamp_unix":1768328362,"latitude":16.0544,"longitude":108.2022,"aqi":1,"pm2_5":19.14,...}
Processed a total of 5 messages
```

**Xác nhận:** Kafka lưu trữ messages thành công ✅

---

### **Step 3: Spark Streaming đọc và xử lý**

**Chức năng:**
- Subscribe Kafka topic `air_quality_data`
- Parse JSON schema
- Transform: thêm cột `city` (Hanoi/HCM/DaNang), `timestamp`, `ingested_at`
- Chạy micro-batch mỗi 5 giây

**Minh chứng 1: Xem Spark logs processing**

```powershell
kubectl logs -f deployment/spark-processor -n air-quality --tail=50
```

**Output mẫu:**
```
>>> Đang xử lý dữ liệu từ OpenWeatherMap API giả lập...

=== Batch 1 ===
+--------------+-----------------------+---------+--------+---+------+-----+------+----+
|timestamp_unix|processed_time         |longitude|latitude|aqi|pm2_5 |pm10 |co    |no2 |
+--------------+-----------------------+---------+--------+---+------+-----+------+----+
|1768328352    |2026-01-13 18:18:48.643|105.8542 |21.0285 |3  |74.17 |35.92|203.18|1.28|
|1768328352    |2026-01-13 18:18:48.643|106.6297 |10.8231 |3  |100.83|18.59|299.89|0.55|
|1768328352    |2026-01-13 18:18:48.643|108.2022 |16.0544 |3  |61.48 |20.39|204.61|0.71|
+--------------+-----------------------+---------+--------+---+------+-----+------+----+

=== Batch 2 ===
...
```

**Minh chứng 2: Kiểm tra Spark application status**

```powershell
# Mở Spark Master UI
minikube service spark-master -n air-quality
# Truy cập: http://MINIKUBE_IP:30080
```

**Trong UI:**
- **Running Applications**: `OpenWeatherProcessor` (Status: RUNNING)
- **Executors**: 2 executors đang active
- **Cores Used**: 2/2

**Xác nhận:** Spark đọc Kafka và process batches thành công ✅

---

### **Step 4: Ghi dữ liệu vào HDFS (Parquet)**

**Chức năng:**
- Sau khi transform, Spark ghi Parquet files vào HDFS
- Path: `/data/air_quality_v2/`
- Format: Snappy-compressed Parquet

**Minh chứng 1: Liệt kê files trong HDFS**

```powershell
kubectl exec -it namenode-0 -n air-quality -- \
  hdfs dfs -ls /data/air_quality_v2
```

**Output mẫu:**
```
Found 7 items
-rw-r--r--   3 root supergroup          0 2026-01-13 18:19 /data/air_quality_v2/_SUCCESS
drwxr-xr-x   - root supergroup          0 2026-01-12 17:57 /data/air_quality_v2/_spark_metadata
-rw-r--r--   3 root supergroup       2925 2026-01-13 18:19 /data/air_quality_v2/part-00000-1c37afdb-...snappy.parquet
-rw-r--r--   3 root supergroup     150758 2026-01-13 18:18 /data/air_quality_v2/part-00000-26569eed-...snappy.parquet
-rw-r--r--   3 root supergroup       1038 2026-01-13 18:18 /data/air_quality_v2/part-00000-8026f422-...snappy.parquet
```

**Minh chứng 2: Đọc nội dung Parquet file (sample)**

```powershell
kubectl exec -it namenode-0 -n air-quality -- \
  hdfs dfs -cat /data/air_quality_v2/part-00000-*.parquet | head -c 200
```

**Output:** Binary Parquet data (không đọc được text, chứng tỏ đúng format)

**Minh chứng 3: Xem HDFS NameNode UI**

```powershell
minikube service namenode -n air-quality
# Truy cập: http://MINIKUBE_IP:30870
```

**Trong UI:**
- **Utilities → Browse the file system**
- Navigate: `/data/air_quality_v2/`
- Thấy danh sách Parquet files với size > 0

**Xác nhận:** Parquet files được ghi vào HDFS thành công ✅

---

### **Step 5: Ghi dữ liệu vào PostgreSQL**

**Chức năng:**
- Spark ghi cùng dữ liệu vào PostgreSQL
- Database: `air_quality`
- Table: `air_quality_final`
- Schema: `timestamp`, `city`, `aqi`, `pm2_5`, `pm10`, `co`, `no2`, `ingested_at`

**Minh chứng 1: Đếm số records**

```powershell
kubectl exec -it postgres-0 -n air-quality -- \
  psql -U admin -d air_quality -c "SELECT COUNT(*) FROM air_quality_final;"
```

**Output mẫu:**
```
 count
-------
  8241
(1 row)
```

**Minh chứng 2: Xem sample data**

```powershell
kubectl exec -it postgres-0 -n air-quality -- \
  psql -U admin -d air_quality -c \
  "SELECT city, timestamp, aqi, pm2_5, ingested_at FROM air_quality_final ORDER BY ingested_at DESC LIMIT 5;"
```

**Output mẫu:**
```
  city  |      timestamp      | aqi | pm2_5  |       ingested_at
--------+---------------------+-----+--------+-------------------------
 Hanoi  | 2026-01-13 18:19:36 |   3 | 119.87 | 2026-01-13 18:19:36.182
 HCM    | 2026-01-13 18:19:36 |   1 |  18.70 | 2026-01-13 18:19:36.182
 DaNang | 2026-01-13 18:19:36 |   3 |  50.15 | 2026-01-13 18:19:36.182
 Hanoi  | 2026-01-13 18:19:31 |   3 | 140.51 | 2026-01-13 18:19:31.167
 HCM    | 2026-01-13 18:19:31 |   3 | 141.04 | 2026-01-13 18:19:31.167
```

**Minh chứng 3: Phân tích theo city**

```powershell
kubectl exec -it postgres-0 -n air-quality -- \
  psql -U admin -d air_quality -c \
  "SELECT city, COUNT(*) as count, ROUND(AVG(aqi), 2) as avg_aqi FROM air_quality_final GROUP BY city ORDER BY city;"
```

**Output mẫu:**
```
  city  | count | avg_aqi
--------+-------+---------
 DaNang |  2741 |    3.03
 Hanoi  |  2741 |    3.02
 HCM    |  2741 |    3.00
(3 rows)
```

**Xác nhận:**
- PostgreSQL nhận dữ liệu liên tục ✅
- Dữ liệu phân bố đều cho 3 thành phố ✅
- Trung bình AQI ~3 (hợp lý với dữ liệu giả lập) ✅

---

### **Step 6: Grafana hiển thị dashboard**

**Chức năng:**
- Kết nối PostgreSQL
- Query dữ liệu real-time
- Visualize: Time-series charts, tables, heatmaps

**Minh chứng 1: Truy cập Grafana**

```powershell
minikube service grafana -n air-quality
# URL: http://MINIKUBE_IP:30300
# Login: admin / admin123
```

**Minh chứng 2: Setup PostgreSQL Data Source (Nếu chưa có)**

> **Lưu ý:** Nếu vào Grafana lần đầu chưa thấy datasource, làm theo các bước sau:

1. **Vào Configuration → Data Sources**
   - Click **Configuration** (cog icon) → **Data Sources**
   - Click **Add data source**

2. **Chọn PostgreSQL**
   - Search: "PostgreSQL"
   - Click **PostgreSQL**

3. **Điền thông tin kết nối**
   ```
   Name: PostgreSQL Air Quality (hoặc tên bất kỳ)
   Host: postgres:5432
   Database: air_quality
   User: admin
   Password: password123
   SSL Mode: disable
   ```
   
   **Chi tiết các field:**
   - **Host**: Tên service Kubernetes + port (postgres là service name)
   - **Database**: `air_quality` (do secret setup)
   - **User**: `admin` (do secret setup)
   - **Password**: `password123` (do secret setup)
   - **SSL Mode**: `disable` (local network, không cần SSL)

4. **Test Connection**
   - Click **Save & Test**
   - Nếu thấy "Database Connection OK" → ✅ Success

5. **Troubleshooting nếu connection fail:**
   
   ```powershell
   # Kiểm tra PostgreSQL pod running
   kubectl get pods -n air-quality | findstr postgres
   
   # Kiểm tra service
   kubectl get svc -n air-quality | findstr postgres
   
   # Test connection từ Grafana pod
   kubectl exec -it grafana-* -n air-quality -- \
     psql -h postgres -p 5432 -U admin -d air_quality -c "SELECT 1"
   ```

**Minh chứng 3: Tạo Dashboard (Từ scratch)**

Nếu chưa có dashboard "Air Quality Monitoring", tạo mới:

1. **Tạo Dashboard mới**
   - Click **Create → Dashboard**
   - Click **Add panel**

2. **Panel 1: Time-series Chart (PM2.5 trends)**
   
   **Query:**
   ```sql
   SELECT
     ingested_at as time,
     pm2_5,
     city
   FROM air_quality_final
   WHERE ingested_at > now() - interval '1 hour'
   ORDER BY ingested_at
   ```
   
   **Panel Settings:**
   - **Title**: PM2.5 Trends
   - **Type**: Time series
   - **Axes → Y-axis**: Min 0, Max 200
   - **Legend**: Show (Multiple)
   - **Refresh**: Auto 5s

3. **Panel 2: Table (Latest values)**
   
   **Query:**
   ```sql
   SELECT
     city,
     ROUND(AVG(aqi), 2) as aqi,
     ROUND(AVG(pm2_5), 2) as pm2_5,
     ROUND(AVG(pm10), 2) as pm10,
     MAX(ingested_at) as last_update
   FROM air_quality_final
   WHERE ingested_at > now() - interval '5 minutes'
   GROUP BY city
   ORDER BY city
   ```
   
   **Panel Settings:**
   - **Title**: Latest Readings
   - **Type**: Table
   - **Column width**: Auto

4. **Panel 3: Gauge (Current AQI)**
   
   **Query:**
   ```sql
   SELECT
     ROUND(AVG(aqi), 0) as aqi_avg
   FROM air_quality_final
   WHERE ingested_at > now() - interval '1 minute'
   ```
   
   **Panel Settings:**
   - **Title**: Current AQI (All cities)
   - **Type**: Gauge
   - **Thresholds**: Green (0-50), Yellow (50-100), Red (100+)
   - **Unit**: None

5. **Save Dashboard**
   - Click **Save** (Ctrl+S)
   - Name: "Air Quality Monitoring"
   - Folder: "General"

**Minh chứng 4: Xem Dashboard chạy**

- Dashboard auto-refresh mỗi 5s
- Thấy 3 lines PM2.5: Hanoi, HCM, DaNang
- Table cập nhật với latest readings
- Gauge thay đổi theo real-time AQI

**Xác nhận:** Grafana hiển thị dữ liệu real-time thành công ✅

---

## 🧪 Test E2E Flow (End-to-End)

### Test Scenario: Tạo dữ liệu mới → Xuất hiện trong tất cả outputs

**Bước 1: Ghi lại timestamp hiện tại**

```powershell
# Xem batch gần nhất
kubectl logs deployment/spark-processor -n air-quality --tail=20 | Select-String "Batch"
# Output: === Batch 125 ===
```

**Bước 2: Đợi 10 giây (2 batches)**

```powershell
Start-Sleep -Seconds 10
```

**Bước 3: Kiểm tra Kafka có message mới**

```powershell
kubectl exec -it air-quality-kafka-air-quality-pool-0 -n air-quality -- \
  /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:29092 \
  --topic air_quality_data \
  --max-messages 3 \
  --from-beginning
```

**Bước 4: Kiểm tra Spark đã process**

```powershell
kubectl logs deployment/spark-processor -n air-quality --tail=20 | Select-String "Batch"
# Output: === Batch 127 === (tăng lên)
```

**Bước 5: Kiểm tra HDFS có file mới**

```powershell
kubectl exec -it namenode-0 -n air-quality -- \
  hdfs dfs -ls -t /data/air_quality_v2/ | head -5
# File mới nhất sẽ ở trên cùng
```

**Bước 6: Kiểm tra PostgreSQL count tăng**

```powershell
# Count trước
kubectl exec -it postgres-0 -n air-quality -- \
  psql -U admin -d air_quality -c "SELECT COUNT(*) FROM air_quality_final;"
# Output: 8241

# Đợi 10s
Start-Sleep -Seconds 10

# Count sau
kubectl exec -it postgres-0 -n air-quality -- \
  psql -U admin -d air_quality -c "SELECT COUNT(*) FROM air_quality_final;"
# Output: 8250+ (tăng lên)
```

**Bước 7: Xem Grafana dashboard refresh**

- Mở Grafana UI
- Dashboard tự động refresh
- Thấy điểm dữ liệu mới xuất hiện trên chart

**✅ Kết luận:** Dữ liệu flow từ Producer → Kafka → Spark → HDFS/PostgreSQL/Grafana hoàn toàn tự động!

---

## 📈 Metrics & Monitoring

### Resource Usage

```powershell
# CPU/Memory của pods
kubectl top pods -n air-quality
```

**Output mẫu:**
```
NAME                               CPU(cores)   MEMORY(bytes)
kafka-0                            45m          1024Mi
namenode-0                         25m          768Mi
postgres-0                         18m          234Mi
producer-6b9c8d7f5e-8jhg7          5m           128Mi
spark-master-5c4d6e8f9a-2nkl3      32m          512Mi
spark-processor-68cb7dcd78-7w2wm   65m          1580Mi
spark-worker-6c8d788744-24jtx      28m          678Mi
```

### Kafka Lag (Consumer đọc kịp Producer không?)

```powershell
kubectl exec -it air-quality-kafka-air-quality-pool-0 -n air-quality -- \
  /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:29092 \
  --describe \
  --group spark-kafka-source-*
```

**Output mẫu:**
```
GROUP                  TOPIC             PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
spark-kafka-source-... air_quality_data  0          12450           12450           0
```

**LAG = 0** → Spark đọc kịp Producer, không bị tụt hậu ✅

---

## 🚨 Troubleshooting Common Issues

### Issue 1: Spark logs không thấy batch mới

**Kiểm tra:**
```powershell
kubectl logs deployment/spark-processor -n air-quality --tail=100 | Select-String "error|Error|Exception"
```

**Nguyên nhân thường gặp:**
- Kafka topic không tồn tại
- Spark executors crash (xem worker logs)
- Out of memory

### Issue 2: PostgreSQL không nhận data

**Kiểm tra:**
```powershell
kubectl exec -it postgres-0 -n air-quality -- \
  psql -U admin -d air_quality -c "\dt"
# Verify table air_quality_final tồn tại
```

**Nguyên nhân:**
- Table chưa được tạo (Spark sẽ tạo tự động lần đầu)
- Connection string sai
- Credentials sai

### Issue 3: HDFS không có file

**Kiểm tra:**
```powershell
kubectl exec -it namenode-0 -n air-quality -- \
  hdfs dfs -ls /data/
# Verify /data/air_quality_v2 tồn tại
```

**Nguyên nhân:**
- NameNode chưa sẵn sàng
- Permission denied
- Disk full

---

## 📝 Summary Checklist

Để verify toàn bộ flow hoạt động:

- [x] Producer logs hiển thị "Message published successfully"
- [x] Kafka topic `air_quality_data` có messages
- [x] Spark logs hiển thị "=== Batch X ===" tăng dần
- [x] HDFS có Parquet files trong `/data/air_quality_v2/`
- [x] PostgreSQL table `air_quality_final` có records > 0
- [x] PostgreSQL count tăng mỗi 5 giây
- [x] Grafana dashboard hiển thị time-series charts
- [x] Kafka consumer lag = 0

**Nếu tất cả ✅ → Hệ thống hoạt động hoàn hảo!** 🎉
