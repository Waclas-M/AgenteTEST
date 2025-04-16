# -*- coding: cp1252 -*-
# tools/llm_clients.py
import os
from ..config import settings # U�ycie �cie�ki wzgl�dnej do importu z config

# Warunkowe importowanie bibliotek LLM
try:
    import openai
    openai.api_key = settings.OPENAI_API_KEY
except ImportError:
    openai = None
    print("Ostrze�enie: Biblioteka OpenAI nie jest zainstalowana lub klucz API nie jest dost�pny.")

try:
    import google.generativeai as genai
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
    else:
        genai = None # Nie konfiguruj, je�li nie ma klucza
        print("Ostrze�enie: Klucz API Gemini nie jest dost�pny.")
except ImportError:
    genai = None
    print("Ostrze�enie: Biblioteka Google Generative AI nie jest zainstalowana.")

# Mo�na doda� obs�ug� Perplexity (PPLX) je�li potrzeba

def generate_completion(prompt: str, model_preference: str = "gemini", max_tokens: int = 1000) -> str:
    """
    Generuje uzupe�nienie tekstu u�ywaj�c preferowanego dostawcy LLM.

    Args:
        prompt (str): Tekst wej�ciowy dla LLM.
        model_preference (str): Preferowany dostawca ('gemini' lub 'openai').
        max_tokens (int): Maksymalna liczba token�w w odpowiedzi.

    Returns:
        str: Wygenerowany tekst lub komunikat b��du.
    """
    chosen_provider = model_preference if (model_preference == "gemini" and genai and settings.GEMINI_API_KEY) or \
                                         (model_preference == "openai" and openai and settings.OPENAI_API_KEY) \
                                      else settings.DEFAULT_LLM_PROVIDER

    print(f"Pr�ba u�ycia LLM: {chosen_provider}")

    if chosen_provider == "gemini" and genai:
        try:
            # Wybierz odpowiedni model Gemini (np. gemini-pro)
            model = genai.GenerativeModel('gemini-1.5-flash-002')
            response = model.generate_content(prompt)
            # Sprawd� czy odpowied� zawiera tekst (mo�e by� zablokowana)
            if response.parts:
                 return response.text
            else:
                 # Sprawd� przyczyn� braku odpowiedzi (np. blokada bezpiecze�stwa)
                 print(f"Ostrze�enie: Odpowied� Gemini nie zawiera tekstu. Pow�d: {response.prompt_feedback}")
                 return f"B��d: Odpowied� Gemini by�a pusta lub zablokowana ({response.prompt_feedback})."
        except Exception as e:
            print(f"B��d podczas komunikacji z Gemini API: {e}")
            return f"B��d Gemini API: {e}"

    elif chosen_provider == "openai" and openai:
        try:
            # U�yj nowszego API (v1.x) je�li dost�pne
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY) # Utw�rz klienta
            response = client.chat.completions.create(
                model="gpt-3.5-turbo", # lub gpt-4
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"B��d podczas komunikacji z OpenAI API: {e}")
            # Sprawd� czy b��d wynika z braku klucza (mo�e by� inny problem)
            if "authentication" in str(e).lower():
                 print("B��d autentykacji OpenAI. Sprawd� sw�j klucz API.")
            return f"B��d OpenAI API: {e}"

    else:
        print("Nie skonfigurowano �adnego dzia�aj�cego dostawcy LLM.")
        return "B��d: Brak dost�pnego LLM."

# --- Przyk�adowe u�ycie (mo�na uruchomi� ten plik bezpo�rednio do test�w) ---
if __name__ == '__main__':
    test_prompt = "Napisz kr�tki opis dzia�ania sieci neuronowej."
    print("\nTestowanie generowania LLM:")

    print("\n--- Test Gemini ---")
    gemini_response = generate_completion(test_prompt, model_preference="gemini")
    print(gemini_response)

    print("\n--- Test OpenAI ---")
    openai_response = generate_completion(test_prompt, model_preference="openai")
    print(openai_response)

    print("\n--- Test Domy�lny ---")
    default_response = generate_completion(test_prompt) # U�yje domy�lnego wg settings
    print(default_response)