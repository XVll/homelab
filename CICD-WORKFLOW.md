# CI/CD Workflow Documentation

**Platform:** GitHub Actions → GitHub Container Registry → Dokploy

**Applies to:** All homelab applications (10 apps)

---

## Architecture Diagram

```
┌─────────────┐
│   Developer │
└──────┬──────┘
       │ git push
       ▼
┌─────────────────────────────────────────────┐
│            GitHub Repository                │
│  ┌──────────────────────────────────────┐  │
│  │     .github/workflows/build.yaml     │  │
│  └──────────────────────────────────────┘  │
└──────┬──────────────────────────────────────┘
       │ Triggers on push
       ▼
┌─────────────────────────────────────────────┐
│         GitHub Actions Runner               │
│  ┌────────────────────────────────────┐    │
│  │  1. Run Tests (bun test)           │    │
│  │  2. Run Linting (bun lint)         │    │
│  │  3. Type Check (tsc --noEmit)      │    │
│  └────────────────────────────────────┘    │
│            │ If all pass                    │
│            ▼                                │
│  ┌────────────────────────────────────┐    │
│  │  4. Build Docker Image             │    │
│  │  5. Push to ghcr.io                │    │
│  └────────────────────────────────────┘    │
│            │ If build succeeds              │
│            ▼                                │
│  ┌────────────────────────────────────┐    │
│  │  6. Trigger Dokploy Webhook        │    │
│  └────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│   GitHub Container Registry (ghcr.io)       │
│   Image: ghcr.io/xvill/<app>:latest        │
└──────┬──────────────────────────────────────┘
       │ Webhook triggers
       ▼
┌─────────────────────────────────────────────┐
│    Dokploy (deploy.onurx.com)              │
│  ┌────────────────────────────────────┐    │
│  │  1. Pull image from ghcr.io        │    │
│  │  2. Deploy container                │    │
│  │  3. Health check                    │    │
│  └────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│        Production (Running App)             │
└─────────────────────────────────────────────┘
```

---

## Workflow Steps

### 1. Developer Push
```bash
git add .
git commit -m "Feature: add new functionality"
git push origin main
```

### 2. GitHub Actions (Automated)
**Trigger:** Push to `main` branch

**Quality Gates:**
- ✅ Tests must pass
- ✅ Linting must pass
- ✅ Type checking must pass
- ❌ If any fail → **STOP** (no build, no deploy)

**Build:**
- Only runs if all quality gates pass
- Builds Docker image using Dockerfile
- Tags: `latest`, `main`, `main-<commit-sha>`

**Publish:**
- Pushes image to `ghcr.io/xvill/<app-name>:latest`
- Uses `GITHUB_TOKEN` (automatic, no secrets needed)

**Deploy Trigger:**
- Calls Dokploy webhook
- Uses `DOKPLOY_WEBHOOK_URL` secret

**Duration:** ~2-3 minutes total

### 3. Dokploy Deployment (Automated)
**Trigger:** Webhook from GitHub Actions

**Process:**
- Authenticates to ghcr.io
- Pulls latest image
- Stops old container
- Starts new container
- Runs health checks

**Duration:** ~30 seconds

### 4. Production
- Application running with new code
- Accessible via configured domain

---

## Repository Structure

```
app-name/
├── .github/
│   └── workflows/
│       └── build-deploy.yaml    # CI/CD pipeline
├── src/                         # Application code
├── Dockerfile                   # Container build instructions
├── package.json                 # Dependencies + scripts
├── tsconfig.json               # TypeScript config
└── DEPLOYMENT.md               # Setup documentation
```

---

## Required Configuration

### GitHub Repository Secrets
| Secret | Value | Purpose |
|--------|-------|---------|
| `DOKPLOY_WEBHOOK_URL` | `https://deploy.onurx.com/api/...` | Auto-trigger deployment |

*Note: `GITHUB_TOKEN` is automatically provided*

### Dokploy Application Settings
| Setting | Value |
|---------|-------|
| **Type** | Docker Image |
| **Image** | `ghcr.io/xvill/<app-name>:main` |
| **Registry** | `ghcr.io` |
| **Username** | `xvill` |
| **Password** | GitHub PAT with `read:packages` |

---

## Quality Gates

### Tests Block Deployment
```yaml
- run: bun test
  # If tests fail → workflow stops → no build → no deploy
```

### Lint Enforces Code Quality
```yaml
- run: bun lint
  # If linting fails → workflow stops
```

### Type Safety Required
```yaml
- run: bun run type-check
  # If TypeScript errors → workflow stops
```

**Result:** Only quality code reaches production ✅

---

## Rollback Strategy

### Quick Rollback (Instant)
```bash
# In Dokploy: Change image tag to previous version
ghcr.io/xvill/app:main-abc1234  # Previous working commit
```

### Full Rollback (Via Git)
```bash
git revert <bad-commit>
git push origin main
# Triggers full pipeline with reverted code
```

---

## Monitoring

### GitHub Actions
- **URL:** `https://github.com/xvill/<app>/actions`
- **Check:** Build status, test results, logs

### GitHub Container Registry
- **URL:** `https://github.com/xvill?tab=packages`
- **Check:** Published images, storage usage

### Dokploy
- **URL:** `https://deploy.onurx.com`
- **Check:** Deployment status, application logs, health

---

## Cost & Limits

### GitHub Pro ($4/month)
- **Actions Minutes:** 3,000/month
- **Storage:** 2 GB (container registry)
- **Bandwidth:** 10 GB/month

### Usage Optimization
**Strategy:** Keep only `latest` and last 2 commits
- Delete old image versions monthly
- Each app ~200-300 MB → 10 apps = ~2-3 GB (within limit)

**Estimated Minutes:**
- Per build: ~3-5 minutes
- 10 apps × 2 deployments/day = ~600-1000 min/month
- **Well within 3,000 limit** ✅

---

## Failure Scenarios

| Scenario | What Happens | Action |
|----------|--------------|--------|
| Tests fail | Workflow stops, no build | Fix tests, push again |
| Build fails | No image pushed, no deploy | Fix Dockerfile, push again |
| Image push fails | Deployment doesn't trigger | Check GitHub Container Registry permissions |
| Webhook fails | Image pushed but not deployed | Manually redeploy in Dokploy |
| Deployment fails | Old version keeps running | Check Dokploy logs, fix issue |

---

## Best Practices

✅ **Always run tests locally** before pushing
```bash
bun test && bun lint && git push
```

✅ **Use meaningful commit messages**
```bash
git commit -m "fix: resolve MQTT connection timeout"
```

✅ **Check Actions tab** after pushing
- Ensure workflow completes successfully
- Review any warnings or errors

✅ **Monitor first deployment** of each app
- Check Dokploy logs
- Verify application starts correctly
- Test critical functionality

✅ **Keep images clean**
- Delete old versions monthly
- Keep only: `latest`, `main`, last 2 SHA tags

---

## Adding New Application

1. **Create repository** with Dockerfile
2. **Add workflow:** Copy `.github/workflows/build-deploy.yaml`
3. **Configure secrets:** Add `DOKPLOY_WEBHOOK_URL`
4. **Create Dokploy app:**
   - Type: Docker Image
   - Image: `ghcr.io/xvill/<app-name>:main`
   - Add environment variables
5. **Push code** → Pipeline runs automatically

**Template repository available:** Use `ha-ws` as reference

---

## Support & Troubleshooting

**Workflow issues:** Check GitHub Actions logs
**Registry issues:** Verify at github.com/xvill?tab=packages
**Deployment issues:** Check Dokploy application logs

**Common fixes:**
- Re-run failed GitHub Action
- Manually redeploy in Dokploy
- Check environment variables in Dokploy
- Verify network connectivity to dependencies
