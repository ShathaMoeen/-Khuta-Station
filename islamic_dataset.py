import json, re, os, requests
from datasets import load_dataset, get_dataset_config_names
from pypdf import PdfReader
from tqdm import tqdm

OUT_DIR = "islamic_data"
os.makedirs(OUT_DIR, exist_ok=True)
OUT_FILE = os.path.join(OUT_DIR, "unified.jsonl")

def pick(row, keys, default=""):
    """يرجع أول حقل موجود من قائمة أسماء محتملة (لأن أسماء الأعمدة تختلف)."""
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return row[k]
    return default

def clean(t):
    return re.sub(r"\s+", " ", str(t)).strip()

records = []

# ---------- 1) الأحاديث: quranlab/hadith ----------
def load_hadith(max_per_config=None):
    repo = "quranlab/hadith"
    configs = get_dataset_config_names(repo)
    print("hadith configs:", configs)
    for cfg in configs:
        # نتجاوز فهرس المجموعات والترجمات، ونأخذ المتن العربي فقط
        if cfg == "collections" or cfg.startswith("hadeethenc-"):
            continue
        try:
            ds = load_dataset(repo, cfg, split="train")
        except Exception as e:
            print("skip", cfg, e)
            continue
        print(cfg, "columns:", ds.column_names)  
        for i, row in enumerate(tqdm(ds, desc=cfg)):
            if max_per_config and i >= max_per_config:
                break
            text = clean(pick(row, ["arabic", "matn", "text", "hadith_ar", "arabic_text"]))
            if len(text) < 20:
                continue
            records.append({
                "type": "hadith",
                "text": text,
                "source": f"quranlab/hadith:{cfg}",
                "reference": clean(pick(row, ["hadith_key", "reference", "number", "hadith_number"])),
                "grade": clean(pick(row, ["grade", "authenticity", "grade_normalized", "ruling"])),
                "url": f"https://huggingface.co/datasets/{repo}",
            })

# ---------- 2) التفسير: quranlab/quran-tafsir ----------
TAFSIR_CONFIGS = ["tafsir-tabari-ar", "tafsir-ibnkathir-ar"]

def load_tafsir():
    repo = "quranlab/quran-tafsir"
    for cfg in TAFSIR_CONFIGS:
        try:
            ds = load_dataset(repo, cfg, split="train")
        except Exception as e:
            print("skip", cfg, e)
            continue
        print(cfg, "columns:", ds.column_names)
        for row in tqdm(ds, desc=cfg):
            text = clean(pick(row, ["text", "tafsir", "content"]))
            if len(text) < 20:
                continue
            records.append({
                "type": "tafsir",
                "text": text,
                "source": cfg,
                "reference": clean(pick(row, ["verse_key", "ayah_key", "verse"])),
                "grade": "",
                "url": f"https://huggingface.co/datasets/{repo}",
            })

# ---------- 3) القرآن (النص العثماني) ----------
def load_quran():
    repo = "quranlab/quran"
    ds = load_dataset(repo, split="train")  
    print("quran columns:", ds.column_names)
    for row in tqdm(ds, desc="quran"):
        text = clean(pick(row, ["text", "arabic", "ayah_text"]))
        if not text:
            continue
        records.append({
            "type": "quran",
            "text": text,
            "source": "quranlab/quran:arabic-uthmani",
            "reference": clean(pick(row, ["verse_key", "ayah_key", "verse"])),
            "grade": "",
            "url": f"https://huggingface.co/datasets/{repo}",
        })

# ---------- 4) كتاب بينات (الشبهات والأسئلة المتكررة) ----------
BAYINAT_PDF = "https://dawa.center/storage/files/AMYj6DfmHlSnZ766Zz0VlBNwmYtdwhAl31XMETlT.pdf"
BAYINAT_PAGE = "https://dawa.center/file/7937"

def load_bayinat(chunk_size=1200):
    path = os.path.join(OUT_DIR, "bayinat.pdf")
    if not os.path.exists(path):
        r = requests.get(BAYINAT_PDF, timeout=120)
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
    reader = PdfReader(path)
    for page_no, page in enumerate(tqdm(reader.pages, desc="bayinat"), start=1):
        text = clean(page.extract_text() or "")
        for j in range(0, len(text), chunk_size):
            chunk = text[j:j + chunk_size]
            if len(chunk) < 100:
                continue
            records.append({
                "type": "faq_shubuhat",
                "text": chunk,
                "source": "بينات: أسئلة وأجوبة عن الإسلام - مركز أصول",
                "reference": f"p.{page_no}",
                "grade": "",
                "url": BAYINAT_PAGE,
            })

# التشغيل 
if __name__ == "__main__":
    load_hadith()      
    load_tafsir()
    load_quran()
    load_bayinat()

    # إزالة التكرار
    seen, final = set(), []
    for r in records:
        key = (r["type"], r["text"])
        if key not in seen:
            seen.add(key)
            final.append(r)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for r in final:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"تم حفظ {len(final)} سجل في {OUT_FILE}")