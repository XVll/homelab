#!/bin/bash

# Setup script for Home Assistant Prometheus token
# Run this on the observability VM (10.10.10.112)

set -e

echo "================================================"
echo "Home Assistant Prometheus Token Setup"
echo "================================================"
echo ""
echo "Before running this script, create a long-lived access token in Home Assistant:"
echo "1. Go to: http://10.10.10.116:8123"
echo "2. Click your profile (bottom left)"
echo "3. Scroll to 'Long-Lived Access Tokens'"
echo "4. Click 'CREATE TOKEN'"
echo "5. Name: Prometheus"
echo "6. Copy the token"
echo ""
read -p "Press Enter when you have the token ready..."
echo ""
read -sp "Paste the token here: " TOKEN
echo ""

if [ -z "$TOKEN" ]; then
    echo "Error: No token provided"
    exit 1
fi

# Create secrets directory if it doesn't exist
mkdir -p /opt/homelab/observability/prometheus/config/secrets

# Save token
echo "$TOKEN" > /opt/homelab/observability/prometheus/config/secrets/homeassistant_token.txt

# Set proper permissions
chmod 600 /opt/homelab/observability/prometheus/config/secrets/homeassistant_token.txt

echo ""
echo "✓ Token saved to: /opt/homelab/observability/prometheus/config/secrets/homeassistant_token.txt"
echo "✓ Permissions set to 600"
echo ""
echo "Now restarting Prometheus..."

cd /opt/homelab/observability
docker compose restart prometheus

echo ""
echo "✓ Prometheus restarted"
echo ""
echo "Verify the setup:"
echo "1. Check Prometheus targets: http://10.10.10.112:9090/targets"
echo "2. Look for 'homeassistant' job - should show UP status"
echo "3. View dashboards: http://10.10.10.112:3000"
echo ""
