import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin" / "lastbook-curation-gate"
REAL = ROOT / "examples" / "in" / "content"

sys.path.insert(0, str(ROOT / "tests"))
from fixtures import topic, write_pack  # noqa: E402


def run(args, cwd=ROOT):
    return subprocess.run([sys.executable, str(BIN)] + args, cwd=cwd,
                          capture_output=True, text=True, timeout=60)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="lbgate-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def pack(self, topics, gaps=None):
        return write_pack(self.tmp, topics, gaps)


class TestRealContent(Base):
    def test_real_content_exits_1_with_schema_errors(self):
        r = run(["check", "--topics", str(REAL / "topics"), "--gaps", str(REAL / "gaps.json")])
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("LB07", r.stdout)
        self.assertIn("LB09", r.stdout)

    def test_json_is_parseable_and_stable(self):
        a = run(["check", "--topics", str(REAL / "topics"), "--gaps", str(REAL / "gaps.json"), "--json"])
        b = run(["check", "--topics", str(REAL / "topics"), "--gaps", str(REAL / "gaps.json"), "--json"])
        self.assertEqual(a.returncode, 1)
        payload = json.loads(a.stdout)
        self.assertEqual(payload["topics"], 14)
        self.assertEqual(payload["counts"], {"error": 8, "warning": 14})
        self.assertEqual(a.stdout, b.stdout)

    def test_gaps_subcommand_reports_backlog(self):
        r = run(["gaps", "--topics", str(REAL / "topics"), "--gaps", str(REAL / "gaps.json"), "--json"])
        self.assertEqual(r.returncode, 0, r.stderr)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["domains"], 14)
        self.assertEqual(payload["missing_total"], 40)
        self.assertEqual(payload["disagree_total"], 7)


class TestContractRules(Base):
    def test_clean_pack_exits_0(self):
        self.pack({"water": topic("water")})
        r = run(["check", "--topics", str(self.tmp / "topics"), "--gaps", str(self.tmp / "gaps.json"), "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["counts"], {"error": 0, "warning": 0})

    def test_choice_with_five_readings_is_lb05(self):
        t = topic("water")
        t["choices"][0]["read"] = t["choices"][0]["read"] * 5
        self.pack({"water": t})
        r = run(["check", "--topics", str(self.tmp / "topics"), "--gaps", str(self.tmp / "gaps.json"), "--json"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("LB05", [f["rule"] for f in json.loads(r.stdout)["findings"]])

    def test_prepare_below_minimum_is_lb06(self):
        t = topic("water")
        t["prepare"] = t["prepare"][:2]
        self.pack({"water": t})
        r = run(["check", "--topics", str(self.tmp / "topics"), "--gaps", str(self.tmp / "gaps.json"), "--json"])
        self.assertIn("LB06", [f["rule"] for f in json.loads(r.stdout)["findings"]])

    def test_learn_without_route_is_lb04(self):
        t = topic("water", mode="learn")
        t["route"] = []
        t["choices"] = []
        self.pack({"water": t})
        r = run(["check", "--topics", str(self.tmp / "topics"), "--gaps", str(self.tmp / "gaps.json"), "--json"])
        self.assertIn("LB04", [f["rule"] for f in json.loads(r.stdout)["findings"]])

    def test_note_over_thirty_words_is_lb09(self):
        t = topic("water")
        t["prepare"][0]["note"] = " ".join(["word"] * 31)
        self.pack({"water": t})
        r = run(["check", "--topics", str(self.tmp / "topics"), "--gaps", str(self.tmp / "gaps.json"), "--json"])
        self.assertIn("LB09", [f["rule"] for f in json.loads(r.stdout)["findings"]])

    def test_limit_without_source_is_lb08(self):
        t = topic("water")
        t["limits"] = [{"text": "Stop and call a professional."}]
        self.pack({"water": t})
        r = run(["check", "--topics", str(self.tmp / "topics"), "--gaps", str(self.tmp / "gaps.json"), "--json"])
        self.assertIn("LB08", [f["rule"] for f in json.loads(r.stdout)["findings"]])

    def test_unknown_gap_domain_is_lb18(self):
        self.pack({"water": topic("water")}, gaps={"water": {"missing": []}, "volcano": {"missing": ["x"]}})
        r = run(["check", "--topics", str(self.tmp / "topics"), "--gaps", str(self.tmp / "gaps.json"), "--json"])
        self.assertIn("LB18", [f["rule"] for f in json.loads(r.stdout)["findings"]])

    def test_duplicate_gap_across_domains_warns_and_strict_fails(self):
        gaps = {"water": {"missing": ["No CDC page."]}, "food": {"missing": ["No CDC page."]}}
        self.pack({"water": topic("water"), "food": topic("food")}, gaps=gaps)
        r = run(["check", "--topics", str(self.tmp / "topics"), "--gaps", str(self.tmp / "gaps.json"), "--json"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("LB19", [f["rule"] for f in json.loads(r.stdout)["findings"]])
        strict = run(["check", "--topics", str(self.tmp / "topics"), "--gaps", str(self.tmp / "gaps.json"),
                      "--json", "--strict"])
        self.assertEqual(strict.returncode, 1)

    def test_missing_topics_dir_is_usage_error(self):
        r = run(["check", "--topics", str(self.tmp / "nope"), "--json"])
        self.assertEqual(r.returncode, 2)
        self.assertFalse(json.loads(r.stdout)["ok"])

    def test_no_subcommand_is_usage_error(self):
        self.assertEqual(run([]).returncode, 2)


if __name__ == "__main__":
    unittest.main()
