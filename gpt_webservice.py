import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import openai
app = FastAPI()
openai.api_key = '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'
class ChatInput(BaseModel):
    input_text: str
class ChatOutput(BaseModel):
    response: str
@app.post("/chat", response_model=ChatOutput)
def chat(input: ChatInput):
    # Use OpenAI's API to generate a response
    response = openai.Completion.create(
        engine="davinci",
        prompt=input.input_text,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.7,
    )
    response_text = response.choices[0].text.strip()
    return {"response": response_text}
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=5000)

