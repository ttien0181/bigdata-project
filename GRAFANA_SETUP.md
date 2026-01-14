# 📊 Hướng Dẫn Setup Grafana & Tạo Dashboards

> Chi tiết từng bước để setup Grafana datasource PostgreSQL và tạo dashboards hiển thị dữ liệu Air Quality

---

## 🔑 Thông Tin Đăng Nhập Grafana

| Thông tin | Giá trị |
|-----------|--------|
| **URL** | http://MINIKUBE_IP:30300 |
| **Username** | admin |
| **Password** | admin123 |
| **Database Host** | postgres (Kubernetes service) |
| **Database Port** | 5432 |
| **Database Name** | air_quality |
| **DB User** | admin |
| **DB Password** | password123 |

---

## 📋 Bước 1: Mở Grafana

```powershell
# Mở Grafana UI (tự động mở browser)
minikube service grafana -n air-quality
```

Hoặc nhập URL thủ công:
```
http://192.168.49.2:30300
```

**Login:**
- Username: `admin`
- Password: `admin123`
- Click **Log in**

---

## 🔌 Bước 2: Tạo PostgreSQL Data Source

### 2.1 Vào Data Sources

1. Click **Configuration** (⚙️ icon) → **Data Sources**
2. Click **Add data source**
3. Search `PostgreSQL` → Click **PostgreSQL**

### 2.2 Điền thông tin kết nối

Nhập các trường sau:

```
┌─────────────────────────────────────┐
│ Name: PostgreSQL Air Quality        │ (Tên tuỳ ý)
├─────────────────────────────────────┤
│ Host: postgres:5432                 │ (K8s service)
│ Database: air_quality               │ (Schema name)
│ User: admin                         │ (PostgreSQL user)
│ Password: password123               │ (PostgreSQL password)
│ SSL Mode: disable                   │ (No SSL)
│ Version: 11                         │ (Auto-detect)
│ TimescaleDB: OFF                    │
└─────────────────────────────────────┘
```

**Screenshots:**
```
┌─────────────────────────────────────────┐
│ Configuration                           │
├─────────────────────────────────────────┤
│ [1] Name                                │
│     PostgreSQL Air Quality              │
│                                         │
│ [2] PostgreSQL Connection               │
│     Host: postgres:5432                 │
│     Database: air_quality               │
│     User: admin                         │
│     Password: ••••••••••                │
│     SSL Mode: [disable ▼]               │
│     Default region: (blank)             │
│                                         │
│ [3] PostgreSQL details                  │
│     Version: [11 ▼]                     │
│     Min interval: 10s                   │
│     TimescaleDB: [OFF]                  │
│                                         │
│ [Save & test] [Test]                    │
└─────────────────────────────────────────┘
```

### 2.3 Test Connection

1. Click **Save & test** button
2. Nếu kết nối thành công, sẽ thấy:
   ```
   ✅ Database Connection OK
   ✅ 9.x (PostgreSQL version)
   ```

3. Nếu fail, kiểm tra:
   - PostgreSQL pod running: `kubectl get pods -n air-quality | grep postgres`
   - Service tồn tại: `kubectl get svc -n air-quality | grep postgres`
   - Credentials đúng: Kiểm tra secret `kubectl get secret postgres-secret -n air-quality -o yaml`

### 2.4 Xác nhận Data Source

- Vào **Configuration → Data Sources** lại
- Thấy **PostgreSQL Air Quality** trong danh sách
- Status: Green ✅

---

## 📈 Bước 3: Tạo Dashboard

### 3.1 Tạo Dashboard mới

1. Click **Create** (+ icon) → **Dashboard**
2. Click **Add panel** → **Add new panel**

### 3.2 Panel 1: PM2.5 Time-Series Chart

**Query Builder:**

```sql
SELECT
  ingested_at as time,
  pm2_5,
  city
FROM air_quality_final
WHERE ingested_at > now() - interval '1 hour'
ORDER BY ingested_at
```

**Hoặc dùng Query Editor:**
- Click **Code** (để dùng SQL)
- Paste SQL trên
- Run query

**Panel Settings:**

1. **General**
   - Title: `PM2.5 Trends`
   - Description: `PM2.5 levels for 3 cities (Hanoi, HCM, DaNang)`

2. **Visualization**
   - Type: `Time series`
   - Panel type: `Time series`

3. **Options**
   - **Show legend**: ON
   - **Legend placement**: `Bottom`
   - **Legend mode**: `List`

4. **Field overrides** (optional)
   - PM2.5 unit: µg/m³
   - Min Y-axis: 0
   - Max Y-axis: 200

5. **Refresh**
   - Auto refresh: `5s`
   - Relative time: `Last 1 hour`

6. Click **Save** (Ctrl+S)

**Output mẫu:**
```
PM2.5 Trends
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  200 │     ╱╲    ╱╲
      │    ╱  ╲  ╱  ╲
  100 │   ╱    ╲╱    
      │  ╱ Hanoi      ╱
    0 │_╱___________╱_____
      │ HCM (line)
      │ DaNang (line)
     18:00    18:30    19:00
```

---

### 3.3 Panel 2: Latest AQI Values Table

**Query:**

```sql
SELECT
  city,
  ROUND(AVG(aqi), 2)::text as aqi,
  ROUND(AVG(pm2_5), 2)::text as pm2_5,
  ROUND(AVG(pm10), 2)::text as pm10,
  ROUND(AVG(co), 2)::text as co,
  ROUND(AVG(no2), 2)::text as no2,
  MAX(ingested_at)::text as last_update
FROM air_quality_final
WHERE ingested_at > now() - interval '5 minutes'
GROUP BY city
ORDER BY city
```

**Panel Settings:**

1. **General**
   - Title: `Latest Readings (Last 5 min)`

2. **Visualization**
   - Type: `Table`

3. **Options**
   - **Show header**: ON
   - **Footer mode**: `Show total`
   - **Table type**: `Fixed size`

4. **Column Configuration**
   - **city**: Width auto, Align left
   - **aqi**: Decimals 0, Unit none
   - **pm2_5**: Decimals 1, Unit µg/m³
   - **pm10**: Decimals 1, Unit µg/m³
   - **last_update**: Type DateTime, Format: `YYYY-MM-DD HH:mm:ss`

5. Click **Save**

**Output mẫu:**
```
Latest Readings (Last 5 min)
┌─────────┬───────┬────────┬────────┬──────┬──────┬──────────────────────┐
│ city    │ aqi   │ pm2_5  │ pm10   │ co   │ no2  │ last_update          │
├─────────┼───────┼────────┼────────┼──────┼──────┼──────────────────────┤
│ DaNang  │ 3.03  │ 50.15  │ 30.13  │ 278  │ 0.86 │ 2026-01-13 18:19:36  │
│ Hanoi   │ 3.02  │ 119.87 │ 11.72  │ 232  │ 1.48 │ 2026-01-13 18:19:36  │
│ HCM     │ 3.00  │ 18.70  │ 34.89  │ 269  │ 1.03 │ 2026-01-13 18:19:36  │
└─────────┴───────┴────────┴────────┴──────┴──────┴──────────────────────┘
Total: 3 rows
```

---

### 3.4 Panel 3: Current AQI Gauge

**Query:**

```sql
SELECT
  ROUND(AVG(aqi), 1) as "AQI Average"
FROM air_quality_final
WHERE ingested_at > now() - interval '1 minute'
```

**Panel Settings:**

1. **General**
   - Title: `Current AQI Level`
   - Description: `Real-time AQI average across all cities`

2. **Visualization**
   - Type: `Gauge`

3. **Options**
   - **Min value**: 0
   - **Max value**: 10
   - **Decimals**: 1

4. **Thresholds**
   - Base color: Green
   - Step 1: value=5 → Yellow
   - Step 2: value=8 → Red

5. **Gauge display**
   - Show: Value + Percent
   - Orientation: Auto

6. Click **Save**

**Output mẫu:**
```
Current AQI Level
┌─────────────────┐
│      3.0        │  ◄ Needle position
│                 │
│ ◄─ Green Yellow ◄ Red ─►
│ 0              10
└─────────────────┘
Real-time AQI average across all cities
```

---

### 3.5 Panel 4: AQI Distribution by City (Pie Chart)

**Query:**

```sql
SELECT
  city,
  COUNT(*) as count
FROM air_quality_final
WHERE ingested_at > now() - interval '1 hour'
GROUP BY city
ORDER BY count DESC
```

**Panel Settings:**

1. **General**
   - Title: `Data Distribution by City`

2. **Visualization**
   - Type: `Pie chart`

3. **Options**
   - **Display**: Pie chart
   - **Legend**: ON (Bottom)
   - **Tooltip**: Show value
   - **Value format**: Decimals 0

4. Click **Save**

**Output mẫu:**
```
Data Distribution by City
┌─────────────────────┐
│        ◐ Hanoi      │ 33.3%
│       ╱ │ ╲         │
│      ╱  │  ╲        │
│     │HCM  DaNang│   │ 33.3% each
│      ╲  │  ╱        │
│       ╲ │ ╱         │
│        ◑           │
└─────────────────────┘
```

---

## 💾 Bước 4: Lưu Dashboard

1. **Đặt tên Dashboard**
   - Title: `Air Quality Monitoring`
   - Tags: `air-quality`, `monitoring`, `real-time`

2. **Chọn folder**
   - Folder: `General` (hoặc tạo folder mới)

3. **Click Save** (Ctrl+S)

Dashboard sẽ được lưu với URL: `http://MINIKUBE_IP:30300/d/xxxxx/air-quality-monitoring`

---

## 🔄 Bước 5: Auto-Refresh Dashboard

1. Click **Refresh** icon (circular arrow) ở top-right
2. Chọn `5s` → Auto-refresh mỗi 5 giây
3. Dashboard sẽ tự update khi Spark process batches mới

---

## ⚙️ Advanced: Alerting (Optional)

### Thiết lập Alert khi AQI cao

1. **Tạo Alert Rule**
   - Vào **Alerting → Alert rules**
   - Click **New alert rule**

2. **Query:**
   ```sql
   SELECT AVG(aqi) as avg_aqi FROM air_quality_final 
   WHERE ingested_at > now() - interval '5 minutes'
   ```

3. **Condition:**
   - When: `avg_aqi > 5`
   - Evaluate every: `1m`
   - For: `1m`

4. **Notification**
   - Send to: Email/Slack (tùy setup)

---

## 🐛 Troubleshooting Grafana

### Issue 1: "Connection refused" khi test datasource

**Nguyên nhân:** PostgreSQL pod không running

**Fix:**
```powershell
# Check PostgreSQL pod
kubectl get pods -n air-quality | grep postgres

# If not running, restart
kubectl delete pod postgres-0 -n air-quality
# K8s sẽ tự tạo pod mới
```

---

### Issue 2: Datasource shows "No data"

**Nguyên nhân:** 
- Spark chưa ghi data
- Table chưa tồn tại
- Time range quá hẹp

**Fix:**
```powershell
# Check data exists
kubectl exec -it postgres-0 -n air-quality -- \
  psql -U admin -d air_quality -c \
  "SELECT COUNT(*) FROM air_quality_final;"

# If count=0, wait for Spark to process batches
# Check Spark logs
kubectl logs deployment/spark-processor -n air-quality --tail=20
```

---

### Issue 3: Dashboard chậm, query timeout

**Nguyên nhân:** Query quá nặng hoặc database slow

**Fix:**
```sql
-- Giảm time range
WHERE ingested_at > now() - interval '1 hour'  -- Thay vì 7 days

-- Hoặc add index
CREATE INDEX idx_ingested_at ON air_quality_final(ingested_at);
```

---

### Issue 4: Panel hiển thị "No data"

**Kiểm tra:**
1. **Datasource kết nối OK?** → Click "Save & test"
2. **Query syntax đúng?** → Chạy thủ công trong psql
3. **Thời gian range có data?** → Kiểm tra `SELECT COUNT(*)`
4. **Các cột đã select đúng?** → Column phải tồn tại trong table

---

## 📊 SQL Queries Hữu Ích

### Query tổng quát dữ liệu

```sql
-- Xem tất cả columns
SELECT * FROM air_quality_final LIMIT 5;

-- Count by city
SELECT city, COUNT(*) FROM air_quality_final GROUP BY city;

-- Hourly average
SELECT 
  DATE_TRUNC('hour', ingested_at) as hour,
  city,
  AVG(aqi) as avg_aqi,
  AVG(pm2_5) as avg_pm25
FROM air_quality_final
GROUP BY hour, city
ORDER BY hour DESC;

-- Max pollution today
SELECT
  city,
  MAX(aqi) as max_aqi,
  MAX(pm2_5) as max_pm25
FROM air_quality_final
WHERE DATE(ingested_at) = CURRENT_DATE
GROUP BY city;
```

---

## 📚 Variable & Templating (Advanced)

Để tạo dashboard linh hoạt với dropdown chọn city:

1. Click **Dashboard settings** (gear icon)
2. Click **Variables**
3. Click **New variable**

**Config:**
```
Name: city
Type: Query
Data source: PostgreSQL Air Quality
Query: SELECT DISTINCT city FROM air_quality_final ORDER BY city
```

4. Dùng variable trong query:
   ```sql
   WHERE city = '$city'  -- hoặc ${city:singlequote}
   ```

---

## ✅ Checklist Setup Grafana

- [ ] Truy cập được Grafana UI (http://MINIKUBE_IP:30300)
- [ ] Login thành công (admin/admin123)
- [ ] PostgreSQL datasource tạo được
- [ ] Test datasource → "Connection OK"
- [ ] Dashboard "Air Quality Monitoring" tạo được
- [ ] Panel 1 (PM2.5 chart) hiển thị 3 lines
- [ ] Panel 2 (Table) hiển thị 3 rows (3 cities)
- [ ] Panel 3 (Gauge) hiển thị AQI value
- [ ] Auto-refresh 5s hoạt động
- [ ] Data cập nhật real-time khi Spark process batches

---

## 🎥 Tips Chụp Screenshot cho Report

1. **Toàn dashboard**: `Ctrl+F5` → Full screen view
2. **Individual panel**: Hover → Click 3 dots → Inspect
3. **Export**: Click 3 dots → Export
4. **Refresh UI**: `F5` hoặc click refresh icon

---

**🎉 Hoàn tất! Dashboard Grafana đã sẵn sàng hiển thị dữ liệu real-time!** 📊
