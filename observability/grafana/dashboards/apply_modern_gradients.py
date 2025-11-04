#!/usr/bin/env python3
"""
Apply modern gradient styling to all timeseries graphs
Using hue gradient mode with proper fill for vibrant, modern look
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

        # Update gradientMode and fillOpacity in fieldConfig.defaults.custom
        if 'fieldConfig' in panel and 'defaults' in panel['fieldConfig']:
            defaults = panel['fieldConfig']['defaults']
            if 'custom' in defaults:
                custom = defaults['custom']

                # Set gradient mode to 'hue' for vibrant colors
                old_gradient = custom.get('gradientMode', 'none')
                custom['gradientMode'] = 'hue'

                # Set fill opacity for visible gradient
                # 10-20 is good for multiple series (not too busy)
                # 30-50 is good for single or few series (more visible)
                old_fill = custom.get('fillOpacity', 0)

                # Different fill based on panel type
                if 'history' in panel_title.lower():
                    # Single series - more fill
                    custom['fillOpacity'] = 30
                elif 'Guests' in panel_title or 'LXC' in panel_title:
                    # Multiple series - less fill to avoid clutter
                    custom['fillOpacity'] = 15
                elif 'IO' in panel_title:
                    # IO graphs - moderate fill
                    custom['fillOpacity'] = 20
                else:
                    # Default
                    custom['fillOpacity'] = 20

                updated_panels.append({
                    'title': panel_title,
                    'old_gradient': old_gradient,
                    'new_gradient': 'hue',
                    'old_fill': old_fill,
                    'new_fill': custom['fillOpacity']
                })

                print(f"✓ {panel_title}:")
                print(f"    gradient: {old_gradient} → hue")
                print(f"    fill: {old_fill} → {custom['fillOpacity']}")

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print(f"\n✅ Updated {len(updated_panels)} timeseries panels with modern gradients!")

print("\n📊 Gradient Configuration:")
print("  Mode: hue (vibrant, colorful)")
print("  Fill opacity:")
print("    - History panels (single series): 30%")
print("    - Guest panels (multiple series): 15%")
print("    - IO panels: 20%")

print("\n✨ Visual Benefits:")
print("  - Vibrant, modern hue-based gradients")
print("  - Proper fill opacity shows gradient effect")
print("  - Different fill levels optimize readability")
print("  - Area under curves visible but not overwhelming")
print("  - Professional, polished appearance")

print("\n💡 Alternative: If you prefer subtle/minimal, we can use:")
print("  - gradientMode: 'opacity' (subtle)")
print("  - fillOpacity: 10-20 (semi-transparent)")
