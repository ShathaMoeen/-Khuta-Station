import json, os, re, html, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.basename(HERE) == "islamic_data" else os.path.join(HERE, "islamic_data")
ZIP = os.path.join(BASE, "quranpedia", "translations-all.zip")
OUT = os.path.join(BASE, "translations_unified.jsonl")
CATALOG = os.path.join(BASE, "translations_catalog.txt")

SELECT = {
    "13638": "quran",    # الإنجليزية - Sahih International
    "1959":  "quran",    # التركية - مجمع الملك فهد
    "1962":  "quran",    # الإندونيسية - وزارة الشؤون الإسلامية
    "1966":  "quran",    # الأردية
    "27812": "quran",    # الفرنسية - محمد حميد الله
    "27824": "tafsir",   # المختصر - الإنجليزية
    "2004":  "tafsir",   # المختصر - التركية
    "27825": "tafsir",   # المختصر - الروسية
    "27826": "tafsir",   # المختصر - البنغالية
    "27827": "tafsir",   # المختصر - الصينية
}

# الأصل العربي الذي تترجمه: المصحف (id=1) أو المختصر العربي (book 2003)
ARABIC_BOOK = {"quran": 1, "tafsir": 2003}

def clean(t):
    t = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", t or "")
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    t = re.sub(r"^\s*\(?\d+\s*[.\-)）、:]\s*", "", t)  # ترقيم أول النص: 1. و2) و2、
    t = re.sub(r"[ \t]+", " ", t)
    return "\n".join(l.strip() for l in t.split("\n") if l.strip()).strip()

FOOT_SEP = re.compile(r"\n?_{4,}\n?")

def split_footnote(t):
    parts = FOOT_SEP.split(t, maxsplit=1)
    main = parts[0].strip()
    note = parts[1].strip() if len(parts) > 1 else ""
    if note:
        main = re.sub(r"\s*\*+", "", main).strip()  # علامات الإحالة تُحذف من النص الرئيسي
    return main, note

def version_of(data):
    lic = data.get("license")
    return lic.get("version", "") if isinstance(lic, dict) else ""

with zipfile.ZipFile(ZIP) as z:
    names = sorted(n for n in z.namelist() if n.endswith(".json"))

    # 1) كتالوج بكل الترجمات المتاحة
    with open(CATALOG, "w", encoding="utf-8") as cat:
        for n in names:
            with z.open(n) as f:
                d = json.load(f)
            cat.write(f"{d.get('id')}\t{d.get('locale_code')}\t{d.get('name')}\t{len(d.get('ayahs', []))}\n")
    print("الكتالوج:", CATALOG)

    # 2) بناء الترجمات المختارة
    total = 0
    with open(OUT, "w", encoding="utf-8") as out:
        for tid, kind in SELECT.items():
            match = [n for n in names if os.path.basename(n) == f"{tid}.json"]
            if not match:
                print(f"{tid}: غير موجود")
                continue
            with z.open(match[0]) as f:
                d = json.load(f)
            version = version_of(d)
            n_rec = 0
            for a in d.get("ayahs", []):
                text, note = split_footnote(clean(a.get("translated_text", "")))
                if not text:
                    continue
                s, ay = str(a.get("surah_number")), str(a.get("ayah_number"))
                rec = {
                    "type": "quran_translation" if kind == "quran" else "tafsir_translation",
                    "text": text,
                    "lang": d.get("locale_code"),
                    "lang_name": d.get("language"),
                    "direction": d.get("direction"),
                    "source": d.get("name"),
                    "book_id": d.get("id"),
                    "reference": f"{s}:{ay}",
                    "surah": s,
                    "ayah": ay,
                    "translation_of_type": "quran" if kind == "quran" else "tafsir",
                    "translation_of_book_id": ARABIC_BOOK[kind],
                    "url": "https://quranpedia.net",
                    "attribution": f"Quranpedia.net, dump version {version}",
                }
                if note:
                    rec["footnote"] = note
                rec["translation_description"] = d.get("description")
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n_rec += 1
            total += n_rec
            print(f"\n[{tid}] {d.get('locale_code')} | {d.get('name')} | {n_rec} سجل")
            print("  عيّنة:", split_footnote(clean(d["ayahs"][1].get("translated_text", "")))[0][:120])

print("\nالمجموع:", total)
print("الملف:", OUT)