import json, os, random
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.basename(HERE) == "islamic_data" else os.path.join(HERE, "islamic_data")

INPUTS = [
    os.path.join(BASE, "quranpedia_unified.jsonl"),
    os.path.join(BASE, "unified.jsonl"),
]
OUT = os.path.join(BASE, "islamic_knowledge_base.jsonl")

FIELDS = ["type", "text", "source", "reference", "surah", "ayah", "grade", "url", "attribution"]

def hadith_cfg(src):
    return src.split(":", 1)[-1]         

def keep(r):
    t, src = r.get("type"), r.get("source", "")
    if t == "quran":
        return not src.startswith("quranlab/")            
    if t == "tafsir":
        return src not in ("tafsir-tabari-ar", "tafsir-ibnkathir-ar")   
    if t == "hadith":
        return hadith_cfg(src).endswith("-ar")          
    return True

counts, hadith_cfgs, seen = Counter(), Counter(), set()
graded = 0

with open(OUT, "w", encoding="utf-8") as out:
    for path in INPUTS:
        if not os.path.exists(path):
            print("غير موجود (تخطّيته):", os.path.basename(path))
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if not keep(r):
                    continue
                key = (r.get("type"), r.get("source"), r.get("reference"), r.get("text"))
                if key in seen:
                    continue
                seen.add(key)
                rec = {k: r.get(k, "") for k in FIELDS}
                for k, v in r.items():
                    if k not in rec:
                        rec[k] = v
                if rec["type"] == "hadith":
                    cfg = hadith_cfg(rec["source"])
                    rec["sahihayn"] = cfg.startswith(("bukhari", "muslim"))
                    hadith_cfgs[cfg] += 1
                    if rec["grade"]:
                        graded += 1
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                counts[rec["type"]] += 1

print("\nالمجموع حسب النوع:", dict(counts))
print("\nالأحاديث حسب الكتاب:")
for cfg, n in hadith_cfgs.most_common():
    print(f"  {cfg}: {n}")
print(f"\nأحاديث لها حقل درجة: {graded} من {counts['hadith']}")
print("الملف:", OUT)

with open(OUT, encoding="utf-8") as f:
    lines = f.readlines()
for line in random.sample(lines, min(4, len(lines))):
    r = json.loads(line)
    print("\n---", r["type"], "|", r["source"], "|", r["reference"], "|", r.get("grade", ""))
    print(r["text"][:200])