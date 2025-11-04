#!/usr/bin/env python3
"""
Convert Proxmox dashboard table to Beszel-style design:
- Progress bars (gradient display mode) for CPU, Memory, Disk metrics
- Color thresholds matching Beszel (green, yellow/orange, red)
- Clean, modern appearance
- Compact layout with proper sizing
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Find the table panel (id: 19)
for panel in dashboard['panels']:
    if panel.get('id') == 19:
        print("Converting table to Beszel-style design...")

        # Update field overrides for Beszel-style progress bars
        overrides = panel['fieldConfig']['overrides']

        # Status column - keep as-is (colored circle)
        print("  ✓ Status: colored circle indicator")

        # Name column - clean text
        for override in overrides:
            if override['matcher'].get('options') == 'Name':
                for prop in override['properties']:
                    if prop['id'] == 'custom.width':
                        prop['value'] = 180
                break
        print("  ✓ Name: clean text (180px)")

        # vCPUs - simple number
        for override in overrides:
            if override['matcher'].get('options') == 'vCPUs':
                for prop in override['properties']:
                    if prop['id'] == 'custom.width':
                        prop['value'] = 70
        print("  ✓ vCPUs: number (70px)")

        # Memory - bytes display
        for override in overrides:
            if override['matcher'].get('options') == 'Memory':
                for prop in override['properties']:
                    if prop['id'] == 'custom.width':
                        prop['value'] = 90
        print("  ✓ Memory: bytes (90px)")

        # Disk - bytes display
        for override in overrides:
            if override['matcher'].get('options') == 'Disk':
                for prop in override['properties']:
                    if prop['id'] == 'custom.width':
                        prop['value'] = 90
        print("  ✓ Disk: bytes (90px)")

        # CPU Usage - PROGRESS BAR with gradient
        cpu_usage_found = False
        for i, override in enumerate(overrides):
            if override['matcher'].get('options') == 'CPU Usage':
                cpu_usage_found = True
                override['properties'] = [
                    {"id": "unit", "value": "percentunit"},
                    {"id": "custom.displayMode", "value": "gradient-gauge"},
                    {"id": "custom.width", "value": 150},
                    {"id": "decimals", "value": 1},
                    {"id": "min", "value": 0},
                    {"id": "max", "value": 1},
                    {"id": "color", "value": {"mode": "thresholds"}},
                    {"id": "thresholds", "value": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 0.7},
                            {"color": "red", "value": 0.9}
                        ]
                    }}
                ]
                break
        if not cpu_usage_found:
            overrides.append({
                "matcher": {"id": "byName", "options": "CPU Usage"},
                "properties": [
                    {"id": "unit", "value": "percentunit"},
                    {"id": "custom.displayMode", "value": "gradient-gauge"},
                    {"id": "custom.width", "value": 150},
                    {"id": "decimals", "value": 1},
                    {"id": "min", "value": 0},
                    {"id": "max", "value": 1},
                    {"id": "color", "value": {"mode": "thresholds"}},
                    {"id": "thresholds", "value": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 0.7},
                            {"color": "red", "value": 0.9}
                        ]
                    }}
                ]
            })
        print("  ✓ CPU Usage: gradient progress bar (green→yellow→red)")

        # Memory Usage - PROGRESS BAR with gradient
        mem_usage_found = False
        for override in overrides:
            if override['matcher'].get('options') == 'Memory Usage':
                mem_usage_found = True
                override['properties'] = [
                    {"id": "unit", "value": "percentunit"},
                    {"id": "custom.displayMode", "value": "gradient-gauge"},
                    {"id": "custom.width", "value": 150},
                    {"id": "decimals", "value": 1},
                    {"id": "min", "value": 0},
                    {"id": "max", "value": 1},
                    {"id": "color", "value": {"mode": "thresholds"}},
                    {"id": "thresholds", "value": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 0.75},
                            {"color": "red", "value": 0.9}
                        ]
                    }}
                ]
                break
        if not mem_usage_found:
            overrides.append({
                "matcher": {"id": "byName", "options": "Memory Usage"},
                "properties": [
                    {"id": "unit", "value": "percentunit"},
                    {"id": "custom.displayMode", "value": "gradient-gauge"},
                    {"id": "custom.width", "value": 150},
                    {"id": "decimals", "value": 1},
                    {"id": "min", "value": 0},
                    {"id": "max", "value": 1},
                    {"id": "color", "value": {"mode": "thresholds"}},
                    {"id": "thresholds", "value": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 0.75},
                            {"color": "red", "value": 0.9}
                        ]
                    }}
                ]
            })
        print("  ✓ Memory Usage: gradient progress bar (green→yellow→red)")

        # Disk Usage - PROGRESS BAR with gradient
        disk_usage_found = False
        for override in overrides:
            if override['matcher'].get('options') == 'Disk Usage':
                disk_usage_found = True
                override['properties'] = [
                    {"id": "unit", "value": "percentunit"},
                    {"id": "custom.displayMode", "value": "gradient-gauge"},
                    {"id": "custom.width", "value": 150},
                    {"id": "decimals", "value": 1},
                    {"id": "min", "value": 0},
                    {"id": "max", "value": 1},
                    {"id": "color", "value": {"mode": "thresholds"}},
                    {"id": "thresholds", "value": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 0.7},
                            {"color": "red", "value": 0.9}
                        ]
                    }}
                ]
                break
        if not disk_usage_found:
            overrides.append({
                "matcher": {"id": "byName", "options": "Disk Usage"},
                "properties": [
                    {"id": "unit", "value": "percentunit"},
                    {"id": "custom.displayMode", "value": "gradient-gauge"},
                    {"id": "custom.width", "value": 150},
                    {"id": "decimals", "value": 1},
                    {"id": "min", "value": 0},
                    {"id": "max", "value": 1},
                    {"id": "color", "value": {"mode": "thresholds"}},
                    {"id": "thresholds", "value": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 0.7},
                            {"color": "red", "value": 0.9}
                        ]
                    }}
                ]
            })
        print("  ✓ Disk Usage: gradient progress bar (green→yellow→red)")

        # Disk I/O - clean number with unit
        for override in overrides:
            if override['matcher'].get('options') == 'Disk I/O':
                for prop in override['properties']:
                    if prop['id'] == 'custom.width':
                        prop['value'] = 100
        print("  ✓ Disk I/O: Bps (100px)")

        # Network I/O - clean number with unit
        for override in overrides:
            if override['matcher'].get('options') == 'Network I/O':
                for prop in override['properties']:
                    if prop['id'] == 'custom.width':
                        prop['value'] = 110
        print("  ✓ Network I/O: Bps (110px)")

        # Set table height
        panel['gridPos']['h'] = 11
        print("  ✓ Table height: 11")

        break

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Beszel-style table design complete!")
print("\nTable layout:")
print("Status (🟢) | Name | vCPUs | Memory | Disk | CPU [▓▓▓░░] | Memory [▓▓▓░░] | Disk [▓▓▓░░] | Disk I/O | Net I/O")
