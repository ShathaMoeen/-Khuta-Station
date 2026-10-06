import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.basename(HERE) == "islamic_data" else os.path.join(HERE, "islamic_data")
SRC = os.path.join(BASE, "islamic_knowledge_base_ready.jsonl")
OUT = os.path.join(BASE, "islamic_knowledge_base_ready2.jsonl")

# الخطوة 1: اتركيها None لتشاهدي الصفحات، ثم ضعي رقم أول صفحة فيها محتوى فعلي
START_PAGE = 22
PREVIEW_UNTIL = 60

def page_of(ref):
    m = re.search(r"\d+", str(ref))
    return int(m.group()) if m else None

if START_PAGE is None:
    seen = set()
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["type"] != "faq_shubuhat":
                continue
            p = page_of(r.get("reference"))
            if p and p <= PREVIEW_UNTIL and p not in seen:
                seen.add(p)
                print(f"ص {p}: {r['text'][:110]!r}")
    print("\nحددي START_PAGE ثم أعيدي التشغيل.")
else:
    kept = dropped = 0
    with open(SRC, encoding="utf-8") as f, open(OUT, "w", encoding="utf-8") as out:
        for line in f:
            r = json.loads(line)
            if r["type"] == "faq_shubuhat":
                p = page_of(r.get("reference"))
                if p is not None and p < START_PAGE:
                    dropped += 1
                    continue
            out.write(line)
            kept += 1
    print(f"محفوظ: {kept} | محذوف (مقدمة): {dropped}")
    print("الملف:", OUT)