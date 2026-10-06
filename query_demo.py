import psycopg
from db_config import psycopg_dsn

with psycopg.connect(psycopg_dsn()) as conn:
    # 1) هل pgvector جاهز؟
    ext = conn.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'").fetchall()
    print("pgvector:", "مثبّت" if ext else "غير مفعّل بعد")

    # 2) آية الكرسي بكل اللغات
    print("\n=== آية الكرسي 2:255 ===")
    for t, lang, txt in conn.execute(
        "SELECT type, lang, left(text, 70) FROM passages "
        "WHERE reference = '2:255' AND type IN ('quran', 'quran_translation') ORDER BY lang"
    ):
        print(f"[{lang}] {txt}")

    # 3) بحث نصي بالعربية (بدون تشكيل)
    print("\n=== بحث: الصبر ===")
    for src, ref, txt in conn.execute(
        "SELECT source, reference, left(text, 80) FROM passages "
        "WHERE type = 'quran' AND text_norm LIKE %s LIMIT 5",
        ("%الصبر%",),
    ):
        print(f"{ref} | {txt}")

    # 4) حديث من الصحيحين مع الحكم
    print("\n=== حديث من الصحيحين ===")
    for src, ref, auth, txt in conn.execute(
        "SELECT source, reference, authenticity_ar_flag, left(text, 70) FROM ("
        "  SELECT source, reference, meta->>'authenticity_ar' AS authenticity_ar_flag, text "
        "  FROM passages WHERE type = 'hadith' LIMIT 3"
        ") s"
    ):
        print(f"{ref} | {auth} | {txt}")
    print("\n=== حديث من الصحيحين ===")
    for ref, auth, txt in conn.execute(
        "SELECT reference, meta->>'authenticity_ar', left(text, 70) FROM passages "
        "WHERE type = 'hadith' AND meta->>'sahihayn' = 'true' LIMIT 3"
    ):
        print(f"{ref} | {auth} | {txt}")
        
        
