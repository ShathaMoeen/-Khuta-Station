from app.scripts.ingest_data import chunk_passage, chunk_text


def test_deterministic_generic_chunking_preserves_overlap():
    text = 'word ' * 700
    first = chunk_text(text, size=1200, overlap=150)
    second = chunk_text(text, size=1200, overlap=150)
    assert first == second
    assert len(first) > 1
    assert first[0][-150:].strip() == first[1][:150].strip()


def test_quran_and_translation_preserve_verse_boundaries():
    exact_text = '  بِسْمِ اللَّهِ\nexact verse text  '
    verse = {'id': 'p1', 'source': 'Hafs', 'reference': '96:1', 'lang': 'ar', 'type': 'quran', 'level': None, 'text': exact_text}
    assert len(chunk_passage(verse)) == 1
    assert chunk_passage(verse)[0]['chunk_text'] == exact_text
    translated = {**verse, 'type': 'quran_translation', 'lang': 'en'}
    assert len(chunk_passage(translated)) == 1
    assert chunk_passage(translated)[0]['reference'] == '96:1'


def test_hadith_record_stays_complete_and_long_text_is_flagged():
    row = {'id': 'h1', 'source': 'Bukhari', 'reference': 'bukhari:3', 'lang': 'ar', 'type': 'hadith', 'level': None, 'text': 'chain and matn ' * 120}
    pieces = chunk_passage(row, size=120, overlap=15)
    assert len(pieces) == 1
    assert pieces[0]['chunk_text'] == row['text']
    assert pieces[0]['review_required'] is True
    assert pieces[0]['review_reason'] == 'unusually_long_hadith'


def test_tafsir_splits_deterministically_at_paragraphs():
    row = {'id': 't1', 'source': 'Tafsir', 'reference': '3:123', 'lang': 'ar', 'type': 'tafsir', 'level': None, 'text': ('first explanation. ' * 30) + '\n\n' + ('second explanation. ' * 30)}
    a = chunk_passage(row, size=180, overlap=20)
    b = chunk_passage(row, size=180, overlap=20)
    assert a == b
    assert len(a) > 1
    assert all(p['passage_id'] == 't1' and p['reference'] == '3:123' and p['chunk_index'] == i for i,p in enumerate(a))
    assert all(p['source'] == 'Tafsir' and p['language'] == 'ar' and p['content_type'] == 'tafsir' for p in a)

