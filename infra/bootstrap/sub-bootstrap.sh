#!/usr/bin/env bash
# Phase B bootstrap for a sub-server (Ubuntu 24.04). Run as root on a fresh box.
#
# Diff from main-bootstrap.sh:
#   - No /etc/traefik dirs (sub has no Traefik)
#   - No public 80/443 in ufw (only 22 + tailscale0 traffic)
#   - REQUIRES TS_AUTHKEY env var: ephemeral=false key from Tailscale admin console
#
# Usage:
#   TS_AUTHKEY=tskey-auth-XXXXXX HOSTNAME=subapp1 \
#     ssh -i <key> root@<sub-ip> 'bash -s' < sub-bootstrap.sh
#
# Idempotent. Re-run safe (Tailscale up is no-op once joined).
set -euo pipefail

: "${TS_AUTHKEY:?TS_AUTHKEY required (Tailscale auth key, ephemeral=false)}"
: "${HOSTNAME:?HOSTNAME required (e.g. subapp1) — used as Tailscale node name}"

log() { printf '\n\033[1;36m[sub-bootstrap]\033[0m %s\n' "$*"; }

# ─── 1. Hostname ────────────────────────────────────────────────────────────
hostnamectl set-hostname "$HOSTNAME"

# ─── 2. System update ───────────────────────────────────────────────────────
log "apt update + upgrade"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y

# ─── 3. Core packages (same set as main, minus restic — backups run on main) ─
log "installing podman, ufw, unattended-upgrades, netavark, age, jq"
apt-get install -y --no-install-recommends \
    podman podman-compose \
    netavark aardvark-dns \
    uidmap slirp4netns fuse-overlayfs \
    ufw unattended-upgrades \
    age \
    curl jq ca-certificates gnupg

# ─── 4. Tailscale install + join ────────────────────────────────────────────
log "installing Tailscale apt repo + binary"
if ! command -v tailscale >/dev/null 2>&1; then
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/noble.noarmor.gpg \
        -o /usr/share/keyrings/tailscale-archive-keyring.gpg
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/noble.tailscale-keyring.list \
        -o /etc/apt/sources.list.d/tailscale.list
    apt-get update -y
    apt-get install -y tailscale
fi
systemctl enable --now tailscaled

log "joining Tailscale (--ssh disabled; SSH stays on key auth)"
tailscale up \
    --authkey="$TS_AUTHKEY" \
    --hostname="$HOSTNAME" \
    --accept-dns=true \
    --accept-routes=false \
    --ssh=false
TS_IP=$(tailscale ip -4 | head -1)
log "Tailscale IP: $TS_IP"

# ─── 5. Firewall ────────────────────────────────────────────────────────────
log "configuring ufw — 22 public (tightened in Phase E), all app traffic via tailscale0"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'ssh'
# Phase E: replace with `ufw allow in on tailscale0 to any port 22` and drop public 22.
# App ports (e.g. 8000) bind to tailscale0 only — no ufw rule needed; main reaches via TS.
#
# CRITICAL for rootful Podman bridge networking: container → host DNS (aardvark
# on the bridge gateway IP) hits the INPUT chain on the podman1 bridge interface.
# Without this rule UFW drops the DNS UDP packet, breaking container-name
# resolution inside the network — symptom is `socket.gaierror: [Errno -3]
# Temporary failure in name resolution`. Hit live on pump-server 2026-05-07.
# Rootless Podman with slirp4netns (e.g. main's portfolio user) does NOT need
# this rule; only rootful bridge networks do.
ufw allow in on podman1 comment 'podman bridge — container DNS via aardvark'
ufw --force enable
ufw status verbose

# ─── 6. Unattended security upgrades ────────────────────────────────────────
log "enabling unattended-upgrades (security only, weekly reboot 04:30)"
cat >/etc/apt/apt.conf.d/50unattended-upgrades <<'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "04:30";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
EOF
cat >/etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF
systemctl enable --now unattended-upgrades

# ─── 7. Users (deploy + app, mirror main) ───────────────────────────────────
log "creating deploy + app users"
if ! id deploy >/dev/null 2>&1; then
    useradd -m -s /bin/bash -G sudo deploy
    install -d -m 0700 -o deploy -g deploy /home/deploy/.ssh
    cp /root/.ssh/authorized_keys /home/deploy/.ssh/authorized_keys
    chown deploy:deploy /home/deploy/.ssh/authorized_keys
    chmod 0600 /home/deploy/.ssh/authorized_keys
fi
install -m 0440 /dev/stdin /etc/sudoers.d/deploy <<'EOF'
deploy ALL=(ALL) NOPASSWD:ALL
EOF

if ! id app >/dev/null 2>&1; then
    useradd -m -s /bin/bash app
fi
grep -q "^app:" /etc/subuid || usermod --add-subuids 100000-165535 app
grep -q "^app:" /etc/subgid || usermod --add-subgids 100000-165535 app
loginctl enable-linger app

# ─── 8. Directories + netavark override (load-bearing per memory) ───────────
log "creating /etc/portfolio, /etc/containers/systemd, app rootless dirs"
install -d -m 0755 -o root -g root /etc/portfolio
install -d -m 0755 -o root -g root /etc/containers/systemd
install -d -m 0755 -o app -g app /home/app/.config/containers
install -d -m 0755 -o app -g app /home/app/.config/containers/systemd

if [[ ! -f /home/app/.config/containers/containers.conf ]]; then
    printf '[network]\nnetwork_backend = "netavark"\n' \
        >/home/app/.config/containers/containers.conf
    chown app:app /home/app/.config/containers/containers.conf
    chmod 0644 /home/app/.config/containers/containers.conf
fi

log "sub-bootstrap complete on $HOSTNAME ($TS_IP)"
log "next: drop Quadlet units in /home/app/.config/containers/systemd, populate /etc/portfolio/*.env"
log "then run harden-ssh.sh once you've verified deploy login from main via Tailscale"
