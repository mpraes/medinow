#!/bin/bash

# MediNow Docker Build and Run Script
# This script helps build and run the MediNow application in Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating template..."
        cat > .env << EOF
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Groq Configuration
GROQ_API_KEY=your_groq_api_key

# Composio Configuration
COMPOSIO_API_KEY=your_composio_api_key

# Application Configuration
ENVIRONMENT=production
DEBUG=false
EOF
        print_warning "Please edit .env file with your actual credentials before running the application."
        return 1
    fi
    return 0
}

# Build Docker image
build_image() {
    print_status "Building MediNow Docker image..."
    docker build -t medinow:latest -f docker/Dockerfile .
    print_success "Docker image built successfully!"
}

# Run container with Docker Compose
run_with_compose() {
    print_status "Starting MediNow with Docker Compose..."
    docker-compose -f docker/docker-compose.yml up -d
    print_success "MediNow is running! Check status with: docker-compose -f docker/docker-compose.yml ps"
}

# Run container directly
run_container() {
    print_status "Running MediNow container..."
    docker run -d \
        --name medinow-container \
        -p 8000:8000 \
        --env-file .env \
        -v "$(pwd)/logs:/app/logs" \
        --restart unless-stopped \
        medinow:latest
    print_success "MediNow container is running!"
}

# Stop containers
stop_containers() {
    print_status "Stopping MediNow containers..."
    docker-compose -f docker/docker-compose.yml down
    print_success "Containers stopped."
}

# Show logs
show_logs() {
    print_status "Showing MediNow logs..."
    docker-compose -f docker/docker-compose.yml logs -f medinow-app
}

# Health check
health_check() {
    print_status "Checking MediNow health..."
    if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        print_success "MediNow is healthy and responding!"
    else
        print_error "MediNow is not responding. Check logs with: $0 logs"
        return 1
    fi
}

# Clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    docker-compose -f docker/docker-compose.yml down --volumes --remove-orphans
    docker image prune -f
    print_success "Cleanup completed."
}

# Main script logic
case "${1:-help}" in
    "build")
        check_env_file && build_image
        ;;
    "run")
        check_env_file && build_image && run_with_compose
        ;;
    "run-simple")
        check_env_file && build_image && run_container
        ;;
    "stop")
        stop_containers
        ;;
    "restart")
        stop_containers && run_with_compose
        ;;
    "logs")
        show_logs
        ;;
    "health")
        health_check
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|*)
        echo "MediNow Docker Management Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  build       Build the Docker image"
        echo "  run         Build and run with Docker Compose (recommended)"
        echo "  run-simple  Build and run with simple Docker run"
        echo "  stop        Stop all containers"
        echo "  restart     Restart the application"
        echo "  logs        Show application logs"
        echo "  health      Check application health"
        echo "  cleanup     Clean up Docker resources"
        echo "  help        Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 run          # Start the application"
        echo "  $0 logs         # View logs"
        echo "  $0 health       # Check if app is running"
        echo "  $0 stop         # Stop the application"
        ;;
esac