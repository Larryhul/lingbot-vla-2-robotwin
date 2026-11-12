"""Build the contest results JSON from our eval TSV files, using the teammate's results_template.json layout.

usage: python make_results_json.py <template.json> <clean.tsv> <randomized.tsv> <model_id> <out.json> [key=value ...]
TSV columns (from shared_eval.sh): label, cfg, task, "Final batch success rate: a/b = x%", vk_fail=N
Tasks with no valid result stay status=not_run (never counted as success).
"""
import json
import re
import sys


def read_tsv(path):
    res = {}
    if not path:
        return res
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except FileNotFoundError:
        return res
    for ln in lines:
        parts = ln.split("\t")
        if len(parts) < 4:
            continue
        m = re.search(r"(\d+)/(\d+)\s*=", parts[3])
        if not m:
            continue  # NO_RESULT lines are ignored, the last valid line per task wins
        vk = 0
        if len(parts) > 4:
            mv = re.search(r"vk_fail=(\d+)", parts[4])
            vk = int(mv.group(1)) if mv else 0
        res[parts[2]] = (int(m.group(1)), int(m.group(2)), vk)
    return res


def fill(block, got):
    if got is None:
        block.update(status="not_run", program_errors=None, policy_episodes=None, successes=None, initialization_failures=None)
        return 0, 0
    s, n, vk = got
    block.update(status="done", program_errors=None, policy_episodes=n, successes=s, initialization_failures=vk)
    return s, n


def main():
    tpl, clean_tsv, rand_tsv, model_id, out = sys.argv[1:6]
    extra = dict(a.split("=", 1) for a in sys.argv[6:])
    d = json.load(open(tpl, encoding="utf-8"))
    d["model_id"] = model_id
    d.update(extra)
    clean, rand = read_tsv(clean_tsv), read_tsv(rand_tsv)
    tot = {"clean": [0, 0, 0], "randomized": [0, 0, 0]}
    for t in d["tasks"]:
        for setting, table in (("clean", clean), ("randomized", rand)):
            s, n = fill(t[setting], table.get(t["task"]))
            tot[setting][0] += s
            tot[setting][1] += n
            tot[setting][2] += 1 if n else 0
    json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    for k, (s, n, tasks) in tot.items():
        print(f"{k}: {s}/{n} episodes over {tasks}/{len(d['tasks'])} tasks")


if __name__ == "__main__":
    main()
