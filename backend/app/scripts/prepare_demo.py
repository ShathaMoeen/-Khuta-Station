"""Idempotently create KHUTA's five-station, source-traceable demo draft.

Source and rights statuses intentionally remain unverified/needs_review. This script
never writes to public.passages and never generates embeddings.
"""
import argparse
import asyncio
import hashlib
import json
from sqlalchemy import text

STATIONS = [
    ('QURAN-01', 'القرآن الكريم', 'Quran', 'Quran', 'Gallery A'),
    ('WAHY-01', 'بداية الوحي', 'Beginning of Revelation', 'Revelation', 'Gallery A'),
    ('HIJRAH-01', 'الهجرة إلى المدينة', 'Hijrah to Madinah', 'Hijrah', 'Gallery A'),
    ('BADR-01', 'غزوة بدر', 'Battle of Badr', 'Badr', 'Gallery A'),
    ('HADITH-01', 'السنة والحديث', 'Sunnah and Hadith', 'Hadith', 'Gallery A'),
]
LEVELS = ('beginner', 'intermediate', 'advanced')

# KHUTA-authored summaries describe only records and text explicitly present in the
# existing corpus. They remain drafts pending human religious-fact and rights review.
CONTENT = {
'QURAN-01': {
'ar': {
'beginner': ('التعرّف إلى القرآن الكريم', 'اقرأ الآية مع رقم السورة والآية. تعرض هذه المحطة سجلات عربية من المصحف الموجود في قاعدة المعرفة، وتعرض ترجمة إنجليزية في سجل مستقل عند توفرها. قارن المرجع قبل الانتقال إلى الآية التالية.'),
'intermediate': ('قراءة الآيات ومراجعها', 'تتضمن السجلات المختارة الآيتين 1:1 و96:1، ولكل منهما رقم مرجعي واضح. في المجموعة ترجمة إنجليزية مرتبطة بالمرجع نفسه. لاحظ الفرق بين نص الآية وسجل الترجمة، واستعن بمرشد المعرض عند الحاجة إلى تفسير.'),
'advanced': ('النص والمرجع والترجمة', 'تنظم قاعدة المعرفة النص العربي بحسب مرجع السورة والآية، وتخزن الترجمة الإنجليزية كسجل منفصل مرتبط بالمرجع. تستخدم هذه المحطة 1:1 و96:1 أمثلةً على التصفح المرجعي، ولا تعرض الترجمة على أنها تفسير.'),
},
'en': {
'beginner': ('Exploring the Quran', 'Read each verse with its surah and verse reference. This station uses Arabic Quran records already stored in the knowledge base and shows an English translation as a separate record where available. Check the reference as you move between verses.'),
'intermediate': ('Reading verses and references', 'The selected records include verses 1:1 and 96:1, each with a clear reference. The collection also has an English translation record for each selected reference. Notice that the verse and its translation are separate records; ask an exhibit guide when you need interpretation.'),
'advanced': ('Text, reference, and translation', 'The knowledge base organizes Arabic text by surah and verse reference and stores English translations as separate records linked to those references. This station uses 1:1 and 96:1 to demonstrate reference-based navigation; it does not present translation as tafsir.'),
}},
'WAHY-01': {
'ar': {
'beginner': ('بداية الوحي في السجلات', 'تضم قاعدة المعرفة الآيات 96:1–5 بالعربية وبترجمة إنجليزية، كما تضم رواية مسجلة برقم البخاري 3. اقرأ كل سجل مع مرجعه، واسأل مرشد المعرض عن السياق التاريخي أو التفسير.'),
'intermediate': ('مقارنة مراجع بداية الوحي', 'تتيح هذه المحطة قراءة الآيات 96:1–5 إلى جانب رواية البخاري رقم 3 كما وردت في قاعدة المعرفة. يظهر سجل الحديث ضمن مصدر البخاري وتوجد له بيانات تصنيف في السجل. المقارنة هنا بين مراجع وأنواع سجلات، وليست حكماً مستقلاً على الرواية.'),
'advanced': ('تمييز أنواع المصادر', 'تجمع المحطة سجلات قرآنية للآيات 96:1–5 وسجلاً حديثياً مرجعه bukhari:3. الأول مرجعه آية، والثاني مرجعه مجموعة ورقم حديث. افحص نص كل سجل وبياناته كما هي؛ يحتاج العرض التاريخي والتوثيق النهائي إلى مراجعة مختص.'),
},
'en': {
'beginner': ('Beginning of revelation in the records', 'The knowledge base contains Quran verses 96:1–5 in Arabic and English translation, and a report stored as Bukhari no. 3. Read each record with its reference, and ask an exhibit guide about historical context or interpretation.'),
'intermediate': ('Comparing references for the beginning of revelation', 'This station places Quran 96:1–5 alongside the report catalogued as Bukhari no. 3 in the existing database. The Hadith record includes source and classification metadata. This comparison identifies record types and references; it is not an independent ruling on the report.'),
'advanced': ('Distinguishing source types', 'The station links Quran records for 96:1–5 with a Hadith record referenced as bukhari:3. One uses a verse reference and the other a collection-specific report reference. Review each text and its stored metadata; historical presentation and final authentication need specialist review.'),
}},
'HIJRAH-01': {
'ar': {
'beginner': ('الهجرة في الآيات المختارة', 'تذكر الآية 2:218 الذين هاجروا، وتذكر الآية 9:40 الغار. اقرأ الآيات مع مراجعها؛ فهذه أمثلة مختارة من قاعدة المعرفة وليست تسلسلاً تاريخياً كاملاً.'),
'intermediate': ('قراءة إشارات الهجرة', 'تضم المجموعة الآيات 2:218 و8:72 و9:40، وتظهر فيها ألفاظ الهجرة والإيواء ويَرِد ذكر الغار في 9:40. قارن النصوص ومراجعها، ولا تستنتج منها وحدها خطاً زمنياً كاملاً للأحداث.'),
'advanced': ('حدود الاستدلال من الآيات المختارة', 'تربط المحطة الآيات 2:218 و8:72 و9:40 بسجلاتها في المصحف والترجمة. تتيح النصوص ملاحظة ألفاظ الهجرة والإيواء وذكر الغار في 9:40، لكنها لا تكفي وحدها لبناء سرد تاريخي شامل؛ ذلك يحتاج إلى مصادر وسياق ومراجعة مختصين.'),
},
'en': {
'beginner': ('Hijrah in selected verses', 'Verse 2:218 mentions those who emigrated, and verse 9:40 mentions the cave. Read the verses with their references. These are selected records from the knowledge base, not a complete historical timeline.'),
'intermediate': ('Reading references to emigration', 'The collection includes verses 2:218, 8:72, and 9:40. Their text includes language about emigration and support, and 9:40 mentions the cave. Compare the texts and references without treating this selection as a complete chronology.'),
'advanced': ('Limits of a selected-verse reading', 'This station links verses 2:218, 8:72, and 9:40 to their Quran and translation records. Their wording includes emigration, support, and the cave in 9:40. These records alone do not establish a full historical narrative; that requires context, additional sources, and specialist review.'),
}},
'BADR-01': {
'ar': {
'beginner': ('بدر في الآية 3:123', 'تذكر الآية 3:123 بدراً صراحةً. تعرض المحطة معها الآيات 3:124–127 من السورة نفسها؛ اقرأ كل آية مع مرجعها ولا تضف تفاصيل غير موجودة في النص المعروض.'),
'intermediate': ('قراءة مجموعة آيات بدر', 'تتضمن المجموعة الآيات 3:123–127، وتذكر الآية 3:123 بدراً. قارن تسلسل الآيات في النص العربي والترجمة الإنجليزية، وميّز بين ما تقوله السجلات وما يحتاج إلى سياق تاريخي إضافي.'),
'advanced': ('حدود النص القرآني والسياق التاريخي', 'تعرض المحطة الآيات 3:123–127، وتسمّي 3:123 بدرًا صراحةً. النص والترجمة متاحان بحسب المرجع في قاعدة المعرفة. أما التسلسل الزمني والتفاصيل التاريخية الأوسع فتتطلب الرجوع إلى مصادر أخرى ومراجعة مختصين.'),
},
'en': {
'beginner': ('Badr in verse 3:123', 'Verse 3:123 names Badr explicitly. This station also presents verses 3:124–127 from the same surah. Read each verse with its reference, and avoid adding details that are not in the displayed text.'),
'intermediate': ('Reading the selected Badr passage', 'The selected set is Quran 3:123–127, and verse 3:123 explicitly names Badr. Compare the Arabic records with the English translation and separate what these records say from historical context that needs further sources.'),
'advanced': ('Textual references and historical context', 'This station presents verses 3:123–127; verse 3:123 names Badr. Arabic text and translation are available by reference in the knowledge base. Broader chronology and historical details require other sources and specialist review.'),
}},
'HADITH-01': {
'ar': {
'beginner': ('التعرّف إلى سجلات الحديث', 'تضم قاعدة المعرفة سجلاً حديثياً مرجعه bukhari:3، ضمن مصدر مسجل باسم مجموعة البخاري. اقرأ المرجع وبيانات السجل مع النص، واستعن بمختص عند السؤال عن التخريج أو الحكم.'),
'intermediate': ('قراءة المصدر والمرجع', 'تعرض المحطة مثالاً لسجل حديثي مرجعه bukhari:3، وتخزن قاعدة المعرفة المصدر وبيانات التصنيف مع النص. يوضح هذا المثال طريقة الفهرسة فقط؛ ولا تغني بيانات السجل عن مراجعة مختص في الحديث.'),
'advanced': ('المرجع والبيانات الوصفية للحديث', 'يرتبط النص الحديثي في هذه المحطة بمصدر quranlab/hadith:bukhari-ar ومرجع bukhari:3، وتوجد في السجل بيانات وصفية للتصنيف. ينبغي فصل بيانات الفهرسة عن التحقق الحديثي المستقل، ومراجعة الإسناد والمتن على يد مختص.'),
},
'en': {
'beginner': ('Exploring Hadith records', 'The knowledge base includes a Hadith record referenced as bukhari:3 under a source named for the Bukhari collection. Read the reference and record metadata with the text; consult a specialist about sourcing or grading.'),
'intermediate': ('Reading source and reference', 'This station uses a Hadith record referenced as bukhari:3. The database stores its source and classification metadata alongside the text. This demonstrates cataloguing only; the stored fields do not replace specialist Hadith review.'),
'advanced': ('Hadith references and metadata', 'The Hadith text shown here is linked to source quranlab/hadith:bukhari-ar and reference bukhari:3, with classification metadata present in the record. Separate catalogue metadata from independent authentication; specialist review of the chain and text is required.'),
}},
}

# (station, source name, type, references, language)
LINKS = []
def add_links(station, source, typ, refs, lang):
    for ref in refs: LINKS.append((station,source,typ,ref,lang))
for ref in ('1:1','96:1'):
    add_links('QURAN-01','مصحف حفص','quran',[ref],'ar')
    add_links('QURAN-01','Sahih International - English translation','quran_translation',[ref],'en')
for ref in [f'96:{i}' for i in range(1,6)]:
    add_links('WAHY-01','مصحف حفص','quran',[ref],'ar')
    add_links('WAHY-01','Sahih International - English translation','quran_translation',[ref],'en')
add_links('WAHY-01','quranlab/hadith:bukhari-ar','hadith',['bukhari:3'],'ar')
for ref in ('2:218','8:72','9:40'):
    add_links('HIJRAH-01','مصحف حفص','quran',[ref],'ar')
    add_links('HIJRAH-01','Sahih International - English translation','quran_translation',[ref],'en')
for ref in [f'3:{i}' for i in range(123,128)]:
    add_links('BADR-01','مصحف حفص','quran',[ref],'ar')
    add_links('BADR-01','Sahih International - English translation','quran_translation',[ref],'en')
add_links('HADITH-01','quranlab/hadith:bukhari-ar','hadith',['bukhari:3'],'ar')


def key(name, typ):
    return hashlib.sha256(f'{name}|{typ}'.encode()).hexdigest()

async def run():
    from app.db.session import SessionFactory
    async with SessionFactory() as session:
        async with session.begin():
            station_ids = {}
            for code,name,topic,english,location in STATIONS:
                await session.execute(text("""insert into app.stations(code,name,topic,location)
                    values(:code,:name,:topic,:location) on conflict(code) do nothing"""),
                    {'code':code,'name':name,'topic':topic,'location':location})
                station_ids[code] = (await session.execute(text('select id from app.stations where code=:code'),{'code':code})).scalar_one()
            content_ids = {}
            for code, langs in CONTENT.items():
                sid=station_ids[code]
                for lang,levels in langs.items():
                    for level,(title,body) in levels.items():
                        await session.execute(text("""insert into app.station_content(station_id,lang,level,title,body,source_note)
                            select :sid,:lang,:level,:title,:body,:note
                            where not exists(select 1 from app.station_content where station_id=:sid and lang=:lang and level=:level and title=:title)"""),
                            {'sid':sid,'lang':lang,'level':level,'title':title,'body':body,'note':'KHUTA-authored draft; source links are in app.station_content_provenance; awaiting human factual and rights review.'})
                        cid=(await session.execute(text('select id from app.station_content where station_id=:sid and lang=:lang and level=:level and title=:title order by id limit 1'),{'sid':sid,'lang':lang,'level':level,'title':title})).scalar_one()
                        content_ids[(code,lang,level)] = cid
            passage_rows={}
            for code,source,typ,ref,lang in LINKS:
                passage_id=(await session.execute(text("""select id from public.passages where source=:source and type=:type and reference=:reference and lang=:lang order by id limit 1"""),{'source':source,'type':typ,'reference':ref,'lang':lang})).scalar_one_or_none()
                if passage_id is None:
                    raise RuntimeError(f'Missing passage anchor: {source}/{typ}/{ref}/{lang}')
                passage_rows[(code,source,typ,ref,lang)] = passage_id
                await session.execute(text("""insert into app.station_passages(station_id,passage_id,relationship_type,priority,notes)
                    values(:sid,:pid,:relationship,:priority,:notes) on conflict(station_id,passage_id,relationship_type) do nothing"""),
                    {'sid':station_ids[code],'pid':passage_id,'relationship':'primary_reference' if typ!='hadith' else 'related_hadith','priority':0.95 if code!='QURAN-01' else 0.8,'notes':'Exact source/type/reference/language match in existing public.passages; source rights remain needs_review.'})
                source_id=(await session.execute(text('select id from app.content_sources where source_key=:key'),{'key':key(source,typ)})).scalar_one()
                for (content_code,lang,level),cid in content_ids.items():
                    if content_code != code: continue
                    await session.execute(text("""insert into app.station_content_provenance(station_content_id,source_id,reference,source_url,verification_status,rights_status,notes)
                        select :cid,:source,:ref,p.url,'unverified','needs_review',:notes from public.passages p where p.id=:pid
                        on conflict(station_content_id,source_id,reference) do nothing"""),
                        {'cid':cid,'source':source_id,'ref':ref,'notes':'Reference linked to exact existing passage. Source authority and reuse rights have not been independently verified.','pid':passage_id})
            counts=(await session.execute(text("""select
                (select count(*) from app.content_sources)::int sources,
                (select count(*) from app.stations)::int stations,
                (select count(*) from app.station_content)::int contents,
                (select count(*) from app.station_passages)::int mappings,
                (select count(*) from app.station_content_provenance)::int provenance,
                (select count(*) from app.embeddings)::int embeddings,
                (select count(*) from public.passages)::int passages"""))).mappings().one()
            print(json.dumps(dict(counts),ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(run())
