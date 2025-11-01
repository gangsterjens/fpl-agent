from openai import OpenAI


def llm(text, system_prompt="You are a helpful assistant that answers concisely.") -> str:
    client = OpenAI()

    response = client.responses.create(
        model="gpt-5-nano",
        instructions=system_prompt,
        input=text
    )

    return response.output_text