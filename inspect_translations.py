import json, os, zipfile, requests

URL = "https://quranpedia.net/dumps/translations-all.zip"
OUT = os.path.join("islamic_data", "quranpedia")
os.makedirs(OUT, exist_ok=True)
ZIP = os.path.join(OUT, "translations-all.zip")

if not os.path.exists(ZIP):
    print("تحميل translations-all.zip ...")
    with requests.get(URL, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(ZIP + ".part", "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    os.replace(ZIP + ".part", ZIP)

def show(obj, indent=0, depth=3):
    pad = " " * indent
    if depth == 0:
        print(pad + "...")
        return
    if isinstance(obj, dict):
        for k, v in list(obj.items())[:8]:
            if isinstance(v, (dict, list)):
                print(f"{pad}{k}: {type(v).__name__} (len={len(v)})")
                show(v, indent + 2, depth - 1)
            else:
                print(f"{pad}{k}: {str(v)[:120]!r}")
    elif isinstance(obj, list) and obj:
        print(f"{pad}[0]:")
        show(obj[0], indent + 2, depth - 1)

# إنجليزي (صحيح إنترناشونال)، تركي (مجمع الملك فهد)، إندونيسي (وزارة الشؤون الإسلامية)،
# أردي، مختصر إنجليزي، مختصر تركي
WANT = ["13638", "1959", "1962", "1966", "27824", "2004"]

with zipfile.ZipFile(ZIP) as z:
    names = z.namelist()
    print("عدد الملفات في الأرشيف:", len(names))
    print("أمثلة:", names[:5])
    for w in WANT:
        match = [n for n in names if os.path.basename(n) == f"{w}.json"]
        if not match:
            print(f"\n{w}: غير موجود")
            continue
        with z.open(match[0]) as f:
            data = json.load(f)
        print(f"\n===== {match[0]} =====")
        print("النوع:", type(data).__name__)
        show(data)