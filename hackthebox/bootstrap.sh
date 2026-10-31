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

# Runs before apt installs Ansible, so this can't be an Ansible task.
# VMs often have IPv4 only, and a regional mirror may return only IPv6 addresses.
fix_apt_network() {
  local sources=(/etc/apt/sources.list /etc/apt/sources.list.d)
  local mirror

  if ip -4 route show default | grep -q .; then
    echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4

    for mirror in $(grep -rhoE '[a-z]{2}\.archive\.ubuntu\.com' "${sources[@]}" 2>/dev/null | sort -u); do
      if ! getent ahostsv4 "$mirror" > /dev/null; then
        echo "$mirror has no IPv4 address, switching to archive.ubuntu.com"
        grep -rlF "$mirror" "${sources[@]}" 2>/dev/null | xargs -r sed -i "s/${mirror//./\\.}/archive.ubuntu.com/g"
      fi
    done
  fi
}

fix_apt_network

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y software-properties-common
add-apt-repository -y universe
add-apt-repository -y multiverse
apt-get install -y ansible-core python3-apt

exec ansible-playbook -i localhost, site.yml -e "target_user=$SUDO_USER" "$@"
