import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.basename(HERE) == "islamic_data" else os.path.join(HERE, "islamic_data")
SRC = os.path.join(BASE, "islamic_knowledge_base_ready2.jsonl")

pages = {}
with open(SRC, encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r["type"] != "faq_shubuhat":
            continue
        m = re.search(r"\d+", str(r.get("reference")))
        if m:
            pages.setdefault(int(m.group()), r["text"])

last = sorted(pages)[-40:]
for p in last:
    print(f"ص {p}: {pages[p][:100]!r}")