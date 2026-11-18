# lastbook-curation-gate

Offline gate for Lastbook's curated guides: it enforces the written `content/SCHEMA.md` contract on `content/topics/*.json` and `content/gaps.json` **without** a downloaded library, so guide edits can be checked in CI — while every other check needs the app's data folder. Why now: the 14 guides are the first thing a reader sees in an emergency, and the contract that keeps them short and sourced is currently prose only.

Upstream: https://github.com/Immortal-Protocols/lastbook

## What the upstream is, and what it does not check

Lastbook is an offline survival library (manuals, videos, maps, a local assistant) for macOS, Windows and Linux. Its curated guides live in `content/topics/*.json`; what curators looked for and did not find lives in `content/gaps.json`. `content/SCHEMA.md` states the editorial contract:

- 1–4 readings per choice, 3–8 in `prepare`, 4–10 in `learn` — [SCHEMA.md#L59](https://github.com/Immortal-Protocols/lastbook/blob/HEAD/content/SCHEMA.md#L59)
- a `note` is at most 30 words — [SCHEMA.md#L30](https://github.com/Immortal-Protocols/lastbook/blob/HEAD/content/SCHEMA.md#L30)
- learning tracks carry an ordered `route` — [SCHEMA.md#L9](https://github.com/Immortal-Protocols/lastbook/blob/HEAD/content/SCHEMA.md#L9)
- `intro` is one or two sentences — [SCHEMA.md#L7](https://github.com/Immortal-Protocols/lastbook/blob/HEAD/content/SCHEMA.md#L7)

The upstream checker `tools/validate_topics.py` cannot run without the multi-gigabyte library: it exits early unless `library-data/catalog.json` exists ([L25-L26](https://github.com/Immortal-Protocols/lastbook/blob/HEAD/tools/validate_topics.py#L25-L26)). Even with the library it only checks doc ids, page ranges and labels ([L65-L81](https://github.com/Immortal-Protocols/lastbook/blob/HEAD/tools/validate_topics.py#L65-L81)). None of the counts, note length, route presence, limit traceability or gap-domain coverage above is machine-checked anywhere in the repository.

## What this tool does / does not do

**Does** — parse the same files with Python's standard library and report findings by rule id:

| Rule | Check | Level |
|---|---|---|
| LB01 | `id` equals the file stem | error |
| LB02 | required top-level fields present | error |
| LB03 | `mode` is `now` or `learn` | error |
| LB04 | `learn` topics define a route | error |
| LB05 | each choice offers 1–4 readings | error |
| LB06 | `prepare` holds 3–8 readings | error |
| LB07 | `learn` holds 4–10 readings | error |
| LB08 | `limits` entries carry `text` and a `doc`/`zim` | error |
| LB09 | `note` is at most 30 words | error |
| LB10 | readings carry a `label` and a source | error |
| LB11 | at least 3 unique keywords | error |
| LB12 | a bucket does not list the same source twice | error |
| LB13 | `related` names an existing topic, not itself | error |
| LB14 | `related` links are symmetric | warning |
| LB15 | `intro` is one or two sentences | error |
| LB16 | no dose/quantity in `intro` or choice `hint` | warning |
| LB17 | route steps have title, goal and readings | error |
| LB18 | every gap domain has a topic file, entries are usable | error |
| LB19 | the same gap text is not filed under two domains | warning |
| LB20 | `now` topics offer at least one choice | warning |

**Does not** — resolve doc ids or page numbers against the catalog (that needs the library, and upstream already does it), judge medical correctness, or rewrite files. It is a gate, not a fixer.

## Install

Python 3.8+. No dependencies, no network, no build step.

```bash
git clone git@github-linmoxi33:linmoxi33/lastbook-curation-gate.git
cd lastbook-curation-gate
python3 bin/lastbook-curation-gate check --topics examples/in/content/topics --gaps examples/in/content/gaps.json
```

Against a Lastbook checkout, run it from the repository root:

```bash
python3 bin/lastbook-curation-gate check --topics content/topics --gaps content/gaps.json
```

## Usage and exit codes

```bash
python3 bin/lastbook-curation-gate check  [--topics DIR] [--gaps FILE] [--json] [--strict]
python3 bin/lastbook-curation-gate gaps   [--topics DIR] [--gaps FILE] [--json]
```

`0` clean (warnings allowed unless `--strict`), `1` findings, `2` usage or input error. `--json` prints one parseable object; output is sorted and byte-stable across runs.

Real result on the upstream content at the time of writing (`examples/in` is that content, copied verbatim):

```console
$ python3 bin/lastbook-curation-gate check --topics examples/in/content/topics --gaps examples/in/content/gaps.json
ERROR   LB07 energy       learn holds 12 readings (4-10)
ERROR   LB05 power        choice 'food-link' offers 0 readings (1-4)
ERROR   LB09 water        choice:bleach[3] note has 32 words (>30)
...
topics: 14  errors: 8  warnings: 14
```

`gaps` reports the curator backlog: 14 domains, 40 `missing` statements, 7 `disagree` statements. The full JSON is in `examples/out/check.json` and `examples/out/gaps.json`.

## Limits

- The quantity heuristic (LB16) is a regex for digits plus common units; it can flag a legitimate number and cannot catch spelled-out doses.
- `related` symmetry (LB14) and empty-choice (LB20) are warnings because `SCHEMA.md` implies rather than states them.
- Page numbers and doc ids are deliberately not resolved; run upstream's `validate_topics.py` with a library for that.
- The example content is a snapshot; counts change when upstream edits its guides.

## 与同类项目的差异

- `Immortal-Protocols/lastbook`'s own `tools/validate_topics.py`: needs `library-data/catalog.json` and checks references only. This tool needs neither and checks the editorial contract; the two are complementary, and the README links the exact upstream lines.
- `ferdousbhai/lastbook-for-omarchy` (the only other Lastbook-named repository found by `gh search repos lastbook`): a packaging fork, not a content checker.
- No repository found by `gh search code "validate_topics.py"` or `gh search code "content/gaps.json"` implements an offline contract gate for these files.

## 本轮创新

First offline enforcement of Lastbook's *written curation contract*: the upstream checker requires the library and validates references, while this gate runs on a bare clone and turns the prose limits (reading counts, note length, route requirement, gap-domain coverage) into rule ids with stable exit codes. It is the first tool to check that `gaps.json` and `content/topics/` agree, and it uses the real 14-guide corpus to show 8 contract violations that upstream's checker would pass.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

13 tests, 8 of them behavioral (subprocess → output/exit code), including the real 14-topic corpus, JSON stability across two runs, `--strict` promotion of warnings, and exit code 2 on bad input.

MIT licensed. Upstream content in `examples/in` is MIT, © Lastbook contributors.
