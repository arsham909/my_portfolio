# GitHub Actions

Two workflows live here:

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `ci.yml` | push, PR | Installs Python deps, runs `ruff check` (warn-only for now), runs `python manage.py check`. |
| `build-and-deploy.yml` | push to `main`, manual `workflow_dispatch` | Builds `portfolio/Dockerfile.prod`, pushes to GHCR (`ghcr.io/<owner>/my_portfolio:latest` + `sha-<7chars>`), SSHes to the main box as `deploy`, pulls the new image, retags it as `:latest`, restarts the rootless `portfolio` Quadlet under the `app` user, and smoke-tests `https://arsham.codes/healthz/`. |

## Required repo secrets

Set under **Repository → Settings → Secrets and variables → Actions → New repository secret**.

| Secret | Source |
| --- | --- |
| `DEPLOY_SSH_KEY` | Private half of an `ed25519` keypair whose public half is in `/home/deploy/.ssh/authorized_keys` on the main box. The bootstrap script + harden-ssh.sh expect SSH key auth only. |

The workflow uses the built-in `GITHUB_TOKEN` for GHCR auth — no separate
`GHCR_PAT` required.

## One-time manual setup

1. **Make the GHCR package public** (otherwise the box can't `podman pull`
   without credentials). After the first successful `build` job:
   - GitHub → your profile → **Packages** → `my_portfolio`.
   - **Package settings** → **Change visibility** → **Public** → confirm.
   - Re-run the failed deploy job, OR push a trivial commit to retrigger.
2. **Verify the deploy SSH key works** before pushing the first deploy:
   ```bash
   ssh -i <local-private-key> -p 22 deploy@134.209.208.211 'whoami; sudo -iu app whoami'
   # → deploy
   # → app
   ```

## Rollback

`build-and-deploy.yml` tags every image with `sha-<git-shortsha>`. To pin a
prior version manually:

```bash
ssh -i ~/.ssh/portfolio deploy@134.209.208.211 \
  "sudo -iu app bash -c 'podman pull ghcr.io/arsham909/my_portfolio:sha-XXXXXXX && \
   podman tag ghcr.io/arsham909/my_portfolio:sha-XXXXXXX ghcr.io/arsham909/my_portfolio:latest && \
   systemctl --user restart portfolio'"
```

A first-class rollback workflow can be added in a future iteration (would
take a `tag` input and run the deploy steps from `build-and-deploy.yml`).

## Future hardening

- Move SSH from main's public IP to the **tailscale0** interface and have the
  workflow connect via a Tailscale OAuth ephemeral key
  (`tailscale/github-action`). This narrows main's `:22` exposure.
  
- Pin Quadlet `Image=` to a digest and rewrite the unit on the box per
  deploy, rather than relying on retagging `:latest`.
- Add `pytest` job once tests exist.
