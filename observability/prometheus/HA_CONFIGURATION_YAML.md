# Home Assistant configuration.yaml for Prometheus

You have two options for allowing Prometheus to scrape metrics from Home Assistant:

## Option 1: Disable Authentication for Prometheus Endpoint (Recommended for Internal Networks)

Add this to your Home Assistant `configuration.yaml`:

```yaml
prometheus:
  namespace: homeassistant
  requires_auth: false  # Disables authentication requirement
```

**Pros:**
- Simple, no token management needed
- Works immediately

**Cons:**
- Anyone on your network can access `/api/prometheus` endpoint
- Not an issue if your network is trusted (which it should be on 10.10.10.0/24)

## Option 2: Keep Authentication but Use Token

Keep your current config and use the bearer token we configured:

```yaml
prometheus:
  namespace: homeassistant
  # requires_auth: true (default)
```

Then use the long-lived access token in Prometheus (which we already configured).

## Option 3: Trusted Networks Authentication (Best of Both Worlds)

If you want to keep authentication enabled for external access but allow Prometheus without a token, add trusted networks:

```yaml
# Enable Prometheus with auth
prometheus:
  namespace: homeassistant

# Allow Prometheus server IP without authentication
homeassistant:
  auth_providers:
    - type: trusted_networks
      trusted_networks:
        - 10.10.10.112/32  # Prometheus server only
        - 10.10.10.0/24    # Or entire homelab network
      allow_bypass_login: true
    - type: homeassistant  # Keep normal login for users
```

**Note**: After adding trusted_networks, you may need to manually add a user for the trusted network the first time it connects.

## Recommended Approach

For your homelab setup on an isolated network (10.10.10.0/24), I recommend **Option 1** - just add `requires_auth: false` to the prometheus section:

```yaml
prometheus:
  namespace: homeassistant
  requires_auth: false
```

This is the simplest and most reliable approach for internal monitoring.

## After Changing Configuration

1. **Restart Home Assistant** to apply changes
2. **Test the endpoint** (should work without authentication):
   ```bash
   curl http://10.10.10.116:8123/api/prometheus | head -50
   ```
3. **Restart Prometheus** (if you remove the token requirement):
   ```bash
   ssh fx@10.10.10.112 'cd /opt/homelab/observability && docker compose restart prometheus'
   ```

## If You Choose Option 1 (No Auth)

You can simplify the Prometheus configuration by removing the bearer token requirement.

Let me know which option you prefer and I can update the Prometheus config accordingly!
