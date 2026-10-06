import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.basename(HERE) == "islamic_data" else os.path.join(HERE, "islamic_data")
SRC = os.path.join(BASE, "islamic_knowledge_base_ready2.jsonl")
OUT = os.path.join(BASE, "islamic_knowledge_base_ready3.jsonl")

END_PAGE = 1253  # بعدها استبانة وليس محتوى

PUA = re.compile(r"[\ue000-\uf8ff]")                 # رموز الآيات التي لم تُستخرج
MASALA = re.compile(r"الم(\d{1,4})س")                 # «المسألة N» المشوّهة
HDR = re.compile(r"^(.{0,50}?)(?<!\d)(\d{1,4})(?!\d)\s*", re.S)

def page_of(ref):
    m = re.search(r"\d+", str(ref))
    return int(m.group()) if m else None

stats = {"kept": 0, "tail": 0, "short": 0, "hdr": 0, "pua": 0, "masala": 0}

with open(SRC, encoding="utf-8") as f, open(OUT, "w", encoding="utf-8") as out:
    for line in f:
        r = json.loads(line)
        if r["type"] == "faq_shubuhat":
            page = page_of(r.get("reference"))
            if page is not None and page > END_PAGE:
                stats["tail"] += 1
                continue
            t = r["text"]

            # 1) ترويسة الصفحة: نص قصير ينتهي برقم قريب من رقم الصفحة
            m = HDR.match(t)
            if m and page is not None and abs(int(m.group(2)) - page) <= 1:
                t = t[m.end():]
                stats["hdr"] += 1

            # 2) رموز الآيات غير المقروءة
            if PUA.search(t):
                stats["pua"] += 1
                t = PUA.sub(" ", t)

            # 3) أرقام المسائل وعبارة الجواب
            if MASALA.search(t):
                stats["masala"] += 1
                t = MASALA.sub(lambda mm: f"\n[المسألة {mm.group(1)}] ", t)
            t = t.replace("الجوابم التفصيليّ", "الجواب التفصيليّ")

            t = re.sub(r"[ \t]+", " ", t)
            t = re.sub(r"\n\s*\n+", "\n", t).strip()
            if len(t) < 100:
                stats["short"] += 1
                continue
            r["text"] = t
            r["quran_verses_missing"] = bool(re.search(r"(قال|وقال|قوله|فقال)\s+(تعالى|الله)[^\n]{0,15}[:،]\s*[،.]", t)) or None
        out.write(json.dumps(r, ensure_ascii=False) + "\n")
        stats["kept"] += 1

print(stats)
print("الملف:", OUT)