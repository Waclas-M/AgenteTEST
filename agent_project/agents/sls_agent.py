# -*- coding: cp1252 -*-
# agents/sls_agent.py
from typing import List, Dict, Any, Optional
import re # Import re do prostego czyszczenia tekstu dla fallbacku
# U¿yj œcie¿ek wzglêdnych do importów
from ..tools.llm_clients import generate_completion
from ..tools.api_clients import search_pubmed_entrez, search_firecrawl

class SLSAgent:
    def __init__(self, use_pubmed_api: bool = True):
        self.use_pubmed_api = use_pubmed_api
        print(f"SLSAgent skonfigurowany do u¿ycia PubMed API: {self.use_pubmed_api}")

    def _generate_scientific_queries(self, input_text: str, num_queries: int = 2) -> List[str]:
        """Generuje zapytania do wyszukiwarek naukowych u¿ywaj¹c LLM na podstawie tekstu wejœciowego."""

        llm_prompt = f"""
                Na podstawie poni¿szego tekstu analitycznego, zidentyfikuj kluczowe pojêcia biomedyczne (np. z sekcji Definitions) i relacje (np. z sekcji Relationships). Nastêpnie wygeneruj {num_queries} zapytañ zoptymalizowanych dla wyszukiwarek literatury naukowej, takich jak PubMed. U¿ywaj precyzyjnych terminów, operatorów logicznych (AND, OR, NOT) i ewentualnie formatowania specyficznego dla PubMed (np. [Title/Abstract], [MeSH Terms]). Skup siê na znalezieniu relevantnych publikacji naukowych potwierdzaj¹cych, rozwijaj¹cych lub kwestionuj¹cych informacje z tekstu wejœciowego.
                Format odpowiedzi: Ka¿de zapytanie w nowej linii, bez numeracji.

                Tekst Wejœciowy:
                ```
                {input_text}
                ```

                Wygenerowane zapytania (format PubMed):
        """
        print("Generowanie zapytañ dla SLS u¿ywaj¹c LLM...")
        raw_queries = generate_completion(llm_prompt)

        # --- POPRAWIONA LOGIKA FALLBACK ---
        if raw_queries.startswith("B³¹d:") or not raw_queries.strip():
             print(f"Nie uda³o siê wygenerowaæ zapytañ naukowych przez LLM. U¿ywanie fallbacku opartego na input_text. B³¹d: {raw_queries}")
             # Prosty fallback: weŸ pierwsze ~10 s³ów z input_text jako zapytanie
             # Usuñ znaki specjalne, weŸ unikalne s³owa
             words = re.findall(r'\b\w+\b', input_text.lower())[:15] # WeŸ pierwsze 15 s³ów
             fallback_query = " ".join(list(dict.fromkeys(words))) # Unikalne s³owa w kolejnoœci
             print(f"Wygenerowano zapytanie fallback: {fallback_query}")
             # Zwróæ listê z jednym zapytaniem fallback lub pust¹ listê, jeœli tekst by³ pusty
             return [fallback_query] if fallback_query else []

        queries = [q.strip() for q in raw_queries.strip().split('\n') if q.strip()]
        print(f"Wygenerowane zapytania naukowe przez LLM: {queries}")
        # --- POPRAWIONA WARTOŒÆ ZWRACANA ---
        # Jeœli LLM zwróci³ pust¹ listê (mimo ¿e nie by³o b³êdu), te¿ u¿yj fallbacku
        if not queries:
             words = re.findall(r'\b\w+\b', input_text.lower())[:15]
             fallback_query = " ".join(list(dict.fromkeys(words)))
             print(f"LLM zwróci³ puste zapytania. Wygenerowano zapytanie fallback: {fallback_query}")
             return [fallback_query] if fallback_query else []
        else:
             return queries


    def search_papers(self, input_text: str, max_results_per_query: int = 5) -> List[Dict[str, Any]]:
        """Wyszukuje artyku³y u¿ywaj¹c PubMed API i/lub Firecrawl z zapytaniami LLM."""
        # --- POPRAWIONE WYWO£ANIE _generate_scientific_queries ---
        queries = self._generate_scientific_queries(input_text=input_text) # Przekazujemy input_text

        if not queries: # Jeœli generowanie zapytañ (nawet fallback) zawiod³o
             print("SLSAgent: Nie uda³o siê wygenerowaæ ¿adnych zapytañ. Zwracam pust¹ listê.")
             return []

        all_articles = []
        pubmed_failed_or_disabled = not self.use_pubmed_api

        for query in queries:
            articles_pubmed = None
            # 1. Spróbuj PubMed Entrez, jeœli w³¹czone
            if self.use_pubmed_api:
                print(f"SLSAgent: Wyszukiwanie w PubMed dla zapytania: '{query}'") # Dodano log
                articles_pubmed = search_pubmed_entrez(query, max_results=max_results_per_query)
                if articles_pubmed is not None:
                    all_articles.extend(articles_pubmed)
                    print(f"Dodano {len(articles_pubmed)} artyku³ów z PubMed dla zapytania '{query}'.")
                else:
                    print(f"PubMed Entrez zwróci³ b³¹d dla zapytania '{query}'.")
                    pubmed_failed_or_disabled = True

            # 2. U¿yj Firecrawl jako fallback
            if pubmed_failed_or_disabled or (self.use_pubmed_api and not articles_pubmed and articles_pubmed is not None):
                # Dodano warunek 'articles_pubmed is not None', aby nie uruchamiaæ Firecrawl, jeœli Entrez mia³ b³¹d, chyba ¿e Entrez jest wy³¹czony
                 if not articles_pubmed and articles_pubmed is not None:
                      print(f"PubMed nie znalaz³ wyników dla '{query}'. Próba za pomoc¹ Firecrawl.")
                 elif pubmed_failed_or_disabled and self.use_pubmed_api: # Jeœli Entrez mia³ b³¹d
                       print(f"Próba wyszukania naukowego za pomoc¹ Firecrawl z powodu b³êdu Entrez dla zapytania: {query}")
                 elif not self.use_pubmed_api: # Jeœli Entrez by³ wy³¹czony
                        print(f"Próba wyszukania naukowego za pomoc¹ Firecrawl (PubMed API wy³¹czone) dla zapytania: {query}")

                 firecrawl_query = f"{query} site:pubmed.ncbi.nlm.nih.gov OR site:scholar.google.com OR site:biorxiv.org OR site:medrxiv.org OR site:arxiv.org"
                 articles_firecrawl = search_firecrawl(firecrawl_query, fetch_content=False) # Domyœlnie nie pobieraj treœci
                 if articles_firecrawl:
                    for article in articles_firecrawl:
                        article['source'] = 'firecrawl_scientific_search'
                    all_articles.extend(articles_firecrawl)
                    print(f"Dodano {len(articles_firecrawl)} potencjalnych artyku³ów z Firecrawl dla zapytania '{query}'.")
                 else:
                      print(f"Firecrawl nie znalaz³ wyników dla zapytania: '{firecrawl_query}'")


        total_articles = len(all_articles)
        print(f"SLSAgent zakoñczy³ pracê, zwracaj¹c ³¹cznie {total_articles} potencjalnych artyku³ów.")
        # TODO: Deduplikacja wyników (np. na podstawie DOI lub tytu³u)
        # TODO: Opcjonalna ocena relevancji przez LLM na podstawie abstraktów/snippetów
        return all_articles