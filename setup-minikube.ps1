#!/usr/bin/env pwsh
# Automated Minikube setup script for Air Quality Project
# Run: .\setup-minikube.ps1

$ErrorActionPreference = "Stop"
$WarningPreference = "Continue"

# ANSI Color Codes using [char]27
$ESC = [char]27
$green = "$ESC[92m"
$yellow = "$ESC[93m"
$red = "$ESC[91m"
$blue = "$ESC[94m"
$reset = "$ESC[0m"

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "$blue===============================================================$reset"
    Write-Host "$blue> $Message$reset"
    Write-Host "$blue===============================================================$reset"
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "$green[OK]$reset $Message"
}

function Write-Warning {
    param([string]$Message)
    Write-Host "$yellow[!]$reset $Message"
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "$red[X]$reset $Message"
}

# Check prerequisites
Write-Header "Checking Prerequisites"

# Check Minikube
try {
    $minikubeVersion = minikube version 2>&1
    Write-Success "Minikube found: $minikubeVersion"
} catch {
    Write-Error-Custom "Minikube is not installed"
    Write-Host "Download from: https://minikube.sigs.k8s.io/docs/start/"
    exit 1
}

# Check kubectl
try {
    $kubectlVersion = kubectl version --client 2>&1 | Select-Object -First 1
    Write-Success "Kubectl found: $kubectlVersion"
} catch {
    Write-Error-Custom "Kubectl is not installed"
    exit 1
}

# Check Docker
try {
    $dockerVersion = docker version --format '{{.Client.Version}}' 2>&1
    Write-Success "Docker found: $dockerVersion"
} catch {
    Write-Error-Custom "Docker is not installed or not running"
    exit 1
}

# Check Minikube status
Write-Header "Checking Minikube Status"

$minikubeRunning = $false
try {
    $statusOutput = minikube status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Minikube is running"
        $minikubeRunning = $true
    }
} catch {
    # Minikube not running
}

if (-not $minikubeRunning) {
    Write-Warning "Minikube is not running, starting now..."
    
    $response = Read-Host 'Start Minikube with default config - 4 CPUs, 8GB RAM? (y/n)'
    if ($response -ne "y") {
        Write-Host "Please run: minikube start"
        exit 1
    }

    # Ensure image repo mirror is configured globally
    try {
        minikube config set image-repository registry.aliyuncs.com/google_containers 2>&1 | Out-Null
    } catch {}
    
    Write-Host "$yellow Starting Minikube (may take a few minutes)...$reset"

    # Build start args and include proxy envs if present
    $startArgs = @("start","--cpus=4","--memory=8192","--disk-size=30g","--driver=docker","--image-repository=registry.aliyuncs.com/google_containers")
    if ($env:HTTP_PROXY)     { $startArgs += "--docker-env=HTTP_PROXY=$($env:HTTP_PROXY)" }
    if ($env:HTTPS_PROXY)    { $startArgs += "--docker-env=HTTPS_PROXY=$($env:HTTPS_PROXY)" }
    if ($env:NO_PROXY)       { $startArgs += "--docker-env=NO_PROXY=$($env:NO_PROXY)" }

    try {
        $startResult = & minikube @startArgs 2>&1
    } catch {
        $startResult = $_.Exception.Message
        $LASTEXITCODE = 1
    }

    # Handle specific errors and retry with adjusted args
    if ($startResult -match "cannot change the memory") {
        Write-Warning "Existing cluster found, starting without changing memory settings..."
        $startResult = minikube start 2>&1
    } elseif ($startResult -match "Failing to connect to https://registry.k8s.io") {
        Write-Warning "Retrying with explicit Kubernetes version and image mirror..."
        $startArgs += "--kubernetes-version=v1.31.0"
        try {
            $startResult = & minikube @startArgs 2>&1
        } catch {
            $startResult = $_.Exception.Message
            $LASTEXITCODE = 1
        }

        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Retrying with alternate mirror (registry.cn-hangzhou.aliyuncs.com)..."
            # swap mirror and retry once more
            $startArgs = $startArgs | ForEach-Object { $_ -replace 'registry.aliyuncs.com/google_containers','registry.cn-hangzhou.aliyuncs.com/google_containers' }
            try {
                $startResult = & minikube @startArgs 2>&1
            } catch {
                $startResult = $_.Exception.Message
                $LASTEXITCODE = 1
            }
        }
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Host $startResult
        Write-Error-Custom "Failed to start Minikube"
        exit 1
    } else {
        Write-Host $startResult
    }
    
    Write-Success "Minikube started successfully"
}

# Get Minikube IP
$MINIKUBE_IP = minikube ip 2>&1
Write-Success "Minikube IP: $MINIKUBE_IP"

# Point Docker to Minikube
Write-Header "Pointing Docker to Minikube"
Write-Host "$yellow Setting Docker environment variables...$reset"

$env:DOCKER_HOST = "tcp://$MINIKUBE_IP`:2375"
$env:DOCKER_CERT_PATH = ""
$env:DOCKER_TLS_VERIFY = ""

# Alternative method
try {
    minikube -p minikube docker-env | Invoke-Expression
    Write-Success "Docker is now pointing to Minikube"
} catch {
    Write-Warning "Could not configure Docker environment, continuing anyway..."
}

# Enable addons
Write-Header "Enabling Kubernetes Addons"

minikube addons enable storage-provisioner 2>&1 | Out-Null
Write-Success "storage-provisioner enabled"

minikube addons enable metrics-server 2>&1 | Out-Null
Write-Success "metrics-server enabled"

# Create namespace
Write-Header "Creating Namespace"

kubectl create namespace air-quality 2>&1 | Out-Null
Write-Success "Namespace 'air-quality' created/already exists"

kubectl config set-context --current --namespace=air-quality 2>&1 | Out-Null
Write-Success "Default namespace set to 'air-quality'"

# Build Docker images
Write-Header "Building Docker Images"

$projectPath = Get-Location
Write-Host "$yellow Building Producer image...$reset"
docker build -t air-producer:latest "$projectPath\producer" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Success "Producer image built successfully"
} else {
    Write-Error-Custom "Failed to build Producer image"
    exit 1
}

Write-Host "$yellow Building Spark Processor image...$reset"
docker build -t spark-processor:latest "$projectPath\spark-processor" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Success "Spark Processor image built successfully"
} else {
    Write-Error-Custom "Failed to build Spark Processor image"
    exit 1
}

# Verify images
Write-Host "$yellow Verifying images...$reset"
docker images | findstr "air-producer\|spark-processor" | ForEach-Object {
    Write-Success $_
}

# Deploy manifests
Write-Header "Deploying Kubernetes Manifests"

$k8sPath = "$projectPath\k8s"

if (-Not (Test-Path $k8sPath)) {
    Write-Error-Custom "k8s directory not found"
    exit 1
}

Write-Host "$yellow Applying manifests...$reset"
kubectl apply -f "$k8sPath\00-namespace-config.yaml" 2>&1 | Out-Null
kubectl apply -f "$k8sPath\01-services.yaml" 2>&1 | Out-Null
kubectl apply -f "$k8sPath\02-kafka.yaml" 2>&1 | Out-Null
kubectl apply -f "$k8sPath\03-hadoop.yaml" 2>&1 | Out-Null
kubectl apply -f "$k8sPath\04-spark.yaml" 2>&1 | Out-Null
kubectl apply -f "$k8sPath\05-database.yaml" 2>&1 | Out-Null
kubectl apply -f "$k8sPath\06-applications.yaml" 2>&1 | Out-Null

Write-Success "All manifests applied successfully"

# Wait for pods to start
Write-Header "Waiting for Pods to Start"

Write-Host "$yellow Waiting for all pods to run (may take 2-5 minutes)...$reset"
Write-Host "$yellow You can check status with: kubectl get pods -w -n air-quality$reset"
Write-Host ""

$maxRetries = 60
$retryCount = 0
$podsReady = $false

while ($retryCount -lt $maxRetries) {
    $readyPods = kubectl get pods -n air-quality 2>&1 | Measure-Object -Line
    
    if ($readyPods.Lines -gt 3) {
        $podsReady = $true
        break
    }
    
    Write-Host "." -NoNewline
    Start-Sleep -Seconds 5
    $retryCount++
}

Write-Host ""

if ($podsReady) {
    Write-Success "Most pods are now running"
} else {
    Write-Warning "Some pods may not be ready yet. Check with: kubectl get pods -n air-quality"
}

# Display information
Write-Header "Access Information"

Write-Host "$blue Minikube IP:$reset $MINIKUBE_IP"
Write-Host ""
Write-Host "$blue Services:$reset"
kubectl get svc -n air-quality --no-headers 2>&1 | ForEach-Object {
    Write-Host "  $_"
}

Write-Host ""
Write-Host "$blue Ports (NodePort):$reset"
Write-Host "  HDFS NameNode UI: http://$MINIKUBE_IP`:30870"
Write-Host "  Spark Master UI:  http://$MINIKUBE_IP`:30080"
Write-Host "  Grafana:          http://$MINIKUBE_IP`:30300"

# Create helper scripts
Write-Header "Creating Helper Scripts"

$portForwardScript = "$projectPath\port-forward.ps1"
@'
#!/usr/bin/env pwsh
# Port forward for services

Write-Host "Starting port forwards..."
Write-Host "Grafana:     http://localhost:3000"
Write-Host "HDFS UI:     http://localhost:9870"
Write-Host "Spark UI:    http://localhost:8080"
Write-Host "PostgreSQL:  localhost:5432"
Write-Host ""
Write-Host "Press Ctrl+C to stop"
Write-Host ""

# Run port forwards
Start-Process -NoNewWindow { kubectl port-forward svc/grafana 3000:3000 -n air-quality }
Start-Process -NoNewWindow { kubectl port-forward svc/namenode 9870:9870 -n air-quality }
Start-Process -NoNewWindow { kubectl port-forward svc/spark-master 8080:8080 -n air-quality }
Start-Process -NoNewWindow { kubectl port-forward svc/postgres 5432:5432 -n air-quality }

# Keep script running
while ($true) { Start-Sleep -Seconds 1 }
'@ | Set-Content $portForwardScript
Write-Success "Created port-forward.ps1"

$logScript = "$projectPath\check-logs.ps1"
@'
#!/usr/bin/env pwsh
# View logs from pods

param(
    [string]$Pod = "producer"
)

Write-Host "=== Logs from $Pod ==="
kubectl logs -f deployment/$Pod -n air-quality

# Or use:
# kubectl logs -f statefulset/kafka -n air-quality
# kubectl logs -f statefulset/namenode -n air-quality
# kubectl logs -f job/spark-processor -n air-quality
'@ | Set-Content $logScript
Write-Success "Created check-logs.ps1"

# Completion
Write-Header "Setup Complete!"

Write-Host "$green Minikube setup successful!$reset"
Write-Host ""

Write-Host "Next steps:"
Write-Host "  1. Check pod status: $yellow kubectl get pods -n air-quality$reset"
Write-Host "  2. View logs: $yellow kubectl logs -f deployment/producer -n air-quality$reset"
Write-Host "  3. Port forward: $yellow .\port-forward.ps1$reset"
Write-Host "  4. Run Dashboard: $yellow streamlit run dashboard_v2.py$reset"
Write-Host ""

Write-Host "Detailed documentation:"
Write-Host "  - $yellow MINIKUBE_SETUP.md$reset - Minikube setup guide"
Write-Host "  - $yellow KUBERNETES_DEPLOYMENT_GUIDE.md$reset - Detailed deployment guide"
Write-Host ""

Write-Host "Dashboard URLs (after running port-forward or minikube service):"
Write-Host "  - Grafana:        http://localhost:3000 (admin:admin123)"
Write-Host "  - HDFS UI:        http://localhost:9870"
Write-Host "  - Spark Master:   http://localhost:8080"
Write-Host ""

Read-Host "Press Enter to exit"
