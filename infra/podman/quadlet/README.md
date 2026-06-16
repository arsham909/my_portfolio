# Podman Quadlet units — main server

Quadlet generates systemd units from these `.container`/`.network`/`.volume` files. Podman 5.x ships with `/usr/lib/systemd/system-generators/podman-system-generator` which reads these locations on `daemon-reload`.

## Install paths

| Scope    | Path                                          | Used by                                |
| -------- | --------------------------------------------- | -------------------------------------- |
| Rootful  | `/etc/containers/systemd/`                    | `traefik.container`, `letsencrypt.volume` |
| Rootless | `~/.config/containers/systemd/` (user `app`)  | `portfolio.container`, `postgres.container`, `portfolio.network`, `pg_data.volume`, `portfolio_media.volume` |

Rationale: Traefik must bind privileged ports `:80/:443` and uses `Network=host` — runs rootful with `CapDrop=ALL` + `AddCapability=NET_BIND_SERVICE`. App + database run rootless under a dedicated `app` user — extra namespace isolation, no daemon.

## First install (Phase A, manual)

Until Ansible role `app_portfolio` exists (Phase F), copy by hand:

```bash
# As root on main:
sudo install -m 0644 traefik.container letsencrypt.volume /etc/containers/systemd/
sudo systemctl daemon-reload
sudo systemctl start traefik.service

# As user `app`:
sudo loginctl enable-linger app
sudo -iu app
mkdir -p ~/.config/containers/systemd
install -m 0644 portfolio.container postgres.container portfolio.network pg_data.volume portfolio_media.volume \
    ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user start postgres.service
systemctl --user start portfolio_media-volume.service
systemctl --user start portfolio.service
```

## Required env files (NOT in repo — created on the server)

| File                            | Owner   | Mode | Contents                                                  |
| ------------------------------- | ------- | ---- | --------------------------------------------------------- |
| `/etc/portfolio/traefik.env`    | root    | 0600 | `CLOUDFLARE_DNS_API_TOKEN=…`                              |
| `/etc/portfolio/db.env`         | app:app | 0600 | `POSTGRES_DB=…`, `POSTGRES_USER=…`, `POSTGRES_PASSWORD=…` |
| `/etc/portfolio/portfolio.env`  | app:app | 0600 | All vars from `.env.prod.example`                         |

`/etc/portfolio/` exists as `0755 root:root`; subfiles use the modes above. Phase F replaces manual creation with SOPS-decrypted Ansible templates.

## Media persistence

Django `MEDIA_ROOT` is `/home/app/web/mediafiles` inside the container. The `portfolio_media` named volume (same pattern as `pg_data`) stores admin uploads across container restarts and image pulls. Data lives under the rootless `app` user's Podman storage — not in the container writable layer.

After changing `portfolio.container` or `portfolio_media.volume` on a running box:

```bash
install -m 0644 portfolio.container portfolio_media.volume ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user start portfolio_media-volume.service
systemctl --user restart portfolio
podman volume inspect portfolio_media
podman inspect portfolio --format '{{json .Mounts}}' | jq .
```

## Verify

```bash
sudo systemctl status traefik
systemctl --user --machine=app@ status portfolio postgres portfolio_media-volume
podman ps --format '{{.Names}} {{.Status}}'
podman volume ls    # expect portfolio_media + pg_data
curl -fsS http://127.0.0.1:8000/healthz/    # → {"status":"ok"}
curl -I https://arsham.codes/                # → 200, valid LE cert
```

## Image pinning

Tags above (`:v3.1`, `:15-alpine`, `:latest`) are starter values. Phase F switches to immutable digest pins (`@sha256:…`) and wires Renovate to bump them via PRs. Don't run `:latest` in steady state.
