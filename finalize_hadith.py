import json, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.basename(HERE) == "islamic_data" else os.path.join(HERE, "islamic_data")
SRC = os.path.join(BASE, "islamic_knowledge_base_graded.jsonl")
OUT_FINAL = os.path.join(BASE, "islamic_knowledge_base_final.jsonl")      # للتسليم
OUT_FULL = os.path.join(BASE, "islamic_knowledge_base_full_labeled.jsonl") # للمرجع فقط

# "all": لا يُقبل الحديث إلا إذا اتفق كل الحكّام  |  "majority": يكفي أن يرجّح الأكثر
MODE = "all"

WEAK = ("daif", "da'if", "mawdu", "munkar", "shadh", "batil")
NOT_PROPHETIC = ("mauquf", "muquf", "maqtu")

AR = {
    "sahih": "صحيح",
    "hasan": "حسن",
    "daif": "ضعيف",
    "disputed": "مختلف فيه بين الحكّام",
    "mawquf_maqtu": "موقوف أو مقطوع (ليس مرفوعًا)",
    "unclassified": "غير مصنَّف",
}
KEEP = {"sahih", "hasan"}

def classify(label):
    s = (label or "").lower()
    if any(k in s for k in NOT_PROPHETIC):
        return "mawquf"
    if any(k in s for k in WEAK):
        return "weak"
    if "sahih" in s or "hasan" in s:
        return "good"
    return "other"

def decide(grades):
    items = [(classify(g.get("grade")), g.get("grade", "")) for g in grades]
    items = [(c, l) for c, l in items if c != "other"]
    if not items:
        return "unclassified"
    cats = [c for c, _ in items]
    if "mawquf" in cats:
        return "mawquf_maqtu"
    good = [l for c, l in items if c == "good"]
    weak = [l for c, l in items if c == "weak"]
    def level():
        return "sahih" if all("sahih" in l.lower() for l in good) else "hasan"
    if good and not weak:
        return level()
    if weak and not good:
        return "daif"
    if MODE == "majority":
        if len(good) > len(weak):
            return level()
        if len(weak) > len(good):
            return "daif"
    return "disputed"

stats, kept_by_book = Counter(), Counter()
disputed_samples = []

with open(SRC, encoding="utf-8") as f, \
     open(OUT_FINAL, "w", encoding="utf-8") as fin, \
     open(OUT_FULL, "w", encoding="utf-8") as full:
    for line in f:
        r = json.loads(line)
        if r["type"] == "hadith":
            if r.get("sahihayn"):
                auth, basis = "sahih", "الصحيحان"
            else:
                auth, basis = decide(r.get("grades", [])), "أحكام الحكّام المذكورة في حقل grades"
            r["authenticity"] = auth
            r["authenticity_ar"] = AR[auth]
            r["authenticity_basis"] = basis
            stats[auth] += 1
            full.write(json.dumps(r, ensure_ascii=False) + "\n")
            if auth in KEEP:
                fin.write(json.dumps(r, ensure_ascii=False) + "\n")
                kept_by_book[r["source"].split(":")[-1]] += 1
            elif auth == "disputed" and len(disputed_samples) < 3:
                disputed_samples.append((r["reference"], r["grade"]))
        else:
            fin.write(line)
            full.write(line)
            stats[r["type"]] += 1

print("\nتصنيف الأحاديث:", {k: v for k, v in stats.items() if k in AR})
print("غير الأحاديث:", {k: v for k, v in stats.items() if k not in AR})
print("\nالأحاديث المقبولة في الملف النهائي حسب الكتاب:")
for b, n in kept_by_book.most_common():
    print(f"  {b}: {n}")
print("\nعينات من المختلف فيه:")
for s in disputed_samples:
    print(" ", s)
print("\nالنهائي:", OUT_FINAL)
print("الكامل (للمرجع فقط):", OUT_FULL)