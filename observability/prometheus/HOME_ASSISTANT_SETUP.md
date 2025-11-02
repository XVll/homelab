# Home Assistant Prometheus Integration Setup

## Step 1: Configure Prometheus Integration in Home Assistant

1. **Open Home Assistant**: http://10.10.10.116:8123 or https://ha.onurx.com

2. **Go to Settings → Devices & Services → Integrations**

3. **Find the Prometheus integration** you added earlier and click **CONFIGURE**

4. **Configure the filter to allow Prometheus server**:
   - Click on the Prometheus integration
   - Click **CONFIGURE** or the gear icon
   - You should see options for:
     - **Filter**: Choose what to include/exclude
     - **Namespace**: Leave as default (`homeassistant`)

5. **Important**: The Prometheus integration should automatically be accessible from your local network. If there's an IP whitelist option, add:
   - `10.10.10.112` (Prometheus server IP)
   - Or `10.10.10.0/24` (entire homelab network)

## Step 2: Create Long-Lived Access Token

1. **Click on your profile** (bottom left corner)

2. **Scroll down to "Long-Lived Access Tokens"**

3. **Click "CREATE TOKEN"**
   - Name: `Prometheus`
   - Click **OK**

4. **Copy the token** (shown only once!)

## Step 3: Save Token to Prometheus

**Method 1 - Manual:**
```bash
# SSH to observability VM
ssh fx@10.10.10.112

# Create secrets directory
mkdir -p /opt/homelab/observability/prometheus/config/secrets

# Create token file (replace YOUR_TOKEN with actual token)
echo "YOUR_TOKEN_HERE" > /opt/homelab/observability/prometheus/config/secrets/homeassistant_token.txt

# Set permissions
chmod 600 /opt/homelab/observability/prometheus/config/secrets/homeassistant_token.txt

# Pull latest config
cd /opt/homelab && git pull

# Restart Prometheus
cd observability
docker compose restart prometheus
```

**Method 2 - Using the setup script:**
```bash
# On your local machine
ssh fx@10.10.10.112 'cd /opt/homelab && git pull'

# Then SSH in and run manually
ssh fx@10.10.10.112
cd /opt/homelab
bash observability/prometheus/setup-ha-token.sh
# (Paste token when prompted)
```

## Step 4: Test the Connection

1. **Test the endpoint directly** (should return 401 without token):
   ```bash
   curl http://10.10.10.116:8123/api/prometheus
   ```

2. **Test with token**:
   ```bash
   TOKEN="your_token_here"
   curl -H "Authorization: Bearer $TOKEN" http://10.10.10.116:8123/api/prometheus | head -50
   ```
   Should return Prometheus metrics in text format.

3. **Check Prometheus targets**: http://10.10.10.112:9090/targets
   - Look for `homeassistant` job
   - Status should be **UP** (green)

4. **View Grafana dashboards**: http://10.10.10.112:3000
   - Systems Overview: Should show Home Assistant with live data
   - Home Assistant Detail: Should show entities, automations, etc.

## Troubleshooting

### Prometheus target shows "DOWN" or "401 Unauthorized"

**Check token is correct:**
```bash
ssh fx@10.10.10.112
cat /opt/homelab/observability/prometheus/config/secrets/homeassistant_token.txt
# Verify token matches what you created in HA
```

**Check token file permissions:**
```bash
ls -la /opt/homelab/observability/prometheus/config/secrets/
# Should show: -rw------- (600)
```

**Verify Prometheus can read the file:**
```bash
docker exec prometheus cat /etc/prometheus/secrets/homeassistant_token.txt
# Should display the token
```

### Prometheus target shows "Connection refused"

**Check Home Assistant is accessible:**
```bash
curl -I http://10.10.10.116:8123
# Should return HTTP 200 OK
```

**Check Prometheus integration is enabled in HA:**
- Go to Settings → Devices & Services → Integrations
- Look for "Prometheus" - should show as configured

### No metrics showing in Grafana

**Check Prometheus has scraped data:**
- Go to http://10.10.10.112:9090
- Try query: `up{job="homeassistant"}`
- Should return `1` if working

**Check dashboard queries:**
- Open Grafana dashboard
- Click "Edit" on a panel
- Check if queries return data

## Alternative: Configuration via YAML (Advanced)

If you prefer to configure via `configuration.yaml`:

```yaml
# configuration.yaml
prometheus:
  namespace: homeassistant
  # No IP filter needed - use bearer token authentication
```

Then restart Home Assistant.

## Security Notes

- The token file is gitignored and will not be committed
- Token provides full API access - keep it secure
- Token does not expire unless you delete it from HA
- You can revoke the token anytime in HA settings
