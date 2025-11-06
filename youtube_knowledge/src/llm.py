from openai import OpenAI


def llm(text_input: str, system_prompt: str = "You are a helpful assistant that answers concisely.", reasoning_effort: str = 'low') -> str:
    client = OpenAI()

    response = client.responses.create(
        model="gpt-5-nano",
        instructions=system_prompt,
        input=text_input,
        reasoning={'effort': reasoning_effort}
    )
    return response.output_text