from google import genai



def get_llm_response(prompt, model="gemini-3-flash-preview"):
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    interaction = client.interactions.create(
        model=model,
        input=prompt,
        tools=[{"type": "google_search"}]
    )
    # Find the text output (not the GoogleSearchResultContent)
    text_output = next((o for o in interaction.outputs if o.type == "text"), None)
    return response

# print(response.text)


# client = genai.Client()

# interaction = client.interactions.create(
#     model="gemini-3-flash-preview",
#     input="Who won the last Super Bowl?",
#     tools=[{"type": "google_search"}]
# )
# # Find the text output (not the GoogleSearchResultContent)
# text_output = next((o for o in interaction.outputs if o.type == "text"), None)
# if text_output:
#     print(text_output.text)


if __name__ == "__main__":
    get_llm_response("Hi. 介绍一下你自己")