# Prometheus Secrets

This directory contains sensitive tokens and credentials used by Prometheus.

## Setup Instructions

### Home Assistant Long-Lived Access Token

1. **Create Token in Home Assistant:**
   - Go to http://10.10.10.116:8123 or https://ha.onurx.com
   - Click on your profile (bottom left)
   - Scroll down to "Long-Lived Access Tokens"
   - Click "CREATE TOKEN"
   - Name: `Prometheus`
   - Copy the generated token

2. **Store Token:**
   ```bash
   # On observability VM (10.10.10.112)
   echo "YOUR_TOKEN_HERE" > /opt/homelab/observability/prometheus/config/secrets/homeassistant_token.txt
   chmod 600 /opt/homelab/observability/prometheus/config/secrets/homeassistant_token.txt
   ```

3. **Restart Prometheus:**
   ```bash
   cd /opt/homelab/observability
   docker compose restart prometheus
   ```

4. **Verify:**
   - Check Prometheus targets: http://10.10.10.112:9090/targets
   - Look for `homeassistant` job - should show "UP" status

## Security Notes

- This directory is gitignored and will NOT be committed to the repository
- Tokens are stored in plain text files for Prometheus to read
- File permissions should be 600 (read/write for owner only)
- Never commit actual tokens to git
