#!/bin/bash
# ─────────────────────────────────────────────────────────────
# tunnel.sh — Expose your local backend via Cloudflare Tunnel
# FREE — no credit card, no account needed for quick tunnels
# Usage: ./scripts/tunnel.sh
# ─────────────────────────────────────────────────────────────

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[TUNNEL]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════╗"
echo "║  RedoClaim — Cloudflare Tunnel Setup     ║"
echo "║  This exposes your local backend to Vercel   ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    log "Installing cloudflared..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
        sudo dpkg -i cloudflared-linux-amd64.deb
        rm cloudflared-linux-amd64.deb
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install cloudflare/cloudflare/cloudflared
    else
        warn "Install cloudflared manually: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
        exit 1
    fi
fi

log "Starting Cloudflare Tunnel on port 8000..."
echo ""
warn "Keep this terminal open while users access your app!"
warn "Copy the https://xxx.trycloudflare.com URL and:"
warn "  1. Set it as NEXT_PUBLIC_API_URL in Vercel dashboard"
warn "  2. Add it to ALLOWED_ORIGINS in your backend .env"
warn "  3. Run: docker compose restart backend"
echo ""

cloudflared tunnel --url http://localhost:8000
