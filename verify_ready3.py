import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.basename(HERE) == "islamic_data" else os.path.join(HERE, "islamic_data")
SRC = os.path.join(BASE, "islamic_knowledge_base_ready3.jsonl")

HDR_LIKE = re.compile(r"^.{0,50}?(?<!\d)\d{3,4}(?!\d)\s")
PUA = re.compile(r"[\ue000-\uf8ff]")
MASALA_BAD = re.compile(r"الم\d{1,4}س")
FAQ_TOTAL = 0
c = {"hdr_like": 0, "pua": 0, "masala_bad": 0, "no_verses": 0}
samples = []

with open(SRC, encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r["type"] != "faq_shubuhat":
            continue
        FAQ_TOTAL += 1
        t = r["text"]
        if HDR_LIKE.match(t):
            c["hdr_like"] += 1
            if len(samples) < 5:
                samples.append(t[:90].replace("\n", " "))
        if PUA.search(t):
            c["pua"] += 1
        if MASALA_BAD.search(t):
            c["masala_bad"] += 1
        if r.get("quran_verses_missing"):
            c["no_verses"] += 1

print("مقاطع بينات:", FAQ_TOTAL)
print(c)
print("\nعيّنات تبدأ بشكل يشبه الترويسة:")
for s in samples:
    print(" ", s)