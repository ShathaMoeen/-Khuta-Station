import json, os, re, random
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.basename(HERE) == "islamic_data" else os.path.join(HERE, "islamic_data")
SRC = os.path.join(BASE, "islamic_knowledge_base_final.jsonl")

AR = re.compile(r"[\u0600-\u06FF]")
by_type = defaultdict(list)

with open(SRC, encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        by_type[r["type"]].append(r)

for t, rows in by_type.items():
    lens = [len(r["text"]) for r in rows]
    low_ar = 0
    for r in rows:
        txt = re.sub(r"\s+", "", r["text"])
        if txt and len(AR.findall(txt)) / len(txt) < 0.5:
            low_ar += 1
    print(f"{t:14} عدد={len(rows):6} متوسط الطول={sum(lens)//len(lens):5} "
          f"أقصر={min(lens)} أطول={max(lens)} | نسبة العربية <50%: {low_ar}")

print("\n--- عيّنات من بينات ---")
for r in random.sample(by_type["faq_shubuhat"], 3):
    print(f"[ص {r.get('reference')}]", r["text"][:250].replace("\n", " "))
    print()