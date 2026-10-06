from datasets import load_dataset, get_dataset_config_names

repo = "quranlab/hadith"
print("configs:", [c for c in get_dataset_config_names(repo) if c.endswith("-ar")][:20])

for cfg in ["bukhari-ar", "abudawud-ar", "collections"]:
    try:
        ds = load_dataset(repo, cfg, split="train")
        print(f"\n== {cfg} ==")
        print("columns:", ds.column_names)
        row = ds[0]
        for k, v in row.items():
            print(f"  {k}: {str(v)[:100]!r}")
    except Exception as e:
        print(cfg, "->", e)