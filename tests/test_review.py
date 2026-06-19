import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "lambda" / "shared" / "review.py"
ORCHESTRATOR_PATH = ROOT / "lambda" / "orchestrator.py"


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


review = load_module("review_module", REVIEW_PATH)


class ReviewHelpersTest(unittest.TestCase):
    def test_estimate_complexity_classifies_branching_function(self):
        result = review.estimate_complexity(
            """
def choose(value):
    if value > 10:
        return "big"
    elif value > 5:
        return "mid"
    return "small"
"""
        )
        self.assertEqual(result["summary"]["function_count"], 1)
        self.assertGreaterEqual(result["summary"]["max_complexity"], 3)

    def test_build_review_prompt_includes_repo_and_pr(self):
        prompt = review.build_review_prompt(
            {
                "repository": {"full_name": "demo/repo"},
                "pull_request": {
                    "number": 12,
                    "title": "Add login",
                    "html_url": "https://github.com/demo/repo/pull/12",
                    "user": {"login": "alice"},
                    "base": {"ref": "main"},
                    "head": {"ref": "feature/login"},
                    "body": "Adds login logic",
                },
                "changed_files": [{"filename": "app.py", "additions": 10, "deletions": 2}],
            }
        )
        self.assertIn("demo/repo", prompt)
        self.assertIn("Add login", prompt)
        self.assertIn("app.py", prompt)


if __name__ == "__main__":
    unittest.main()
