import json, os, re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.basename(HERE) == "islamic_data" else os.path.join(HERE, "islamic_data")
SRC = os.path.join(BASE, "translations_unified.jsonl")

counts, issues, sample = Counter(), defaultdict(Counter), {}
with open(SRC, encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        k = (r["lang"], r["source"])
        counts[k] += 1
        t = r["text"]
        if re.search(r"<[^>]+>", t):
            issues[k]["html"] += 1
        if "____" in t:
            issues[k]["footnote_sep"] += 1
        if "*" in t:
            issues[k]["asterisk"] += 1
        if re.match(r"^\s*\(?\d+\s*[.\-)）、:]", t):
            issues[k]["leading_number"] += 1
        if len(t) < 3:
            issues[k]["very_short"] += 1
        if r.get("footnote"):
            issues[k]["has_footnote_field"] += 1
        if r["reference"] == "2:255":
            sample[k] = t[:160].replace("\n", " ")

for k, n in counts.items():
    print(f"{k[0]:3} {n:6}  {k[1]}  issues={dict(issues[k])}")

print("\nآية الكرسي (2:255):")
for k, t in sample.items():
    print(f"[{k[0]}] {t}")