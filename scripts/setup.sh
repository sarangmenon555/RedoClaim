#!/bin/bash
# ============================================================
# RedoClaim — Complete Setup Script
# Run this ONCE on your server to initialize everything.
# Usage: chmod +x scripts/setup.sh && ./scripts/setup.sh
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[REDOCLAIM]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════╗"
echo "║       RedoClaim — Setup Script         ║"
echo "║   AI Insurance Rights Platform for India   ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}"

# 1. Check Docker
if ! command -v docker &> /dev/null; then
    error "Docker not found. Install Docker first: https://docs.docker.com/engine/install/"
fi
if ! command -v docker compose &> /dev/null; then
    error "Docker Compose not found. Install Docker Compose v2."
fi
log "Docker found: $(docker --version)"

# 2. Check available RAM
TOTAL_RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
log "Total RAM: ${TOTAL_RAM_GB}GB"
if [ "$TOTAL_RAM_GB" -lt 8 ]; then
    warn "Less than 8GB RAM detected. Models will run slower. Recommended: 16GB+"
fi

# 3. Create .env if not exists
if [ ! -f .env ]; then
    log "Creating .env from template..."
    cat > .env << 'EOF'
DATABASE_URL=postgresql+asyncpg://redoclaim:redoclaim_secret@postgres:5432/redoclaim_db
REDIS_URL=redis://redis:6379/0
OLLAMA_BASE_URL=http://ollama:11434
QDRANT_URL=http://qdrant:6333
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
JWT_SECRET=CHANGE_THIS_IMMEDIATELY_USE_openssl_rand_hex_32
JWT_ALGORITHM=HS256
ENVIRONMENT=production
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
    warn "IMPORTANT: Edit .env and set JWT_SECRET to a random 32+ char string!"
    warn "Run: openssl rand -hex 32"
fi

# 4. Start infrastructure first (no Ollama yet)
log "Starting infrastructure services..."
docker compose up -d postgres redis minio qdrant
sleep 5
log "Waiting for PostgreSQL..."
until docker compose exec postgres pg_isready -U redoclaim -d redoclaim_db > /dev/null 2>&1; do
    sleep 2
done
log "PostgreSQL ready."

# 5. Start Ollama
log "Starting Ollama..."
docker compose up -d ollama
sleep 5

# 6. Pull AI models
echo ""
log "Pulling local AI models via Ollama..."
log "This may take 10-30 minutes depending on your internet speed."
echo ""

MODEL_PLAN=(
    "nomic-embed-text:latest:274MB:Embeddings (RAG)"
    "qwen2.5:7b:4.7GB:Clause extraction + classification"
    "mistral:7b:4.1GB:Appeal letter drafting"
    "deepseek-r1:8b:4.9GB:Legal reasoning (IRDAI audit)"
)

for entry in "${MODEL_PLAN[@]}"; do
    IFS=':' read -r model size desc <<< "$entry"
    log "Pulling $model ($size) — $desc"
    docker compose exec ollama ollama pull "$model" || warn "Failed to pull $model, skipping"
    echo ""
done

# CPU-only fallback (lighter models)
TOTAL_RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM_GB" -lt 12 ]; then
    warn "Low RAM: Consider using smaller models."
    warn "Alternative: qwen2.5:3b (2GB) instead of qwen2.5:7b"
fi

# 7. Start backend + worker
log "Starting backend services..."
docker compose up -d backend worker beat

# 8. Run DB migrations
log "Running database migrations..."
sleep 5
docker compose exec backend python -c "
import asyncio
from app.core.database import init_db
asyncio.run(init_db())
print('Database initialized.')
"

# 9. Seed IRDAI regulations into Qdrant
log "Seeding IRDAI regulations into vector database..."
docker compose exec backend python -c "
import asyncio
from app.services.rag.rag_pipeline import ensure_collections
asyncio.run(ensure_collections())
print('Qdrant collections ready.')
"

# 10. Start nginx
log "Starting Nginx..."
docker compose up -d nginx

# 11. Health check
sleep 3
if curl -s http://localhost:8000/api/health | grep -q "ok"; then
    log "Backend API is healthy!"
else
    warn "Backend may still be starting up. Check: docker compose logs backend"
fi

# Summary
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           RedoClaim is running! 🎉                   ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Backend API:   http://localhost:8000/api/docs           ║${NC}"
echo -e "${GREEN}║  Ollama:        http://localhost:11434                   ║${NC}"
echo -e "${GREEN}║  MinIO console: http://localhost:9001                   ║${NC}"
echo -e "${GREEN}║  Qdrant:        http://localhost:6333/dashboard         ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Frontend: Deploy /frontend to Vercel                   ║${NC}"
echo -e "${GREEN}║  Set NEXT_PUBLIC_API_URL=https://your-server-ip:8000    ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
warn "Remember to:"
warn "1. Set JWT_SECRET in .env (openssl rand -hex 32)"
warn "2. Configure firewall: allow port 8000 from Vercel only"
warn "3. Set ALLOWED_ORIGINS in backend to your Vercel domain"
