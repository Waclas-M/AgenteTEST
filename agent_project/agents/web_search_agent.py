# -*- coding: cp1252 -*-

# agents/web_search_agent.py
from typing import List, Dict, Any
# U¿yj œcie¿ek wzglêdnych do importów
from ..tools.llm_clients import generate_completion
from ..tools.api_clients import search_firecrawl

class WebSearchAgent:
    def _generate_queries(self, subgraph: Any, prompt: str, num_queries: int = 3) -> List[str]:
        """Generuje zapytania do wyszukiwarki u¿ywaj¹c LLM."""
        # Przygotuj prompt dla LLM
        # TODO: Ulepszyæ ekstrakcjê informacji z subgraph
        subgraph_str = str(subgraph) # Prosta konwersja na string, mo¿na ulepszyæ
        llm_prompt = f"""
        Na podstawie poni¿szego podgrafu wiedzy i g³ównego zapytania u¿ytkownika, wygeneruj {num_queries} ró¿norodnych zapytañ do ogólnej wyszukiwarki internetowej (np. Google).
        Zapytania powinny pomóc znaleŸæ ogólne informacje, kontekst, wiadomoœci i potencjalnie powi¹zane koncepcje.
        Format odpowiedzi: Ka¿de zapytanie w nowej linii, bez numeracji.

        Podgraf:
        {subgraph_str}

        G³ówne zapytanie u¿ytkownika:
        {prompt}

        Wygenerowane zapytania:
        """
        print("Generowanie zapytañ dla WebSearch u¿ywaj¹c LLM...")
        raw_queries = generate_completion(llm_prompt)

        if raw_queries.startswith("B³¹d:") or not raw_queries.strip():
             print(f"Nie uda³o siê wygenerowaæ zapytañ przez LLM. U¿ywanie domyœlnego zapytania. B³¹d: {raw_queries}")
             return [prompt] # Fallback

        # Przetwarzanie odpowiedzi LLM
        queries = [q.strip() for q in raw_queries.strip().split('\n') if q.strip()]
        print(f"Wygenerowane zapytania przez LLM: {queries}")
        return queries if queries else [prompt] # Zwróæ wygenerowane lub fallback

    def search(self, subgraph: Any, prompt: str, max_results_per_query: int = 3) -> List[Dict[str, Any]]:
        """Przeszukuje internet u¿ywaj¹c Firecrawl z zapytaniami generowanymi przez LLM."""
        queries = self._generate_queries(subgraph, prompt)
        all_results = []

        for query in queries:
            # U¿yj funkcji z api_clients
            results = search_firecrawl(query, fetch_content=True, max_results=max_results_per_query)
            all_results.extend(results)
            # Opcjonalnie: Zastosuj LLM do podsumowania/ekstrakcji z 'content' wyników, jeœli potrzebne
            # for result in results:
            #     if result.get('content'):
            #         summary_prompt = f"Podsumuj poni¿szy tekst w kontekœcie zapytania '{query}':\n\n{result['content'][:2000]}" # Ogranicz d³ugoœæ
            #         summary = generate_completion(summary_prompt)
            #         result['llm_summary'] = summary # Dodaj podsumowanie do wyniku

        total_results = len(all_results)
        print(f"WebSearchAgent zakoñczy³ pracê, zwracaj¹c {total_results} wyników.")
        # Mo¿na dodaæ logikê deduplikacji wyników, jeœli wiele zapytañ zwraca te same URL
        # unique_results = {r['url']: r for r in all_results}.values()
        # print(f"Po deduplikacji pozosta³o {len(unique_results)} wyników.")
        # return list(unique_results)
        return all_results