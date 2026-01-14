# 🚀 Hướng Dẫn Chi Tiết: Chạy Air Quality Project trên Minikube (Windows)

> Hướng dẫn từng bước với output mẫu để deploy Big Data Air Quality monitoring system lên Kubernetes (Minikube)

---

## 📋 Yêu cầu Hệ Thống

- **OS**: Windows 10/11 (Pro, Enterprise hoặc Home với WSL2)
- **RAM**: Tối thiểu 12GB (8GB cho Minikube, 4GB cho Windows)
- **CPU**: 4 cores trở lên
- **Disk**: 40GB dung lượng trống
- **Internet**: Để tải images và dependencies

---

## 📦 Các Công Cụ Cần Thiết

| Công cụ | Phiên bản | Mục đích |
|---------|-----------|----------|
| Minikube | v1.35+ | Kubernetes cluster local |
| kubectl | v1.31+ | Quản lý Kubernetes |
| Docker Desktop | v27+ | Build & run containers |
| PowerShell | 5.1+ hoặc 7+ | Chạy scripts |

---

## 1️⃣ BƯỚC 1: Cài Đặt Prerequisites

### 1.1 Cài đặt Minikube

**Download Minikube:**
```powershell
# Mở PowerShell as Administrator
# Giải thích: Tải file cài đặt Minikube phiên bản mới nhất cho Windows
Invoke-WebRequest -OutFile 'minikube.exe' -Uri 'https://github.com/kubernetes/minikube/releases/latest/download/minikube-windows-amd64.exe' -UseBasicParsing

# Giải thích: Tạo thư mục C:\minikube và thêm vào system PATH để chạy minikube từ bất kỳ đâu
New-Item -Path 'C:\minikube' -Type Directory -Force
Move-Item 'minikube.exe' 'C:\minikube\minikube.exe'
$env:Path += ";C:\minikube"
[Environment]::SetEnvironmentVariable("Path", $env:Path, [System.EnvironmentVariableTarget]::Machine)
```

**Output mẫu:**
```
Directory: C:\

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d-----        1/12/2026   3:30 PM                minikube
```

**Kiểm tra cài đặt:**
```powershell
# Giải thích: Hiển thị phiên bản Minikube đã cài để xác nhận cài đặt thành công
minikube version
```

**Output mẫu:**
```
minikube version: v1.35.0
commit: dd5d320e41b5451cdf3c01891bc4e13d189586ed
```

---

### 1.2 Cài đặt kubectl

```powershell
# Giải thích: Tải kubectl - công cụ command-line để quản lý Kubernetes cluster
curl.exe -LO "https://dl.k8s.io/release/v1.32.0/bin/windows/amd64/kubectl.exe"

# Giải thích: Di chuyển kubectl.exe vào thư mục C:\minikube (đã có trong PATH)
Move-Item kubectl.exe C:\minikube\kubectl.exe
```

**Kiểm tra:**
```powershell
# Giải thích: Hiển thị phiên bản kubectl client để xác nhận cài đặt thành công
kubectl version --client
```

**Output mẫu:**
```
Client Version: v1.32.3
Kustomize Version: v5.0.4-0.20230601165947-6ce0bf390ce3
```

---

### 1.3 Cài đặt Docker Desktop

1. Tải từ: https://www.docker.com/products/docker-desktop
2. Chạy installer
3. Khởi động lại Windows
4. Mở Docker Desktop và chờ khởi động

**Kiểm tra:**
```powershell
# Giải thích: Hiển thị phiên bản Docker client và server để xác nhận Docker Desktop đã chạy
docker version
```

**Output mẫu:**
```
Client:
 Version:           27.5.1
 API version:       1.47
 Go version:        go1.22.10
 Git commit:        7de81f1
 Built:             Wed Dec 18 15:21:25 2024
 OS/Arch:           windows/amd64
 Context:           default

Server: Docker Desktop 4.37.4 (178371)
 Engine:
  Version:          27.5.1
  API version:      1.47 (minimum version 1.24)
  Go version:       go1.22.10
  Git commit:       48c5c73
  Built:            Wed Dec 18 15:21:30 2024
  OS/Arch:          linux/amd64
```

---

## 2️⃣ BƯỚC 2: Khởi Động Minikube Cluster

### 2.1 Start Minikube với cấu hình phù hợp

```powershell
# Giải thích: Khởi động Minikube cluster với 4 CPUs, 8GB RAM, 30GB disk, sử dụng Docker driver
# Lưu ý: Chạy trong PowerShell Administrator, hoặc trong VSCode với quyền admin
minikube start --cpus=4 --memory=8192 --disk-size=30g --driver=docker
```

**Output mẫu:**
```
😄  minikube v1.35.0 on Microsoft Windows 11 Home 10.0.26100.7462
✨  Using the docker driver based on user configuration
📌  Using Docker Desktop driver with root privileges
👍  Starting "minikube" primary control-plane node in "minikube" cluster
🚜  Pulling base image v0.0.45 ...
🔥  Creating docker container (CPUs=4, Memory=8192MB) ...
🐳  Preparing Kubernetes v1.31.0 on Docker 27.3.1 ...
    ▪ Generating certificates and keys ...
    ▪ Booting up control plane ...
    ▪ Configuring RBAC rules ...
🔗  Configuring bridge CNI (Container Networking Interface) ...
🔎  Verifying Kubernetes components...
    ▪ Using image gcr.io/k8s-minikube/storage-provisioner:v5
🌟  Enabled addons: storage-provisioner, default-storageclass
🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```

**Thời gian**: ~3-5 phút lần đầu (tùy tốc độ internet)

---

### 2.2 Kiểm tra Minikube status

```powershell
# Giải thích: Hiển thị trạng thái của Minikube cluster (host, kubelet, apiserver)
minikube status
```

**Output mẫu:**
```
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured
```

---

### 2.3 Kiểm tra Kubernetes cluster

```powershell
# Giải thích: Hiển thị thông tin cluster (API server URL, CoreDNS URL)
kubectl cluster-info
```

**Output mẫu:**
```
Kubernetes control plane is running at https://127.0.0.1:51812
CoreDNS is running at https://127.0.0.1:51812/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```

---

### 2.4 Lấy Minikube IP

```powershell
# Giải thích: Hiển thị địa chỉ IP của Minikube cluster để truy cập services qua NodePort
minikube ip
```

**Output mẫu:**
```
192.168.49.2
```

> ⚠️ **Lưu IP này** - Bạn sẽ dùng để truy cập services qua NodePort

---

### 2.5 Enable Kubernetes Addons

```powershell
# Giải thích: Bật addon storage-provisioner để tự động tạo PersistentVolumes
minikube addons enable storage-provisioner

# Giải thích: Bật addon metrics-server để xem CPU/Memory usage của nodes và pods
minikube addons enable metrics-server
```

**Output mẫu:**
```
💡  storage-provisioner is an addon maintained by minikube. For any concerns contact minikube on GitHub.
You can view the list of minikube maintainers at: https://github.com/kubernetes/minikube/blob/master/OWNERS
    ▪ Using image gcr.io/k8s-minikube/storage-provisioner:v5
🌟  The 'storage-provisioner' addon is enabled

💡  metrics-server is an addon maintained by Kubernetes. For any concerns contact minikube on GitHub.
You can view the list of minikube maintainers at: https://github.com/kubernetes/minikube/blob/master/OWNERS
    ▪ Using image registry.k8s.io/metrics-server/metrics-server:v0.7.2
🌟  The 'metrics-server' addon is enabled
```

---

## 3️⃣ BƯỚC 3: Build Docker Images cho Project

### 3.1 Point Docker CLI tới Minikube

```powershell
# Giải thích: Chuyển Docker CLI sang Docker daemon của Minikube để build images trực tiếp trong cluster
# Quan trọng: Sau lệnh này, mọi docker commands sẽ chạy trong Minikube, không phải Docker Desktop
minikube -p minikube docker-env | Invoke-Expression
```

**Output mẫu:**
```
$Env:DOCKER_TLS_VERIFY = "1"
$Env:DOCKER_HOST = "tcp://192.168.49.2:2376"
$Env:DOCKER_CERT_PATH = "C:\Users\YourUser\.minikube\certs"
$Env:MINIKUBE_ACTIVE_DOCKERD = "minikube"
# To point your shell to minikube's docker-daemon, run:
# & minikube -p minikube docker-env --shell powershell | Invoke-Expression
```

> 💡 **Quan trọng**: Sau khi chạy lệnh này, tất cả docker commands sẽ chạy trong Minikube VM, không phải Docker Desktop!

---

### 3.2 Di chuyển vào thư mục project

```powershell
# Giải thích: Di chuyển vào thư mục chứa source code của project
# Lưu ý: Thay đổi đường dẫn cho phù hợp với máy của bạn
cd D:\BigData\bigdata
```

---

### 3.3 Build Producer Image

```powershell
# Giải thích: Build Docker image cho Producer từ Dockerfile trong thư mục ./producer
# Image được tag là air-producer:latest để sử dụng trong K8s manifests
docker build -t air-producer:latest ./producer
```

**Output mẫu:**
```
[+] Building 45.2s (10/10) FINISHED
 => [internal] load build definition from Dockerfile                      0.0s
 => => transferring dockerfile: 456B                                      0.0s
 => [internal] load metadata for docker.io/library/python:3.9-slim        2.1s
 => [internal] load .dockerignore                                         0.0s
 => => transferring context: 2B                                           0.0s
 => [1/5] FROM docker.io/library/python:3.9-slim@sha256:abc123...        15.4s
 => [internal] load build context                                         0.1s
 => => transferring context: 4.52kB                                       0.0s
 => [2/5] WORKDIR /app                                                    0.3s
 => [3/5] COPY requirements.txt .                                         0.0s
 => [4/5] RUN pip install --no-cache-dir -r requirements.txt             25.8s
 => [5/5] COPY sensor_sim.py .                                            0.0s
 => exporting to image                                                    1.5s
 => => exporting layers                                                   1.4s
 => => writing image sha256:def456...                                     0.0s
 => => naming to docker.io/library/air-producer:latest                   0.0s
```

**Thời gian**: ~30-60 giây (lần đầu ~2-3 phút)

---

### 3.4 Build Spark Processor Image

```powershell
# Giải thích: Build Docker image cho Spark Processor từ Dockerfile trong thư mục ./spark-processor
# Image được tag là spark-processor:latest để sử dụng trong K8s manifests
docker build -t spark-processor:latest ./spark-processor
```

**Output mẫu:**
```
[+] Building 78.5s (12/12) FINISHED
 => [internal] load build definition from Dockerfile                      0.0s
 => => transferring dockerfile: 612B                                      0.0s
 => [internal] load metadata for docker.io/bitnami/spark:3.0              3.2s
 => [1/7] FROM docker.io/bitnami/spark:3.0@sha256:xyz789...              35.2s
 => [internal] load build context                                         0.2s
 => => transferring context: 15.3kB                                       0.1s
 => [2/7] USER root                                                       0.5s
 => [3/7] WORKDIR /app                                                    0.3s
 => [4/7] COPY stream_app.py .                                            0.1s
 => [5/7] COPY viewer.py .                                                0.0s
 => [6/7] COPY libs/ /opt/bitnami/spark/jars/                             0.2s
 => [7/7] RUN chmod +x stream_app.py viewer.py                            0.8s
 => exporting to image                                                    2.1s
 => => exporting layers                                                   2.0s
 => => writing image sha256:uvw012...                                     0.0s
 => => naming to docker.io/library/spark-processor:latest                0.0s
```

---

### 3.5 Verify Images

```powershell
# Giải thích: Liệt kê các Docker images đã build để xác nhận air-producer và spark-processor tồn tại
docker images | findstr "air-producer spark-processor"
```

**Output mẫu:**
```
air-producer       latest    def456789abc   2 minutes ago   456MB
spark-processor    latest    uvw012345xyz   1 minute ago    823MB
```

---

## 4️⃣ BƯỚC 4: Deploy Application lên Kubernetes

### 4.1 Tạo Namespace

```powershell
# Giải thích: Tạo namespace air-quality để cô lập resources của project với các nhóm khác
kubectl create namespace air-quality
```

**Output mẫu:**
```
namespace/air-quality created
```

**Set default namespace:**
```powershell
# Giải thích: Đặt air-quality làm namespace mặc định để không cần gõ -n air-quality trong mọi lệnh
kubectl config set-context --current --namespace=air-quality
```

**Output mẫu:**
```
Context "minikube" modified.
```

---

### 4.2 Deploy tất cả Kubernetes manifests

```powershell
# Giải thích: Apply các file YAML theo thứ tự để tạo ConfigMaps, Secrets, PVs, Services, Deployments, StatefulSets
# Chú ý: Chạy từng lệnh theo thứ tự, không chạy cùng lúc
kubectl apply -f k8s/00-namespace-config.yaml
kubectl apply -f k8s/01-services.yaml
kubectl apply -f k8s/kafka-strimzi.yaml
kubectl apply -f k8s/03-hadoop.yaml
kubectl apply -f k8s/04-spark.yaml
kubectl apply -f k8s/05-database.yaml
kubectl apply -f k8s/06-applications.yaml
```

> 💡 **Lưu ý:** Sử dụng `kafka-strimzi.yaml` (Strimzi Kafka Operator) thay vì `02-kafka.yaml` (Confluent). Strimzi là giải pháp Kubernetes-native ổn định.

**Output mẫu:**
```
namespace/air-quality unchanged
configmap/hadoop-config created
secret/postgres-secret created
secret/openweather-secret created
persistentvolume/namenode-pv created
persistentvolume/datanode-pv created
persistentvolume/postgres-pv created
persistentvolume/zookeeper-pv created
persistentvolume/kafka-pv created

service/zookeeper created
service/kafka created
service/kafka-headless created
service/namenode created
service/datanode created
service/spark-master created
service/spark-worker created
service/postgres created
service/grafana created

statefulset.apps/zookeeper created
statefulset.apps/kafka created

statefulset.apps/namenode created
statefulset.apps/datanode created

deployment.apps/spark-master created
deployment.apps/spark-worker created

statefulset.apps/postgres created
deployment.apps/grafana created

deployment.apps/producer created
deployment.apps/spark-processor created
service/spark-processor created
```

---

### 4.3 Kiểm tra Pods đang khởi động

```powershell
# Giải thích: Theo dõi trạng thái pods realtime (-w = watch mode), nhấn Ctrl+C để thoát
kubectl get pods -w
```

**Output mẫu (ban đầu):**
```
NAME                                        READY   STATUS              RESTARTS   AGE
air-quality-kafka-air-quality-pool-0        0/1     ContainerCreating   0          10s
datanode-0                                  0/1     ContainerCreating   0          5s
datanode-1                                  0/1     Pending             0          5s
grafana-7d5b8f6c9d-4xk2m                    0/1     ContainerCreating   0          5s
namenode-0                                  0/1     ContainerCreating   0          10s
postgres-0                                  0/1     ContainerCreating   0          5s
producer-6b9c8d7f5e-8jhg7                   0/1     Init:0/1            0          3s
spark-master-5c4d6e8f9a-2nkl3               0/1     ContainerCreating   0          8s
spark-processor-68cb7dcd78-7w2wm            0/1     Init:0/1            0          3s
spark-worker-7f8g9h0i1j-6mlp4               0/1     Pending             0          8s
spark-worker-7f8g9h0i1j-9qrs5               0/1     Pending             0          8s
strimzi-cluster-operator-586d796fb5-b7pnr   1/1     Running             0          3m
```

**Output mẫu (sau 2-3 phút):**
```
NAME                            READY   STATUS      RESTARTS   AGE
datanode-0                      1/1     Running     0          3m12s
datanode-1                      1/1     Running     0          2m45s
grafana-7d5b8f6c9d-4xk2m        1/1     Running     0          3m15s
kafka-0                         1/1     Running     0          3m20s
namenode-0                      1/1     Running     0          3m22s
postgres-0                      1/1     Running     0          3m15s
producer-6b9c8d7f5e-8jhg7       1/1     Running     0          2m58s
spark-master-5c4d6e8f9a-2nkl3   1/1     Running     0          3m18s
spark-processor-68cb7dcd78-7w2wm 1/1    Running     0          2m45s
spark-worker-7f8g9h0i1j-6mlp4   1/1     Running     0          3m18s
spark-worker-7f8g9h0i1j-9qrs5   1/1     Running     0          3m18s
zookeeper-0                     1/1     Running     0          3m25s
```

> ⏱️ **Thời gian chờ**: 2-5 phút để tất cả pods Running

**Nhấn Ctrl+C để thoát watch mode**

---

### 4.4 Kiểm tra tất cả resources

```powershell
# Giải thích: Hiển thị tất cả Kubernetes resources (pods, services, deployments, statefulsets, jobs)
kubectl get all
```

**Output mẫu:**
```
NAME                                READY   STATUS      RESTARTS   AGE
pod/datanode-0                      1/1     Running     0          5m
pod/datanode-1                      1/1     Running     0          4m
pod/grafana-7d5b8f6c9d-4xk2m        1/1     Running     0          5m
pod/kafka-0                         1/1     Running     0          6m
pod/namenode-0                      1/1     Running     0          6m
pod/postgres-0                      1/1     Running     0          5m
pod/producer-6b9c8d7f5e-8jhg7       1/1     Running     0          4m
pod/spark-master-5c4d6e8f9a-2nkl3   1/1     Running     0          5m
pod/spark-processor-68cb7dcd78-7w2wm 1/1    Running     0          4m
pod/spark-worker-7f8g9h0i1j-6mlp4   1/1     Running     0          5m
pod/spark-worker-7f8g9h0i1j-9qrs5   1/1     Running     0          5m
pod/zookeeper-0                     1/1     Running     0          6m

NAME                     TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
service/datanode         ClusterIP   None            <none>        9864/TCP                     6m
service/grafana          NodePort    10.96.45.123    <none>        3000:30300/TCP               5m
service/kafka            ClusterIP   10.96.78.234    <none>        9092/TCP,29092/TCP           6m
service/kafka-headless   ClusterIP   None            <none>        9092/TCP,29092/TCP           6m
service/namenode         NodePort    10.96.12.345    <none>        9000:30900/TCP,9870:30870/TCP 6m
service/postgres         ClusterIP   10.96.56.789    <none>        5432/TCP                     5m
service/spark-master     NodePort    10.96.89.012    <none>        7077:30077/TCP,8080:30080/TCP 5m
service/spark-processor  ClusterIP   None            <none>        7078/TCP,7079/TCP            5m
service/spark-worker     ClusterIP   None            <none>        8081/TCP                     5m
service/zookeeper        ClusterIP   10.96.23.456    <none>        2181/TCP,2888/TCP,3888/TCP   6m

NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/grafana        1/1     1            1           5m
deployment.apps/producer       1/1     1            1           4m
deployment.apps/spark-master   1/1     1            1           5m
deployment.apps/spark-processor 1/1    1            1           4m
deployment.apps/spark-worker   2/2     2            2           5m

NAME                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/grafana-7d5b8f6c9d        1         1         1       5m
replicaset.apps/producer-6b9c8d7f5e       1         1         1       4m
replicaset.apps/spark-master-5c4d6e8f9a   1         1         1       5m
replicaset.apps/spark-processor-68cb7dcd78 1        1         1       4m
replicaset.apps/spark-worker-7f8g9h0i1j   2         2         2       5m

NAME                         READY   AGE
statefulset.apps/datanode    2/2     5m
statefulset.apps/kafka       1/1     6m
statefulset.apps/namenode    1/1     6m
statefulset.apps/postgres    1/1     5m
statefulset.apps/zookeeper   1/1     6m
```

---

### 4.5 Kiểm tra PersistentVolumeClaims

```powershell
# Giải thích: Hiển thị PersistentVolumeClaims (PVCs) để xác nhận storage đã được bind
kubectl get pvc
```

**Output mẫu:**
```
NAME                        STATUS   VOLUME         CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data-datanode-0             Bound    datanode-pv    10Gi       RWO            standard       5m
data-datanode-1             Bound    pvc-abc123     10Gi       RWO            standard       4m
data-kafka-0                Bound    kafka-pv       10Gi       RWO            standard       6m
data-postgres-0             Bound    postgres-pv    5Gi        RWO            standard       5m
datalog-zookeeper-0         Bound    pvc-def456     1Gi        RWO            standard       6m
logs-zookeeper-0            Bound    pvc-ghi789     1Gi        RWO            standard       6m
name-namenode-0             Bound    namenode-pv    10Gi       RWO            standard       6m
```

---

## 5️⃣ BƯỚC 5: Xem Logs & Verify Data Flow

### 5.1 Kiểm tra Producer logs

```powershell
# Giải thích: Hiển thị 50 dòng logs cuối của Producer và theo dõi realtime (-f = follow)
kubectl logs -f deployment/producer --tail=50
```

**Output mẫu:**
```
Connecting to Kafka at kafka:29092...
Kafka connection established successfully
Fetching air quality data from OpenWeather API...
API Key: *********************abc
City: Hanoi
Publishing message to topic: air_quality
{"timestamp": "2026-01-12T15:30:00", "aqi": 156, "pm25": 45.2, "pm10": 89.1, "co": 0.8, "no2": 32.5, "o3": 45.1}
Message published successfully
Sleeping for 60 seconds...

Publishing message to topic: air_quality
{"timestamp": "2026-01-12T15:31:00", "aqi": 158, "pm25": 46.1, "pm10": 90.3, "co": 0.9, "no2": 33.2, "o3": 44.8}
Message published successfully
Sleeping for 60 seconds...
```

---

### 5.2 Kiểm tra Kafka logs (Strimzi)

```powershell
# Giải thích: Hiển thị 30 dòng logs cuối của Kafka broker pod
kubectl logs pod/air-quality-kafka-air-quality-pool-0 --tail=30
```

**Output mẫu:**
```
[2026-01-12 15:30:15,234] INFO [KafkaServer id=0] started (kafka.server.KafkaServer)
[2026-01-12 15:30:15,456] INFO [ReplicaFetcherManager on broker 0] Removed fetcher for partitions Set(air-quality-0) (kafka.server.ReplicaFetcherManager)
[2026-01-12 15:30:45,678] INFO [GroupCoordinator 0]: Preparing to rebalance group spark-kafka-consumer with old generation 1 (kafka.coordinator.group.GroupCoordinator)
[2026-01-12 15:30:45,890] INFO [GroupCoordinator 0]: Assignment received from leader for group spark-kafka-consumer for generation 2 (kafka.coordinator.group.GroupCoordinator)
[2026-01-12 15:31:00,123] INFO [Log partition=air-quality-0, dir=/opt/kafka/data] Rolled new log segment at offset 1234 (kafka.log.Log)
```

**Verify Kafka topics:**
```powershell
# Giải thích: Liệt kê tất cả topics trong Kafka cluster (kết nối từ bên trong pod)
kubectl exec -it air-quality-kafka-air-quality-pool-0 -- /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:29092
```

**Output mẫu:**
```
air-quality
__consumer_offsets
__strimzi_store_topic
__strimzi-topic-operator-kstreams-topic-store-changelog
```

**Xem chi tiết topic:**
```powershell
# Giải thích: Hiển thị chi tiết topic air-quality (partitions, replicas, leader)
kubectl exec -it air-quality-kafka-air-quality-pool-0 -- /opt/kafka/bin/kafka-topics.sh --describe --topic air-quality --bootstrap-server localhost:29092
```

**Output mẫu:**
```
Topic: air-quality      PartitionCount: 1       ReplicationFactor: 1    Configs: 
        Topic: air-quality      Partition: 0    Leader: 0       Replicas: 0     Isr: 0
```

**Consume messages (test):**
```powershell
# Giải thích: Đọc 5 messages từ đầu topic air_quality_data để kiểm tra dữ liệu
# Lưu ý: Thay air_quality_data bằng tên topic bạn muốn kiểm tra
kubectl exec -it air-quality-kafka-air-quality-pool-0 -- /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:29092 --topic air_quality_data --from-beginning --max-messages 5
```

**Output mẫu:**
```
{"timestamp":"2026-01-12T15:30:00","aqi":156,"pm25":45.2,"pm10":89.1,"co":0.8,"no2":32.5,"o3":45.1}
{"timestamp":"2026-01-12T15:31:00","aqi":158,"pm25":46.1,"pm10":90.3,"co":0.9,"no2":33.2,"o3":44.8}
{"timestamp":"2026-01-12T15:32:00","aqi":159,"pm25":47.3,"pm10":91.2,"co":1.0,"no2":34.1,"o3":43.5}
Processed a total of 5 messages
```

---

### 5.3 Kiểm tra Spark Processor Deployment

```powershell
# Giải thích: Tìm pod của spark-processor deployment để lấy tên cho lệnh xem logs
kubectl get pods | findstr spark-processor
```

**Output:**
```
spark-processor-68cb7dcd78-7w2wm     1/1     Running   0          10m
```

**Xem logs:**
```powershell
# Giải thích: Hiển thị 100 dòng logs cuối của Spark Processor deployment
# Lưu ý: THAY "ten-spark-processor" bằng tên pod thực tế lấy được ở lệnh trên
kubectl logs ten-spark-processor --tail=100

# Hoặc xem logs realtime
kubectl logs -f deployment/spark-processor --tail=50
```

**Output mẫu:**
```
26/01/12 15:32:10 INFO SparkContext: Running Spark version 3.0.0
26/01/12 15:32:12 INFO ResourceUtils: Using Spark default resources file
26/01/12 15:32:15 INFO SparkContext: Submitted application: AirQualityStreaming
26/01/12 15:32:18 INFO Utils: Successfully started service 'sparkDriver' on port 35217
26/01/12 15:32:20 INFO KafkaSourceProvider: Kafka source starting with options: Map(kafka.bootstrap.servers -> kafka:29092, subscribe -> air_quality)
26/01/12 15:32:25 INFO ConsumerConfig: ConsumerConfig values:
        bootstrap.servers = [kafka:29092]
        group.id = spark-kafka-source-12345
26/01/12 15:32:30 INFO StreamingQuery: Starting streaming query [id = abc-123-def, runId = ghi-456-jkl]
26/01/12 15:32:35 INFO MicroBatchExecution: Streaming query made progress: {
  "timestamp" : "2026-01-12T15:32:35.123Z",
  "batchId" : 0,
  "numInputRows" : 15,
  "processedRowsPerSecond" : 25.5
}
26/01/12 15:33:00 INFO MicroBatchExecution: Batch 1 committed
26/01/12 15:33:00 INFO PostgreSQL: Inserted 15 records to air_quality_data table
26/01/12 15:33:05 INFO HDFS: Wrote parquet file to hdfs://namenode:9000/data/air_quality_v2/batch_001.parquet
```

---

### 5.4 Kiểm tra HDFS data

```powershell
# Giải thích: Liệt kê các files trong thư mục /data/air_quality_v2 trên HDFS để xác nhận Spark đã ghi dữ liệu
kubectl exec -it namenode-0 -- hdfs dfs -ls /data/air_quality_v2
```

**Output mẫu:**
```
Found 5 items
-rw-r--r--   2 root supergroup    4523234 2026-01-12 15:33 /data/air_quality_v2/batch_001.parquet
-rw-r--r--   2 root supergroup    4512890 2026-01-12 15:34 /data/air_quality_v2/batch_002.parquet
-rw-r--r--   2 root supergroup    4534567 2026-01-12 15:35 /data/air_quality_v2/batch_003.parquet
drwxr-xr-x   - root supergroup          0 2026-01-12 15:35 /data/air_quality_v2/_spark_metadata
```

---

### 5.5 Kiểm tra PostgreSQL data

```powershell
# Giải thích: Đếm số records trong bảng air_quality_final để xác nhận Spark đã insert dữ liệu
kubectl exec -it postgres-0 -- psql -U admin -d air_quality -c "SELECT COUNT(*) FROM air_quality_final;"
```

**Output mẫu:**
```
 count
-------
   456
(1 row)
```

**Xem 5 records mới nhất:**
```powershell
# Giải thích: Lấy 5 records gần đây nhất để kiểm tra dữ liệu chất lượng không khí
kubectl exec -it postgres-0 -- psql -U admin -d air_quality -c "SELECT * FROM air_quality_final ORDER BY ingested_at DESC LIMIT 5;"
```

**Output mẫu:**
```
          timestamp          | aqi  | pm25 | pm10 |  co  | no2  |  o3
-----------------------------+------+------+------+------+------+------
 2026-01-12 15:35:00+00      |  158 | 46.1 | 90.3 |  0.9 | 33.2 | 44.8
 2026-01-12 15:34:00+00      |  156 | 45.2 | 89.1 |  0.8 | 32.5 | 45.1
 2026-01-12 15:33:00+00      |  159 | 47.3 | 91.2 |  1.0 | 34.1 | 43.5
 2026-01-12 15:32:00+00      |  155 | 44.8 | 88.7 |  0.7 | 31.9 | 45.6
 2026-01-12 15:31:00+00      |  157 | 45.9 | 89.8 |  0.8 | 32.8 | 44.2
(5 rows)
```

---

## 6️⃣ BƯỚC 6: Truy Cập Dashboards

### 6.1 Lấy URLs của Services

```powershell
# Giải thích: Hiển thị danh sách services và ports để biết cách truy cập UI
kubectl get svc
```

**Output mẫu:**
```
NAME             TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                         AGE
grafana          NodePort    10.96.45.123     <none>        3000:30300/TCP                  15m
namenode         NodePort    10.96.12.345     <none>        9000:30900/TCP,9870:30870/TCP   15m
spark-master     NodePort    10.96.89.012     <none>        7077:30077/TCP,8080:30080/TCP   15m
```

**Lấy Minikube IP:**
```powershell
minikube ip
```

**Output:**
```
192.168.49.2
```

---

### 6.2 Mở Grafana Dashboard

**Option 1: Dùng minikube service (tự động mở browser)**
```powershell
# Giải thích: Mở Grafana dashboard trong browser mặc định, Minikube tự động tạo tunnel
minikube service grafana -n air-quality
```

**Output mẫu:**
```
|---------------|---------|-------------|---------------------------|
|   NAMESPACE   |  NAME   | TARGET PORT |            URL            |
|---------------|---------|-------------|---------------------------|
| air-quality   | grafana |        3000 | http://192.168.49.2:30300 |
|---------------|---------|-------------|---------------------------|
🎉  Opening service air-quality/grafana in default browser...
```

**Option 2: Truy cập manual**
```
URL: http://192.168.49.2:30300
Username: admin
Password: admin123
```

**Browser sẽ mở tự động!**

---

### 6.3 Mở HDFS NameNode UI

```powershell
# Giải thích: Mở HDFS NameNode web UI để xem HDFS files, datanodes, cluster health
minikube service namenode -n air-quality
```

**Output mẫu:**
```
|---------------|----------|-------------|---------------------------|
|   NAMESPACE   |   NAME   | TARGET PORT |            URL            |
|---------------|----------|-------------|---------------------------|
| air-quality   | namenode | http/9870   | http://192.168.49.2:30870 |
|               |          | hdfs/9000   | http://192.168.49.2:30900 |
|---------------|----------|-------------|---------------------------|
🎉  Opening service air-quality/namenode in default browser...
```

**Hoặc truy cập:**
```
URL: http://192.168.49.2:30870
```

---

### 6.4 Mở Spark Master UI

```powershell
# Giải thích: Mở Spark Master web UI để xem workers, running applications, job progress
minikube service spark-master -n air-quality
```

**Output mẫu:**
```
|---------------|--------------|-------------|---------------------------|
|   NAMESPACE   |     NAME     | TARGET PORT |            URL            |
|---------------|--------------|-------------|---------------------------|
| air-quality   | spark-master | rpc/7077    | http://192.168.49.2:30077 |
|               |              | http/8080   | http://192.168.49.2:30080 |
|---------------|--------------|-------------|---------------------------|
🎉  Opening service air-quality/spark-master in default browser...
```

**Web UI:**
```
URL: http://192.168.49.2:30080
```

---

### 6.5 Port-forward PostgreSQL (nếu cần kết nối từ tools)

```powershell
# Giải thích: Chuyển tiếp port 5432 của PostgreSQL pod đến localhost:5432 để kết nối bằng DB tools
# Lưu ý: Giữ terminal này mở, nếu đóng thì mất kết nối
kubectl port-forward svc/postgres 5432:5432
```

**Output mẫu:**
```
Forwarding from 127.0.0.1:5432 -> 5432
Forwarding from [::1]:5432 -> 5432
```

**Connection string:**
```
Host: localhost
Port: 5432
Database: air_quality
Username: admin
Password: password123
```

> 💡 Giữ terminal này mở để duy trì port-forward!

---

## 7️⃣ BƯỚC 7: Chạy Streamlit Dashboard

### 7.1 Cài đặt Python dependencies (nếu chưa có)

```powershell
# Giải thích: Tạo Python virtual environment để cô lập packages khỏi hệ thống
python -m venv .venv

# Giải thích: Kích hoạt virtual environment (sau khi activate, prompt sẽ có (.venv) ở đầu)
.\.venv\Scripts\Activate.ps1
```

**Output:**
```
(.venv) PS D:\BigData\bigdata>
```

**Cài packages:**
```powershell
# Giải thích: Cài đặt các thư viện Python cần thiết cho Streamlit dashboard
pip install -r requirements.txt
```

**Output mẫu:**
```
Collecting streamlit
  Downloading streamlit-1.40.2-py2.py3-none-any.whl (8.7 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 8.7/8.7 MB 5.2 MB/s eta 0:00:00
Collecting pandas
  Downloading pandas-2.2.3-cp39-cp39-win_amd64.whl (11.6 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 11.6/11.6 MB 6.8 MB/s eta 0:00:00
...
Successfully installed streamlit-1.40.2 pandas-2.2.3 psycopg2-binary-2.9.10
```

---

### 7.2 Chạy Dashboard

```powershell
# Giải thích: Khởi động Streamlit web server với dashboard_v2.py, browser tự động mở
streamlit run dashboard_v2.py
```

**Output mẫu:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.105:8501

  For better performance, install the Watchdog module:

  $ pip install watchdog
```

**Browser tự động mở:** http://localhost:8501

---

## 8️⃣ Monitoring & Troubleshooting

### 8.1 Kiểm tra Resource Usage

```powershell
# Giải thích: Hiển thị CPU và Memory usage của Minikube node (cần metrics-server addon)
kubectl top nodes
```

**Output mẫu:**
```
NAME       CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
minikube   1245m        31%    6234Mi          76%
```

**Pods resource usage:**
```powershell
# Giải thích: Hiển thị CPU và Memory usage của từng pod trong namespace hiện tại
kubectl top pods
```

**Output mẫu:**
```
NAME                            CPU(cores)   MEMORY(bytes)
datanode-0                      15m          512Mi
datanode-1                      12m          489Mi
grafana-7d5b8f6c9d-4xk2m        8m           156Mi
kafka-0                         45m          1024Mi
namenode-0                      25m          768Mi
postgres-0                      18m          234Mi
producer-6b9c8d7f5e-8jhg7       5m           128Mi
spark-master-5c4d6e8f9a-2nkl3   32m          512Mi
spark-worker-7f8g9h0i1j-6mlp4   28m          678Mi
spark-worker-7f8g9h0i1j-9qrs5   30m          712Mi
zookeeper-0                     10m          256Mi
```

---

### 8.2 Debug Pod không chạy

**Xem describe để tìm lỗi:**
```powershell
# Giải thích: Hiển thị chi tiết pod bao gồm events, resource requests/limits, lỗi pull image, v.v.
# Lưu ý: THAY <pod-name> bằng tên pod thực tế (lấy từ kubectl get pods)
kubectl describe pod <pod-name>
```

**Output mẫu (lỗi):**
```
Events:
  Type     Reason     Age                From               Message
  ----     ------     ----               ----               -------
  Warning  Failed     2m (x5 over 5m)    kubelet            Failed to pull image "air-producer:latest": image not found
  Warning  BackOff    1m (x10 over 4m)   kubelet            Back-off pulling image "air-producer:latest"
```

**Giải pháp:** Build lại image trong Minikube Docker environment

---

### 8.3 Xem Events của cluster

```powershell
# Giải thích: Hiển thị 20 events gần đây nhất trong cluster để debug lỗi
kubectl get events --sort-by='.lastTimestamp' | Select-Object -Last 20
```

**Output mẫu:**
```
LAST SEEN   TYPE      REASON              OBJECT                          MESSAGE
2m          Normal    Scheduled           pod/producer-abc123             Successfully assigned air-quality/producer-abc123 to minikube
2m          Normal    Pulling             pod/producer-abc123             Pulling image "air-producer:latest"
2m          Normal    Pulled              pod/producer-abc123             Successfully pulled image "air-producer:latest"
2m          Normal    Created             pod/producer-abc123             Created container producer
2m          Normal    Started             pod/producer-abc123             Started container producer
1m          Warning   Unhealthy           pod/kafka-0                     Liveness probe failed: connection refused
```

---

### 8.4 Restart một Pod

```powershell
# Giải thích: Restart tất cả pods của deployment producer (Kubernetes tự động tạo pods mới)
kubectl rollout restart deployment/producer
```

**Output:**
```
deployment.apps/producer restarted
```

---

### 8.5 Scale Services

**Scale Producer:**
```powershell
# Giải thích: Tăng số replicas của producer lên 2 để chạy 2 pods song song
kubectl scale deployment producer --replicas=2
```

**Output:**
```
deployment.apps/producer scaled
```

**Verify:**
```powershell
kubectl get pods | findstr producer
```

**Output:**
```
producer-6b9c8d7f5e-8jhg7       1/1     Running   0          15m
producer-6b9c8d7f5e-9xyz2       1/1     Running   0          10s
```

---

## 9️⃣ Clean Up & Reset

### 9.1 Xóa Application (giữ Minikube)

```powershell
# Giải thích: Xóa toàn bộ namespace air-quality và tất cả resources bên trong (pods, services, pvc, ...)
kubectl delete namespace air-quality
```

**Output:**
```
namespace "air-quality" deleted
```

---

### 9.2 Stop Minikube

```powershell
# Giải thích: Dừng Minikube cluster (giữ dữ liệu, có thể start lại sau)
minikube stop
```

**Output:**
```
✋  Stopping node "minikube"  ...
🛑  Powering off "minikube" via SSH ...
🛑  1 node stopped.
```

---

### 9.3 Delete Minikube Cluster

```powershell
# Giải thích: Xóa hoàn toàn Minikube cluster và tất cả dữ liểu (KHÔNG thể khôi phục)
minikube delete
```

**Output:**
```
🔥  Deleting "minikube" in docker ...
🔥  Deleting container "minikube" ...
🔥  Removing C:\Users\YourUser\.minikube\machines\minikube ...
💀  Removed all traces of the "minikube" cluster.
```

---

## 🔄 Quick Command Reference

### Start Project
```powershell
# Khởi động Minikube cluster
minikube start

# Deploy tất cả manifests trong thư mục k8s/
kubectl apply -f k8s/ -n air-quality

# Theo dõi pods khởi động (Ctrl+C để thoát)
kubectl get pods -w
```

### Check Status
```powershell
# Kiểm tra trạng thái Minikube
minikube status

# Liệt kê tất cả pods trong namespace air-quality
kubectl get pods -n air-quality

# Liệt kê tất cả services và ports
kubectl get svc -n air-quality
```

### View Logs
```powershell
# Xem logs Producer realtime
kubectl logs -f deployment/producer -n air-quality

# Xem logs Kafka realtime
kubectl logs -f statefulset/kafka -n air-quality
```

### Access Services
```powershell
# Mở Grafana dashboard trong browser
minikube service grafana -n air-quality

# Mở HDFS NameNode UI trong browser
minikube service namenode -n air-quality

# Mở Spark Master UI trong browser
minikube service spark-master -n air-quality
```

### Port Forward
```powershell
# Chuyển tiếp PostgreSQL port đến localhost (giữ terminal mở)
kubectl port-forward svc/postgres 5432:5432 -n air-quality

# Chuyển tiếp Grafana port đến localhost (giữ terminal mở)
kubectl port-forward svc/grafana 3000:3000 -n air-quality
```

### Troubleshoot
```powershell
# Xem chi tiết pod để tìm lỗi (THAY <pod-name> bằng tên pod thực tế)
kubectl describe pod <pod-name>

# Xem 20 events gần đây nhất
kubectl get events --sort-by='.lastTimestamp'

# Xem CPU/Memory usage của nodes
kubectl top nodes

# Xem CPU/Memory usage của pods
kubectl top pods
```

---

## 📊 Service URLs Summary

Sau khi deploy, truy cập các URL sau (thay `192.168.49.2` bằng IP của bạn):

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://192.168.49.2:30300 | admin / admin123 |
| **HDFS NameNode UI** | http://192.168.49.2:30870 | - |
| **Spark Master UI** | http://192.168.49.2:30080 | - |
| **PostgreSQL** | localhost:5432 (sau port-forward) | admin / password123 |
| **Streamlit Dashboard** | http://localhost:8501 | - |

---

## ❗ Common Issues & Solutions

### **Issue 0: Kafka pod stuck in "CrashLoopBackOff" (✅ RESOLVED)**

**Nguyên nhân (trước đây):** Confluent CP-Kafka image có bug trong init script - không tương thích với Kubernetes env variables

**Trạng thái:** ✅ **ĐÃ GIẢI QUYẾT - Dùng Strimzi Kafka Operator**

**Giải pháp áp dụng:**

```powershell
# Strimzi Kafka Operator được cài sẵn
helm list -n air-quality
# Output: strimzi-kafka-operator v0.49.1

# Kafka cluster được deploy từ kafka-strimzi.yaml
kubectl get kafka -n air-quality
# Output: air-quality-kafka

# Kafka pod chạy bình thường
kubectl get pods | findstr kafka
# Output: air-quality-kafka-air-quality-pool-0   1/1     Running
```

**Tại sao Strimzi giải quyết được:**
- ✅ Kubernetes-native approach (không dùng Confluent image bug)
- ✅ Quản lý Kafka + Zookeeper tự động
- ✅ Robust và production-ready
- ✅ Tự động handle KRaft mode (Kafka 4.0+)
- ✅ Không cần custom workarounds

---

### Issue 1: Pod stuck in "ImagePullBackOff"

**Nguyên nhân:** Docker image không tồn tại trong Minikube

**Giải pháp:**
```powershell
# Point Docker to Minikube
minikube -p minikube docker-env | Invoke-Expression

# Rebuild images
docker build -t air-producer:latest ./producer
docker build -t spark-processor:latest ./spark-processor

# Verify
docker images | findstr "air-producer spark-processor"
```

---

### Issue 2: Pod stuck in "Pending"

**Nguyên nhân:** Không đủ resources

**Check:**
```powershell
kubectl describe pod <pod-name> | findstr "Insufficient"
```

**Giải pháp:**
```powershell
minikube stop
minikube start --cpus=6 --memory=12288
```

---

### Issue 3: Service not accessible

**Nguyên nhân:** NodePort không hoạt động

**Giải pháp:**
```powershell
# Dùng minikube service thay vì truy cập trực tiếp IP
minikube service <service-name> -n air-quality

# Hoặc port-forward
kubectl port-forward svc/<service-name> <local-port>:<service-port>
```

---

### Issue 4: HDFS connection timeout

**Check NameNode pod:**
```powershell
kubectl get pods | findstr namenode
kubectl logs namenode-0
```

**Restart nếu cần:**
```powershell
kubectl delete pod namenode-0
# Kubernetes sẽ tự động tạo pod mới
```

---

## 💡 Pro Tips

1. **Tăng performance Minikube:**
```powershell
minikube config set cpus 6
minikube config set memory 12288
minikube config set disk-size 50g
```

2. **Enable Kubernetes Dashboard:**
```powershell
minikube dashboard
```

3. **Tạo alias cho kubectl:**
```powershell
Set-Alias -Name k -Value kubectl
# Sau đó dùng: k get pods
```

4. **Watch logs realtime từ nhiều pods:**
```powershell
# Cài Stern (log aggregator)
choco install stern

# Xem logs tất cả producer pods
stern producer -n air-quality
```

5. **Backup HDFS data:**
```powershell
kubectl exec -it namenode-0 -- hdfs dfs -get /data /backup
```

---

## 📚 Tài Liệu Tham Khảo

- **Minikube Docs**: https://minikube.sigs.k8s.io/docs/
- **Kubernetes Docs**: https://kubernetes.io/docs/
- **Docker Docs**: https://docs.docker.com/
- **Kafka on K8s**: https://strimzi.io/
- **Spark on K8s**: https://spark.apache.org/docs/latest/running-on-kubernetes.html

---

## ✅ Checklist Hoàn Thành

- [ ] Cài đặt Minikube, kubectl, Docker Desktop
- [ ] Start Minikube với 4 CPUs, 8GB RAM
- [ ] Build air-producer và spark-processor images
- [ ] Deploy tất cả K8s manifests
- [ ] Verify tất cả pods đang Running
- [ ] Kiểm tra data flow: Producer → Kafka → Spark → HDFS + PostgreSQL
- [ ] Truy cập Grafana dashboard (http://MINIKUBE_IP:30300)
- [ ] Truy cập HDFS UI (http://MINIKUBE_IP:30870)
- [ ] Truy cập Spark UI (http://MINIKUBE_IP:30080)
- [ ] Chạy Streamlit dashboard (http://localhost:8501)

---

**🎉 Chúc bạn thành công! Nếu gặp vấn đề, xem lại phần Troubleshooting hoặc check logs.**

