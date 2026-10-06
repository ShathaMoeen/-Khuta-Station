import json, os, ast
from collections import Counter
from datasets import load_dataset, get_dataset_config_names

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.basename(HERE) == "islamic_data" else os.path.join(HERE, "islamic_data")
SRC = os.path.join(BASE, "islamic_knowledge_base.jsonl")
OUT = os.path.join(BASE, "islamic_knowledge_base_graded.jsonl")
REPO = "quranlab/hadith"

def parse_grades(v):
    if isinstance(v, list):
        return v
    if isinstance(v, str) and v.strip():
        for fn in (json.loads, ast.literal_eval):
            try:
                out = fn(v)
                return out if isinstance(out, list) else []
            except Exception:
                pass
    return []

# 1) جمع الأحكام من كل المجموعات العربية
grades_map = {}
cfgs = [c for c in get_dataset_config_names(REPO)
        if c.endswith("-ar") and not c.startswith("hadeethenc")]
for cfg in cfgs:
    ds = load_dataset(REPO, cfg, split="train")
    n = 0
    for row in ds:
        gl = parse_grades(row.get("grades"))
        if gl:
            grades_map[row["hadith_key"]] = {
                "summary": row.get("grade_summary") or "",
                "grades": gl,
            }
            n += 1
    print(f"{cfg}: {n} حديثًا له حكم")

# 2) دمج الأحكام وكتابة الملف الجديد
stats, graded_by_book, dropped = Counter(), Counter(), 0
with open(SRC, encoding="utf-8") as f, open(OUT, "w", encoding="utf-8") as out:
    for line in f:
        r = json.loads(line)
        if r["type"] == "hadith":
            info = grades_map.get(r.get("reference"))
            if info:
                r["grade"] = info["summary"]
                r["grades"] = info["grades"]
                r["graded"] = True
                graded_by_book[r["source"].split(":")[-1]] += 1
            else:
                r["graded"] = False
            if r.get("sahihayn") and not r["grade"]:
                r["grade"] = "من الصحيحين"
            if not (r.get("sahihayn") or r["graded"]):
                dropped += 1
                continue
        out.write(json.dumps(r, ensure_ascii=False) + "\n")
        stats[r["type"]] += 1

print("\nالمجموع:", dict(stats))
print("أحاديث لها حكم (خارج الصحيحين) حسب الكتاب:")
for b, n in graded_by_book.most_common():
    print(f"  {b}: {n}")
print("محذوف (بلا حكم):", dropped)
print("الملف:", OUT)