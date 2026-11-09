import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

def get_gemini_response(chat_history: list) -> str:
    formatted_contents = []
    for msg in chat_history:
        formatted_contents.append(
            types.Content(
                role=msg.role,
                parts=[types.Part.from_text(text=msg.content)]
            )
        )

    # Lista con modelos oficiales
    models_to_try = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-3.8-flash"
    ]
    
    last_error = None
    # Probamos cada modelo con 2 reintentos y pausa breve
    for model_name in models_to_try:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=formatted_contents
                )
                return response.text
            except Exception as e:
                last_error = e
                time.sleep(1.5)  # Breve pausa para esperar que pase el pico de tráfico
                continue

    raise last_error
