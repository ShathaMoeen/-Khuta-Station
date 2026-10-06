import csv, psycopg
from pathlib import Path
from db_config import psycopg_dsn

CSV_FILE = Path(__file__).with_name("stations.csv")

def clean(v):
    v = (v or "").strip()
    return v or None

with open(CSV_FILE, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

if any('تجريبي' in (r.get('body') or '') or 'sample' in (r.get('source_note') or '').lower() for r in rows):
    raise RuntimeError('stations.csv contains sample placeholder text and must not be imported.')

with psycopg.connect(psycopg_dsn()) as conn:
    for r in rows:
        lang = (r.get("lang") or "ar").strip()
        level = (r.get("level") or "beginner").strip()
        code = r["code"].strip()

        if lang == "ar":
            # بيانات المحطة الأساسية تؤخذ من الصف العربي فقط
            inserted = conn.execute(
                "INSERT INTO app.stations (code, name, topic, location) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (code) DO NOTHING RETURNING id",
                (code, r["name"].strip(), clean(r.get("topic")), clean(r.get("location"))),
            ).fetchone()
        else:
            # الصفوف بلغات أخرى: ننشئ المحطة إن لم توجد، ولا نغيّر بياناتها
            inserted = conn.execute(
                "INSERT INTO app.stations (code, name, topic, location) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (code) DO NOTHING RETURNING id",
                (code, r["name"].strip(), clean(r.get("topic")), clean(r.get("location"))),
            ).fetchone()
        station_id = inserted[0] if inserted else conn.execute(
            "SELECT id FROM app.stations WHERE code = %s", (code,)
        ).fetchone()[0]

        exists = conn.execute(
            "SELECT 1 FROM app.station_content WHERE station_id = %s AND lang = %s AND level = %s LIMIT 1",
            (station_id, lang, level),
        ).fetchone()
        if exists:
            continue
        conn.execute(
            "INSERT INTO app.station_content (station_id, lang, level, title, body, source_note) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (station_id, lang, level, clean(r.get("title")), r["body"].strip(), clean(r.get("source_note"))),
        )
    conn.commit()
    print("تم تحميل", len(rows), "صف")
    for row in conn.execute(
        "SELECT s.code, s.name, count(c.id) FROM app.stations s "
        "LEFT JOIN app.station_content c ON c.station_id = s.id GROUP BY 1, 2 ORDER BY 1"
    ):
        print(row)
