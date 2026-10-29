import os, json

with open('backend/benchmarks/ieee_conference_technical_report.md', 'r', encoding='utf-8') as f:
    ieee = f.read()

print('Successfully read IEEE report:', len(ieee))
