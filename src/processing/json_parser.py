from src.processing.llm import llm
import json

def tekst2json(json_text: str) -> dict:
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        # Use the LLM to clean the input
        system_prompt = f"""
          Your task is to clean the following text so that it becomes valid JSON, suitable for parsing with Python's json.loads().

        Instructions:
        - Return **only** the corrected JSON. No explanation, no markdown, no wrapping.
        - Ensure all boolean values are lowercase (`true` or `false`), as required by JSON.
        - Correct any trailing commas, mismatched quotes, or structural issues.
        - If the input is not an object or array, wrap it in one.
        - Do not invent missing values unless clearly implied.
        - Output must be strict RFC 8259-compliant JSON.

        Text:
        """
        cleaned_json = llm(json_text, system_prompt=system_prompt)

        # Recursive call with cleaned text
        return tekst2json(cleaned_json)
