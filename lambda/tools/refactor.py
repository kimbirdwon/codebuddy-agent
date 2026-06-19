from typing import Dict

from shared.review import generate_refactor_prompt, invoke_text_model


def suggest_refactor(code: str, goals: str = "") -> Dict:
    prompt = generate_refactor_prompt(code, goals)
    return {"draft": invoke_text_model(prompt)}
