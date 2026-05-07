# Traefik — main server (consolidated edge + app)

Since 2026-05 the Server A / Server B split is replaced by a single 4GB main box
running Traefik (rootful Quadlet) plus the portfolio app + Postgres (rootless
Quadlet). Sub-apps live on 2GB sub-boxes joined via Tailscale and are routed
through this Traefik via the file provider.

## Files
- `traefik.yml` — static config: entryPoints, file provider, ACME (DNS-01 via
  Cloudflare). Mounted read-only at `/etc/traefik/traefik.yml` in the container.
- `dynamic/portfolio.yml` — router + service for `arsham.codes` /
  `www.arsham.codes`. Requests one wildcard cert (`*.arsham.codes`) so future
  sub-app routers don't trigger a fresh ACME order.
- `dynamic/<subapp>.yml` — one file per sub-app, dropped at runtime. File
  provider hot-reloads — no Traefik restart.
- `docker-compose.yml` — DEPRECATED, will be deleted post-cutover.

## Container runtime
Authoritative unit: `infra/podman/quadlet/traefik.container` (rootful, host
networking, `MemoryHigh=128M`, `CapDrop=ALL`+`NET_BIND_SERVICE`, read-only FS
with `/tmp` + `/run` tmpfs). The compose file in this dir is reference only.

## Required state on the main box
| Path                                | Owner | Mode | Source of truth |
| ----------------------------------- | ----- | ---- | --------------- |
| `/etc/traefik/traefik.yml`          | root  | 0644 | this `traefik.yml` (Ansible role `traefik_edge` from Phase F) |
| `/etc/traefik/dynamic/portfolio.yml`| root  | 0644 | `dynamic/portfolio.yml`                       |
| `/etc/traefik/dynamic/<sub>.yml`    | root  | 0644 | one file per sub-app                          |
| `/etc/portfolio/traefik.env`        | root  | 0600 | `CLOUDFLARE_DNS_API_TOKEN=…` (NOT in repo)    |
| `letsencrypt` named volume          | root  | 0700 | `acme.json` cert storage                      |

## Phase A deploy (manual — pre-Ansible)

### 1. DNS (Cloudflare)
Point apex + www at the new main IP:
```
arsham.codes      A   <new-main-ip>
www.arsham.codes  A   <new-main-ip>
```
For staging/cutover, use a temporary subdomain that doesn't displace the live
site:
```
staging.arsham.codes  A  <new-main-ip>
```

### 2. Cloudflare API token
Cloudflare → Profile → API Tokens → Create Token → "Edit zone DNS" template →
Zone Resources: Specific zone → `arsham.codes`. Paste into
`/etc/portfolio/traefik.env`:
```
CLOUDFLARE_DNS_API_TOKEN=<token>
```
File mode: `chmod 600 /etc/portfolio/traefik.env && chown root:root <file>`.

### 3. Install Traefik static + dynamic config
```bash
sudo mkdir -p /etc/traefik/dynamic /etc/portfolio
sudo install -m 0644 traefik.yml /etc/traefik/traefik.yml
sudo install -m 0644 dynamic/portfolio.yml /etc/traefik/dynamic/portfolio.yml
```

### 4. Start Traefik via Quadlet
See `infra/podman/quadlet/README.md` for the full sequence; relevant lines:
```bash
sudo install -m 0644 ../podman/quadlet/traefik.container \
                     ../podman/quadlet/letsencrypt.volume \
                     /etc/containers/systemd/
sudo systemctl daemon-reload
sudo systemctl start traefik.service
journalctl -u traefik -f
```

### 5. Verify backend reachability
On the main box, after the rootless app stack is up:
```bash
curl -fsS http://127.0.0.1:8000/healthz/    # → {"status":"ok"}
```

### 6. Verify staging cert
`traefik.yml` defaults to LE staging CA during cutover (untrusted, but proves
DNS-01 works without burning prod rate limits):
```bash
curl -kI https://staging.arsham.codes/      # expect 200, cert from "(STAGING) Pretend Pear X1"
```

### 7. Flip to production CA
Once step 6 is green, comment out the `caServer:` line in `traefik.yml`,
delete the staging cert from the `letsencrypt` volume, and restart Traefik:
```bash
sudo podman volume inspect letsencrypt        # locate the mountpoint
sudo rm /var/lib/containers/storage/volumes/letsencrypt/_data/acme.json
sudo systemctl restart traefik
curl -I https://arsham.codes/                  # expect 200, valid Let's Encrypt cert
```

### 8. Cutover
After 24h of green traffic on `staging.arsham.codes`, swap apex + www DNS at
Cloudflare to the new main IP. The wildcard cert covers them already.

## Adding sub-apps (Phase B onward)
Drop a new file in `dynamic/`:
```yaml
# dynamic/subapp1.yml
http:
  routers:
    subapp1:
      rule: "Host(`app1.arsham.codes`)"
      entryPoints: [websecure]
      service: subapp1
      tls:
        certResolver: letsencrypt
  services:
    subapp1:
      loadBalancer:
        servers:
          - url: "http://subapp1.tailnet:8000"   # Tailscale MagicDNS hostname
        healthCheck:
          path: /healthz/
          interval: 30s
```
Cloudflare CNAME: `app1.arsham.codes → arsham.codes`. Wildcard cert covers it
(no new ACME order). Traefik picks up the file inside ~1s — no restart.

## Adding apps later
Each app gets its own file in `dynamic/`. No Traefik restart needed.
