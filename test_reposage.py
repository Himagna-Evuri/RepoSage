
import unittest
import subprocess
import csv
import tempfile
from pathlib import Path

from reposage_extract import (
    rank_commits_by_risk,
    predict_defect_risk,
    extract_commit_features,
    get_recent_commits,
    export_results_to_csv,
    get_changed_files,
    build_dependency_graph,
    find_impacted_files
)


class TestRepoSage(unittest.TestCase):

    def test_rank_commits_by_risk(self):
        results = [
            {"commit_sha": "commit_A", "probability": 0.30, "prediction": 0},
            {"commit_sha": "commit_B", "probability": 0.85, "prediction": 1},
            {"commit_sha": "commit_C", "probability": 0.55, "prediction": 0}
        ]

        ranked = rank_commits_by_risk(results)

        self.assertEqual(
            [item["commit_sha"] for item in ranked],
            ["commit_B", "commit_C", "commit_A"]
        )

    def test_empty_results(self):
        ranked = rank_commits_by_risk([])

        self.assertEqual(ranked, [])

    def test_equal_probabilities(self):
        results = [
            {"commit_sha": "commit_A", "probability": 0.70, "prediction": 1},
            {"commit_sha": "commit_B", "probability": 0.70, "prediction": 1},
            {"commit_sha": "commit_C", "probability": 0.40, "prediction": 0}
        ]

        ranked = rank_commits_by_risk(results)

        self.assertEqual(len(ranked), 3)
        self.assertEqual(ranked[0]["probability"], 0.70)
        self.assertEqual(ranked[1]["probability"], 0.70)
        self.assertEqual(ranked[2]["probability"], 0.40)

    def test_predict_defect_risk(self):
        features = {
            "nfiles": 2,
            "la": 100,
            "ld": 20,
            "hunks": 3,
            "ndirs": 2,
            "nexts": 2,
            "test_ratio": 0.5,
            "msg_len": 30,
            "msg_ref": 1
        }

        probability, prediction, risk_category = predict_defect_risk(features)

        self.assertGreaterEqual(probability, 0.0)
        self.assertLessEqual(probability, 1.0)

        self.assertEqual(prediction, int(probability >= 0.7))

        self.assertIn(
            risk_category,
            ["Low", "Medium", "High", "Critical"]
        )

    def test_extract_commit_features(self):
        repo_path = (
            r"C:\Users\himag\OneDrive\Documents\RepoSage-Test"
        )

        commit_sha = "d53867641c8a002aef79894e7324ba2bc6bfa00f"

        features = extract_commit_features(repo_path, commit_sha)

        expected_features = [
            "nfiles", "la", "ld", "hunks", "ndirs",
            "nexts", "test_ratio", "msg_len", "msg_ref"
        ]

        self.assertEqual(
            set(features.keys()),
            set(expected_features)
        )

        self.assertEqual(features["nfiles"], 3)
        self.assertAlmostEqual(features["test_ratio"], 1 / 3)
        self.assertEqual(features["msg_ref"], 1)

    def test_invalid_commit_sha(self):
        repo_path = (
            r"C:\Users\himag\OneDrive\Documents\RepoSage-Test"
        )

        with self.assertRaises(subprocess.CalledProcessError):
            extract_commit_features(
                repo_path,
                "invalid_commit_sha"
            )

    def test_get_recent_commits(self):
        repo_path = (
            r"C:\Users\himag\OneDrive\Documents\RepoSage-Test"
        )

        commits = get_recent_commits(repo_path, limit=10)

        self.assertGreater(len(commits), 0)
        self.assertLessEqual(len(commits), 10)

        for sha in commits:
            self.assertRegex(sha, r"^[0-9a-f]{40}$")

    def test_invalid_commit_limit(self):
        repo_path = (
            r"C:\Users\himag\OneDrive\Documents\RepoSage-Test"
        )

        with self.assertRaises(ValueError):
            get_recent_commits(repo_path, limit=0)

        with self.assertRaises(ValueError):
            get_recent_commits(repo_path, limit=-5)

    def test_empty_repository(self):
        repo_path = Path(
            r"C:\Users\himag\OneDrive\Documents\EmptyRepo"
        )

        with self.assertRaises(ValueError):
            get_recent_commits(repo_path, limit=5)

    def test_csv_export(self):

        results = [
            {
                "commit_sha": "abc123",
                "probability": 0.85,
                "risk_category": "Critical",
                "prediction": 1
            },
            {
                "commit_sha": "def456",
                "probability": 0.35,
                "risk_category": "Medium",
                "prediction": 0
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:

            csv_path = Path(temp_dir) / "test_results.csv"

            export_results_to_csv(results, str(csv_path))

            self.assertTrue(csv_path.exists())

            with open(
                csv_path,
                "r",
                newline="",
                encoding="utf-8"
            ) as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 2)

            self.assertEqual(rows[0]["commit_sha"], "abc123")
            self.assertEqual(rows[1]["commit_sha"], "def456")

            self.assertEqual(rows[0]["risk_category"], "Critical")
            self.assertEqual(rows[1]["risk_category"], "Medium")

    def test_empty_csv_export(self):

        with tempfile.TemporaryDirectory() as temp_dir:

            csv_path = Path(temp_dir) / "empty_results.csv"

            export_results_to_csv([], str(csv_path))

            self.assertFalse(csv_path.exists())

    
    def test_get_changed_files(self):

        repo_path = (
            r"C:\Users\himag\OneDrive\Documents\RepoSage-Test"
        )

        commit_sha = "d3c88f71e9640a2b6dc6876fdb86de3ec20fbe48"

        changed_files = get_changed_files(repo_path, commit_sha)

        self.assertEqual(
            changed_files,
            ["utils/Helper.java"]
        )

    def test_build_dependency_graph(self):

        repo_path = (
            r"C:\Users\himag\OneDrive\Documents\RepoSage-Test"
        )

        dependency_graph = build_dependency_graph(repo_path)

        self.assertEqual(
            dependency_graph,
            {
                "Main.java": ["utils/Helper.java"]
            }
        )

    def test_direct_impact_detection(self):

        dependency_graph = {
            "Main.java": ["utils/Helper.java"]
        }

        impacted_files = find_impacted_files(
            ["utils/Helper.java"],
            dependency_graph
        )

        self.assertEqual(
            impacted_files,
            ["Main.java"]
        )

    def test_indirect_impact_detection(self):

        dependency_graph = {
            "Main.java": ["utils/Helper.java"],
            "tests/MainTest.java": ["Main.java"]
        }

        impacted_files = find_impacted_files(
            ["utils/Helper.java"],
            dependency_graph
        )

        self.assertEqual(
            impacted_files,
            ["Main.java", "tests/MainTest.java"]
        )



if __name__ == "__main__":
    unittest.main()
