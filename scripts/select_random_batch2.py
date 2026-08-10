import pickle
import json
import os
import random

OUT_DIR = "/tmp/claude-0/-home-user-comfort-choice-helper/df71759e-1127-5ed0-ab07-ff2e70e7a1bc/scratchpad"
CACHE_PATH = os.path.join(OUT_DIR, "all_episodes_cache.pkl")
TEXT_DIR = os.path.join(OUT_DIR, "episode_texts_random2")
os.makedirs(TEXT_DIR, exist_ok=True)

ALREADY_CODED_CHRONO = 40  # V2EP001-040
N_RANDOM = 40

with open(CACHE_PATH, "rb") as f:
    all_episodes = pickle.load(f)

prev_random_meta = json.load(open(os.path.join(OUT_DIR, "episodes_meta_random40.json"), encoding="utf-8"))
already_random_admission_sets = {tuple(sorted(m["admission_nos"])) for m in prev_random_meta}

pool = [
    ep for i, ep in enumerate(all_episodes)
    if i >= ALREADY_CODED_CHRONO and tuple(sorted(ep["admission_nos"])) not in already_random_admission_sets
]
print(f"total in cache: {len(all_episodes)}, excluding first {ALREADY_CODED_CHRONO} chrono + {len(already_random_admission_sets)} already-random, pool size: {len(pool)}")

random.seed()
sample = random.sample(pool, N_RANDOM)
sample.sort(key=lambda e: e["start"])

meta = []
for i, ep in enumerate(sample):
    episode_id = f"RND2EP{i+1:03d}"
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

meta_path = os.path.join(OUT_DIR, "episodes_meta_random2_40.json")
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print(f"random sample: {len(meta)} episodes")
print(f"meta written to {meta_path}")
for m in meta:
    print(m["episode_id"], m["admission_nos"], m["entry_date"], "linked" if m["linked"] else "")
