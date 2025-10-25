from openai import OpenAI


def llm(text, system_prompt="You are a helpful assistant that answers concisely.") -> str:
    client = OpenAI()

    response = client.responses.create(
        model="gpt-5-nano",
        instructions="You are a concise assistant.",
        input="What is photosynthesis?"
    )

    return response.output_text

    return response.output_text