import sys
import json
sys.path.append('backend')
from injector_sped import processar_f200

data = processar_f200(959, 2024, 5, dry_run=True)
with open('backend/dump_f200.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
