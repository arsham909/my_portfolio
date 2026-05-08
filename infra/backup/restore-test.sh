#!/usr/bin/env bash
# Monthly restore drill. Restores newest snapshot to throwaway path,
# parses dump header, deletes. "Untested backups are not backups."
set -euo pipefail

export RESTIC_PASSWORD_FILE=/etc/portfolio/restic.pw
export RESTIC_REPOSITORY="s3:s3.us-east-1.amazonaws.com/amazon-arsham.codes-portfolio-backup-2026/main"
export AWS_ACCESS_KEY_ID="$(cat /etc/portfolio/aws.key)"
export AWS_SECRET_ACCESS_KEY="$(cat /etc/portfolio/aws.secret)"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

# Two separate snapshots (dump + globals); --path filter picks the right one.
restic restore latest --tag weekly --path /portfolio.dump --target "$WORKDIR"
restic restore latest --tag weekly --path /globals.sql   --target "$WORKDIR"

DUMP="$WORKDIR/portfolio.dump"
GLOBALS="$WORKDIR/globals.sql"

[ -s "$DUMP" ] || { echo "FAIL: portfolio.dump missing/empty"; exit 1; }
[ -s "$GLOBALS" ] || { echo "FAIL: globals.sql missing/empty"; exit 1; }

# Custom-format dump — pg_restore --list parses without writing.
# Use the postgres container's pg_restore so host needs no postgresql-client package.
sudo -u app XDG_RUNTIME_DIR=/run/user/1001 \
    podman exec -i -u postgres postgres pg_restore --list < "$DUMP" >/dev/null

echo "OK: snapshot restorable, $(stat -c%s "$DUMP") bytes (dump), $(stat -c%s "$GLOBALS") bytes (globals)."
