# MediNow with ngrok Setup Guide

This guide explains how to use MediNow with Docker and expose it using ngrok for external access (useful for Twilio webhooks and testing).

## Prerequisites

1. **Docker & Docker Compose** installed
2. **ngrok** account and installation
3. **Environment variables** configured

## Quick Start

### 1. Setup Environment Variables

```bash
# Copy and edit the environment file
cp .env.example .env
# Edit .env with your actual credentials
```

### 2. Build and Run with Docker

```bash
# Using the convenience script (recommended)
./docker-run.sh run

# Or manually with docker-compose
docker-compose up -d
```

### 3. Verify Application is Running

```bash
# Check health
./docker-run.sh health

# Or manually
curl http://localhost:8000/health
```

## ngrok Integration

### Install ngrok

```bash
# Download and install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Or using snap
sudo snap install ngrok
```

### Configure ngrok

```bash
# Add your authtoken (get it from https://dashboard.ngrok.com/get-started/your-authtoken)
ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
```

### Expose MediNow with ngrok

```bash
# Start ngrok tunnel to your Docker container
ngrok http 8000

# For a custom subdomain (requires paid plan)
ngrok http 8000 --subdomain=medinow-yourname

# For a custom domain (requires paid plan)
ngrok http 8000 --hostname=medinow.yourdomain.com
```

### Configure Twilio Webhook

1. Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)
2. In your Twilio Console:
   - Go to Phone Numbers → Manage → Active numbers
   - Select your WhatsApp number
   - Set webhook URL to: `https://your-ngrok-url.ngrok.io/webhook/twilio`

## Production Deployment Options

### Option 1: Simple Docker Run

```bash
# Build and run directly
./docker-run.sh run-simple
```

### Option 2: With Nginx Reverse Proxy

```bash
# Run with nginx (production profile)
docker-compose --profile production up -d
```

### Option 3: Cloud Deployment

For production, consider deploying to:
- **DigitalOcean App Platform**
- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Instances**

## Useful Commands

```bash
# View logs
./docker-run.sh logs

# Stop application
./docker-run.sh stop

# Restart application
./docker-run.sh restart

# Clean up Docker resources
./docker-run.sh cleanup

# Manual Docker commands
docker-compose ps                    # Check status
docker-compose logs -f medinow-app  # Follow logs
docker-compose exec medinow-app bash # Shell access
```

## ngrok Advanced Configuration

### Create ngrok Configuration File

```bash
# Create ~/.ngrok2/ngrok.yml
mkdir -p ~/.ngrok2
cat > ~/.ngrok2/ngrok.yml << EOF
version: "2"
authtoken: YOUR_AUTHTOKEN_HERE
tunnels:
  medinow:
    proto: http
    addr: 8000
    subdomain: medinow-yourname  # requires paid plan
    inspect: true
  medinow-secure:
    proto: http
    addr: 8000
    hostname: medinow.yourdomain.com  # requires paid plan
    inspect: true
EOF
```

### Use Named Tunnels

```bash
# Start specific tunnel
ngrok start medinow

# Start multiple tunnels
ngrok start medinow medinow-secure
```

## Monitoring and Debugging

### Check Application Health

```bash
# Health endpoint
curl http://localhost:8000/health

# Through ngrok
curl https://your-ngrok-url.ngrok.io/health
```

### View ngrok Dashboard

Open `http://localhost:4040` to see:
- Active tunnels
- Request history
- Traffic inspection

### Debug Webhooks

1. Check ngrok request logs at `http://localhost:4040`
2. View application logs: `./docker-run.sh logs`
3. Test webhook manually:

```bash
curl -X POST https://your-ngrok-url.ngrok.io/webhook/twilio \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+1234567890&Body=test&AccountSid=your_account_sid"
```

## Environment Variables Reference

```bash
# Required for Twilio
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Required for AI
GROQ_API_KEY=your_groq_api_key

# Required for Calendar
COMPOSIO_API_KEY=your_composio_api_key

# Optional
ENVIRONMENT=production
DEBUG=false
```

## Troubleshooting

### Common Issues

1. **Container won't start**
   ```bash
   # Check logs
   docker-compose logs medinow-app
   
   # Check if port is available
   lsof -i :8000
   ```

2. **ngrok tunnel disconnects**
   ```bash
   # Use --log to see detailed logs
   ngrok http 8000 --log=stdout
   
   # Check your account limits
   ngrok credits
   ```

3. **Twilio webhook fails**
   - Verify ngrok URL is accessible
   - Check Twilio webhook configuration
   - Validate request format in ngrok dashboard

### Health Checks

The application includes health checks at:
- `/health` - Basic health status
- Docker health check every 30 seconds
- ngrok tunnel monitoring

## Security Considerations

1. **Never commit .env files**
2. **Use secrets management in production**
3. **Enable HTTPS in production**
4. **Configure proper CORS settings**
5. **Use ngrok's authentication features for sensitive data**

For production deployments, replace ngrok with proper domain and SSL certificate management.