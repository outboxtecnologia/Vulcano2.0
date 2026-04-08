import sys
import json
sys.path.append('backend')
from main import get_vulcano_recebimentos

data = get_vulcano_recebimentos(959)
with open('backend/dump_rec.json', 'w', encoding='utf-8') as f:
    json.dump(data[:2], f, indent=2)
