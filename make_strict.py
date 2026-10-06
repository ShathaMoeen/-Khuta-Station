import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.basename(HERE) == "islamic_data" else os.path.join(HERE, "islamic_data")
SRC = os.path.join(BASE, "islamic_knowledge_base.jsonl")
OUT = os.path.join(BASE, "islamic_knowledge_base_strict.jsonl")

kept = dropped = 0
with open(SRC, encoding="utf-8") as f, open(OUT, "w", encoding="utf-8") as out:
    for line in f:
        r = json.loads(line)
        if r["type"] == "hadith" and not r.get("sahihayn"):
            dropped += 1
            continue
        out.write(line)
        kept += 1

print(f"محفوظ: {kept} | محذوف (أحاديث بلا حكم): {dropped}")
print("الملف:", OUT)