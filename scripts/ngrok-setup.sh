# 🏥 MediNow - WhatsApp Medical Appointment Bot

A WhatsApp chatbot for medical appointment scheduling using natural language, integrated with Google Calendar and designed for easy scalability across multiple doctors and clinics.

## 🎯 Overview

MediNow solves the pain point of difficulty and delays in finding and booking medical appointments by providing a conversational WhatsApp interface. Users can schedule, check, reschedule, and cancel appointments using natural language.

**Current Scope**: Porto Feliz with one doctor  
**Future**: Scalable architecture for multiple doctors and clinics

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "External Services"
        WA[WhatsApp Business API<br/>via Twilio]
        GC[Google Calendar API<br/>via Composio]
        GROQ[Groq LLM API]
    end
    
    subgraph "MediNow Application"
        subgraph "API Layer"
            FA[FastAPI Server<br/>Port 8000]
            WH[Webhook Handler<br/>/webhook/twilio]
        end
        
        subgraph "Business Logic"
            CM[Conversation Manager]
            SM[State Machine]
            MH[Message Handlers]
        end
        
        subgraph "Integrations"
            CC[Calendar Service<br/>Composio Integration]
            TWC[Twilio WhatsApp Client]
        end
        
        subgraph "Storage"
            DB[(SQLite Database<br/>Conversations & State)]
        end
    end
    
    subgraph "Infrastructure"
        DOC[Docker Container]
        NG[ngrok Tunnel<br/>External Access]
    end
    
    %% Flow
    WA -->|Incoming Messages| WH
    WH --> CM
    CM --> SM
    SM --> MH
    MH --> CC
    MH --> TWC
    CC --> GC
    TWC --> WA
    CM --> DB
    
    %% Infrastructure
    FA --> DOC
    NG --> FA
    
    %% AI Processing
    CM --> GROQ
    
    style WA fill:#25D366,color:#fff
    style FA fill:#009688,color:#fff
    style CM fill:#2196F3,color:#fff
    style GC fill:#4285f4,color:#fff
    style DOC fill:#2496ED,color:#fff
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- ngrok account and authtoken
- Twilio WhatsApp Business account
- Groq API key
- Composio API key

### Setup

1. **Configure Environment**
   ```bash
cp .env.example .env
   # Edit .env with your API keys and credentials
```

2. **Start Application**
   ```bash
cd scripts/
   ./docker-run run
```

3. **Setup External Access**
   ```bash
./ngrok-setup setup
```

4. **Configure Twilio Webhook**
   - Get ngrok URL: `./ngrok-setup info`
   - Set Twilio webhook: `https://your-url.ngrok.io/webhook/twilio`

## 💬 Conversation Flow

The bot handles multiple conversation types:

- **📅 Scheduling**: Request appointment → Check availability → Collect data → Confirm
- **🔍 Consultation**: Check existing appointments by user identity
- **📝 Rescheduling**: Find appointment → Choose new time → Update calendar
- **❌ Cancellation**: Find appointment → Confirm cancellation
- **🔔 Proactive**: Bot suggests available slots for the day

### Context Management
- Never terminates session on topic changes
- Saves context and returns to previous flow
- Only ends session when user shows no scheduling interest

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI + Python 3.13 | REST API and webhook handling |
| **AI/LLM** | Groq API | Natural language processing |
| **Calendar** | Google Calendar via Composio | Appointment management |
| **Messaging** | Twilio WhatsApp API | WhatsApp integration |
| **Database** | SQLite | Conversation state and history |
| **Deployment** | Docker + docker-compose | Containerization |
| **Tunneling** | ngrok | External webhook access |

## 📁 Project Structure

```
medinow/
├── main.py                    # Application entry point
├── pyproject.toml            # Dependencies and project config
├── backend/                  # Core application
│   ├── api/                 # FastAPI endpoints
│   ├── agents/              # Conversation logic
│   ├── integrations/        # External service integrations
│   └── storage/             # Database and persistence
├── scripts/                 # Management and deployment scripts
├── docker/                  # Docker configuration
└── docs/                    # Documentation (requirements only)
```

## 🔧 Management Commands

```bash
# Docker Management
cd scripts/
./docker-run run             # Start application
./docker-run health          # Check health status
./docker-run logs            # View application logs
./docker-run stop            # Stop application

# ngrok Management  
./ngrok-setup setup          # Complete setup
./ngrok-setup start-bg       # Start tunnel in background
./ngrok-setup info           # Get tunnel URLs
./ngrok-setup status         # Show complete status
```

## 📋 Requirements

For detailed requirements, conversation flows, and business logic, see [docs/requisitos.md](docs/requisitos.md).

## 🚀 Production Deployment

The application is containerized and ready for deployment to cloud platforms:
- **Cloud Platforms**: DigitalOcean, AWS ECS, Google Cloud Run, Azure Container Instances
- **VPS**: Use included nginx configuration for reverse proxy
- **Docker Registry**: Build and push the container image

## 📞 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/webhook/twilio` | POST | WhatsApp webhook |
| `/api/chat` | POST | Direct chat interface |
| `/api/calendar/events` | POST | Create calendar events |
| `/api/calendar/available-slots` | GET | Get available time slots |

---

**Built for simplicity, designed for scale** 🎯
#!/bin/bash

# MediNow ngrok Setup and Management Script
# This script helps setup and manage ngrok tunnels for MediNow

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

# Check if ngrok is installed
check_ngrok() {
    if ! command -v ngrok &> /dev/null; then
        print_error "ngrok is not installed. Please install it first."
        echo ""
        echo "Installation options:"
        echo "1. Using snap: sudo snap install ngrok"
        echo "2. Using apt:"
        echo "   curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null"
        echo "   echo \"deb https://ngrok-agent.s3.amazonaws.com buster main\" | sudo tee /etc/apt/sources.list.d/ngrok.list"
        echo "   sudo apt update && sudo apt install ngrok"
        echo "3. Download from: https://ngrok.com/download"
        exit 1
    fi
}

# Check if MediNow is running
check_medinow() {
    if ! curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        print_error "MediNow is not running on port 8000."
        echo ""
        echo "Start MediNow first:"
        echo "  ./docker-run.sh run"
        echo "  OR"
        echo "  docker-compose up -d"
        exit 1
    fi
    print_success "MediNow is running and healthy!"
}

# Setup ngrok authtoken
setup_authtoken() {
    read -p "Enter your ngrok authtoken (from https://dashboard.ngrok.com/get-started/your-authtoken): " authtoken
    if [ -n "$authtoken" ]; then
        ngrok config add-authtoken "$authtoken"
        print_success "Authtoken configured successfully!"
    else
        print_error "Authtoken cannot be empty."
        exit 1
    fi
}

# Create ngrok configuration
create_config() {
    local config_dir="$HOME/.ngrok2"
    local config_file="$config_dir/ngrok.yml"
    
    mkdir -p "$config_dir"
    
    read -p "Enter a subdomain for your tunnel (optional, requires paid plan): " subdomain
    read -p "Enter a custom domain (optional, requires paid plan): " hostname
    
    cat > "$config_file" << EOF
version: "2"
authtoken: $(ngrok config check | grep authtoken | cut -d: -f2 | xargs)
tunnels:
  medinow:
    proto: http
    addr: 8000
    inspect: true
EOF

    if [ -n "$subdomain" ]; then
        echo "    subdomain: $subdomain" >> "$config_file"
    fi
    
    if [ -n "$hostname" ]; then
        cat >> "$config_file" << EOF
  medinow-custom:
    proto: http
    addr: 8000
    hostname: $hostname
    inspect: true
EOF
    fi
    
    print_success "ngrok configuration created at $config_file"
}

# Start ngrok tunnel
start_tunnel() {
    local tunnel_type="${1:-simple}"
    
    check_ngrok
    check_medinow
    
    case "$tunnel_type" in
        "simple")
            print_status "Starting simple ngrok tunnel..."
            print_warning "This will run in foreground. Press Ctrl+C to stop."
            echo ""
            ngrok http 8000
            ;;
        "background")
            print_status "Starting ngrok tunnel in background..."
            nohup ngrok http 8000 > ngrok.log 2>&1 &
            sleep 3
            local tunnel_url=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok\.io')
            if [ -n "$tunnel_url" ]; then
                print_success "ngrok tunnel started successfully!"
                echo "Tunnel URL: $tunnel_url"
                echo "Dashboard: http://localhost:4040"
                echo "Logs: tail -f ngrok.log"
            else
                print_error "Failed to get tunnel URL. Check ngrok.log for details."
            fi
            ;;
        "named")
            if [ ! -f "$HOME/.ngrok2/ngrok.yml" ]; then
                print_error "No ngrok configuration found. Run '$0 setup' first."
                exit 1
            fi
            print_status "Starting named tunnel 'medinow'..."
            ngrok start medinow
            ;;
    esac
}

# Get tunnel info
get_tunnel_info() {
    if ! curl -f http://localhost:4040/api/tunnels > /dev/null 2>&1; then
        print_error "ngrok is not running or dashboard is not accessible."
        exit 1
    fi
    
    local tunnels=$(curl -s http://localhost:4040/api/tunnels)
    local https_url=$(echo "$tunnels" | grep -o 'https://[^"]*\.ngrok\.io' | head -1)
    local http_url=$(echo "$tunnels" | grep -o 'http://[^"]*\.ngrok\.io' | head -1)
    
    if [ -n "$https_url" ]; then
        print_success "Active ngrok tunnels:"
        echo "HTTPS URL: $https_url"
        echo "HTTP URL: $http_url"
        echo "Dashboard: http://localhost:4040"
        echo ""
        echo "For Twilio webhook, use: ${https_url}/webhook/twilio"
        
        # Test the tunnel
        print_status "Testing tunnel..."
        if curl -f "${https_url}/api/health" > /dev/null 2>&1; then
            print_success "Tunnel is working correctly!"
        else
            print_warning "Tunnel may not be working properly. Check the application."
        fi
    else
        print_error "No active tunnels found."
    fi
}

# Stop ngrok
stop_tunnel() {
    print_status "Stopping ngrok tunnels..."
    pkill -f ngrok || true
    print_success "ngrok stopped."
}

# Complete setup workflow
setup_complete() {
    print_status "Starting complete MediNow + ngrok setup..."
    
    # Check if ngrok is installed
    check_ngrok
    
    # Setup authtoken if not configured
    if ! ngrok config check > /dev/null 2>&1; then
        print_warning "ngrok authtoken not configured."
        setup_authtoken
    fi
    
    # Start MediNow if not running
    if ! curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        print_status "Starting MediNow..."
        ./docker-run.sh run
        sleep 10
    fi
    
    # Create ngrok config
    if [ ! -f "$HOME/.ngrok2/ngrok.yml" ]; then
        print_status "Creating ngrok configuration..."
        create_config
    fi
    
    # Start tunnel
    start_tunnel background
    
    # Show info
    sleep 2
    get_tunnel_info
    
    print_success "Setup complete! Your MediNow application is now accessible via ngrok."
    echo ""
    echo "Next steps:"
    echo "1. Copy the HTTPS URL above"
    echo "2. Configure your Twilio webhook to: [HTTPS_URL]/webhook/twilio"
    echo "3. Test your WhatsApp integration"
}

# Show status
show_status() {
    echo "=== MediNow + ngrok Status ==="
    
    # Check MediNow
    if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        print_success "✓ MediNow is running (port 8000)"
    else
        print_error "✗ MediNow is not running"
    fi
    
    # Check ngrok
    if curl -f http://localhost:4040/api/tunnels > /dev/null 2>&1; then
        print_success "✓ ngrok is running (port 4040)"
        get_tunnel_info
    else
        print_error "✗ ngrok is not running"
    fi
    
    # Check Docker
    if docker ps --filter "name=medinow" --format "table {{.Names}}\t{{.Status}}" | grep -q medinow; then
        print_success "✓ Docker containers:"
        docker ps --filter "name=medinow" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        print_warning "! No MediNow Docker containers running"
    fi
}

# Main script logic
case "${1:-help}" in
    "setup")
        setup_complete
        ;;
    "start")
        start_tunnel "${2:-simple}"
        ;;
    "start-bg")
        start_tunnel background
        ;;
    "start-named")
        start_tunnel named
        ;;
    "info")
        get_tunnel_info
        ;;
    "stop")
        stop_tunnel
        ;;
    "status")
        show_status
        ;;
    "config")
        create_config
        ;;
    "authtoken")
        setup_authtoken
        ;;
    "help"|*)
        echo "MediNow ngrok Management Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  setup         Complete setup (MediNow + ngrok)"
        echo "  start         Start ngrok tunnel (foreground)"
        echo "  start-bg      Start ngrok tunnel (background)"
        echo "  start-named   Start named tunnel from config"
        echo "  info          Show tunnel information"
        echo "  stop          Stop ngrok tunnels"
        echo "  status        Show complete status"
        echo "  config        Create ngrok configuration"
        echo "  authtoken     Setup ngrok authtoken"
        echo "  help          Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 setup         # Complete first-time setup"
        echo "  $0 start-bg      # Quick background tunnel"
        echo "  $0 info          # Get tunnel URLs"
        echo "  $0 status        # Check everything"
        echo ""
        echo "Quick start:"
        echo "  1. Get ngrok authtoken from https://dashboard.ngrok.com"
        echo "  2. Run: $0 setup"
        echo "  3. Configure Twilio webhook with the provided URL"
        ;;
esac