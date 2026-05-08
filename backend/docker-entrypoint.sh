#!/bin/sh
set -e

BOOTSTRAP_ON_START="${BOOTSTRAP_ON_START:-1}"
BOOTSTRAP_TARGET="${BOOTSTRAP_TARGET:-all}"
BOOTSTRAP_STRICT="${BOOTSTRAP_STRICT:-0}"

if [ "$BOOTSTRAP_ON_START" = "1" ]; then
  echo "[entrypoint] Running schema bootstrap (target=$BOOTSTRAP_TARGET)..."
  if python bootstrap_schema.py --target "$BOOTSTRAP_TARGET"; then
    echo "[entrypoint] Bootstrap completed."
  else
    if [ "$BOOTSTRAP_STRICT" = "1" ]; then
      echo "[entrypoint] Bootstrap failed and BOOTSTRAP_STRICT=1. Aborting startup."
      exit 1
    fi
    echo "[entrypoint] Bootstrap failed, continuing startup (BOOTSTRAP_STRICT=0)."
  fi
else
  echo "[entrypoint] Bootstrap skipped (BOOTSTRAP_ON_START=0)."
fi

exec uvicorn main:app --host 0.0.0.0 --port 8000
