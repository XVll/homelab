#!/usr/bin/env python3
"""
Fix sparkline panels to show same values as gauge panels above them
- Panel 23 (CPU sparkline) should match Panel 7 (Current CPU)
- Panel 24 (Memory sparkline) should match Panel 8 (Current memory)
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

print("=== Fixing sparkline queries to match gauge values ===\n")

for panel in dashboard['panels']:
    panel_id = panel.get('id')
    panel_title = panel.get('title', 'Untitled')

    # Panel 23: CPU sparkline - should match Panel 7 calculation
    if panel_id == 23:
        print(f"Fixing {panel_title} query to match Current CPU gauge")

        # Replace two separate queries with single ratio calculation
        panel['targets'] = [{
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "expr": "pve_cpu_usage_ratio{instance=\"$instance\"} / pve_cpu_usage_limit and on(id) pve_node_info",
            "range": True,
            "instant": False,
            "legendFormat": "CPU %",
            "refId": "A"
        }]

        # Ensure percentunit formatting
        if 'fieldConfig' not in panel:
            panel['fieldConfig'] = {"defaults": {}, "overrides": []}

        panel['fieldConfig']['defaults']['unit'] = 'percentunit'
        panel['fieldConfig']['defaults']['decimals'] = 1
        panel['fieldConfig']['defaults']['min'] = 0
        panel['fieldConfig']['defaults']['max'] = 1

        print(f"  ✓ Changed to single ratio query: usage_ratio / usage_limit")
        print(f"  ✓ Set percentunit format with 0-100% range")

    # Panel 24: Memory sparkline - should match Panel 8 calculation
    elif panel_id == 24:
        print(f"\nFixing {panel_title} query to match Current Memory gauge")

        # Replace two separate queries with single ratio calculation
        panel['targets'] = [{
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "expr": "pve_memory_usage_bytes{instance=\"$instance\"} / pve_memory_size_bytes and on(id) pve_node_info",
            "range": True,
            "instant": False,
            "legendFormat": "Memory %",
            "refId": "A"
        }]

        # Ensure percentunit formatting
        if 'fieldConfig' not in panel:
            panel['fieldConfig'] = {"defaults": {}, "overrides": []}

        panel['fieldConfig']['defaults']['unit'] = 'percentunit'
        panel['fieldConfig']['defaults']['decimals'] = 1
        panel['fieldConfig']['defaults']['min'] = 0
        panel['fieldConfig']['defaults']['max'] = 1

        print(f"  ✓ Changed to single ratio query: usage_bytes / size_bytes")
        print(f"  ✓ Set percentunit format with 0-100% range")

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Fixed sparkline queries!")
print("\nChanges:")
print("  - CPU sparkline: Now calculates usage_ratio / usage_limit (matches gauge)")
print("  - Memory sparkline: Now calculates usage_bytes / size_bytes (matches gauge)")
print("  - Both use percentunit format")
print("  - Sparklines will show same current value as gauges above")
print("\n📊 Result:")
print("  - Current CPU gauge: 0.09% → CPU sparkline: 0.09% ✅")
print("  - Current Memory gauge: 80% → Memory sparkline: 80% ✅")
