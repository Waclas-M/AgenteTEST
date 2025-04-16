# -*- coding: cp1252 -*-
# tools/llm_clients.py
import os
from ..config import settings # U¿ycie œcie¿ki wzglêdnej do importu z config

# Warunkowe importowanie bibliotek LLM
try:
    import openai
    openai.api_key = settings.OPENAI_API_KEY
except ImportError:
    openai = None
    print("Ostrze¿enie: Biblioteka OpenAI nie jest zainstalowana lub klucz API nie jest dostêpny.")

try:
    import google.generativeai as genai
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
    else:
        genai = None # Nie konfiguruj, jeœli nie ma klucza
        print("Ostrze¿enie: Klucz API Gemini nie jest dostêpny.")
except ImportError:
    genai = None
    print("Ostrze¿enie: Biblioteka Google Generative AI nie jest zainstalowana.")

# Mo¿na dodaæ obs³ugê Perplexity (PPLX) jeœli potrzeba

def generate_completion(prompt: str, model_preference: str = "gemini", max_tokens: int = 1000) -> str:
    """
    Generuje uzupe³nienie tekstu u¿ywaj¹c preferowanego dostawcy LLM.

    Args:
        prompt (str): Tekst wejœciowy dla LLM.
        model_preference (str): Preferowany dostawca ('gemini' lub 'openai').
        max_tokens (int): Maksymalna liczba tokenów w odpowiedzi.

    Returns:
        str: Wygenerowany tekst lub komunikat b³êdu.
    """
    chosen_provider = model_preference if (model_preference == "gemini" and genai and settings.GEMINI_API_KEY) or \
                                         (model_preference == "openai" and openai and settings.OPENAI_API_KEY) \
                                      else settings.DEFAULT_LLM_PROVIDER

    print(f"Próba u¿ycia LLM: {chosen_provider}")

    if chosen_provider == "gemini" and genai:
        try:
            # Wybierz odpowiedni model Gemini (np. gemini-pro)
            model = genai.GenerativeModel('gemini-1.5-flash-002')
            response = model.generate_content(prompt)
            # SprawdŸ czy odpowiedŸ zawiera tekst (mo¿e byæ zablokowana)
            if response.parts:
                 return response.text
            else:
                 # SprawdŸ przyczynê braku odpowiedzi (np. blokada bezpieczeñstwa)
                 print(f"Ostrze¿enie: OdpowiedŸ Gemini nie zawiera tekstu. Powód: {response.prompt_feedback}")
                 return f"B³¹d: OdpowiedŸ Gemini by³a pusta lub zablokowana ({response.prompt_feedback})."
        except Exception as e:
            print(f"B³¹d podczas komunikacji z Gemini API: {e}")
            return f"B³¹d Gemini API: {e}"

    elif chosen_provider == "openai" and openai:
        try:
            # U¿yj nowszego API (v1.x) jeœli dostêpne
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY) # Utwórz klienta
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
            print(f"B³¹d podczas komunikacji z OpenAI API: {e}")
            # SprawdŸ czy b³¹d wynika z braku klucza (mo¿e byæ inny problem)
            if "authentication" in str(e).lower():
                 print("B³¹d autentykacji OpenAI. SprawdŸ swój klucz API.")
            return f"B³¹d OpenAI API: {e}"

    else:
        print("Nie skonfigurowano ¿adnego dzia³aj¹cego dostawcy LLM.")
        return "B³¹d: Brak dostêpnego LLM."

# --- Przyk³adowe u¿ycie (mo¿na uruchomiæ ten plik bezpoœrednio do testów) ---
if __name__ == '__main__':
    test_prompt = "Napisz krótki opis dzia³ania sieci neuronowej."
    print("\nTestowanie generowania LLM:")

    print("\n--- Test Gemini ---")
    gemini_response = generate_completion(test_prompt, model_preference="gemini")
    print(gemini_response)

    print("\n--- Test OpenAI ---")
    openai_response = generate_completion(test_prompt, model_preference="openai")
    print(openai_response)

    print("\n--- Test Domyœlny ---")
    default_response = generate_completion(test_prompt) # U¿yje domyœlnego wg settings
    print(default_response)