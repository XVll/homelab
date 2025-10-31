# Media Stack Setup Guide

Complete setup instructions for the media automation stack on VM 113.

## Architecture Overview

```
User → Overseerr (requests) → Sonarr/Radarr (automation)
                                     ↓
                            Prowlarr (indexers)
                                     ↓
                    SABnzbd (Usenet) ← PRIMARY
                    qBittorrent+VPN (Torrents) ← FALLBACK
                                     ↓
                            Downloads complete
                                     ↓
                    Bazarr (adds subtitles)
                                     ↓
                            Plex (serves media)
```

## Storage Structure

**Synology NAS (10.10.10.100):**
```
/volume1/media/                      # Mounted via NFS to /mnt/nas/media on VM
├── library/                         # Final media location
│   ├── movies/                      # Created by Radarr
│   └── tv/                          # Created by Sonarr
└── downloads/
    ├── sabnzbd/                     # Usenet downloads
    │   ├── incomplete/              # Created automatically
    │   └── complete/                # Created automatically
    └── torrents/                    # Torrent downloads
        ├── incomplete/              # Created automatically
        └── complete/                # Created automatically
```

## Prerequisites

### 1. Add Secrets to 1Password

Create these items in 1Password vault "Server":

**plex** (new item):
- `claim-token`: Get from https://www.plex.tv/claim/ (valid for 4 minutes)

**privado-vpn** (new item):
- `username`: Your Privado VPN username
- `password`: Your Privado VPN password

### 2. Verify NFS Mount

```bash
# On media VM
df -h | grep media
ls /mnt/nas/media/library
ls /mnt/nas/media/downloads
```

## Deployment

### Step 1: Deploy Monitoring (Already Running)

```bash
cd /opt/homelab/media
op run --env-file=.env -- docker compose up -d portainer-agent alloy beszel-agent
```

### Step 2: Deploy Plex

**IMPORTANT:** Get Plex claim token first (valid 4 minutes):
1. Visit https://www.plex.tv/claim/
2. Copy the claim token
3. Add to 1Password: `op item create --category=login --title="plex" --vault="Server" claim-token="<token>"`

```bash
op run --env-file=.env -- docker compose up -d plex
docker logs -f plex
```

**Initial Plex Setup:**
1. Visit http://10.10.10.113:32400/web
2. Sign in with your Plex account
3. Skip library setup for now (we'll add after content arrives)

### Step 3: Deploy SABnzbd (Usenet - PRIMARY)

```bash
op run --env-file=.env -- docker compose up -d sabnzbd
docker logs -f sabnzbd
```

**Configure Newshosting:**
1. Visit http://10.10.10.113:8085
2. Quick Setup Wizard:
   - Language: English
   - Server:
     - Host: `news.newshosting.com`
     - Port: `563`
     - SSL: ✅ Enabled
     - Connections: `30` (or up to 50)
     - Username: Your Newshosting username
     - Password: Your Newshosting password
     - Priority: `0` (highest)
     - Test: Click "Test Server" ✅
   - Folders:
     - Temporary Download Folder: `/downloads/incomplete`
     - Completed Download Folder: `/downloads/complete`
   - Categories: Skip for now (default is fine)
3. Finish wizard

### Step 4: Deploy Prowlarr (Indexer Manager)

```bash
op run --env-file=.env -- docker compose up -d prowlarr
docker logs -f prowlarr
```

**Add Indexers:**
1. Visit http://10.10.10.113:9696
2. Settings → Indexers → Add Indexer
3. Add **NZBFinder**:
   - Name: NZBFinder
   - URL: `https://nzbfinder.ws`
   - API Key: (from your NZBFinder account)
   - Categories: Select all
   - Test → Save
4. Add **DrunkenSlug**:
   - Name: DrunkenSlug
   - URL: `https://drunkenslug.com`
   - API Key: (from your DrunkenSlug account)
   - Categories: Select all
   - Test → Save
5. Add **NinjaCentral**:
   - Name: NinjaCentral
   - URL: `https://ninjacentral.co.za`
   - API Key: (from your NinjaCentral account)
   - Categories: Select all
   - Test → Save

### Step 5: Deploy Sonarr + Radarr

```bash
op run --env-file=.env -- docker compose up -d sonarr radarr
docker logs -f sonarr
docker logs -f radarr
```

**Configure Sonarr (TV Shows):**
1. Visit http://10.10.10.113:8989
2. Settings → Media Management:
   - ✅ Rename Episodes
   - ✅ Use Hardlinks instead of Copy (CRITICAL!)
   - Episode Title Required: Always
3. Settings → Profiles: (Keep default for now, Notifiarr will sync TRaSH profiles later)
4. Settings → Indexers → Add → Prowlarr:
   - Name: Prowlarr
   - URL: `http://prowlarr:9696`
   - API Key: (copy from Prowlarr → Settings → General → API Key)
   - Sync Level: Full Sync
   - Test → Save
5. Settings → Download Clients → Add → SABnzbd:
   - Name: SABnzbd
   - Host: `sabnzbd`
   - Port: `8080`
   - API Key: (from SABnzbd → Config → General → API Key)
   - Category: `tv`
   - Test → Save
6. Settings → Root Folders → Add Root Folder:
   - Path: `/tv`
   - Save

**Configure Radarr (Movies):**
1. Visit http://10.10.10.113:7878
2. Follow same steps as Sonarr, but:
   - SABnzbd Category: `movies`
   - Root Folder: `/movies`

### Step 6: Deploy Gluetun + qBittorrent (VPN + Torrents)

```bash
op run --env-file=.env -- docker compose up -d gluetun qbittorrent
docker logs -f gluetun
# Wait for "connected" message
docker logs -f qbittorrent
```

**Configure qBittorrent:**
1. Visit http://10.10.10.113:8080
2. Default login:
   - Username: `admin`
   - Password: Check logs: `docker logs qbittorrent 2>&1 | grep "temporary password"`
3. Tools → Options:
   - Downloads:
     - Default Save Path: `/downloads/complete`
     - Keep incomplete torrents in: `/downloads/incomplete`
     - ✅ Use Automatic Torrent Management
   - Connection:
     - Listening Port: `6881`
     - ✅ Use UPnP / NAT-PMP port forwarding (if supported by VPN)
   - BitTorrent:
     - ✅ Enable DHT
     - ✅ Enable PeX
     - ✅ Enable Local Peer Discovery
   - Web UI:
     - Change password!
4. Save

**Add qBittorrent to Sonarr/Radarr:**
1. Sonarr → Settings → Download Clients → Add → qBittorrent:
   - Name: qBittorrent
   - Host: `gluetun` (routes through VPN container)
   - Port: `8080`
   - Username: `admin`
   - Password: (your new password)
   - Category: `tv`
   - Priority: `2` (lower than SABnzbd)
   - Test → Save
2. Repeat for Radarr with Category: `movies`

**Configure Delay Profiles (Usenet Priority):**
1. Sonarr → Settings → Delay Profiles:
   - Protocol: Prefer Usenet
   - Usenet Delay: `0` minutes
   - Torrent Delay: `60` minutes
2. Repeat for Radarr

### Step 7: Deploy Bazarr (Subtitles)

```bash
op run --env-file=.env -- docker compose up -d bazarr
docker logs -f bazarr
```

**Configure Bazarr:**
1. Visit http://10.10.10.113:6767
2. Settings → Sonarr:
   - ✅ Enabled
   - Address: `sonarr`
   - Port: `8989`
   - API Key: (from Sonarr)
   - Test → Save
3. Settings → Radarr:
   - ✅ Enabled
   - Address: `radarr`
   - Port: `7878`
   - API Key: (from Radarr)
   - Test → Save
4. Settings → Providers:
   - Add **OpenSubtitles**:
     - Username/Password: (create free account at opensubtitles.org)
   - Add **Subscene**
   - Add **Podnapisi**
5. Settings → Languages:
   - Languages Filter: Add your languages (e.g., English)
   - Default Enabled: ✅
6. Settings → Subtitles:
   - Minimum Score: `50`
   - ✅ Automatic Subtitles Synchronization
   - Series Score Threshold: `96.1`

### Step 8: Deploy Overseerr (Request UI)

```bash
op run --env-file=.env -- docker compose up -d overseerr
docker logs -f overseerr
```

**Configure Overseerr:**
1. Visit http://10.10.10.113:5055
2. Welcome Screen → **Sign in with Plex**
3. Select your Plex server
4. Configure Services:
   - Radarr:
     - Server: `radarr`
     - Port: `7878`
     - API Key: (from Radarr)
     - URL Base: (leave empty)
     - Quality Profile: HD-1080p (or your preference)
     - Root Folder: `/movies`
     - Test → Save
   - Sonarr:
     - Server: `sonarr`
     - Port: `8989`
     - API Key: (from Sonarr)
     - URL Base: (leave empty)
     - Quality Profile: HD-1080p
     - Root Folder: `/tv`
     - Test → Save
5. Finish setup

### Step 9: Deploy Notifiarr (TRaSH Sync)

```bash
op run --env-file=.env -- docker compose up -d notifiarr
```

**Configure Notifiarr:**
1. Get API key from https://notifiarr.com/ (Patron account required)
2. Edit config file:
   ```bash
   nano /opt/homelab/media/notifiarr/config/notifiarr.conf
   ```
3. Add your API key and configure integrations
4. Restart: `docker restart notifiarr`

## Post-Deployment

### Add Plex Libraries

1. Visit http://10.10.10.113:32400/web
2. Add Libraries:
   - **Movies**:
     - Type: Movies
     - Folder: `/media/movies`
     - Scanner: Plex Movie
     - Agent: Plex Movie
   - **TV Shows**:
     - Type: TV Shows
     - Folder: `/media/tv`
     - Scanner: Plex TV Series
     - Agent: Plex TV Series

### Test the Workflow

1. Open Overseerr: http://10.10.10.113:5055
2. Search for a movie or TV show
3. Click **Request**
4. Watch the magic:
   - Radarr/Sonarr searches via Prowlarr
   - Download starts in SABnzbd (or qBittorrent if Usenet unavailable)
   - On completion, Radarr/Sonarr hardlinks to library
   - Bazarr downloads subtitles
   - Plex scans and adds to library
5. Watch in Plex!

## Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Plex | http://10.10.10.113:32400/web | Media server |
| Overseerr | http://10.10.10.113:5055 | Request UI |
| Sonarr | http://10.10.10.113:8989 | TV automation |
| Radarr | http://10.10.10.113:7878 | Movie automation |
| Prowlarr | http://10.10.10.113:9696 | Indexer manager |
| SABnzbd | http://10.10.10.113:8085 | Usenet downloader |
| qBittorrent | http://10.10.10.113:8080 | Torrent downloader |
| Bazarr | http://10.10.10.113:6767 | Subtitles |
| Notifiarr | http://10.10.10.113:5454 | TRaSH sync |

## Troubleshooting

### NFS Mount Issues
```bash
sudo umount /mnt/nas/media
sudo mount -a
df -h | grep media
```

### Container Not Starting
```bash
docker logs <container-name>
docker restart <container-name>
```

### VPN Not Connecting
```bash
docker logs gluetun
# Look for "connected" message
# If failing, check Privado credentials in 1Password
```

### Downloads Not Moving to Library
- Check Sonarr/Radarr logs
- Verify hardlinks are enabled (Settings → Media Management)
- Ensure both downloads and library are on same mount (`/mnt/nas/media`)

### Permission Issues
```bash
# On Synology NAS
sudo chown -R 1000:1000 /volume1/media
sudo chmod -R 755 /volume1/media
```

## When Adding GPU

When you add Intel Arc A380 (recommended) or other GPU:

1. **Verify GPU in Proxmox:**
   ```bash
   lspci | grep VGA
   ```

2. **Pass through to VM** (in Proxmox UI or CLI)

3. **Uncomment in docker-compose.yml:**
   ```yaml
   plex:
     devices:
       - /dev/dri:/dev/dri
   ```

4. **Restart Plex:**
   ```bash
   docker restart plex
   ```

5. **Enable in Plex:**
   - Settings → Server → Transcoder
   - ✅ Use hardware acceleration when available
   - Save

6. **Test transcoding:**
   - Play media that requires transcoding
   - Check: Settings → Server → Dashboard (should show "hw" for transcode sessions)
