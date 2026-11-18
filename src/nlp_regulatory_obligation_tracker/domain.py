import json
from pathlib import Path

def load_facts(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def summarize(facts):
    return {
        'received': [item['ref'] for item in facts['filings'] if item['issuer'] == facts['publisher']],
        'active_documents': [doc['id'] for doc in facts['documents'] if doc['stage'] == '正式'],
    }
