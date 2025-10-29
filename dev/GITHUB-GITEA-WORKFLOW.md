# GitHub → Gitea Workflow Guide

**Strategy:** Use GitHub as primary (industry standard), automatically mirror to Gitea for self-hosted CI/CD.

## Overview

```
You → Push to GitHub → GitHub webhook → Gitea (instant sync) → Gitea Actions (act_runner)
                ↓
            Industry standard,
            familiar workflow
```

**Benefits:**
- ✅ Keep using GitHub (industry standard, familiar)
- ✅ Self-hosted CI/CD with Gitea Actions (no minute limits)
- ✅ One runner for ALL repos (no organization needed)
- ✅ Access to homelab services in CI/CD
- ✅ Gitea container registry for custom images
- ✅ Automatic sync (real-time, no manual work)

---

## Setup: Mirror GitHub Repo → Gitea

### Option 1: Using Gitea's Pull Mirror (Simpler)

**Best for:** Quick setup, don't mind periodic sync (updates every 8 hours by default)

1. **In Gitea UI** (http://10.10.10.114:3001 or https://git.onurx.com):
   - Click "+" → "New Migration"
   - Select "GitHub"
   - Enter GitHub repo URL: `https://github.com/username/repo`
   - Check "This repository will be a mirror"
   - Enter GitHub credentials or token
   - Click "Migrate Repository"

2. **Gitea will automatically:**
   - Clone the repo
   - Sync every 8 hours
   - Pull new commits, branches, tags

**Limitation:** Not real-time (8-hour sync interval)

---

### Option 2: Using GitHub Push Mirror (Real-time, Recommended)

**Best for:** Instant sync, CI/CD triggers immediately on push

#### Step 1: Create Repo in Gitea

1. Go to Gitea: http://10.10.10.114:3001
2. Click "+" → "New Repository"
3. Repository name: Same as GitHub repo name
4. Make it private if needed
5. Click "Create Repository"

#### Step 2: Get Gitea Access Token

1. In Gitea: User icon → Settings → Applications
2. Generate New Token:
   - Token name: `github-push-mirror`
   - Scopes: Check "write:repository"
3. Copy the token (save it securely)

#### Step 3: Add Gitea as Remote in GitHub Repo

On your local machine:

```bash
# Clone your GitHub repo (if not already)
git clone https://github.com/username/repo.git
cd repo

# Add Gitea as a remote
git remote add gitea https://<username>:<token>@git.onurx.com/username/repo.git

# Or if using IP:
git remote add gitea https://<username>:<token>@10.10.10.114:3001/username/repo.git

# Push to both remotes
git push origin main
git push gitea main
```

#### Step 4: Automate with GitHub Actions (Best Method)

Create `.github/workflows/mirror-to-gitea.yml` in your GitHub repo:

```yaml
name: Mirror to Gitea

on:
  push:
    branches:
      - '**'  # All branches
  delete:
    branches:
      - '**'

jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - name: Mirror to Gitea
        uses: pixta-dev/repository-mirroring-action@v1
        with:
          target_repo_url: https://git.onurx.com/username/repo.git
          ssh_private_key: ${{ secrets.GITEA_SSH_KEY }}
```

**Or simpler version using HTTPS:**

```yaml
name: Mirror to Gitea

on: [push, delete]

jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for proper mirroring

      - name: Push to Gitea
        run: |
          git remote add gitea https://${{ secrets.GITEA_USERNAME }}:${{ secrets.GITEA_TOKEN }}@git.onurx.com/${{ github.repository }}.git
          git push gitea --all --force
          git push gitea --tags --force
```

**Add secrets to GitHub:**
- Go to GitHub repo → Settings → Secrets and variables → Actions
- Add:
  - `GITEA_USERNAME`: Your Gitea username
  - `GITEA_TOKEN`: Token from Step 2

---

## Using Gitea Actions (CI/CD)

### Enable Gitea Actions

Gitea Actions should already be enabled. Verify:
1. Go to Gitea → Site Administration → Configuration
2. Search for "Actions"
3. Verify `ENABLED = true`

### Create Workflow

In your repo, create `.gitea/workflows/build.yml`:

```yaml
name: Build and Test

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm install

      - name: Run tests
        run: npm test

      - name: Build
        run: npm run build
```

**Notes:**
- Gitea Actions uses same syntax as GitHub Actions
- Most GitHub Actions work in Gitea Actions
- Your `act_runner` executes these workflows

### Check Workflow Status

1. Go to Gitea repo → Actions tab
2. See running/completed workflows
3. Click on workflow to see logs

---

## Using Gitea Container Registry

Gitea includes a built-in container registry (like Docker Hub).

### Push Image to Gitea Registry

```bash
# Login to Gitea registry
docker login git.onurx.com -u <username> -p <token>

# Or using IP:
docker login 10.10.10.114:3001 -u <username> -p <token>

# Tag your image
docker tag myapp:latest git.onurx.com/username/myapp:latest

# Push to Gitea registry
docker push git.onurx.com/username/myapp:latest
```

### Pull Image from Gitea Registry

```bash
# From any VM in homelab
docker pull git.onurx.com/username/myapp:latest
```

### Build and Push in Gitea Actions

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [main]

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to Gitea Container Registry
        run: echo "${{ secrets.GITEA_TOKEN }}" | docker login git.onurx.com -u ${{ gitea.actor }} --password-stdin

      - name: Build and push
        run: |
          docker build -t git.onurx.com/${{ gitea.repository }}:${{ gitea.sha }} .
          docker build -t git.onurx.com/${{ gitea.repository }}:latest .
          docker push git.onurx.com/${{ gitea.repository }}:${{ gitea.sha }}
          docker push git.onurx.com/${{ gitea.repository }}:latest
```

### View Images in Gitea

1. Go to Gitea repo → Packages
2. See all published container images
3. Click to see tags and details

---

## Access Homelab Services from Gitea Actions

Since `act_runner` runs on your dev VM, workflows can access all homelab services:

```yaml
jobs:
  integration-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Test with PostgreSQL
        env:
          DATABASE_URL: postgresql://user:pass@10.10.10.111:5432/testdb
        run: npm run integration-test

      - name: Test with Redis
        env:
          REDIS_URL: redis://10.10.10.111:6379/0
        run: npm run cache-test
```

**Available services:**
- PostgreSQL: `10.10.10.111:5432`
- MongoDB: `10.10.10.111:27017`
- Redis: `10.10.10.111:6379`
- MinIO: `10.10.10.111:9000`
- MQTT: `10.10.10.111:1883`

---

## Workflow Examples

### Node.js App with Tests

```yaml
name: Node.js CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm test
      - run: npm run build
```

### Deploy to Dokploy After Build

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: |
          docker build -t git.onurx.com/${{ gitea.repository }}:latest .
          echo "${{ secrets.GITEA_TOKEN }}" | docker login git.onurx.com -u ${{ gitea.actor }} --password-stdin
          docker push git.onurx.com/${{ gitea.repository }}:latest

      - name: Trigger Dokploy deployment
        run: |
          curl -X POST https://deploy.onurx.com/api/deploy \
            -H "Authorization: Bearer ${{ secrets.DOKPLOY_TOKEN }}" \
            -d '{"project": "myapp"}'
```

---

## Troubleshooting

### Mirror not updating

**Check GitHub Action logs:**
- GitHub repo → Actions tab → Mirror workflow

**Check Gitea webhook:**
- If using webhooks: GitHub repo → Settings → Webhooks
- Check delivery status

### act_runner not running workflows

```bash
# SSH to dev VM
docker compose logs -f act-runner

# Check if runner is registered
# Gitea → Site Admin → Actions → Runners
# Should see "homelab-runner" with green status
```

### Container registry authentication failed

```bash
# Generate new token in Gitea
# User icon → Settings → Applications → Generate New Token
# Scope: write:package

# Login with new token
docker login git.onurx.com -u <username> -p <new-token>
```

### Workflows can't access homelab services

Check network - `act_runner` should be on `dev_net` bridge which can reach other VMs:

```bash
# SSH to dev VM
docker exec -it act-runner ping 10.10.10.111
```

---

## Summary: Your Workflow

1. **Develop on GitHub** (normal workflow, nothing changes)
2. **Push to GitHub** (git push origin main)
3. **GitHub auto-mirrors to Gitea** (via GitHub Action or webhook)
4. **Gitea Actions runs** (your self-hosted runner executes workflows)
5. **Build/test/deploy** (with access to homelab services)
6. **Push images to Gitea registry** (if needed)

**Result:** Best of both worlds - GitHub's ecosystem + self-hosted CI/CD!
