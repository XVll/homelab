#!/usr/bin/env python3
"""
Fix missing Disk Usage column and restore Status header
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Find the table panel (id: 19)
for panel in dashboard['panels']:
    if panel.get('id') == 19:
        print("Fixing Disk Usage column and Status header...")

        # Issue 1: Restore Status header (was empty string)
        org_transform = panel['transformations'][1]['options']
        org_transform['renameByName']['Value #status'] = 'Status'
        print("✓ Restored 'Status' header")

        # Issue 2: Check Disk Usage query (query 6: diskusg_percent)
        # The problem is it only returns data for LXC containers, not QEMU VMs
        # Let's make it work for ALL VMs, not just LXC

        print("\n✓ Current diskusg_percent query (index 6):")
        print(f"  {panel['targets'][6]['expr']}")

        # Fix: Remove type="lxc" filter so it shows for all VMs
        panel['targets'][6]['expr'] = 'sum by (id) (pve_disk_usage_bytes{instance="$instance"} / pve_disk_size_bytes and on (id, instance) pve_guest_info{template!="1"})'

        print("\n✓ Updated diskusg_percent query:")
        print(f"  {panel['targets'][6]['expr']}")
        print("  (Removed type='lxc' filter to show disk usage for ALL VMs)")

        # Make sure Disk Usage is not hidden
        if 'Value #diskusg_percent' in org_transform.get('excludeByName', {}):
            del org_transform['excludeByName']['Value #diskusg_percent']
            print("\n✓ Removed Disk Usage from exclusion list")

        # Verify column order includes Disk Usage
        if 'Value #diskusg_percent' in org_transform.get('indexByName', {}):
            print(f"\n✓ Disk Usage is at position {org_transform['indexByName']['Value #diskusg_percent']} in column order")

        break

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Fixes applied!")
print("\nSummary:")
print("1. Status header restored (fixes emoji value mappings)")
print("2. Disk Usage query fixed to work for ALL VMs (not just LXC)")
print("\nExpected column order:")
print("Status | Name | vCPUs | Memory | Disk | CPU Usage | Memory Usage | Disk Usage | Disk I/O | Network I/O")
