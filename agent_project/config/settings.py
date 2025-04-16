# -*- coding: cp1252 -*-
# config/settings.py
import os
from dotenv import load_dotenv

# Wczytaj zmienne z pliku .env (jeœli istnieje)
# Plik .env powinien znajdowaæ siê w g³ównym katalogu projektu (agent_project)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)
print(f"Wczytano zmienne œrodowiskowe z: {dotenv_path}") # Debug print

# --- Klucze API LLM ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PPLX_API_KEY = os.getenv("PPLX_API_KEY") # Perplexity API Key

# --- Klucze API Narzêdzi ---
FIRECRAWL_API_KEY = os.getenv("FIRECLAWL_API_KEY") # Poprawiona nazwa zmiennej
PUBMED_API_KEY = os.getenv("PUBMED_API_KEY") # Chocia¿ Entrez czêœciej u¿ywa email

# --- Inne Konfiguracje ---
# PubMed (Entrez) wymaga adresu email
PUBMED_EMAIL = os.getenv("PUBMED_EMAIL", "wiktortobota13@Gmail.com") # U¿yj zmiennej œrodowiskowej lub domyœlnej

# Sprawdzenie, czy klucze zosta³y wczytane (opcjonalne logowanie)
print(f"OPENAI_API_KEY loaded: {'Yes' if OPENAI_API_KEY else 'No'}")
print(f"GEMINI_API_KEY loaded: {'Yes' if GEMINI_API_KEY else 'No'}")
print(f"FIRECRAWL_API_KEY loaded: {'Yes' if FIRECRAWL_API_KEY else 'No'}")
print(f"PUBMED_EMAIL set to: {PUBMED_EMAIL}")

# Mo¿esz dodaæ tu logikê wyboru domyœlnego LLM, jeœli chcesz
DEFAULT_LLM_PROVIDER = "gemini" if GEMINI_API_KEY else "openai" if OPENAI_API_KEY else None
print(f"Default LLM Provider based on available keys: {DEFAULT_LLM_PROVIDER}")