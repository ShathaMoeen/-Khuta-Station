# pip install requests
import gzip, hashlib, json, os, requests

BASE = "https://quranpedia.net/dumps/"
OUT = os.path.join("islamic_data", "quranpedia")
os.makedirs(OUT, exist_ok=True)


FILES = {
    # القرآن والسور
    "mushafs-1.json.gz": "مصحف حفص",
    "surahs.json.gz": "معلومات السور (114)",
    # التفسير: مصادر القرون الأولى (تتوافق مع شرط الوثيقة)
    "tafsir-book-4.json.gz": "جامع البيان في تأويل آي القرآن (الطبري)",
    "tafsir-book-149.json.gz": "تفسير ابن أبي حاتم",
    "tafsir-book-269.json.gz": "تفسير مجاهد",
    "tafsir-book-27755.json.gz": "تفسير مقاتل بن سليمان",
    "tafsir-book-27758.json.gz": "تفسير سفيان الثوري",
    "tafsir-book-27766.json.gz": "تفسير يحيى بن سلام",
    "tafsir-book-295.json.gz": "تفسير ابن المنذر",
    # تفاسير مساندة (متأخرة، اذكري ذلك في الحقول)
    "tafsir-book-136.json.gz": "تفسير القرآن العظيم",
    "tafsir-book-2003.json.gz": "المختصر في تفسير القرآن الكريم",
    # أسباب النزول
    "asbab-book-2919.json.gz": "أسباب نزول القرآن - الواحدي",
    "asbab-book-460.json.gz": "المحرر في أسباب نزول القرآن من خلال الكتب التسعة",
}

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def load_manifest():
    r = requests.get(BASE + "manifest.json", timeout=60)
    r.raise_for_status()
    m = r.json()
    print("نسخة البيانات:", m.get("version"))
    return {f["name"]: f["sha256"] for f in m["files"]}, m.get("version")

def download(name, expected_sha):
    path = os.path.join(OUT, name)
    if os.path.exists(path):
        print("موجود:", name)
        return path
    print("تحميل:", name)
    with requests.get(BASE + name, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(path + ".part", "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    os.replace(path + ".part", path)
    if expected_sha and sha256(path) != expected_sha:
        print("  تنبيه: البصمة لا تطابق قائمة الموقع (ربما تحدّث الملف). راجعيها قبل الاعتماد.")
    return path

def describe(path, label):
    """يطبع بنية الملف لنعرف أسماء الحقول قبل كتابة المحوّل."""
    with gzip.open(path, "rt", encoding="utf-8") as f:
        data = json.load(f)
    print(f"\n=== {label} ({os.path.basename(path)}) ===")
    print("النوع:", type(data).__name__)
    if isinstance(data, dict):
        print("المفاتيح:", list(data.keys())[:15])
        for k, v in list(data.items())[:3]:
            print(" ", k, "->", str(v)[:200])
    elif isinstance(data, list) and data:
        print("عدد العناصر:", len(data))
        print("أول عنصر:", str(data[0])[:400])

if __name__ == "__main__":
    shas, version = load_manifest()
    with open(os.path.join(OUT, "VERSION.txt"), "w", encoding="utf-8") as f:
        f.write(f"Source: https://quranpedia.net (dump version {version})\n")
    for name, label in FILES.items():
        p = download(name, shas.get(name))
        describe(p, label)
    print("\nتم. الملفات في:", OUT)