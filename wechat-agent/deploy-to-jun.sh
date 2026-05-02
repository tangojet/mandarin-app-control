#!/usr/bin/env bash
# Deploy wechat-agent (WeChat desktop automation) to Jun's Mac Mini
# Usage: bash wechat-agent/deploy-to-jun.sh
#
# Architecture:
#   wechat-net (Docker network)
#   └── wechat-desktop  (Xvfb + WeChat Linux + AT-SPI agent, noVNC on host:56090, agent API on host:55007)
#
# The wechat-agent FastAPI service runs on the host (not in Docker) and calls
# the AT-SPI agent inside the container via http://localhost:55007.
#
# State directory: ~/openclaw-local/wechat-data (WeChat config persistence)
set -euo pipefail

JUN_HOST="jun@192.168.1.181"
DOCKER="/Applications/Docker.app/Contents/Resources/bin/docker"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Paths on Jun's machine
REMOTE_DIR="\$HOME/openclaw-local/services/wechat-agent"
WECHAT_DATA_DIR="\$HOME/openclaw-local/wechat-data"

NOVNC_HOST_PORT=56090
AGENT_API_PORT=55007
VNC_PASSWORD="wechat1"
SERVICE_PORT=8091

echo "============================================================"
echo "  WeChat Agent Deploy"
echo "============================================================"
echo ""

# ── Step 1: Verify ozaiya-desktop image exists ──────────────────────────────
echo "=== Step 1: Verify Docker image ==="
ssh "${JUN_HOST}" "${DOCKER} image inspect ozaiya-desktop:latest --format '{{.Id}}' >/dev/null 2>&1" \
  || { echo "ERROR: ozaiya-desktop:latest image not found on Jun's machine."; echo "Build it first: ozaiya/scripts/desktop-container/deploy-to-jun.sh"; exit 1; }
echo "  ozaiya-desktop:latest: OK"

# ── Step 2: Ensure directories exist ────────────────────────────────────────
echo ""
echo "=== Step 2: Ensure directories ==="
ssh "${JUN_HOST}" "mkdir -p ${WECHAT_DATA_DIR} ${REMOTE_DIR}"
echo "  ${WECHAT_DATA_DIR} (WeChat config)"
echo "  ${REMOTE_DIR} (agent service)"

# ── Step 3: Sync wechat-agent files ─────────────────────────────────────────
echo ""
echo "=== Step 3: Sync wechat-agent files ==="
rsync -avzP --exclude '.venv' --exclude '__pycache__' --exclude '.env' \
    "${SCRIPT_DIR}/" "${JUN_HOST}:${REMOTE_DIR}/"
echo "  Synced to ${REMOTE_DIR}"

# ── Step 4: Install Python dependencies ─────────────────────────────────────
echo ""
echo "=== Step 4: Install Python dependencies ==="
ssh "${JUN_HOST}" "cd ${REMOTE_DIR} && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"

# ── Step 5: docker compose up (desktop container) ───────────────────────────
echo ""
echo "=== Step 5: Start wechat-desktop container ==="
ssh "${JUN_HOST}" "${DOCKER} rm -f wechat-desktop 2>/dev/null || true"
ssh "${JUN_HOST}" "cd ${REMOTE_DIR} && ${DOCKER} compose up -d"
echo "  Container started"

# ── Step 6: Verify container ────────────────────────────────────────────────
echo ""
echo "=== Step 6: Verify ==="
sleep 5
ssh "${JUN_HOST}" "${DOCKER} ps --filter name=wechat --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

echo ""
echo "Testing AT-SPI agent..."
ssh "${JUN_HOST}" "curl -sS --max-time 5 http://localhost:${AGENT_API_PORT}/health" | python3 -m json.tool 2>/dev/null || echo "  (Agent may still be starting...)"

# ── Step 7: .env setup hint ─────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  DEPLOY COMPLETE"
echo "============================================================"
echo ""
echo "  wechat-desktop:  noVNC at http://192.168.1.181:${NOVNC_HOST_PORT}/vnc.html?password=${VNC_PASSWORD}"
echo "  AT-SPI agent:    http://192.168.1.181:${AGENT_API_PORT}"
echo "  WeChat data:     ${WECHAT_DATA_DIR}"
echo "  Agent service:   ${REMOTE_DIR}"
echo ""
echo "  To start the wechat-agent FastAPI service:"
echo "    ssh ${JUN_HOST} 'cd ${REMOTE_DIR} && nohup .venv/bin/python main.py > wechat-agent.log 2>&1 &'"
echo ""
echo "  First time: open noVNC and log into WeChat manually."
echo ""
echo "  Management:"
echo "    ssh ${JUN_HOST} 'cd ${REMOTE_DIR} && ${DOCKER} compose ps'"
echo "    ssh ${JUN_HOST} 'cd ${REMOTE_DIR} && ${DOCKER} compose logs -f'"
echo "    ssh ${JUN_HOST} 'cd ${REMOTE_DIR} && ${DOCKER} compose restart'"
echo "    ssh ${JUN_HOST} 'cd ${REMOTE_DIR} && ${DOCKER} compose down'"
echo ""
