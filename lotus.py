import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = FastAPI(title="Lotus Voice AI")

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

class ChatRequest(BaseModel):
    message: str

# UI Implementation - Root path par ek button wala clean interface dikhega
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
            body {
                background-color: #121212;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }
            .container { text-align: center; }
            h1 { font-size: 2.5rem; margin-bottom: 10px; color: #a855f7; }
            p { color: #aaa; margin-bottom: 30px; font-size: 1.1rem; }
            .btn {
                width: 200px;
                height: 200px;
                border-radius: 50%;
                border: none;
                background: linear-gradient(135deg, #8b5cf6, #ec4899);
                color: white;
                font-size: 1.5rem;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 0 20px rgba(139, 92, 246, 0.4);
                transition: all 0.3s ease;
            }
            .btn.active {
                background: linear-gradient(135deg, #ef4444, #f97316);
                box-shadow: 0 0 30px rgba(239, 68, 68, 0.6);
                animation: pulse 1.5s infinite;
            }
            .status { margin-top: 20px; font-size: 1.2rem; font-style: italic; color: #e9d5ff; }
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
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
            
            // Browser Speech API Setup
            const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!Recognition) {
                alert("Your browser doesn't support Speech Recognition. Use Chrome/Edge.");
            }
            const recognition = new Recognition();
            recognition.continuous = false;
            recognition.lang = 'hi-IN'; // Listens to Hindi/Hinglish

            function toggleAI() {
                if (!isRunning) {
                    isRunning = true;
                    startBtn.innerText = "STOP AI";
                    startBtn.classList.add('active');
                    statusText.innerText = "Lotus: Processing greeting...";
                    speak("नमस्ते, मैं लोटस हूँ। मैं सक्रिय हो चुकी हूँ। कहिए, मैं आपकी क्या मदद कर सकती हूँ?", () => {
                        if(isRunning) startListening();
                    });
                } else {
                    isRunning = false;
                    startBtn.innerText = "START AI";
                    startBtn.classList.remove('active');
                    statusText.innerText = "Offline";
                    recognition.stop();
                    window.speechSynthesis.cancel();
                }
            }

            function startListening() {
                if (!isRunning) return;
                statusText.innerText = "Listening (Lotus sun rahi hai)...";
                recognition.start();
            }

            recognition.onresult = async (event) => {
                const userText = event.results[0][0].transcript;
                statusText.innerText = "You: " + userText;
                
                // Call Groq FastAPI Backend
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: userText })
                    });
                    const data = await response.json();
                    
                    if (data.reply) {
                        statusText.innerText = "Lotus: " + data.reply;
                        speak(data.reply, () => {
                            // Infinite Loop: Speak khatam hone ke baad firse sunna shuru karega
                            if (isRunning) startListening();
                        });
                    } else {
                        if (isRunning) startListening();
                    }
                } catch (error) {
                    console.error(error);
                    if (isRunning) startListening();
                }
            };

            recognition.onerror = () => {
                if (isRunning) startListening();
            };

            recognition.onend = () => {
                // Keep trying to listen if it stopped without result
                if (isRunning && statusText.innerText.includes("Listening")) {
                    startListening();
                }
            };

            function speak(text, callback) {
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'hi-IN'; // Indian voice accent
                utterance.onend = callback;
                window.speechSynthesis.speak(utterance);
            }
        </script>
    </body>
    </html>
    """

@app.post("/chat")
def chat_with_lotus(request: ChatRequest):
    if not client:
        return {"reply": "Groq API Key is missing on the server!"}
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
        return {"reply": f"Error: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("lotus:app", host="0.0.0.0", port=port)
