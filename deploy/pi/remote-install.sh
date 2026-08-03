#!/usr/bin/env bash
# Run ON the Pi inside the app tree (invoked by sync-to-pi.sh).
# Starts Postgres, installs deps, migrates, seeds if empty, builds SPA, restarts unit.
set -euo pipefail

DIR="${SQUADRON_OPS_DIR:-/mnt/agent-data/agent/apps/squadron-ops}"
cd "$DIR"

export PATH="/usr/local/bin:$HOME/.local/bin:$HOME/.npm-global/bin:$PATH"

echo "==> ensure .env"
if [[ ! -f .env ]]; then
  if [[ -f deploy/pi/env.pi.example ]]; then
    cp deploy/pi/env.pi.example .env
    # Generate secrets on first install
    if command -v openssl >/dev/null 2>&1; then
      PW="$(openssl rand -hex 16)"
      SK="$(openssl rand -hex 32)"
      sed -i "s/CHANGE_ME_LONG_RANDOM/${PW}/g" .env
      sed -i "s/CHANGE_ME_OPENSSL_RAND_HEX_32/${SK}/g" .env
      # DATABASE_URL embeds password — rewrite fully
      sed -i "s#DATABASE_URL=.*#DATABASE_URL=postgresql+psycopg://squadron_ops:${PW}@127.0.0.1:5433/squadron_ops#" .env
      echo "    wrote .env with generated POSTGRES_PASSWORD + SECRET_KEY"
    else
      echo "warn: openssl missing — edit .env and set CHANGE_ME_* secrets" >&2
    fi
  else
    echo "missing deploy/pi/env.pi.example and .env" >&2
    exit 1
  fi
fi
chmod 600 .env 2>/dev/null || true

# shellcheck disable=SC1091
set -a
# shellcheck source=/dev/null
source .env
set +a

echo "==> Postgres (docker compose)"
if ! command -v docker >/dev/null 2>&1; then
  echo "docker required on Pi" >&2
  exit 1
fi
docker compose up -d

echo "==> wait for Postgres :5433"
for i in $(seq 1 40); do
  if docker compose exec -T db pg_isready -U "${POSTGRES_USER:-squadron_ops}" >/dev/null 2>&1; then
    break
  fi
  if [[ $i -eq 40 ]]; then
    echo "Postgres not ready" >&2
    exit 1
  fi
  sleep 1
done

echo "==> backend venv + deps"
cd "$DIR/backend"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -U pip
# WeasyPrint is best-effort: install requirements; PDF may 503 if system libs missing
pip install -q -r requirements.txt || {
  echo "warn: full requirements failed — retry without weasyprint pin change" >&2
  pip install -q -r requirements.txt
}

echo "==> alembic upgrade"
# .env is at repo root; database.py loads parents[2]/.env from backend/app/database.py → repo root
alembic upgrade head

echo "==> seed if empty"
python - <<'PY'
from app.database import SessionLocal
from app.models.models import Person

db = SessionLocal()
try:
    n = db.query(Person).count()
finally:
    db.close()

if n == 0:
    print("DB empty — running seed.py")
    import runpy
    runpy.run_path("seed.py", run_name="__main__")
else:
    print(f"DB has {n} persons — skip seed")
PY

echo "==> frontend production build (same-origin API)"
cd "$DIR/frontend"
if [[ ! -d node_modules ]]; then
  npm ci
else
  npm ci --prefer-offline 2>/dev/null || npm ci
fi
# Empty base → relative /api on same host:port (see client.ts)
VITE_API_BASE_URL= npm run build

echo "==> systemd user unit"
mkdir -p "$HOME/.config/systemd/user"
cp -f "$DIR/deploy/pi/squadron-ops-api.service" "$HOME/.config/systemd/user/squadron-ops-api.service"
systemctl --user daemon-reload
systemctl --user enable squadron-ops-api.service
systemctl --user restart squadron-ops-api.service
sleep 2
systemctl --user --no-pager --full status squadron-ops-api.service | head -25
curl -sS -m 8 -o /dev/null -w "health_http=%{http_code}\n" http://127.0.0.1:3091/health || true
curl -sS -m 8 -o /dev/null -w "spa_http=%{http_code}\n" http://127.0.0.1:3091/ || true

echo "==> remote-install done"
