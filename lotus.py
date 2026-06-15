import os
import uvicorn
import tempfile
import base64
import edge_tts
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = FastAPI(title="Lotus Voice AI")

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

CONFIG = {
    "LLM_MODEL": "llama-3.1-8b-instant",
    "VOICE": "hi-IN-SwaraNeural"
}

class ChatRequest(BaseModel):
    message: str

# Premium Dark Theme UI
@app.get("/", response_class=HTMLResponse)
def get_ui():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lotus Voice AI</title>
        <style>
            body { background-color: #121212; color: #ffffff; font-family: 'Segoe UI', Arial, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
            .container { text-align: center; }
            h1 { font-size: 2.5rem; margin-bottom: 10px; color: #a855f7; }
            p { color: #aaa; margin-bottom: 30px; font-size: 1.1rem; }
            .btn { width: 200px; height: 200px; border-radius: 50%; border: none; background: linear-gradient(135deg, #8b5cf6, #ec4899); color: white; font-size: 1.5rem; font-weight: bold; cursor: pointer; box-shadow: 0 0 20px rgba(139, 92, 246, 0.4); transition: all 0.3s ease; }
            .btn.active { background: linear-gradient(135deg, #ef4444, #f97316); box-shadow: 0 0 30px rgba(239, 68, 68, 0.6); animation: pulse 1.5s infinite; }
            .status { margin-top: 20px; font-size: 1.2rem; font-style: italic; color: #e9d5ff; }
            @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>LOTUS VOICE BRAIN</h1>
            <p>Click the button below to start continuous conversation</p>
            <button id="startBtn" class="btn" onclick="toggleAI()">START AI</button>
            <div id="statusText" class="status">Offline</div>
        </div>

        <script>
            let isRunning = false;
            const startBtn = document.getElementById('startBtn');
            const statusText = document.getElementById('statusText');
            
            const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new Recognition();
            recognition.continuous = false;
            recognition.interimResults = false; 
            recognition.lang = 'hi-IN'; // Default Hinglish listening

            function toggleAI() {
                if (!isRunning) {
                    isRunning = true;
                    startBtn.innerText = "STOP AI";
                    startBtn.classList.add('active');
                    statusText.innerText = "Connecting to Lotus...";
                    
                    // Bootup call to get the greeting audio
                    fetchChat("नमस्ते"); 
                } else {
                    isRunning = false;
                    startBtn.innerText = "START AI";
                    startBtn.classList.remove('active');
                    statusText.innerText = "Offline";
                    recognition.stop();
                }
            }

            function startListening() {
                if (!isRunning) return;
                statusText.innerText = "Listening... (Boliye)";
                recognition.start();
            }

            recognition.onresult = async (event) => {
                const userText = event.results[0][0].transcript;
                statusText.innerText = "You: " + userText;
                fetchChat(userText);
            };

            recognition.onerror = (e) => {
                if (isRunning) startListening();
            };

            recognition.onend = () => {
                if (isRunning && statusText.innerText.includes("Listening")) {
                    startListening();
                }
            };

            async function fetchChat(text) {
                try {
                    statusText.innerText = "Lotus is thinking...";
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: text })
                    });
                    const data = await response.json();
                    
                    if (data.audio) {
                        statusText.innerText = "Lotus: " + data.reply;
                        const audio = new Audio("data:audio/mp3;base64," + data.audio);
                        audio.play();
                        audio.onended = () => {
                            if (isRunning) startListening();
                        };
                    } else {
                        if (isRunning) startListening();
                    }
                } catch (error) {
                    console.error(error);
                    if (isRunning) startListening();
                }
            }
        </script>
    </body>
    </html>
    """

async def generate_speech(text: str) -> str:
    """Generate audio using Edge-TTS and return Base64 string"""
    communicate = edge_tts.Communicate(text, CONFIG["VOICE"])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        temp_path = fp.name
    
    await communicate.save(temp_path)
    
    with open(temp_path, "rb") as f:
        audio_data = base64.b64encode(f.read()).decode("utf-8")
        
    os.remove(temp_path)
    return audio_data

@app.post("/chat")
async def chat_with_lotus(request: ChatRequest):
    if not client:
        return {"reply": "Groq API Key error."}
    
    try:
        # Custom Prompt to make Lotus smart and fix pronunciation 
        system_prompt = """You are Lotus (लोटस), a highly intelligent and friendly humanoid robot. 
        Always reply in conversational Hinglish. Keep your answers extremely short, exactly 1 or 2 sentences like a real human chat. 
        Do not use difficult Hindi words, use everyday casual Hinglish. Do not use emojis."""
        
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            model=CONFIG["LLM_MODEL"]
        )
        reply_text = completion.choices[0].message.content.strip()
        
        # Generate neural voice audio
        audio_b64 = await generate_speech(reply_text)
        
        return {"reply": reply_text, "audio": audio_b64}
        
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("lotus:app", host="0.0.0.0", port=port)
