# pip install "psycopg[binary]"
import json, os, re, hashlib, unicodedata, psycopg
from db_config import psycopg_dsn

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE if os.path.basename(HERE) == "islamic_data" else os.path.join(HERE, "islamic_data")
SOURCES = [
    os.path.join(BASE, "islamic_knowledge_base_ready3.jsonl"),
    os.path.join(BASE, "translations_unified.jsonl"),
]

SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS passages (
    id                      TEXT PRIMARY KEY,
    type                    TEXT NOT NULL,
    lang                    TEXT NOT NULL DEFAULT 'ar',
    source                  TEXT NOT NULL,
    reference               TEXT,
    surah                   INT,
    ayah                    INT,
    text                    TEXT NOT NULL,
    text_norm               TEXT NOT NULL,
    authenticity            TEXT,
    grade                   TEXT,
    translation_of_type     TEXT,
    translation_of_book_id  INT,
    attribution             TEXT,
    url                     TEXT,
    char_len                INT,
    meta                    JSONB
);
ALTER TABLE passages ADD COLUMN IF NOT EXISTS lang TEXT NOT NULL DEFAULT 'ar';
ALTER TABLE passages ADD COLUMN IF NOT EXISTS translation_of_type TEXT;
ALTER TABLE passages ADD COLUMN IF NOT EXISTS translation_of_book_id INT;
CREATE INDEX IF NOT EXISTS idx_passages_type ON passages (type);
CREATE INDEX IF NOT EXISTS idx_passages_lang ON passages (lang);
CREATE INDEX IF NOT EXISTS idx_passages_ayah ON passages (surah, ayah);
CREATE INDEX IF NOT EXISTS idx_passages_fts
    ON passages USING GIN (to_tsvector('simple', text_norm));
"""

TASHKEEL = re.compile(r"[\u064B-\u065F\u0670\u0640]")

def normalize(t, lang):
    t = unicodedata.normalize("NFKC", t)
    if lang == "ar":
        t = TASHKEEL.sub("", t)
        t = re.sub("[إأآٱ]", "ا", t)
        t = t.replace("ى", "ي").replace("ة", "ه")
    else:
        t = t.lower()
    return re.sub(r"\s+", " ", t).strip()

def to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None

def nz(s):
    return s.replace("\x00", "") if isinstance(s, str) else s

MAIN = {"type", "lang", "text", "source", "reference", "surah", "ayah", "authenticity",
        "grade", "attribution", "url", "translation_of_type", "translation_of_book_id"}

def rows():
    seen = set()
    for path in SOURCES:
        if not os.path.exists(path):
            print("غير موجود (تخطّيته):", path)
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                lang = r.get("lang") or "ar"
                text = nz(r["text"])
                key = "|".join([r["type"], lang, r.get("source", ""), str(r.get("reference", "")), text])
                rid = hashlib.sha1(key.encode("utf-8")).hexdigest()
                if rid in seen:
                    continue
                seen.add(rid)
                meta = {k: v for k, v in r.items() if k not in MAIN}
                yield (
                    rid, r["type"], lang, nz(r.get("source", "")), str(r.get("reference", "")),
                    to_int(r.get("surah")), to_int(r.get("ayah")),
                    text, normalize(text, lang),
                    r.get("authenticity") or None, nz(r.get("grade")) or None,
                    r.get("translation_of_type") or None, to_int(r.get("translation_of_book_id")),
                    r.get("attribution") or None, r.get("url") or None,
                    len(text), nz(json.dumps(meta, ensure_ascii=False)),
                )

if __name__ == "__main__":
    with psycopg.connect(psycopg_dsn()) as conn:
        conn.execute(SCHEMA)
        conn.execute("""CREATE TEMP TABLE passages_staging (
            id text, type text, lang text, source text, reference text, surah int, ayah int,
            text text, text_norm text, authenticity text, grade text, translation_of_type text,
            translation_of_book_id int, attribution text, url text, char_len int, meta jsonb
        ) ON COMMIT DROP""")
        n = 0
        with conn.cursor() as cur:
            with cur.copy(
                "COPY passages_staging (id, type, lang, source, reference, surah, ayah, text, text_norm, "
                "authenticity, grade, translation_of_type, translation_of_book_id, "
                "attribution, url, char_len, meta) FROM STDIN"
            ) as copy:
                for row in rows():
                    copy.write_row(row)
                    n += 1
        conn.execute("""INSERT INTO passages
            (id,type,lang,source,reference,surah,ayah,text,text_norm,authenticity,grade,
             translation_of_type,translation_of_book_id,attribution,url,char_len,meta)
            SELECT id,type,lang,source,reference,surah,ayah,text,text_norm,authenticity,grade,
             translation_of_type,translation_of_book_id,attribution,url,char_len,meta
            FROM passages_staging ON CONFLICT (id) DO NOTHING""")
        conn.commit()
        print("Processed", n, "source records; existing IDs were preserved without overwrite.")
        for t, l, c in conn.execute(
            "SELECT type, lang, count(*) FROM passages GROUP BY 1, 2 ORDER BY 3 DESC"
        ):
            print(f"  {t:20} {l:3} {c}")
