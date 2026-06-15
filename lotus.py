import os
import asyncio
import sounddevice as sd
import soundfile as sf
import edge_tts
from dotenv import load_dotenv
from groq import Groq
from playsound import playsound

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("Error: GROQ_API_KEY .env file mein nahi mili!")
    exit(1)

client = Groq(api_key=api_key)

# Configuration
CONFIG = {
    "VOICE": "hi-IN-SwaraNeural",  # Extremely natural neural Hindi voice
    "LLM_MODEL": "llama-3.1-8b-instant",  # Ultra-fast model
    "STT_MODEL": "whisper-large-v3",
    "RECORD_DUR": 4,
    "SAMPLE_RATE": 16000
}

async def speak(text, filename="reply.mp3"):
    """Convert text to speech and play it using playsound"""
    print(f"Lotus: {text}")
    try:
        # Convert text to human-like speech
        communicate = edge_tts.Communicate(text, CONFIG["VOICE"])
        await communicate.save(filename)
        
        # Play the audio file (blocking till completion)
        playsound(filename)
        
    except Exception as e:
        print(f"Voice output error: {e}")
    finally:
        # Clean up audio file
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass

def record_voice(filename="user.wav", duration=4, sample_rate=16000):
    """Record input voice from standard microphone"""
    print("\n>> Lotus sun raha hai (kuch boliye)...")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()  # Wait for recording to complete
    sf.write(filename, audio_data, sample_rate)

async def main():
    print("=== Lotus Voice Brain Ready! (Ctrl+C to stop) ===")
    
    # First speak greeting on startup
    greeting = "नमस्ते, मैं लोटस हूँ। मैं सक्रिय हो चुकी हूँ। कहिए, मैं आपकी क्या मदद कर सकती हूँ?"
    await speak(greeting)
    
    messages = [
        {
            "role": "system",
            "content": "You are Lotus, a smart humanoid robot. Reply in exactly 1 short sentence in Hinglish. Talk like a friendly real human."
        },
        {
            "role": "assistant",
            "content": greeting
        }
    ]
    
    while True:
        try:
            # 1. Record voice
            record_voice("user.wav", duration=CONFIG["RECORD_DUR"])
            
            # 2. Transcribe voice using Groq Whisper API
            with open("user.wav", "rb") as f:
                transcription = client.audio.transcriptions.create(
                    file=("user.wav", f.read()),
                    model=CONFIG["STT_MODEL"]
                )
            user_query = transcription.text.strip()
            print(f"Aap: {user_query}")
            
            if not user_query:
                continue
                
            if any(word in user_query.lower() for word in ['exit', 'quit', 'bye', 'alvida', 'band karo']):
                await speak("Alvida! Phir milenge.")
                break
            
            # Add user query to conversation history
            messages.append({"role": "user", "content": user_query})
            
            # 3. Generate response using Groq Llama 3.1
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=CONFIG["LLM_MODEL"]
            )
            response = chat_completion.choices[0].message.content.strip()
            
            # Add response to history
            messages.append({"role": "assistant", "content": response})
            
            # 4. Speak response out loud
            await speak(response)
            
            # Cleanup input file
            if os.path.exists("user.wav"):
                os.remove("user.wav")
                
        except KeyboardInterrupt:
            print("\nLotus system offline.")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
    if __name__ == "__main__":
    import uvicorn
    import os
    
    # Cloud platforms automatically PORT variable dete hain, agar na mile toh default 8080 use hoga
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("lotus:app", host="0.0.0.0", port=port)


