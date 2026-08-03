# Squadron Ops on personal-pi

Durable local deploy: **Raspberry Pi** + **Tailscale/LAN only**.  
**Mac** = git working repository. **Pi** = always-on demo runtime.

No Funnel. No public port-forward. Portfolio demo accounts only (not internet-facing production).

## Access (after first deploy)

| Client | URL |
|--------|-----|
| Phone / Mac (Tailscale) | `http://100.66.35.41:3091/` |
| MagicDNS | `http://personal-pi.tail35da0c.ts.net:3091/` |
| Home LAN | `http://personal-pi:3091/` |

Single origin on port **3091**: SPA + `/api/*` + `/health` (uvicorn serves static `frontend/dist`).

Demo login: `anderson.robert` / `demo1234` (and other README accounts).

## Layout on Pi

| Path | Role |
|------|------|
| `/mnt/agent-data/agent/apps/squadron-ops` | App tree (rsync from Mac) |
| `…/.env` | Secrets (created on first install; **not** overwritten by sync) |
| `…/frontend/dist` | Production SPA build |
| `…/backend/.venv` | Python deps |
| Docker volume `squadron_ops_db` | Postgres data |
| `~/.config/systemd/user/squadron-ops-api.service` | Auto-start API+SPA |

## First install / update (from Mac)

```bash
cd /Users/dilloncooley/Documents/GitHub/squadron-ops
bash deploy/pi/sync-to-pi.sh
```

What it does:

1. rsync code → Pi (preserves Pi `.env`)
2. `docker compose up -d` (Postgres on `127.0.0.1:5433`)
3. venv + `pip install -r requirements.txt` (WeasyPrint **best-effort**; PDF may 503 if system libs missing)
4. `alembic upgrade head`
5. **seed if DB has zero persons** (first install)
6. `VITE_API_BASE_URL= npm run build` (same-origin API)
7. enable/restart `squadron-ops-api` on **:3091**

Options:

```bash
bash deploy/pi/sync-to-pi.sh --no-build   # rsync only
bash deploy/pi/sync-to-pi.sh --reseed     # force seed wipe+reload after install
```

First run can take several minutes on aarch64 (npm + pip).

## Ops on Pi

```bash
HOST=$(bash "$HOME/Documents/agent-shared/skills/personal-pi/scripts/ensure-connectivity.sh")
ssh "$HOST" '
systemctl --user status squadron-ops-api --no-pager | head -20
curl -sS -m 3 http://127.0.0.1:3091/health
docker compose -f /mnt/agent-data/agent/apps/squadron-ops/docker-compose.yml ps
'
```

Logs: `journalctl --user -u squadron-ops-api -f`

## Security model

- Trust boundary = **Tailscale / home LAN** (same class as syllabus `:3090`).
- Demo user passwords (`demo1234`) are for **portfolio demo**, not public internet.
- `ENVIRONMENT=development` on Pi so demo logins work; **first install generates** a long random `SECRET_KEY` and Postgres password (not the repo demo JWT default).
- Pi `.env` is mode **600** and is **never** rsynced from Mac (sync excludes `.env`).
- Postgres publishes only on **`127.0.0.1:5433`** (host loopback).
- API+SPA bind **`0.0.0.0:3091`** for Tailscale reachability — **not** for the public internet.
- Do **not** enable Tailscale **Funnel** or WAN port-forward for **3091**.
- OpenAPI `/docs` is enabled on the Pi for technical demos (same trust boundary as the app).
- If UFW blocks Tailscale → phone: allow `3091/tcp` from `100.64.0.0/10` (and LAN if desired) — needs sudo on Pi.

### Security checklist (ops)

| Check | Expected |
|-------|----------|
| Funnel / public port-forward | **Off** |
| Postgres bind | `127.0.0.1:5433` only |
| App port | `3091` on tailnet/LAN only |
| `.env` mode | `600` |
| `SECRET_KEY` | Not the repo demo default string |
| GitHub | No Pi `.env` or real passwords committed |

## Status (as of first live deploy)

- Unit: `squadron-ops-api.service` (user systemd)
- Health: `GET /health` → 200
- Demo seed loaded (empty-DB first install)

## Workflow (ongoing)

1. Edit on **Mac** git repo.
2. Commit / push GitHub as you prefer.
3. Deploy: `bash deploy/pi/sync-to-pi.sh`
4. Open phone URL on Tailscale.

Mac tree is never replaced by the Pi. Pi is a deploy target only.

## Limitations

1. **WeasyPrint / PDF** — optional system libraries; export endpoints may return 503 until libs installed.
2. **RAM** — Postgres + uvicorn (MemoryMax 1G on unit); avoid competing heavy builds with OpenClaw peaks.
3. **Reseed** — only on empty DB or explicit `--reseed` (seed **wipes** demo world).
4. **Two databases** — Mac Docker DB and Pi DB do not sync.
5. **Build on Pi** — npm/pip on aarch64 is slow; future: optional Mac cross-build not included.

## Uninstall

```bash
ssh personal-pi '
systemctl --user disable --now squadron-ops-api.service
rm -f ~/.config/systemd/user/squadron-ops-api.service
cd /mnt/agent-data/agent/apps/squadron-ops && docker compose down
# optional: rm -rf /mnt/agent-data/agent/apps/squadron-ops
'
```
