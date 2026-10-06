import gzip, json, os, re, html, hashlib

# ---------- المسارات ----------
HERE = os.path.dirname(os.path.abspath(__file__))
CANDIDATES = [
    os.path.join(HERE, "islamic_data", "quranpedia"),
    os.path.join(HERE, "quranpedia"),
    os.path.join(os.getcwd(), "islamic_data", "quranpedia"),
]
SRC_DIR = next((p for p in CANDIDATES if os.path.isdir(p)), None)
if not SRC_DIR:
    raise SystemExit("ما لقيت مجلد quranpedia. شغّلي fetch_quranpedia أولًا.")
OUT_FILE = os.path.join(os.path.dirname(SRC_DIR), "quranpedia_unified.jsonl")

MAX_CHARS = 1500  # أقصى طول للمقطع الواحد

# ---------- أدوات ----------
def load(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)

def clean_html(t):
    t = re.sub(r"(?i)<br\s*/?>|</p>|</h[1-6]>|</div>", "\n", t or "")
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t).replace("\ufeff", "")
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    return "\n".join(l.strip() for l in t.split("\n") if l.strip())

def split_text(text, max_chars=MAX_CHARS):
    parts, buf = [], ""
    for para in text.split("\n"):
        while len(para) > max_chars:
            cut = para.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            if buf:
                parts.append(buf)
                buf = ""
            parts.append(para[:cut])
            para = para[cut:].lstrip()
        if buf and len(buf) + len(para) + 1 > max_chars:
            parts.append(buf)
            buf = para
        else:
            buf = (buf + "\n" + para) if buf else para
    if buf:
        parts.append(buf)
    return [p for p in parts if len(p.strip()) >= 20]

# ---------- التفسير وأسباب النزول ----------
def process_book(path, rtype, out, seen):
    data = load(path)
    book = data.get("book", {}) or {}
    version = (data.get("license") or {}).get("version", "")
    book_id = book.get("id")
    name = clean_html(str(book.get("name", "")))
    count = 0
    for a in data.get("ayahs", []):
        surah, ayah = a.get("surah"), a.get("ayah")
        for c in a.get("content", []):
            text = clean_html(c.get("text", ""))
            if len(text) < 20:
                continue
            key = hashlib.md5(
                f"{book_id}|{c.get('part')}|{c.get('page')}|{text}".encode("utf-8")
            ).hexdigest()
            if key in seen:  
                continue
            seen.add(key)
            for i, chunk in enumerate(split_text(text)):
                rec = {
                    "type": rtype,
                    "text": chunk,
                    "source": name,
                    "book_id": book_id,
                    "reference": f"{surah}:{ayah}",
                    "surah": surah,
                    "ayah": ayah,
                    "covers_ayahs": c.get("ayahs"),
                    "part": c.get("part"),
                    "page": c.get("page"),
                    "chunk": i,
                    "url": "https://quranpedia.net",
                    "attribution": f"Quranpedia.net, dump version {version}",
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1
    return count

# ---------- القرآن ----------
def process_quran(path, out):
    data = load(path)
    d = data["data"]
    version = (data.get("license") or {}).get("version", "")
    count = 0
    for s in d["surahs"]:
        for ay in s["ayahs"]:
            text = (ay.get("text") or "").replace("\ufeff", "").strip()
            if not text:
                continue
            rec = {
                "type": "quran",
                "text": text,
                "source": d.get("name", "مصحف حفص"),
                "book_id": d.get("id"),
                "reference": f"{ay.get('surah', s['id'])}:{ay.get('number')}",
                "surah": str(s["id"]),
                "surah_name": s.get("name"),
                "ayah": str(ay.get("number")),
                "juz": ay.get("juz"),
                "page": ay.get("page_number"),
                "url": "https://quranpedia.net",
                "attribution": f"Quranpedia.net, dump version {version}",
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1
    return count

# ---------- التشغيل ----------
if __name__ == "__main__":
    totals, seen = {}, set()
    with open(OUT_FILE, "w", encoding="utf-8") as out:
        for fname in sorted(os.listdir(SRC_DIR)):
            path = os.path.join(SRC_DIR, fname)
            if fname.startswith("tafsir-book-"):
                n = process_book(path, "tafsir", out, seen)
                totals["tafsir"] = totals.get("tafsir", 0) + n
            elif fname.startswith("asbab-book-"):
                n = process_book(path, "asbab_nuzul", out, seen)
                totals["asbab_nuzul"] = totals.get("asbab_nuzul", 0) + n
            elif fname == "mushafs-1.json.gz":
                n = process_quran(path, out)
                totals["quran"] = totals.get("quran", 0) + n
            else:
                continue
            print(f"{fname}: {n} سجل")

    print("\nالمجموع:", totals)
    print("الملف:", OUT_FILE)

    # عيّنة للتأكد
    with open(OUT_FILE, encoding="utf-8") as f:
        for line in list(f)[:1]:
            print("\nعيّنة:", line[:500])