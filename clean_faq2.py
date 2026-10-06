import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.basename(HERE) == "islamic_data" else os.path.join(HERE, "islamic_data")
SRC = os.path.join(BASE, "islamic_knowledge_base_final_clean.jsonl")
OUT = os.path.join(BASE, "islamic_knowledge_base_ready.jsonl")

AR_LETTER = re.compile(r"[\u0621-\u064A]")
ANY_LETTER = re.compile(r"[^\W\d_]", re.UNICODE)

HEADER = re.compile(r"\d{0,4}\s*بينات\s*[-–]\s*أسئلة\s*منتقاة\s*حول\s*الإسلام")
ORG = re.compile(r"[ح©]?\s*جمعية\s*الدعوة\s*والإرشاد\s*وتوعية\s*الجالي\w*")

def ar_ratio(t):
    letters = ANY_LETTER.findall(t)
    return len(AR_LETTER.findall(t)) / len(letters) if letters else 0

def garbled(t):
    words = t.split()
    return len(words) >= 5 and sum(1 for w in words if len(w) == 1) / len(words) > 0.25

def bad(t):
    return (
        "المحتويات" in t
        or t.count("\ufffd") >= 3
        or ar_ratio(t) < 0.5
        or garbled(t)
    )

kept = dropped = header_removed = 0
samples = []

with open(SRC, encoding="utf-8") as f, open(OUT, "w", encoding="utf-8") as out:
    for line in f:
        r = json.loads(line)
        if r["type"] == "faq_shubuhat":
            t = r["text"]
            if bad(t):
                dropped += 1
                continue
            new_t = ORG.sub(" ", HEADER.sub(" ", t))
            new_t = re.sub(r"[ \t]+", " ", new_t).strip()
            if new_t != t:
                header_removed += 1
            if len(new_t) < 100 or bad(new_t):
                dropped += 1
                continue
            r["text"] = new_t
            if len(samples) < 3 and header_removed:
                samples.append(new_t[:160].replace("\n", " "))
        out.write(json.dumps(r, ensure_ascii=False) + "\n")
        kept += 1

print(f"محفوظ: {kept} | محذوف: {dropped} | أُزيلت منها الترويسة: {header_removed}")
print("\nعيّنات بعد التنظيف:")
for s in samples:
    print(" ", s)
print("\nالملف:", OUT)