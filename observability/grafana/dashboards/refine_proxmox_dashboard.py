#!/usr/bin/env python3
"""
Refine Proxmox Overview Dashboard:
1. Redesign table with more columns and compact status indicator
2. Compact PVE stats section
3. Move guest chart legends to bottom
4. Optimize layout to reduce wasted space
"""

import json
import os

# Change to script directory
os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

# Read current dashboard
with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Update panels
for panel in dashboard['panels']:
    panel_id = panel.get('id')

    # Panel 19: Resource allocation summary table
    if panel_id == 19:
        print("Updating table panel...")

        # Add CPU usage query
        panel['targets'].append({
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "editorMode": "code",
            "exemplar": False,
            "expr": "sum by (id) ((pve_cpu_usage_ratio{instance=\"$instance\"} / pve_cpu_usage_limit) and on (id, instance) pve_guest_info and on(id) pve_up==1)",
            "format": "table",
            "hide": False,
            "instant": True,
            "legendFormat": "",
            "range": False,
            "refId": "cpu_usage"
        })

        # Add disk I/O query (read + write)
        panel['targets'].append({
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "editorMode": "code",
            "exemplar": False,
            "expr": "sum by (id) ((rate(pve_disk_write_bytes{instance=\"$instance\"}[5m]) + rate(pve_disk_read_bytes{instance=\"$instance\"}[5m])) and on (id, instance) pve_guest_info and on(id) pve_up==1)",
            "format": "table",
            "hide": False,
            "instant": True,
            "legendFormat": "",
            "range": False,
            "refId": "disk_io"
        })

        # Add network I/O query (rx + tx)
        panel['targets'].append({
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "editorMode": "code",
            "exemplar": False,
            "expr": "sum by (id) ((rate(pve_network_receive_bytes{instance=\"$instance\"}[5m]) + rate(pve_network_transmit_bytes{instance=\"$instance\"}[5m])) and on (id, instance) pve_guest_info and on(id) pve_up==1)",
            "format": "table",
            "hide": False,
            "instant": True,
            "legendFormat": "",
            "range": False,
            "refId": "network_io"
        })

        # Update transformations to include new columns
        panel['transformations'][1]['options']['renameByName'].update({
            "Value #cpu_usage": "CPU Usage",
            "Value #disk_io": "Disk I/O",
            "Value #network_io": "Network I/O"
        })

        # Update field overrides for new columns
        # Status: color-background for circle effect
        status_override = next((o for o in panel['fieldConfig']['overrides'] if o['matcher']['options'] == 'Status'), None)
        if status_override:
            for prop in status_override['properties']:
                if prop['id'] == 'custom.displayMode':
                    prop['value'] = 'color-background'  # Circle indicator
                if prop['id'] == 'custom.width':
                    prop['value'] = 60  # Smaller width

        # Add CPU Usage column formatting
        panel['fieldConfig']['overrides'].append({
            "matcher": {"id": "byName", "options": "CPU Usage"},
            "properties": [
                {"id": "unit", "value": "percentunit"},
                {"id": "custom.displayMode", "value": "color-text"},
                {"id": "custom.width", "value": 100},
                {"id": "mappings", "value": [
                    {"options": {"from": 0, "to": 0.7, "result": {"color": "green", "index": 0}}, "type": "range"},
                    {"options": {"from": 0.7, "to": 0.9, "result": {"color": "orange", "index": 1}}, "type": "range"},
                    {"options": {"from": 0.9, "to": 2, "result": {"color": "red", "index": 2}}, "type": "range"}
                ]}
            ]
        })

        # Add Disk I/O column formatting
        panel['fieldConfig']['overrides'].append({
            "matcher": {"id": "byName", "options": "Disk I/O"},
            "properties": [
                {"id": "unit", "value": "Bps"},
                {"id": "decimals", "value": 0},
                {"id": "custom.width", "value": 90}
            ]
        })

        # Add Network I/O column formatting
        panel['fieldConfig']['overrides'].append({
            "matcher": {"id": "byName", "options": "Network I/O"},
            "properties": [
                {"id": "unit", "value": "Bps"},
                {"id": "decimals", "value": 0},
                {"id": "custom.width", "value": 110}
            ]
        })

        # Compact vCPUs, Memory, Disk columns
        for override in panel['fieldConfig']['overrides']:
            if override['matcher']['options'] == 'vCPUs':
                for prop in override['properties']:
                    if prop['id'] == 'custom.width':
                        prop['value'] = 50
            elif override['matcher']['options'] == 'Memory':
                for prop in override['properties']:
                    if prop['id'] == 'custom.width':
                        prop['value'] = 80
            elif override['matcher']['options'] == 'Disk':
                for prop in override['properties']:
                    if prop['id'] == 'custom.width':
                        prop['value'] = 70

        # Expand table to full width
        panel['gridPos'] = {
            "h": 10,  # Reduced height
            "w": 24,  # Full width
            "x": 0,
            "y": 0
        }

    # Panel 23 & 24: CPU and Memory history - make more compact
    elif panel_id == 23:
        print("Compacting CPU history panel...")
        panel['gridPos'] = {
            "h": 5,  # Reduced from 7
            "w": 9,  # Increased width
            "x": 0,
            "y": 10
        }

    # Panel 7: Current CPU gauge - make smaller
    elif panel_id == 7:
        print("Compacting CPU gauge...")
        panel['gridPos'] = {
            "h": 5,
            "w": 3,
            "x": 9,
            "y": 10
        }

    # Panel 22: CPUs stat - remove (redundant)
    elif panel_id == 22:
        print("Removing CPUs stat panel...")
        panel['gridPos'] = {
            "h": 0,
            "w": 0,
            "x": 0,
            "y": 0
        }
        panel['title'] = "HIDDEN - CPUs"

    # Panel 24: Memory history
    elif panel_id == 24:
        print("Compacting Memory history panel...")
        panel['gridPos'] = {
            "h": 5,
            "w": 9,
            "x": 12,
            "y": 10
        }

    # Panel 8: Current memory gauge
    elif panel_id == 8:
        print("Compacting Memory gauge...")
        panel['gridPos'] = {
            "h": 5,
            "w": 3,
            "x": 21,
            "y": 10
        }

    # Panel 20: Memory stat - remove (redundant)
    elif panel_id == 20:
        print("Removing Memory stat panel...")
        panel['gridPos'] = {
            "h": 0,
            "w": 0,
            "x": 0,
            "y": 0
        }
        panel['title'] = "HIDDEN - Memory"

    # Panel 2: Guests CPU usage - move legend to bottom
    elif panel_id == 2:
        print("Moving Guests CPU legend to bottom...")
        panel['options']['legend']['placement'] = 'bottom'
        panel['gridPos'] = {
            "h": 9,  # Slightly reduced
            "w": 12,
            "x": 0,
            "y": 15
        }

    # Panel 5: Guests memory usage - move legend to bottom
    elif panel_id == 5:
        print("Moving Guests Memory legend to bottom...")
        panel['options']['legend']['placement'] = 'bottom'
        panel['gridPos'] = {
            "h": 9,
            "w": 12,
            "x": 12,
            "y": 15
        }

    # Panel 11: Storage usage
    elif panel_id == 11:
        panel['gridPos'] = {
            "h": 9,
            "w": 3,
            "x": 0,
            "y": 24
        }

    # Panel 15: Space allocation
    elif panel_id == 15:
        panel['gridPos'] = {
            "h": 9,
            "w": 4,
            "x": 3,
            "y": 24
        }

    # Panel 9: LXC guests disk usage - move legend to bottom
    elif panel_id == 9:
        print("Moving LXC Disk legend to bottom...")
        panel['options']['legend']['placement'] = 'bottom'
        panel['gridPos'] = {
            "h": 9,
            "w": 17,
            "x": 7,
            "y": 24
        }

    # Panel 13: Network IO - move legend to bottom
    elif panel_id == 13:
        print("Moving Network IO legend to bottom...")
        panel['options']['legend']['placement'] = 'bottom'
        panel['gridPos'] = {
            "h": 9,
            "w": 24,
            "x": 0,
            "y": 33
        }

    # Panel 12: Disk IO - move legend to bottom
    elif panel_id == 12:
        print("Moving Disk IO legend to bottom...")
        panel['options']['legend']['placement'] = 'bottom'
        panel['gridPos'] = {
            "h": 8,
            "w": 24,
            "x": 0,
            "y": 42
        }

# Write updated dashboard
with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\nDashboard refinement complete!")
print("Changes:")
print("1. ✓ Table expanded to full width with CPU Usage, Disk I/O, Network I/O columns")
print("2. ✓ Status column shows colored circle (color-background)")
print("3. ✓ Compact PVE stats section (CPU/Memory)")
print("4. ✓ All guest charts have legends at bottom")
print("5. ✓ Layout optimized to reduce wasted space")
