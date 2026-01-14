# 📘 Giải thích Kubernetes Manifests

## 📑 Cấu trúc k8s/ folder

```
k8s/
├── 00-namespace-config.yaml    # Namespace, ConfigMap, Secret, PV
├── 01-services.yaml            # Service definitions
├── 02-kafka.yaml               # Kafka & Zookeeper StatefulSet
├── 03-hadoop.yaml              # NameNode & DataNode StatefulSet
├── 04-spark.yaml               # Spark Master & Worker Deployment
├── 05-database.yaml            # PostgreSQL & Grafana
└── 06-applications.yaml        # Producer & Spark Processor
```

---

## 📄 File 1: 00-namespace-config.yaml

### Namespace
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: air-quality
```
**Ý nghĩa**: Tạo namespace riêng để tách biệt resources (giống folder).

---

### ConfigMap (Hadoop Configuration)
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hadoop-config
  namespace: air-quality
data:
  CORE_CONF_fs_defaultFS: "hdfs://namenode:9000"
  HDFS_CONF_dfs_replication: "1"
```
**Ý nghĩa**: Lưu trữ config files (non-secret) dưới dạng key-value.
- `CORE_CONF_*` = core-site.xml configuration
- `HDFS_CONF_*` = hdfs-site.xml configuration
- Pods sử dụng: `envFrom: - configMapRef: name: hadoop-config`

---

### Secret (PostgreSQL Credentials)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: air-quality
type: Opaque
stringData:
  POSTGRES_USER: admin
  POSTGRES_PASSWORD: password123
  POSTGRES_DB: air_quality
```
**Ý nghĩa**: Lưu trữ sensitive data (mật khẩu, API keys).
- `type: Opaque` = base64 encoded
- Pods sử dụng: `envFrom: - secretRef: name: postgres-secret`

---

### PersistentVolume (Storage)
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: namenode-pv
spec:
  capacity:
    storage: 20Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/data/namenode"
```
**Ý nghĩa**: Tạo storage trên host Minikube.
- `capacity: 20Gi` = dung lượng
- `hostPath` = lưu trữ trên Minikube VM
- Pods sử dụng: `volumeClaimTemplates` hoặc `PersistentVolumeClaim`

---

## 📄 File 2: 01-services.yaml

### Service (Expose Pod)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: kafka
  namespace: air-quality
spec:
  type: ClusterIP
  ports:
    - port: 29092
      targetPort: 29092
      name: internal
  selector:
    app: kafka
```
**Ý nghĩa**: Tạo endpoint để pods khác kết nối.
- `type: ClusterIP` = chỉ trong cluster (mặc định)
- `type: NodePort` = expose ra bên ngoài (cho web UI)
- `ports.port` = port service (trong cluster)
- `ports.targetPort` = port pod (thực tế)
- `selector` = chọn pods nào (label matching)

**Ví dụ kết nối**:
```python
# Từ pod khác, kết nối đến Kafka
producer = KafkaProducer(bootstrap_servers=['kafka:29092'])
# Kubernetes DNS tự động resolve 'kafka' → Service IP
```

---

### NodePort Service (Expose Web UI)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: namenode
spec:
  type: NodePort
  ports:
    - port: 9870
      targetPort: 9870
      nodePort: 30870  # Truy cập từ host
```
**Ý nghĩa**: Expose port ra ngoài cluster.
- Truy cập: `http://minikube-ip:30870`
- Minikube sẽ forward port 30870 → pod port 9870

---

## 📄 File 3: 02-kafka.yaml

### StatefulSet (For Kafka & Zookeeper)
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kafka
spec:
  serviceName: kafka-headless  # Headless service cho DNS
  replicas: 1
  selector:
    matchLabels:
      app: kafka
  template:
    metadata:
      labels:
        app: kafka
    spec:
      containers:
      - name: kafka
        image: confluentinc/cp-kafka:7.4.0
        ports:
        - containerPort: 29092
        env:
        - name: KAFKA_BROKER_ID
          value: "1"
        volumeMounts:
        - name: kafka-data
          mountPath: /var/lib/kafka/data
  volumeClaimTemplates:
  - metadata:
      name: kafka-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
```

**Ý nghĩa**: StatefulSet dùng cho stateful apps (database, message queue).
- `serviceName` = headless service (DNS stable)
- `volumeClaimTemplates` = tự động tạo PVC cho mỗi replica
- Stable hostname: `kafka-0.kafka-headless.air-quality.svc.cluster.local`
- Dữ liệu persist ngay cả khi pod restart

---

## 📄 File 4: 03-hadoop.yaml

### NameNode StatefulSet
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: namenode
spec:
  serviceName: namenode
  replicas: 1
  template:
    spec:
      containers:
      - name: namenode
        image: bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8
        envFrom:
        - configMapRef:
            name: hadoop-config  # Dùng ConfigMap ở file 00
        volumeMounts:
        - name: namenode-data
          mountPath: /hadoop/dfs/name
```

**Ý nghĩa**:
- `envFrom: configMapRef` = tải tất cả config từ ConfigMap
- `volumeMounts` = gắn storage vào pod
- NameNode lưu metadata filesystem trên `namenode-data` volume

---

### DataNode StatefulSet
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: datanode
spec:
  replicas: 2  # 2 DataNodes
  template:
    spec:
      initContainers:
      - name: wait-for-namenode
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          until nc -z namenode 9870; do
            sleep 2
          done
```

**Ý nghĩa**:
- `replicas: 2` = tạo 2 DataNode pods (datanode-0, datanode-1)
- `initContainers` = chạy trước container chính (wait for NameNode)
- `nc -z namenode 9870` = kiểm tra NameNode sẵn sàng

---

## 📄 File 5: 04-spark.yaml

### Deployment (For Spark Master & Worker)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spark-master
spec:
  replicas: 1
  selector:
    matchLabels:
      app: spark-master
  template:
    metadata:
      labels:
        app: spark-master
    spec:
      containers:
      - name: spark-master
        image: bde2020/spark-master:3.0.0-hadoop3.2
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

**Ý nghĩa**: Deployment dùng cho stateless apps.
- Không cần `volumeClaimTemplates`
- Dễ scale: `kubectl scale deployment spark-worker --replicas=5`
- `requests` = tối thiểu cần thiết
- `limits` = maximum cho phép

---

## 📄 File 6: 05-database.yaml

### StatefulSet (PostgreSQL)
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 1
  template:
    spec:
      containers:
      - name: postgres
        image: postgres:13
        envFrom:
        - secretRef:
            name: postgres-secret  # Dùng Secret
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U admin
          initialDelaySeconds: 30
          periodSeconds: 10
```

**Ý nghĩa**:
- `secretRef` = tải biến từ Secret (mật khẩu)
- `livenessProbe` = kiểm tra pod còn sống không, nếu fail → restart

---

### Deployment (Grafana)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "admin123"
        volumes:
        - name: grafana-storage
          emptyDir: {}  # Không persist (nếu muốn persist → PVC)
```

**Ý nghĩa**:
- `emptyDir` = lưu tạm, mất nếu pod restart
- Để persist → dùng `persistentVolumeClaim`

---

## 📄 File 7: 06-applications.yaml

### Deployment (Producer)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: producer
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: producer
        image: air-producer:latest
        imagePullPolicy: Never  # Dùng local image (không pull từ registry)
        env:
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka:29092"
      initContainers:
      - name: wait-for-kafka
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          until nc -z kafka 29092; do
            echo "Waiting for Kafka..."
            sleep 2
          done
```

**Ý nghĩa**:
- `imagePullPolicy: Never` = không fetch từ Docker Hub, dùng local Minikube docker
- `initContainers` = đợi Kafka sẵn sàng rồi mới start producer

---

### Deployment (Spark Processor)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spark-processor
spec:
  replicas: 1
  template:
    spec:
      subdomain: spark-processor
      hostname: spark-processor-driver
      containers:
      - name: spark-processor
        image: spark-processor:v5
        env:
        - name: SPARK_LOCAL_HOSTNAME
          value: "spark-processor-driver.spark-processor.air-quality.svc.cluster.local"
```

**Ý nghĩa**:
- `Deployment` = chạy liên tục (streaming job)
- `subdomain` + `hostname` = tạo stable DNS name cho driver pod
- `SPARK_LOCAL_HOSTNAME` = FQDN để executors kết nối driver
- Thay đổi từ Job vì Spark streaming cần chạy liên tục

---

### Headless Service (Spark Driver DNS)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: spark-processor
spec:
  clusterIP: None  # Headless service
  selector:
    app: spark-processor
  ports:
  - name: driver-rpc
    port: 7078
  - name: blockmanager
    port: 7079
```

**Ý nghĩa**:
- `clusterIP: None` = headless service (không load balance)
- Tạo DNS record: `spark-processor-driver.spark-processor.air-quality.svc.cluster.local`
- Executors dùng DNS này để kết nối driver
- Giải quyết lỗi "UnknownHostException" khi executors kết nối driver

---

## 🔄 Lifecycle trong Kubernetes

```
1. Apply manifests
   kubectl apply -f k8s/

2. Create Namespace
   Namespace 'air-quality' created

3. Create ConfigMap & Secret
   ConfigMap, Secret lưu trữ sẵn

4. Create PersistentVolumes
   PV '/data/namenode', '/data/datanode' etc tạo

5. Create Services
   Services expose pods

6. Create Zookeeper StatefulSet
   zookeeper-0 pod khởi động

7. Create Kafka StatefulSet
   initContainer chờ Zookeeper ready
   kafka-0 pod khởi động

8. Create Hadoop StatefulSet
   namenode-0 khởi động
   datanode-0, datanode-1 khởi động (chờ namenode sẵn sàng)

9. Create Spark Deployment
   spark-master khởi động
   spark-worker-0, spark-worker-1 khởi động (chờ master)

10. Create Database Deployment
    postgres-0, grafana pod khởi động

11. Create Applications
    producer deployment khởi động (chờ kafka)
    spark-processor deployment khởi động (chờ dependencies)
    spark-processor headless service tạo DNS record cho driver
```

---

## 🔧 Chỉnh sửa Manifests

### Thay đổi replicas
```yaml
# File 04-spark.yaml
kind: Deployment
metadata:
  name: spark-worker
spec:
  replicas: 2  # Thay 2 → 5 để có 5 workers
```

### Thay đổi resources
```yaml
spec:
  template:
    spec:
      containers:
      - name: spark-worker
        resources:
          requests:
            memory: "2Gi"    # Tăng từ 1Gi
            cpu: "1000m"     # Tăng từ 500m
          limits:
            memory: "4Gi"    # Tăng từ 2Gi
```

### Thay đổi image
```yaml
containers:
- name: kafka
  image: confluentinc/cp-kafka:7.5.0  # Upgrade version
```

### Thêm environment variable
```yaml
env:
- name: KAFKA_BOOTSTRAP_SERVERS
  value: "kafka:29092"
- name: NEW_VAR           # Thêm
  value: "new_value"      # Thêm
```

---

## 🚀 Apply Changes

```powershell
# Áp dụng từng file
kubectl apply -f k8s/04-spark.yaml

# Áp dụng tất cả
kubectl apply -f k8s/

# Xem thay đổi
kubectl diff -f k8s/

# Undo (rollback)
kubectl rollout undo deployment/spark-worker -n air-quality
```

---

## 📊 Kiểm tra Manifests

```powershell
# Validate YAML
kubectl apply -f k8s/ --dry-run=client

# Xem resources sẽ được tạo
kubectl apply -f k8s/ --dry-run=client -o yaml

# Check differences
kubectl diff -f k8s/
```

---

## 💡 Best Practices

1. **Dùng ConfigMap & Secret** cho config, tránh hardcode
2. **Dùng StatefulSet** cho database, message queue
3. **Dùng Deployment** cho stateless apps
4. **Thêm livenessProbe & readinessProbe** để health check
5. **Set resource requests & limits** để tránh resource starvation
6. **Dùng initContainers** để chờ dependencies
7. **Dùng Labels & Selectors** để organize resources

---

## 📖 Tài liệu Kubernetes

- [Kubernetes Objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/)
- [StatefulSet vs Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [ConfigMaps & Secrets](https://kubernetes.io/docs/concepts/configuration/configmap/)
