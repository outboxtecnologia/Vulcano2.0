#!/usr/bin/env bash
# auto-commit.sh — Checkpoint automático do repositório Vulcano2.0
# Rodado a cada 8h pelo Windows Task Scheduler (via Git Bash)

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="$REPO_DIR/scripts/auto-commit.log"
MAX_LOG_LINES=500

cd "$REPO_DIR" || { echo "ERRO: diretório não encontrado"; exit 1; }

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(timestamp)] $*" | tee -a "$LOG_FILE"; }

has_changes() {
  ! git diff --quiet 2>/dev/null ||
  ! git diff --cached --quiet 2>/dev/null ||
  [ -n "$(git ls-files --others --exclude-standard 2>/dev/null)" ]
}

if ! has_changes; then
  log "Sem mudanças detectadas — checkpoint ignorado."
  exit 0
fi

git add -A
CHANGED=$(git diff --cached --stat | tail -1)
MSG="chore: checkpoint automático $(date '+%Y-%m-%d %H:%M') | $CHANGED"

if git commit -m "$MSG"; then
  log "OK  — $MSG"
else
  log "ERRO — falha ao commitar"
  exit 1
fi

if git push origin master >> "$LOG_FILE" 2>&1; then
  log "PUSH — enviado para GitHub com sucesso"
else
  log "AVISO — push falhou (sem internet?), commit local salvo"
fi

if [ -f "$LOG_FILE" ]; then
  tail -n "$MAX_LOG_LINES" "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
fi
