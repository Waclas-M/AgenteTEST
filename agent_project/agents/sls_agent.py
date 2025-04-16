# -*- coding: cp1252 -*-
# agents/sls_agent.py
from typing import List, Dict, Any, Optional
import re # Import re do prostego czyszczenia tekstu dla fallbacku
# U�yj �cie�ek wzgl�dnych do import�w
from ..tools.llm_clients import generate_completion
from ..tools.api_clients import search_pubmed_entrez, search_firecrawl

class SLSAgent:
    def __init__(self, use_pubmed_api: bool = True):
        self.use_pubmed_api = use_pubmed_api
        print(f"SLSAgent skonfigurowany do u�ycia PubMed API: {self.use_pubmed_api}")

    def _generate_scientific_queries(self, input_text: str, num_queries: int = 2) -> List[str]:
        """Generuje zapytania do wyszukiwarek naukowych u�ywaj�c LLM na podstawie tekstu wej�ciowego."""

        llm_prompt = f"""
                Na podstawie poni�szego tekstu analitycznego, zidentyfikuj kluczowe poj�cia biomedyczne (np. z sekcji Definitions) i relacje (np. z sekcji Relationships). Nast�pnie wygeneruj {num_queries} zapyta� zoptymalizowanych dla wyszukiwarek literatury naukowej, takich jak PubMed. U�ywaj precyzyjnych termin�w, operator�w logicznych (AND, OR, NOT) i ewentualnie formatowania specyficznego dla PubMed (np. [Title/Abstract], [MeSH Terms]). Skup si� na znalezieniu relevantnych publikacji naukowych potwierdzaj�cych, rozwijaj�cych lub kwestionuj�cych informacje z tekstu wej�ciowego.
                Format odpowiedzi: Ka�de zapytanie w nowej linii, bez numeracji.

                Tekst Wej�ciowy:
                ```
                {input_text}
                ```

                Wygenerowane zapytania (format PubMed):
        """
        print("Generowanie zapyta� dla SLS u�ywaj�c LLM...")
        raw_queries = generate_completion(llm_prompt)

        # --- POPRAWIONA LOGIKA FALLBACK ---
        if raw_queries.startswith("B��d:") or not raw_queries.strip():
             print(f"Nie uda�o si� wygenerowa� zapyta� naukowych przez LLM. U�ywanie fallbacku opartego na input_text. B��d: {raw_queries}")
             # Prosty fallback: we� pierwsze ~10 s��w z input_text jako zapytanie
             # Usu� znaki specjalne, we� unikalne s�owa
             words = re.findall(r'\b\w+\b', input_text.lower())[:15] # We� pierwsze 15 s��w
             fallback_query = " ".join(list(dict.fromkeys(words))) # Unikalne s�owa w kolejno�ci
             print(f"Wygenerowano zapytanie fallback: {fallback_query}")
             # Zwr�� list� z jednym zapytaniem fallback lub pust� list�, je�li tekst by� pusty
             return [fallback_query] if fallback_query else []

        queries = [q.strip() for q in raw_queries.strip().split('\n') if q.strip()]
        print(f"Wygenerowane zapytania naukowe przez LLM: {queries}")
        # --- POPRAWIONA WARTO�� ZWRACANA ---
        # Je�li LLM zwr�ci� pust� list� (mimo �e nie by�o b��du), te� u�yj fallbacku
        if not queries:
             words = re.findall(r'\b\w+\b', input_text.lower())[:15]
             fallback_query = " ".join(list(dict.fromkeys(words)))
             print(f"LLM zwr�ci� puste zapytania. Wygenerowano zapytanie fallback: {fallback_query}")
             return [fallback_query] if fallback_query else []
        else:
             return queries


    def search_papers(self, input_text: str, max_results_per_query: int = 5) -> List[Dict[str, Any]]:
        """Wyszukuje artyku�y u�ywaj�c PubMed API i/lub Firecrawl z zapytaniami LLM."""
        # --- POPRAWIONE WYWO�ANIE _generate_scientific_queries ---
        queries = self._generate_scientific_queries(input_text=input_text) # Przekazujemy input_text

        if not queries: # Je�li generowanie zapyta� (nawet fallback) zawiod�o
             print("SLSAgent: Nie uda�o si� wygenerowa� �adnych zapyta�. Zwracam pust� list�.")
             return []

        all_articles = []
        pubmed_failed_or_disabled = not self.use_pubmed_api

        for query in queries:
            articles_pubmed = None
            # 1. Spr�buj PubMed Entrez, je�li w��czone
            if self.use_pubmed_api:
                print(f"SLSAgent: Wyszukiwanie w PubMed dla zapytania: '{query}'") # Dodano log
                articles_pubmed = search_pubmed_entrez(query, max_results=max_results_per_query)
                if articles_pubmed is not None:
                    all_articles.extend(articles_pubmed)
                    print(f"Dodano {len(articles_pubmed)} artyku��w z PubMed dla zapytania '{query}'.")
                else:
                    print(f"PubMed Entrez zwr�ci� b��d dla zapytania '{query}'.")
                    pubmed_failed_or_disabled = True

            # 2. U�yj Firecrawl jako fallback
            if pubmed_failed_or_disabled or (self.use_pubmed_api and not articles_pubmed and articles_pubmed is not None):
                # Dodano warunek 'articles_pubmed is not None', aby nie uruchamia� Firecrawl, je�li Entrez mia� b��d, chyba �e Entrez jest wy��czony
                 if not articles_pubmed and articles_pubmed is not None:
                      print(f"PubMed nie znalaz� wynik�w dla '{query}'. Pr�ba za pomoc� Firecrawl.")
                 elif pubmed_failed_or_disabled and self.use_pubmed_api: # Je�li Entrez mia� b��d
                       print(f"Pr�ba wyszukania naukowego za pomoc� Firecrawl z powodu b��du Entrez dla zapytania: {query}")
                 elif not self.use_pubmed_api: # Je�li Entrez by� wy��czony
                        print(f"Pr�ba wyszukania naukowego za pomoc� Firecrawl (PubMed API wy��czone) dla zapytania: {query}")

                 firecrawl_query = f"{query} site:pubmed.ncbi.nlm.nih.gov OR site:scholar.google.com OR site:biorxiv.org OR site:medrxiv.org OR site:arxiv.org"
                 articles_firecrawl = search_firecrawl(firecrawl_query, fetch_content=False) # Domy�lnie nie pobieraj tre�ci
                 if articles_firecrawl:
                    for article in articles_firecrawl:
                        article['source'] = 'firecrawl_scientific_search'
                    all_articles.extend(articles_firecrawl)
                    print(f"Dodano {len(articles_firecrawl)} potencjalnych artyku��w z Firecrawl dla zapytania '{query}'.")
                 else:
                      print(f"Firecrawl nie znalaz� wynik�w dla zapytania: '{firecrawl_query}'")


        total_articles = len(all_articles)
        print(f"SLSAgent zako�czy� prac�, zwracaj�c ��cznie {total_articles} potencjalnych artyku��w.")
        # TODO: Deduplikacja wynik�w (np. na podstawie DOI lub tytu�u)
        # TODO: Opcjonalna ocena relevancji przez LLM na podstawie abstrakt�w/snippet�w
        return all_articles