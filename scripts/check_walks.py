"""Check two independently rebuilt scenes for spatial and experimental equivalence."""

import argparse
import csv
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--data", type=Path, required=True)
p.add_argument("--layouts", type=Path, required=True)
p.add_argument("--reference", type=Path)
a = p.parse_args()


def read(path):
    return json.loads(path.read_text())


long, short = (
    read(a.layouts / (name + ".json")) for name in ("main-layout", "control-layout")
)
assert long.keys() == short.keys()
for name, record in long.items():
    other = short[name]
    assert other["moves"] == record["moves"]
    dx = 2.2 if record["moves"] else 0.0
    for original, moved in zip(record["points"], other["points"], strict=True):
        assert all(
            abs(v - u - d) < 0.0001 for u, v, d in zip(original, moved, (dx, 0, 0))
        ), name
traces = []
for size in ("3.30", "1.10"):
    base = "walk-" + size
    with (a.data / (base + ".csv")).open() as stream:
        rows = list(csv.DictReader(stream))
    traces.append(rows)
    report = read(a.data / (base + ".json"))
    assert [int(r["frame"]) for r in rows] == list(range(217, 314)) + list(
        range(337, 458)
    )
    assert (
        abs(
            report["exit"]["exact_seconds"]
            - report["entry"]["exact_seconds"]
            - float(size)
        )
        < 1e-6
    )
    assert report["first_samples_by_min_hits"]["1"]["frame"] == 337
    if a.reference:
        baseline = list(
            csv.DictReader((a.reference / (base + ".csv")).read_text().splitlines())
        )
        assert len(rows) == len(baseline)
        for actual, expected in zip(rows, baseline):
            for key in ("frame", "track", "eye_x_m", "eye_y_m"):
                assert actual[key] == expected[key], (base, key, actual)
            for key in ("dancer_hits", "drummer_hits", "farewell_host_hits"):
                if expected[key]:
                    assert abs(int(actual[key]) - int(expected[key])) <= 3, (
                        base,
                        key,
                        actual,
                    )
for main, control in zip(*traces):
    assert all(
        main[k] == control[k]
        for k in ("track", "frame", "eye_x_m", "eye_y_m", "dancer_hits", "drummer_hits")
    )
print(
    "Verified both camera tracks and paired object extents for", len(long), "objects."
)
