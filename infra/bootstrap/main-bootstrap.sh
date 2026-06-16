#!/usr/bin/env bash
# Phase A bootstrap for the main box (Ubuntu 24.04). Run as root.
#
# Idempotent where practical. Each block can be re-run.
# Phase F replaces this with an Ansible role (`common` + `podman_host` +
# `traefik_edge` + `app_portfolio`); keep this script as the spec.
set -euo pipefail

log() { printf '\n\033[1;36m[bootstrap]\033[0m %s\n' "$*"; }

# ─── 1. System update ───────────────────────────────────────────────────────
log "apt update + upgrade"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y

# ─── 2. Core packages ───────────────────────────────────────────────────────
# podman 4.9 ships in Ubuntu 24.04 noble — has Quadlet support (Quadlet
# stabilised in podman 4.4). Phase F may switch to upstream PPA for podman 5.x
# if a feature gap shows up; 4.9 is enough for current Quadlet units.
# `sops` is NOT in noble repos; installed below from upstream release.
log "installing podman, ufw, unattended-upgrades, restic, age, curl, jq, netavark"
apt-get install -y --no-install-recommends \
    podman podman-compose \
    netavark aardvark-dns \
    uidmap slirp4netns fuse-overlayfs \
    ufw unattended-upgrades \
    restic \
    age \
    curl jq ca-certificates gnupg

# sops binary from upstream GitHub release (mozilla → getsops org).
# Pin and verify checksum so a compromised release tarball can't slip in.
SOPS_VERSION="3.9.4"
if ! command -v sops >/dev/null 2>&1; then
    log "installing sops ${SOPS_VERSION} from github release"
    tmp=$(mktemp)
    curl -fsSL "https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.amd64" -o "$tmp"
    # Fetch the official checksum file alongside the binary so we don't pin a
    # stale hash in the script. Falls back to skipping verification only if
    # the checksum file is unreachable (logged loudly).
    if curl -fsSL "https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.checksums.txt" -o "${tmp}.sums"; then
        expected=$(awk -v f="sops-v${SOPS_VERSION}.linux.amd64" '$2==f {print $1}' "${tmp}.sums")
        actual=$(sha256sum "$tmp" | awk '{print $1}')
        if [[ "$expected" != "$actual" ]]; then
            echo "sops checksum mismatch: expected $expected, got $actual" >&2
            rm -f "$tmp" "${tmp}.sums"
            exit 1
        fi
        rm -f "${tmp}.sums"
    else
        echo "WARNING: sops checksum file unreachable, installing unverified binary" >&2
    fi
    install -m 0755 "$tmp" /usr/local/bin/sops
    rm -f "$tmp"
fi
sops --version

# ─── 3. Tailscale (binary only — `tailscale up` is manual) ──────────────────
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

# ─── 4. Firewall ────────────────────────────────────────────────────────────
log "configuring ufw (22, 80, 443)"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'ssh'
ufw allow 80/tcp comment 'http'
ufw allow 443/tcp comment 'https'
# Phase E will narrow ssh to tailscale0 only.
ufw --force enable
ufw status verbose

# ─── 5. Unattended security upgrades ────────────────────────────────────────
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

# ─── 6. Users (deploy + app) ────────────────────────────────────────────────
log "creating deploy + app users"
if ! id deploy >/dev/null 2>&1; then
    useradd -m -s /bin/bash -G sudo deploy
    install -d -m 0700 -o deploy -g deploy /home/deploy/.ssh
    cp /root/.ssh/authorized_keys /home/deploy/.ssh/authorized_keys
    chown deploy:deploy /home/deploy/.ssh/authorized_keys
    chmod 0600 /home/deploy/.ssh/authorized_keys
fi
# Sudoers (NOPASSWD for deploys; tighten in Phase F).
install -m 0440 /dev/stdin /etc/sudoers.d/deploy <<'EOF'
deploy ALL=(ALL) NOPASSWD:ALL
EOF

if ! id app >/dev/null 2>&1; then
    useradd -m -s /bin/bash app
fi
# Subuid/subgid auto-populated by adduser on Ubuntu 24.04.
grep -q "^app:" /etc/subuid || usermod --add-subuids 100000-165535 app
grep -q "^app:" /etc/subgid || usermod --add-subgids 100000-165535 app

# Lingering = systemd --user persists across logouts (required for rootless
# Quadlets to start at boot).
loginctl enable-linger app

# ─── 7. Directories ─────────────────────────────────────────────────────────
log "creating /etc/portfolio, /etc/traefik/dynamic, /etc/containers/systemd"
install -d -m 0755 -o root -g root /etc/portfolio
install -d -m 0755 -o root -g root /etc/traefik /etc/traefik/dynamic
install -d -m 0755 -o root -g root /etc/containers/systemd
install -d -m 0755 -o app -g app /home/app/.config/containers
install -d -m 0755 -o app -g app /home/app/.config/containers/systemd

# Force netavark backend for the rootless app user. Default on Ubuntu 24.04 with
# podman 4.9 is still CNI, which has no built-in DNS for rootless networks —
# breaks `service: postgres` hostname lookup from the portfolio container.
if [[ ! -f /home/app/.config/containers/containers.conf ]]; then
    printf '[network]\nnetwork_backend = "netavark"\n' \
        >/home/app/.config/containers/containers.conf
    chown app:app /home/app/.config/containers/containers.conf
    chmod 0644 /home/app/.config/containers/containers.conf
fi

# ─── 8. SSH hardening — run separately ──────────────────────────────────────
# Lockout risk is real, so hardening is a SECOND script, not auto-run here.
# After you've confirmed `ssh -i <key> deploy@<ip> 'sudo whoami'` works, run:
#   ssh -i <key> root@<ip> 'bash -s' < infra/bootstrap/harden-ssh.sh
# That drops in /etc/ssh/sshd_config.d/10-harden.conf with:
#   PermitRootLogin no, PasswordAuthentication no, AllowUsers deploy
# Phase E will additionally bind sshd to tailscale0 only.
log "current sshd auth settings (informational)"
grep -E '^\s*(PasswordAuthentication|PermitRootLogin|AllowUsers)\s' /etc/ssh/sshd_config || true
sshd -T 2>/dev/null | grep -E '^(permitrootlogin|passwordauthentication) ' || true

log "bootstrap step 1 complete — next: Quadlet install (incl. portfolio_media.volume) + env files, then harden-ssh.sh"
log "note: portfolio_media named volume is created on first portfolio.service start (no host bind dir needed)"
