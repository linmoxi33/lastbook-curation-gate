import json
from pathlib import Path


def item(n, page=None):
    d = {"doc": "doc-%02d" % n, "label": "Reading %d" % n, "note": "What page %d describes." % n}
    if page is not None:
        d["page"] = page
    return d


def topic(tid, mode="now"):
    t = {
        "id": tid,
        "mode": mode,
        "title": "Title for %s" % tid,
        "short": "Short line",
        "intro": "One plain sentence about %s." % tid,
        "keywords": [tid, "kit", "plan"],
        "choices": [{"id": "main", "label": "Something happened", "hint": "A situation",
                     "read": [item(1, 4)]}],
        "limits": [{"text": "Stop and get trained help.", "doc": "doc-02", "page": 7}],
        "prepare": [item(3, 1), item(4, 2), item(5, 3)],
        "learn": [item(6), item(7), item(8), item(9)],
        "related": [],
    }
    if mode == "learn":
        t["choices"] = []
        t["route"] = [{"title": "Step 1: start", "goal": "Learn the basics", "read": [item(10, 5)]}]
    return t


def write_pack(root, topics, gaps=None):
    root = Path(root)
    tdir = root / "topics"
    tdir.mkdir(parents=True, exist_ok=True)
    for tid, data in topics.items():
        (tdir / ("%s.json" % tid)).write_text(json.dumps(data, indent=1), encoding="utf-8")
    if gaps is None:
        gaps = {tid: {"missing": [], "disagree": []} for tid in topics}
    gpath = root / "gaps.json"
    gpath.write_text(json.dumps(gaps, indent=1), encoding="utf-8")
    return tdir, gpath
