#!/usr/bin/env python3
"""
Restructure Proxmox dashboard to efficient 2-column layout:

LEFT COLUMN (18 width): Guest VMs
- Table (compact)
- Guests CPU usage
- Guests memory usage
- Disk I/O
- Network I/O

RIGHT COLUMN (6 width): PVE Host
- Current CPU gauge
- Current Memory gauge
- CPU history (compact)
- Memory history (compact)
- Storage usage
- Space allocation
- LXC disk usage (if needed)
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

print("=== Restructuring dashboard to 2-column layout ===\n")

# Grafana uses 24-column grid
# Left: 18 columns (guests), Right: 6 columns (PVE host)
LEFT_WIDTH = 18
RIGHT_WIDTH = 6

for panel in dashboard['panels']:
    panel_id = panel.get('id')
    panel_title = panel.get('title', 'Untitled')

    # === LEFT COLUMN: Guest VMs ===

    # Panel 19: Table (top left, compact)
    if panel_id == 19:
        panel['gridPos'] = {"h": 8, "w": LEFT_WIDTH, "x": 0, "y": 0}
        print(f"✓ {panel_title}: Compact table at top left (8h x 18w)")

    # Panel 2: Guests CPU usage
    elif panel_id == 2:
        panel['gridPos'] = {"h": 7, "w": 9, "x": 0, "y": 8}
        print(f"✓ {panel_title}: Left middle (7h x 9w)")

    # Panel 5: Guests memory usage
    elif panel_id == 5:
        panel['gridPos'] = {"h": 7, "w": 9, "x": 9, "y": 8}
        print(f"✓ {panel_title}: Left middle right (7h x 9w)")

    # Panel 12: Disk IO/s
    elif panel_id == 12:
        panel['gridPos'] = {"h": 6, "w": 9, "x": 0, "y": 15}
        print(f"✓ {panel_title}: Left bottom (6h x 9w)")

    # Panel 13: Network IO/s
    elif panel_id == 13:
        panel['gridPos'] = {"h": 6, "w": 9, "x": 9, "y": 15}
        print(f"✓ {panel_title}: Left bottom right (6h x 9w)")

    # === RIGHT COLUMN: PVE Host ===

    # Panel 7: Current CPU gauge (compact)
    elif panel_id == 7:
        panel['gridPos'] = {"h": 4, "w": 3, "x": 18, "y": 0}
        print(f"✓ {panel_title}: Top right (4h x 3w)")

    # Panel 8: Current memory gauge (compact)
    elif panel_id == 8:
        panel['gridPos'] = {"h": 4, "w": 3, "x": 21, "y": 0}
        print(f"✓ {panel_title}: Top right (4h x 3w)")

    # Panel 23: CPU history (compact)
    elif panel_id == 23:
        panel['gridPos'] = {"h": 4, "w": RIGHT_WIDTH, "x": 18, "y": 4}
        panel['title'] = "PVE CPU"  # Shorter title
        print(f"✓ {panel_title}: Right (4h x 6w)")

    # Panel 24: Memory history (compact)
    elif panel_id == 24:
        panel['gridPos'] = {"h": 4, "w": RIGHT_WIDTH, "x": 18, "y": 8}
        panel['title'] = "PVE Memory"  # Shorter title
        print(f"✓ {panel_title}: Right (4h x 6w)")

    # Panel 11: Storage usage (compact)
    elif panel_id == 11:
        panel['gridPos'] = {"h": 5, "w": RIGHT_WIDTH, "x": 18, "y": 12}
        print(f"✓ {panel_title}: Right (5h x 6w)")

    # Panel 15: Space allocation (compact)
    elif panel_id == 15:
        panel['gridPos'] = {"h": 4, "w": RIGHT_WIDTH, "x": 18, "y": 17}
        print(f"✓ {panel_title}: Right (4h x 6w)")

    # Panel 9: LXC disk usage (if exists, hide or compact)
    elif panel_id == 9:
        # Hide LXC panel since you have no LXC containers
        panel['gridPos'] = {"h": 0, "w": 0, "x": 0, "y": 0}
        panel['title'] = "HIDDEN - " + panel_title
        print(f"✓ {panel_title}: Hidden (no LXC containers)")

    # Panel 22: CPUs stat (already hidden)
    # Panel 20: Memory stat (already hidden)

# Reduce font sizes globally for tidier appearance
dashboard['title'] = 'Proxmox Overview'

print("\n=== Optimizing panel settings ===\n")

# Reduce title font sizes and optimize legends
for panel in dashboard['panels']:
    if panel.get('type') == 'timeseries':
        # Compact legend
        if 'options' in panel and 'legend' in panel['options']:
            panel['options']['legend']['displayMode'] = 'list'
            panel['options']['legend']['showLegend'] = True
            panel['options']['legend']['placement'] = 'bottom'

        # Smaller title
        panel['title'] = panel.get('title', '').replace('Guests ', '').replace('guests ', '')
        print(f"  ✓ Optimized: {panel.get('title')}")

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Dashboard restructured!")
print("\n📊 New Layout:")
print("  LEFT (18 cols) - Guest VMs:")
print("    - Table (compact, 8h)")
print("    - CPU & Memory charts (side by side, 7h)")
print("    - Disk I/O & Network I/O (side by side, 6h)")
print("\n  RIGHT (6 cols) - PVE Host:")
print("    - CPU & Memory gauges (top, 4h each)")
print("    - CPU & Memory history (4h each)")
print("    - Storage usage (5h)")
print("    - Space allocation (4h)")
print("\n✨ Benefits:")
print("  - Much more compact and efficient")
print("  - Clear separation: Guests vs Host")
print("  - Less scrolling needed")
print("  - Better use of horizontal space")
print("  - Professional, tidy appearance")
