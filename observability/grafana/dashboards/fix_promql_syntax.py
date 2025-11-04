#!/usr/bin/env python3
"""
Fix PromQL syntax errors - proper template filtering
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Find the table panel (id: 19)
for panel in dashboard['panels']:
    if panel.get('id') == 19:
        print("Fixing PromQL syntax in table queries...")

        # Query 0: id, name and type - WRONG: {template!="1"}{instance="$instance"}
        panel['targets'][0]['expr'] = 'sum by (id, name, type) (pve_guest_info{instance="$instance",template!="1"})'
        print("✓ Fixed query 0: id, name and type")

        # Query 1: status - WRONG: pve_guest_info{template!="1"}
        panel['targets'][1]['expr'] = 'sum by (id) (pve_up{instance="$instance"} and on (id, instance) pve_guest_info{template!="1"})'
        print("✓ Fixed query 1: status")

        # Query 2: vcpus - WRONG: pve_guest_info{template!="1"}
        panel['targets'][2]['expr'] = 'sum by (id) (pve_cpu_usage_limit{instance="$instance"} and on (id, instance) pve_guest_info{template!="1"})'
        print("✓ Fixed query 2: vcpus")

        # Query 3: memsize - WRONG: pve_guest_info{template!="1"}
        panel['targets'][3]['expr'] = 'sum by (id) (pve_memory_size_bytes{instance="$instance"} and on (id, instance) pve_guest_info{template!="1"})'
        print("✓ Fixed query 3: memsize")

        # Query 4: memusg_percent - needs fixing
        panel['targets'][4]['expr'] = 'sum by (id) (pve_memory_usage_bytes{instance="$instance"} / pve_memory_size_bytes and on (id, instance) pve_guest_info{template!="1"} and on (id) pve_up==1)'
        print("✓ Fixed query 4: memusg_percent")

        # Query 5: disksize - WRONG: pve_guest_info{template!="1"}
        panel['targets'][5]['expr'] = 'sum by (id) (pve_disk_size_bytes{instance="$instance"} and on (id, instance) pve_guest_info{template!="1"})'
        print("✓ Fixed query 5: disksize")

        # Query 6: diskusg_percent - WRONG: {template!="1"}{type="lxc"}
        panel['targets'][6]['expr'] = 'sum by (id) (pve_disk_usage_bytes{instance="$instance"} / pve_disk_size_bytes and on (id, instance) pve_guest_info{template!="1",type="lxc"})'
        print("✓ Fixed query 6: diskusg_percent")

        # Query 7: cpu_usage - WRONG: pve_guest_info{template!="1"}
        panel['targets'][7]['expr'] = 'sum by (id) ((pve_cpu_usage_ratio{instance="$instance"} / pve_cpu_usage_limit) and on (id, instance) pve_guest_info{template!="1"} and on(id) pve_up==1)'
        print("✓ Fixed query 7: cpu_usage")

        # Query 8: disk_io - WRONG: pve_guest_info{template!="1"}
        panel['targets'][8]['expr'] = 'sum by (id) ((rate(pve_disk_write_bytes{instance="$instance"}[5m]) + rate(pve_disk_read_bytes{instance="$instance"}[5m])) and on (id, instance) pve_guest_info{template!="1"} and on(id) pve_up==1)'
        print("✓ Fixed query 8: disk_io")

        # Query 9: network_io - WRONG: pve_guest_info{template!="1"}
        panel['targets'][9]['expr'] = 'sum by (id) ((rate(pve_network_receive_bytes{instance="$instance"}[5m]) + rate(pve_network_transmit_bytes{instance="$instance"}[5m])) and on (id, instance) pve_guest_info{template!="1"} and on(id) pve_up==1)'
        print("✓ Fixed query 9: network_io")

        break

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ All PromQL queries fixed!")
print("\nKey fix: Changed {template!=\"1\"}{instance=\"$instance\"} to {instance=\"$instance\",template!=\"1\"}")
print("All label matchers now in single {} brackets")
