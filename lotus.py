import os
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Web Application object (Iske bina Uvicorn nahi chalega)
app = FastAPI(title="Lotus Voice Brain API")

api_key = os.getenv("GROQ_API_KEY")
if api_key:
    client = Groq(api_key=api_key)
else:
    client = None

CONFIG = {
    "LLM_MODEL": "llama-3.1-8b-instant"
}

# Web payload structure
class ChatRequest(BaseModel):
    message: str

# Root endpoint - Browser me default message dikhayega
@app.get("/")
def home():
    return {"status": "success", "message": "नमस्ते! Lotus Voice Brain is LIVE and Running!"}

# Chat API endpoint
@app.post("/chat")
def chat_with_lotus(request: ChatRequest):
    if not client:
        return {"error": "GROQ_API_KEY missing in server environment"}
        
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are Lotus, a smart humanoid robot. Reply in exactly 1 short sentence in Hinglish. Talk like a friendly real human."},
                {"role": "user", "content": request.message}
            ],
            model=CONFIG["LLM_MODEL"]
        )
        return {"reply": completion.choices[0].message.content.strip()}
    except Exception as e:
        return {"error": str(e)}

# Server Execution
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("lotus:app", host="0.0.0.0", port=port)
