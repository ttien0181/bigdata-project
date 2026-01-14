#!/usr/bin/env bash
# Automated Minikube setup script for Air Quality Project (Linux/Mac)
# Run: bash setup-minikube.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function write_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}► $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

function write_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

function write_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

function write_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check prerequisites
write_header "Checking Prerequisites"

# Check Minikube
if ! command -v minikube &> /dev/null; then
    write_error "Minikube is not installed"
    echo "Download from: https://minikube.sigs.k8s.io/docs/start/"
    exit 1
fi
write_success "Minikube found: $(minikube version)"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    write_error "Kubectl is not installed"
    exit 1
fi
write_success "Kubectl found: $(kubectl version --client 2>&1 | head -1)"

# Check Docker
if ! command -v docker &> /dev/null; then
    write_error "Docker is not installed or not running"
    exit 1
fi
write_success "Docker found: $(docker version --format '{{.Client.Version}}')"

# Check Minikube status
write_header "Checking Minikube Status"

if minikube status &> /dev/null; then
    write_success "Minikube is running"
else
    write_warning "Minikube is not running, starting now..."
    
    read -p "Start Minikube with default config (4 CPUs, 8GB RAM)? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please run: minikube start"
        exit 1
    fi
    
    echo -e "${YELLOW}Waiting for Minikube to start (may take a few minutes)...${NC}"
    minikube start \
        --cpus=4 \
        --memory=8192 \
        --disk-size=30g \
        --driver=docker 2>&1 | tail -5
    
    write_success "Minikube started successfully"
fi

# Get Minikube IP
MINIKUBE_IP=$(minikube ip)
write_success "Minikube IP: $MINIKUBE_IP"

# Point Docker to Minikube
write_header "Pointing Docker to Minikube"
echo -e "${YELLOW}Setting Docker environment variables...${NC}"

eval $(minikube -p minikube docker-env)
write_success "Docker is now pointing to Minikube"

# Enable addons
write_header "Enabling Kubernetes Addons"

minikube addons enable storage-provisioner > /dev/null 2>&1
write_success "storage-provisioner enabled"

minikube addons enable metrics-server > /dev/null 2>&1
write_success "metrics-server enabled"

# Create namespace
write_header "Creating Namespace"

kubectl create namespace air-quality 2>/dev/null || true
write_success "Namespace 'air-quality' created/already exists"

kubectl config set-context --current --namespace=air-quality 2>/dev/null
write_success "Default namespace set to 'air-quality'"

# Build Docker images
write_header "Building Docker Images"

PROJECT_PATH=$(pwd)

echo -e "${YELLOW}Building Producer image...${NC}"
docker build -t air-producer:latest "$PROJECT_PATH/producer" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    write_success "Producer image built successfully"
else
    write_error "Failed to build Producer image"
    exit 1
fi

echo -e "${YELLOW}Building Spark Processor image...${NC}"
docker build -t spark-processor:latest "$PROJECT_PATH/spark-processor" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    write_success "Spark Processor image built successfully"
else
    write_error "Failed to build Spark Processor image"
    exit 1
fi

# Verify images
echo -e "${YELLOW}Verifying images...${NC}"
docker images | grep -E "air-producer|spark-processor" | while read line; do
    write_success "$line"
done

# Deploy manifests
write_header "Deploying Kubernetes Manifests"

K8S_PATH="$PROJECT_PATH/k8s"

if [ ! -d "$K8S_PATH" ]; then
    write_error "k8s directory not found"
    exit 1
fi

echo -e "${YELLOW}Applying manifests...${NC}"
kubectl apply -f "$K8S_PATH/00-namespace-config.yaml"
kubectl apply -f "$K8S_PATH/01-services.yaml"
kubectl apply -f "$K8S_PATH/02-kafka.yaml"
kubectl apply -f "$K8S_PATH/03-hadoop.yaml"
kubectl apply -f "$K8S_PATH/04-spark.yaml"
kubectl apply -f "$K8S_PATH/05-database.yaml"
kubectl apply -f "$K8S_PATH/06-applications.yaml"

write_success "All manifests applied successfully"

# Wait for pods to start
write_header "Waiting for Pods to Start"

echo -e "${YELLOW}Waiting for all pods to run... (may take 2-5 minutes)${NC}"
echo -e "${YELLOW}You can check status with: kubectl get pods -w -n air-quality${NC}\n"

for i in {1..60}; do
    READY_PODS=$(kubectl get pods -n air-quality -o jsonpath='{.items[?(@.status.phase=="Running")].metadata.name}' 2>/dev/null | wc -w)
    if [ "$READY_PODS" -gt 5 ]; then
        break
    fi
    echo -n "."
    sleep 5
done
echo ""

write_success "Most pods are now running"

# Display information
write_header "Access Information"

echo -e "${BLUE}Minikube IP:${NC} $MINIKUBE_IP"
echo ""
echo -e "${BLUE}Services:${NC}"
kubectl get svc -n air-quality --no-headers

echo ""
echo -e "${BLUE}Ports (NodePort):${NC}"
echo "  HDFS NameNode UI: http://$MINIKUBE_IP:30870"
echo "  Spark Master UI:  http://$MINIKUBE_IP:30080"
echo "  Grafana:          http://$MINIKUBE_IP:30300"

# Completion
write_header "Setup Complete!"

echo -e "${GREEN}Minikube setup successful!${NC}\n"

echo "Next steps:"
echo "  1. Check pod status: ${YELLOW}kubectl get pods -n air-quality${NC}"
echo "  2. View logs: ${YELLOW}kubectl logs -f deployment/producer -n air-quality${NC}"
echo "  3. Port forward: ${YELLOW}kubectl port-forward svc/grafana 3000:3000 -n air-quality${NC}"
echo "  4. Run Dashboard: ${YELLOW}streamlit run dashboard_v2.py${NC}"
echo ""

echo "Dashboard URLs:"
echo "  - Grafana:        http://localhost:3000 (admin:admin123)"
echo "  - HDFS UI:        http://localhost:9870"
echo "  - Spark Master:   http://localhost:8080"
