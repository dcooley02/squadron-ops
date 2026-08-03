#!/usr/bin/env bash
# ONE-TIME on personal-pi (interactive sudo). Installs Docker Engine + compose plugin
# and adds user `pi` to the docker group so squadron-ops compose can run without sudo.
#
# On Pi:
#   bash /mnt/agent-data/agent/apps/squadron-ops/deploy/pi/bootstrap-docker-once.sh
# Then log out/in (or reboot) so group membership applies, and from Mac:
#   bash deploy/pi/sync-to-pi.sh

set -euo pipefail

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Run as user pi (script will sudo), not as root." >&2
  exit 1
fi

if command -v docker >/dev/null 2>&1; then
  echo "docker already installed: $(docker --version)"
  docker compose version 2>/dev/null || true
  exit 0
fi

echo "==> Install Docker (official convenience script)"
curl -fsSL https://get.docker.com | sudo sh

echo "==> Add $USER to docker group"
sudo usermod -aG docker "$USER"

echo
echo "Docker installed. You must re-login (or reboot) for group docker to apply:"
echo "  exit  # then ssh back in"
echo "  groups   # should include docker"
echo "  docker ps"
echo
echo "Then from Mac:"
echo "  cd ~/Documents/GitHub/squadron-ops && bash deploy/pi/sync-to-pi.sh"
