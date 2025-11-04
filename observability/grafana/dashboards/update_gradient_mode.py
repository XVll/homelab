#!/usr/bin/env python3
"""
Update all timeseries graphs to use opacity gradient mode
This creates a cleaner, more modern look with transparency
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

updated_panels = []

for panel in dashboard['panels']:
    # Check if it's a timeseries panel
    if panel.get('type') == 'timeseries':
        panel_title = panel.get('title', 'Untitled')

        # Update gradientMode in fieldConfig.defaults.custom
        if 'fieldConfig' in panel and 'defaults' in panel['fieldConfig']:
            defaults = panel['fieldConfig']['defaults']
            if 'custom' in defaults and 'gradientMode' in defaults['custom']:
                old_mode = defaults['custom']['gradientMode']
                defaults['custom']['gradientMode'] = 'opacity'
                updated_panels.append(f"{panel_title} (was: {old_mode})")
                print(f"✓ Updated '{panel_title}': {old_mode} → opacity")

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print(f"\n✅ Updated {len(updated_panels)} timeseries panels to use opacity gradient!")
print("\nUpdated panels:")
for panel_name in updated_panels:
    print(f"  - {panel_name}")

print("\nVisual improvements:")
print("  - Cleaner, more modern appearance")
print("  - Transparent gradients show data density better")
print("  - Easier to see overlapping series")
print("  - Consistent style across all graphs")
