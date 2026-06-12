#!/bin/bash
# ─────────────────────────────────────────────────────────────
# pull-models.sh — Pull all required Ollama models
# Run this separately if setup.sh model pull timed out
# Usage: ./scripts/pull-models.sh [--cpu-only]
# ─────────────────────────────────────────────────────────────

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CPU_ONLY=false
[[ "$1" == "--cpu-only" ]] && CPU_ONLY=true

log() { echo -e "${GREEN}[MODEL]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

echo ""
echo "═══════════════════════════════════════════"
echo "   RedoClaim — Ollama Model Puller"
echo "═══════════════════════════════════════════"
echo ""

pull_model() {
    local model=$1
    local size=$2
    local task=$3
    log "Pulling: $model ($size) → $task"
    docker compose exec ollama ollama pull "$model"
    if [ $? -eq 0 ]; then
        log "✅ $model ready"
    else
        warn "❌ Failed to pull $model. Check internet connection."
    fi
    echo ""
}

# Embeddings (always needed — small and fast)
pull_model "nomic-embed-text:latest" "274MB" "RAG embeddings (required)"

if [ "$CPU_ONLY" = true ]; then
    echo "─── CPU-only mode: using 4-bit quantized models ───"
    echo "    These are ~50% smaller, ~80% quality of full models"
    echo ""
    pull_model "qwen2.5:7b-instruct-q4_K_M" "4.4GB" "Clause extraction"
    pull_model "mistral:7b-instruct-q4_K_M" "4.1GB" "Appeal letter drafting"
    pull_model "deepseek-r1:8b-q4_K_M"      "4.6GB" "Legal reasoning (IRDAI audit)"
else
    echo "─── Full precision models ───"
    pull_model "qwen2.5:7b"     "4.7GB" "Clause extraction + classification"
    pull_model "mistral:7b"     "4.1GB" "Appeal letter drafting"
    pull_model "deepseek-r1:8b" "4.9GB" "Legal reasoning (IRDAI audit)"
fi

echo ""
log "Model check:"
docker compose exec ollama ollama list

echo ""
echo "─── Model RAM requirements ──────────────────────"
echo "  nomic-embed-text : ~500MB RAM"
echo "  qwen2.5:7b       : ~5GB RAM"
echo "  mistral:7b       : ~5GB RAM"
echo "  deepseek-r1:8b   : ~6GB RAM"
echo ""
echo "  ⚠️  Models run sequentially (not all at once)"
echo "     Total needed: ~6GB RAM for largest model"
echo "─────────────────────────────────────────────────"
echo ""
log "All models pulled. Restart backend: docker compose restart backend"
