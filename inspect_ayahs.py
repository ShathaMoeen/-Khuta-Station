# inspect_deep.py
import gzip, json, os

D = os.path.join("islamic_data", "quranpedia")

def load(name):
    with gzip.open(os.path.join(D, name), "rt", encoding="utf-8") as f:
        return json.load(f)

def brief(v, n=300):
    return repr(v)[:n]

# 1) التفسير: أول آية + عناصر content
t = load("tafsir-book-4.json.gz")
a = t["ayahs"][0]
print("== tafsir: ayah keys:", list(a.keys()))
print("content[0] type:", type(a["content"][0]).__name__)
if isinstance(a["content"][0], dict):
    print("content[0] keys:", list(a["content"][0].keys()))
    for k, v in a["content"][0].items():
        print("  ", k, "->", brief(v))
else:
    print("content[0]:", brief(a["content"][0]))
print("content[1]:", brief(a["content"][1]))

# 2) أسباب النزول
s = load("asbab-book-2919.json.gz")
b = s["ayahs"][0]
print("\n== asbab: ayah keys:", list(b.keys()))
print("content[0]:", brief(b["content"][0], 500))

# 3) المصحف
m = load("mushafs-1.json.gz")
d = m["data"]
print("\n== mushaf data keys:", list(d.keys()))
for k, v in d.items():
    if isinstance(v, (list, dict)):
        print(" ", k, type(v).__name__, "len=", len(v))
        first = v[0] if isinstance(v, list) and v else (next(iter(v.items())) if isinstance(v, dict) and v else None)
        print("    first:", brief(first, 400))