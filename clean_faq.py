import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.basename(HERE) == "islamic_data" else os.path.join(HERE, "islamic_data")
SRC = os.path.join(BASE, "islamic_knowledge_base_final.jsonl")
OUT = os.path.join(BASE, "islamic_knowledge_base_final_clean.jsonl")

AR_LETTER = re.compile(r"[\u0621-\u064A]")
ANY_LETTER = re.compile(r"[^\W\d_]", re.UNICODE)
HEADER_NUM = re.compile(r"^([^\d\n]{0,60}?)\b(\d{1,4})\b\s+")
SENT_PUNCT = "،.؛:؟!؟«»\"()"

def ar_ratio(t):
    letters = ANY_LETTER.findall(t)
    return len(AR_LETTER.findall(t)) / len(letters) if letters else 0

def garbled(t):
    words = t.split()
    if len(words) < 5:
        return False
    return sum(1 for w in words if len(w) == 1) / len(words) > 0.25

def strip_header(t):
    """يقص الترويسة + رقم الصفحة من بداية المقطع إن لم يكن فيها علامات ترقيم."""
    m = HEADER_NUM.match(t)
    if m and not any(c in m.group(1) for c in SENT_PUNCT):
        rest = t[m.end():].strip()
        if len(rest) >= 100:
            return rest, True
    return t, False

kept = dropped = trimmed = 0
dropped_samples, trimmed_samples = [], []

with open(SRC, encoding="utf-8") as f, open(OUT, "w", encoding="utf-8") as out:
    for line in f:
        r = json.loads(line)
        if r["type"] == "faq_shubuhat":
            t = r["text"]
            if ar_ratio(t) < 0.5 or garbled(t):
                dropped += 1
                if len(dropped_samples) < 3:
                    dropped_samples.append(t[:120].replace("\n", " "))
                continue
            new_t, changed = strip_header(t)
            if changed:
                trimmed += 1
                if len(trimmed_samples) < 3:
                    trimmed_samples.append((t[:70].replace("\n", " "), new_t[:70].replace("\n", " ")))
                r["text"] = new_t
        out.write(json.dumps(r, ensure_ascii=False) + "\n")
        kept += 1

print(f"محفوظ: {kept} | محذوف (تالف): {dropped} | مقصوص الترويسة: {trimmed}")
print("\nعيّنات المحذوف:")
for s in dropped_samples:
    print(" ", s)
print("\nعيّنات المقصوص (قبل -> بعد):")
for a, b in trimmed_samples:
    print("  قبل:", a)
    print("  بعد:", b, "\n")
print("الملف:", OUT)