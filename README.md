# my_portfolio — Django portfolio + blog

[![main](https://github.com/arsham909/my_portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/arsham909/my_portfolio/actions)

Live at **<https://arsham.codes/>**.

A Django 5.2 site with a personal landing page, project showcase, and a
markdown-driven blog. Production runs on a single 4 GB DigitalOcean droplet
behind Traefik, with Postgres and the Django app as rootless Podman Quadlets.

> Looking for the previous (nginx-based) version of this project? It is
> archived on the `archive-v1` tag in this repo.

## Stack

| Layer | Choice |
| --- | --- |
| Web framework | Django 5.2.8 |
| WSGI | Gunicorn |
| Static files | Whitenoise |
| Database | Postgres 15 |
| Tagging | django-taggit |
| Image uploads | Pillow |
| Reverse proxy | Traefik v3.1 (DNS-01 wildcard via Cloudflare) |
| Container runtime (prod) | Podman + Quadlet (rootless app, rootful edge) |
| Mesh / cross-host SSH | Tailscale |
| TLS | Let's Encrypt — single wildcard cert covers `arsham.codes` + `*.arsham.codes` |

## Repository layout

```
.
├── portfolio/                    # Django project root
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile.dev / .prod    # Local dev + prod images
│   ├── entrypoint.dev.sh / .prod.sh
│   ├── portfolio/                # Project package
│   │   ├── settings/             # base.py + local.py + prod.py
│   │   ├── urls.py, wsgi.py, asgi.py
│   ├── blog/                     # Blog app (posts, tags, RSS, sitemap)
│   ├── homepage/                 # Landing + project showcase
│   ├── templates/                # Shared base templates
│   └── static/                   # User-authored CSS/img + admin static
├── infra/
│   ├── traefik/                  # Static + dynamic router config (see infra/traefik/README.md)
│   ├── podman/quadlet/           # systemd Quadlet units (see infra/podman/quadlet/README.md)
│   └── bootstrap/                # Idempotent shell setup for new boxes
├── docker-compose.local.yaml     # Local dev with Postgres
├── docker-compose.prod.yml       # DEPRECATED — Podman Quadlets are the prod source-of-truth
├── .env.example / .env_db.example / .env.prod.example
└── README.md
```

## Local development

Requires Docker (or Podman) + a working `docker compose` / `podman compose`.

```bash
# 1. Copy env templates and fill in dev-friendly values
cp .env.example       .env
cp .env_db.example    .env_db
# (no real secrets needed for local — defaults in settings/base.py work)

# 2. Bring up Postgres + the dev image
docker compose -f docker-compose.local.yaml up --build

# 3. App is on http://localhost:8000
# Admin at http://localhost:8000/admin/  (create a superuser first):
docker compose -f docker-compose.local.yaml exec web python manage.py createsuperuser
```

The dev image mounts `portfolio/` as a volume and runs `runserver`, so code
edits hot-reload. Migrations run automatically via `entrypoint.dev.sh`.

### Without Docker

```bash
cd portfolio
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=portfolio.settings.local
# Provide a Postgres or override DATABASES to sqlite locally
python manage.py migrate
python manage.py runserver
```

## Production deployment (high level)

The production environment is described in detail across three sub-READMEs:

- **`infra/bootstrap/`** — `main-bootstrap.sh` provisions a clean Ubuntu 24.04
  droplet (Podman, netavark, Tailscale, UFW, unattended-upgrades, deploy + app
  users, lingering for rootless systemd). `harden-ssh.sh` drops root SSH after
  the deploy account is verified.
- **`infra/traefik/README.md`** — Traefik v3.1 edge with a Cloudflare DNS-01
  wildcard cert. File provider hot-reloads dynamic routes without a restart.
- **`infra/podman/quadlet/README.md`** — Quadlet units for `traefik`
  (rootful), `portfolio`, and `postgres` (both rootless under the `app` user).

Production secrets live in `/etc/portfolio/{traefik,db,portfolio}.env` (mode
0600, root-owned). They are **never** committed to git; the
`.env*.example` files in this repo are placeholders only.

## CI / CD

GitHub Actions (`.github/workflows/`) runs on every push:

- `ci.yml` — lint + Django tests on the dev image.
- `build-and-push.yml` — builds `Dockerfile.prod`, pushes to GHCR with a
  digest tag (`ghcr.io/arsham909/my_portfolio:sha-<digest>`).
- `deploy.yml` — joins the tailnet via an OAuth ephemeral key, SSHs to the
  main box as `deploy`, and rolls the `portfolio` Quadlet to the new image
  digest. Smoke-tests `/healthz/` and rolls back on failure.

See `.github/workflows/README.md` for required secrets.

## Health check

The Django app exposes `GET /healthz/` returning `{"status": "ok"}`. Both the
Quadlet HealthCmd and Traefik's loadbalancer use this endpoint.

## Environment variables

| Var | Where | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | prod env | Django session/CSRF signing |
| `DEBUG` | prod env | `False` in prod |
| `ALLOWED_HOSTS` | prod env | Comma-separated hostnames Django will serve |
| `CSRF_TRUSTED_ORIGINS` | prod env | Comma-separated `https://…` origins |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | both | DB credentials |
| `SQL_HOST`, `SQL_PORT` | both | Default `db` / `5432` |
| `GUNICORN_WORKERS` | prod env | Default `4`; tune to droplet RAM |

## License

MIT — see `LICENSE`.
