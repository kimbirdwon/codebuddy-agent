from typing import Dict

from shared.review import estimate_complexity


def analyze_complexity(code: str) -> Dict:
    return estimate_complexity(code)
