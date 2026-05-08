# Backups — restic → AWS S3

Weekly Postgres dump, encrypted client-side (AES-256), pushed to a single S3
bucket. Free-tier-friendly: dump + dedup keeps total storage well under 5 GB.

## Files

| File                        | Purpose                                                |
| --------------------------- | ------------------------------------------------------ |
| `pg-dump-and-backup.sh`     | Streams `pg_dump` into `restic backup --stdin`         |
| `restic-backup.service`     | Oneshot systemd unit, calls the script                 |
| `restic-backup.timer`       | Weekly trigger (Sun 03:30 UTC, randomized 0–10 min)    |
| `restore-test.sh`           | Monthly drill — restores newest snapshot, validates    |

## Required secrets on box (NOT in repo)

| Path                       | Owner | Mode | Contents                  |
| -------------------------- | ----- | ---- | ------------------------- |
| `/etc/portfolio/restic.pw` | root  | 0600 | Restic encryption pwd     |
| `/etc/portfolio/aws.key`   | root  | 0600 | AWS_ACCESS_KEY_ID         |
| `/etc/portfolio/aws.secret`| root  | 0600 | AWS_SECRET_ACCESS_KEY     |

## Install (manual; Phase F Ansible role replaces this)

```bash
# As root on main:
sudo install -m 0755 pg-dump-and-backup.sh /usr/local/bin/pg-dump-and-backup.sh
sudo install -m 0755 restore-test.sh        /usr/local/bin/restore-test.sh
sudo install -m 0644 restic-backup.service  /etc/systemd/system/
sudo install -m 0644 restic-backup.timer    /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now restic-backup.timer
```

## First manual run + verify

```bash
# Trigger immediately, watch it complete.
sudo systemctl start restic-backup.service
sudo journalctl -u restic-backup.service --since '5 min ago'

# List snapshots (should show one).
sudo RESTIC_PASSWORD_FILE=/etc/portfolio/restic.pw \
     AWS_ACCESS_KEY_ID="$(sudo cat /etc/portfolio/aws.key)" \
     AWS_SECRET_ACCESS_KEY="$(sudo cat /etc/portfolio/aws.secret)" \
  restic -r "s3:s3.us-east-1.amazonaws.com/amazon-arsham.codes-portfolio-backup-2026/main" snapshots
```

## Restore (break-glass)

```bash
# 1. Pull newest snapshot to /tmp/restore.
sudo restic -r <repo> --password-file /etc/portfolio/restic.pw \
     restore latest --tag weekly --target /tmp/restore

# 2. Apply globals first.
sudo -u app XDG_RUNTIME_DIR=/run/user/1001 \
    podman exec -i postgres psql < /tmp/restore/tmp/*/globals.sql

# 3. Restore portfolio DB (recreate first if needed).
sudo -u app XDG_RUNTIME_DIR=/run/user/1001 \
    podman exec -i postgres pg_restore -d portfolio_local --clean --if-exists \
    < /tmp/restore/portfolio.dump
```

## Retention

`restic forget --keep-weekly 8 --keep-monthly 12 --prune` runs at end of every
backup. Steady state: ~20 snapshots, dedup keeps storage minimal.
