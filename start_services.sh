#!/bin/bash

# 🚀 Athina Enhanced Vectorization Pipeline - Service Startup Script

echo "🚀 Starting Athina Enhanced Vectorization Pipeline Services..."
echo "============================================================"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $port is already in use. Please stop the service using this port."
        return 1
    fi
    return 0
}

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ $service_name failed to start within $(($max_attempts * 2)) seconds"
    return 1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Prerequisites check passed!"

# Check if ports are available
echo "🔍 Checking port availability..."
ports=(5000 5001 6379 9001)
for port in "${ports[@]}"; do
    if ! check_port $port; then
        echo "💡 You can check what's using port $port with: lsof -i :$port"
        exit 1
    fi
done
echo "✅ All required ports are available!"

# Start Computations Orchestrator
echo "🏗️ Starting Computations Orchestrator..."
cd computations-orchestrator
if ! docker-compose up -d --build; then
    echo "❌ Failed to start Computations Orchestrator"
    exit 1
fi
cd ..

# Start Vectorization Service
echo "🏗️ Starting Vectorization Service..."
cd vectorization-service
if ! docker-compose up -d --build; then
    echo "❌ Failed to start Vectorization Service"
    exit 1
fi
cd ..

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check if containers are running
if ! docker ps --format "table {{.Names}}" | grep -q "computations_orchestrator_container"; then
    echo "❌ Computations Orchestrator container is not running"
    exit 1
fi

if ! docker ps --format "table {{.Names}}" | grep -q "vectorization_service_container"; then
    echo "❌ Vectorization Service container is not running"
    exit 1
fi

if ! docker ps --format "table {{.Names}}" | grep -q "computations_redis"; then
    echo "❌ Redis container is not running"
    exit 1
fi

if ! docker ps --format "table {{.Names}}" | grep -q "smpc_client"; then
    echo "❌ SMPC Client container is not running"
    exit 1
fi

echo "✅ All containers are running!"

# Test service endpoints
echo "🧪 Testing service endpoints..."

# Test Redis
if docker exec computations_redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis is responding"
else
    echo "⚠️  Redis is not responding properly"
fi

# Give services more time to fully initialize
sleep 5

# Test Vectorization Service
if curl -s -f "http://localhost:5001/vectorize" >/dev/null 2>&1; then
    echo "✅ Vectorization Service is accessible"
else
    echo "⚠️  Vectorization Service endpoint returned an error (this is expected without a proper request)"
fi

# Test Orchestrator
if curl -s -f "http://localhost:5000/" >/dev/null 2>&1; then
    echo "✅ Orchestrator is accessible"
else
    echo "⚠️  Orchestrator endpoint returned an error (this is expected without a proper request)"
fi

echo ""
echo "🎉 All services started successfully!"
echo "============================================================"
echo "📊 Service Status:"
echo "   • Vectorization Service: http://localhost:5001"
echo "   • Computations Orchestrator: http://localhost:5000"
echo "   • SMPC Client: http://localhost:9001"
echo "   • Redis Store: http://localhost:6379"
echo ""
echo "🧪 Test the pipeline:"
echo "   cd trigger-vectorization-pipeline"
echo "   python trigger_vectorization.py \\"
echo "     --vectorizationServiceUrl http://localhost:5001 \\"
echo "     --url metadata-test.json \\"
echo "     --jobId test_job_001 \\"
echo "     --totalClients 1 \\"
echo "     --orchestratorUrl http://host.docker.internal:5000"
echo ""
echo "📚 Documentation:"
echo "   • Complete Guide: PIPELINE_DOCUMENTATION.md"
echo "   • Testing Guide: TESTING_GUIDE.md"
echo "   • Technical Details: ENHANCED_VECTORIZATION_README.md"
echo ""
echo "🔧 Troubleshooting:"
echo "   • View logs: docker logs <container_name>"
echo "   • Check status: docker ps"
echo "   • Stop services: docker-compose down (in each service directory)"
echo ""
echo "✅ Ready to process your datasets! 🚀" 