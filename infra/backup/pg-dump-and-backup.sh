#!/usr/bin/env bash
# Weekly Postgres backup → restic → S3.
# Run as root (needs to read /etc/portfolio/* secrets and exec into rootless app's podman).
set -euo pipefail

# Avoid "cannot chdir" warnings when invoked from a dir app cannot read (e.g. /home/deploy).
cd /tmp

# --- env -------------------------------------------------------------------
export RESTIC_PASSWORD_FILE=/etc/portfolio/restic.pw
export RESTIC_REPOSITORY="s3:s3.us-east-1.amazonaws.com/amazon-arsham.codes-portfolio-backup-2026/main"
export AWS_ACCESS_KEY_ID="$(cat /etc/portfolio/aws.key)"
export AWS_SECRET_ACCESS_KEY="$(cat /etc/portfolio/aws.secret)"

# Pull DB creds from the same env file portfolio uses.
set -a
. /etc/portfolio/db.env
set +a

# --- dump ------------------------------------------------------------------
# Both dumps streamed via --stdin so paths are stable (/portfolio.dump, /globals.sql).
# Stable paths let restore-test.sh use `restic restore latest --path` filter cleanly.

# Per-DB custom-format dump.
sudo -u app XDG_RUNTIME_DIR=/run/user/1001 \
    podman exec -u postgres postgres pg_dump -Fc -d "$POSTGRES_DB" -U "$POSTGRES_USER" \
  | restic backup --stdin --stdin-filename portfolio.dump --tag weekly --host main

# Globals (roles, tablespaces) — pg_dump custom format does not include these.
sudo -u app XDG_RUNTIME_DIR=/run/user/1001 \
    podman exec -u postgres postgres pg_dumpall --globals-only -U "$POSTGRES_USER" \
  | restic backup --stdin --stdin-filename globals.sql --tag weekly --host main

# --- retention -------------------------------------------------------------
restic forget --keep-weekly 8 --keep-monthly 12 --prune
