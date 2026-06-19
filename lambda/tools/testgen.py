from typing import Dict

from shared.review import generate_unit_test_prompt, invoke_text_model


def generate_unit_test(code: str, language: str = "python") -> Dict:
    prompt = generate_unit_test_prompt(code, language)
    return {"draft": invoke_text_model(prompt)}
