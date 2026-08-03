#!/usr/bin/env bash
# Sync squadron-ops from Mac → personal-pi, then install/build/restart.
#
# Usage (Mac):
#   bash deploy/pi/sync-to-pi.sh              # rsync + remote install
#   bash deploy/pi/sync-to-pi.sh --no-build   # rsync only (no remote rebuild)
#   bash deploy/pi/sync-to-pi.sh --reseed     # force seed after migrate (WIPES demo data via seed wipe)
#
# Mac = git working repo. Pi = runtime under /mnt/agent-data/agent/apps/squadron-ops.
# Tailscale/LAN only. Do not Funnel port 3091.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE_DIR="/mnt/agent-data/agent/apps/squadron-ops"
NO_BUILD=0
RESEED=0

for arg in "$@"; do
  case "$arg" in
    --no-build) NO_BUILD=1 ;;
    --reseed) RESEED=1 ;;
    -h|--help)
      sed -n '2,14p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown arg: $arg" >&2
      exit 2
      ;;
  esac
done

if [[ -x "$HOME/Documents/agent-shared/skills/personal-pi/scripts/ensure-connectivity.sh" ]]; then
  HOST="$(bash "$HOME/Documents/agent-shared/skills/personal-pi/scripts/ensure-connectivity.sh")"
else
  HOST="${PERSONAL_PI_HOST:-personal-pi}"
fi

echo "→ host: $HOST"
echo "→ remote: $REMOTE_DIR"
echo "→ local: $ROOT"

ssh -o BatchMode=yes "$HOST" "mkdir -p '$REMOTE_DIR'"

RSYNC_EXCLUDES=(
  --exclude node_modules
  --exclude frontend/dist
  --exclude backend/.venv
  --exclude '**/__pycache__'
  --exclude .git
  --exclude .agents
  --exclude .superpowers
  --exclude .worktrees
  --exclude .kilo
  --exclude coverage
  --exclude '*.pyc'
  --exclude .DS_Store
  --exclude frontend/node_modules
)

# Preserve Pi .env (secrets) across deploys
rsync -az --delete \
  "${RSYNC_EXCLUDES[@]}" \
  --exclude .env \
  -e "ssh -o BatchMode=yes" \
  "$ROOT/" \
  "$HOST:$REMOTE_DIR/"

# Always push deploy scripts/examples (env.example only)
rsync -az -e "ssh -o BatchMode=yes" \
  "$ROOT/deploy/pi/" \
  "$HOST:$REMOTE_DIR/deploy/pi/"

if [[ "$NO_BUILD" -eq 1 ]]; then
  echo "→ skip remote install (--no-build)"
  exit 0
fi

echo "→ remote install (compose, venv, migrate, seed-if-empty, SPA build, systemd)"
ssh -o BatchMode=yes "$HOST" \
  "RESEED=$RESEED SQUADRON_OPS_DIR='$REMOTE_DIR' bash '$REMOTE_DIR/deploy/pi/remote-install.sh'"

if [[ "$RESEED" -eq 1 ]]; then
  echo "→ --reseed: force seed (wipe+reload)"
  ssh -o BatchMode=yes "$HOST" "bash -s" <<REMOTE
set -euo pipefail
cd '$REMOTE_DIR/backend'
source .venv/bin/activate
set -a; source ../.env; set +a
python seed.py
systemctl --user restart squadron-ops-api.service
REMOTE
fi

echo
echo "Open on phone/Mac (Tailscale connected):"
echo "  http://100.66.35.41:3091/"
echo "  http://personal-pi:3091/"
echo "  http://personal-pi.tail35da0c.ts.net:3091/"
echo
echo "Service: systemctl --user status squadron-ops-api"
echo "Logs:    journalctl --user -u squadron-ops-api -f"
echo "Health:  curl -sS http://127.0.0.1:3091/health"
