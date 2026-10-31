#!/usr/bin/env bash
# One-time setup for a fresh Ubuntu machine. Safe to re-run.
#   sudo ./bootstrap.sh                 full setup
#   sudo ./bootstrap.sh --tags ssh      one part (base, ssh, firewall, tools, helpers)
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo: sudo ./bootstrap.sh" >&2
  exit 1
fi

if [[ -z "${SUDO_USER:-}" || "$SUDO_USER" == "root" ]]; then
  echo "Run this through sudo from your normal user, not from a root shell." >&2
  exit 1
fi

if ! grep -qi ubuntu /etc/os-release; then
  echo "This setup only supports Ubuntu." >&2
  exit 1
fi

cd "$(dirname "$(readlink -f "$0")")/ansible"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y software-properties-common
add-apt-repository -y universe
add-apt-repository -y multiverse
apt-get install -y ansible-core python3-apt

exec ansible-playbook site.yml -e "target_user=$SUDO_USER" "$@"
