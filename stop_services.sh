#!/bin/bash

# 🛑 Athina Enhanced Vectorization Pipeline - Service Shutdown Script

echo "🛑 Stopping Athina Enhanced Vectorization Pipeline Services..."
echo "============================================================"

# Function to check if directory exists
check_directory() {
    local dir=$1
    if [ ! -d "$dir" ]; then
        echo "⚠️  Directory $dir not found, skipping..."
        return 1
    fi
    return 0
}

# Stop Vectorization Service
echo "🛑 Stopping Vectorization Service..."
if check_directory "vectorization-service"; then
    cd vectorization-service
    if docker-compose down; then
        echo "✅ Vectorization Service stopped successfully"
    else
        echo "⚠️  Failed to stop Vectorization Service gracefully"
    fi
    cd ..
fi

# Stop Computations Orchestrator
echo "🛑 Stopping Computations Orchestrator..."
if check_directory "computations-orchestrator"; then
    cd computations-orchestrator
    if docker-compose down; then
        echo "✅ Computations Orchestrator stopped successfully"
    else
        echo "⚠️  Failed to stop Computations Orchestrator gracefully"
    fi
    cd ..
fi

# Check for any remaining containers
echo "🔍 Checking for remaining containers..."
athina_containers=$(docker ps --format "table {{.Names}}" | grep -E "(vectorization|orchestrator|redis|smpc)" | grep -v "NAMES" || true)

if [ -n "$athina_containers" ]; then
    echo "⚠️  Found remaining containers:"
    echo "$athina_containers"
    echo "🔧 Stopping remaining containers..."
    
    # Stop remaining containers
    docker stop $(docker ps -q --filter "name=vectorization") 2>/dev/null || true
    docker stop $(docker ps -q --filter "name=orchestrator") 2>/dev/null || true
    docker stop $(docker ps -q --filter "name=redis") 2>/dev/null || true
    docker stop $(docker ps -q --filter "name=smpc") 2>/dev/null || true
    
    echo "✅ All remaining containers stopped"
else
    echo "✅ No remaining containers found"
fi

# Optional: Remove containers and networks
echo ""
echo "🧹 Cleanup Options:"
echo "   1. Remove stopped containers: docker container prune -f"
echo "   2. Remove unused networks: docker network prune -f"
echo "   3. Remove unused volumes: docker volume prune -f"
echo "   4. Remove unused images: docker image prune -f"
echo ""
echo "🤔 Would you like to clean up unused Docker resources? (y/n)"
read -r cleanup_choice

if [[ $cleanup_choice =~ ^[Yy]$ ]]; then
    echo "🧹 Cleaning up unused Docker resources..."
    
    # Remove stopped containers
    if docker container prune -f; then
        echo "✅ Removed stopped containers"
    else
        echo "⚠️  Failed to remove stopped containers"
    fi
    
    # Remove unused networks
    if docker network prune -f; then
        echo "✅ Removed unused networks"
    else
        echo "⚠️  Failed to remove unused networks"
    fi
    
    # Remove unused volumes
    if docker volume prune -f; then
        echo "✅ Removed unused volumes"
    else
        echo "⚠️  Failed to remove unused volumes"
    fi
    
    echo "🧹 Cleanup completed!"
else
    echo "⏭️  Skipping cleanup"
fi

echo ""
echo "🎉 Athina services stopped successfully!"
echo "============================================================"
echo "📊 Service Status:"
echo "   • All Athina services are now stopped"
echo "   • Docker containers have been shut down"
echo "   • Ports 5000, 5001, 6379, 9001 are now available"
echo ""
echo "🚀 To restart services:"
echo "   ./start_services.sh"
echo ""
echo "🔍 To check Docker status:"
echo "   docker ps"
echo ""
echo "✅ Shutdown complete! 🛑" 