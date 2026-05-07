#!/usr/bin/env bash
# SSH hardening — run AFTER you've verified `ssh -i ~/.ssh/portfolio deploy@<ip>` works.
# Disables root login + password auth; keeps key auth. Public :22 stays open until
# Phase E binds sshd to tailscale0.
#
# Run as root on the target box:
#   ssh -i ~/.ssh/portfolio root@<ip> 'bash -s' < harden-ssh.sh
#
# Idempotent. Re-run safe.
set -euo pipefail

log() { printf '\n\033[1;36m[harden]\033[0m %s\n' "$*"; }

# ─── 1. Pre-flight: deploy user must exist + have authorized_keys ───────────
if ! id deploy >/dev/null 2>&1; then
    echo "ERROR: deploy user missing — run main-bootstrap.sh first" >&2
    exit 1
fi
if [[ ! -s /home/deploy/.ssh/authorized_keys ]]; then
    echo "ERROR: /home/deploy/.ssh/authorized_keys empty — copy your SSH key first" >&2
    exit 1
fi

# ─── 2. Confirm sudo NOPASSWD wired ─────────────────────────────────────────
if ! sudo -u deploy sudo -n true 2>/dev/null; then
    echo "ERROR: deploy user can't sudo NOPASSWD — check /etc/sudoers.d/deploy" >&2
    exit 1
fi
log "deploy user OK (keys present, sudo NOPASSWD works)"

# ─── 3. Backup sshd_config ──────────────────────────────────────────────────
ts=$(date +%Y%m%d-%H%M%S)
cp -a /etc/ssh/sshd_config "/etc/ssh/sshd_config.bak.${ts}"
log "backup at /etc/ssh/sshd_config.bak.${ts}"

# ─── 4. Apply hardening via drop-in ─────────────────────────────────────────
# Drop-ins win over main file. Cleaner than sed-editing sshd_config.
install -d -m 0755 /etc/ssh/sshd_config.d
cat >/etc/ssh/sshd_config.d/10-harden.conf <<'EOF'
# Managed by infra/bootstrap/harden-ssh.sh
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
ChallengeResponseAuthentication no
PubkeyAuthentication yes
PermitEmptyPasswords no
X11Forwarding no
MaxAuthTries 3
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
AllowUsers deploy
EOF

# ─── 5. Validate before restart ─────────────────────────────────────────────
if ! sshd -t; then
    echo "ERROR: sshd -t failed; reverting drop-in" >&2
    rm -f /etc/ssh/sshd_config.d/10-harden.conf
    exit 1
fi
log "sshd config valid"

# ─── 6. Restart sshd ────────────────────────────────────────────────────────
systemctl restart ssh
log "sshd restarted — root login DISABLED"

# ─── 7. Final state ─────────────────────────────────────────────────────────
sshd -T 2>/dev/null | grep -E '^(permitrootlogin|passwordauthentication|allowusers) ' || true
log "done. Test from a SECOND terminal: ssh -i ~/.ssh/portfolio deploy@<ip> 'sudo whoami'"
log "do NOT close this root session until you've confirmed deploy login works"
