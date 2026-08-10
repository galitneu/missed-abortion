import pickle
import json
import os
import sys

OUT_DIR = "/tmp/claude-0/-home-user-comfort-choice-helper/df71759e-1127-5ed0-ab07-ff2e70e7a1bc/scratchpad"
CACHE_PATH = os.path.join(OUT_DIR, "all_episodes_cache.pkl")
TEXT_DIR = os.path.join(OUT_DIR, "episode_texts_v2")
os.makedirs(TEXT_DIR, exist_ok=True)

OFFSET = int(sys.argv[1])
BATCH_SIZE = int(sys.argv[2])

with open(CACHE_PATH, "rb") as f:
    all_episodes = pickle.load(f)

batch = all_episodes[OFFSET:OFFSET + BATCH_SIZE]

meta = []
for i, ep in enumerate(batch):
    idx = OFFSET + i + 1
    episode_id = f"V2EP{idx:03d}"
    block = "\n\n---\n\n".join(
        f"[{r['entry_date'].isoformat()} | {r['unit_name']}]\n{r['text']}" for r in ep["rows"]
    )
    path = os.path.join(TEXT_DIR, episode_id + ".txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(block)
    meta.append(dict(
        episode_id=episode_id,
        admission_nos=ep["admission_nos"],
        linked=ep["linked"],
        link_confidence=ep["link_confidence"],
        age=ep["age"],
        entry_date=ep["start"].isoformat(),
        discharge_date=ep["end"].isoformat(),
        text_file=path,
        n_rows=len(ep["rows"]),
    ))

meta_path = os.path.join(OUT_DIR, f"episodes_meta_v2_batch_{OFFSET}_{OFFSET+BATCH_SIZE}.json")
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print(f"total episodes in cache: {len(all_episodes)}")
print(f"batch [{OFFSET}:{OFFSET+BATCH_SIZE}] -> {len(meta)} episodes")
print(f"meta written to {meta_path}")
for m in meta:
    print(m["episode_id"], m["admission_nos"], m["entry_date"], "linked" if m["linked"] else "")
