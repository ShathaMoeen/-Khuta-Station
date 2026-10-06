import json, os, re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.basename(HERE) == "islamic_data" else os.path.join(HERE, "islamic_data")
SRC = os.path.join(BASE, "islamic_knowledge_base_graded.jsonl")

graders, labels = Counter(), Counter()
malik_samples, by_book_labels = [], {}

with open(SRC, encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r["type"] != "hadith" or r.get("sahihayn"):
            continue
        book = r["source"].split(":")[-1]
        for g in r.get("grades", []):
            graders[(book, g.get("grader"))] += 1
            labels[g.get("grade")] += 1
            by_book_labels.setdefault(book, Counter())[g.get("grade")] += 1
        if book == "malik-ar" and len(malik_samples) < 3:
            malik_samples.append((r["reference"], r["grade"], r["grades"][:2]))

print("== أكثر الحكّام حسب الكتاب ==")
for (book, gr), n in graders.most_common(15):
    print(f"  {book:12} {gr}: {n}")

print("\n== أكثر 25 تصنيف حكم ==")
for lab, n in labels.most_common(25):
    print(f"  {lab}: {n}")

print("\n== موطأ مالك: عينات ==")
for s in malik_samples:
    print(" ", s)