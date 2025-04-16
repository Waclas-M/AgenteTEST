# -*- coding: cp1252 -*-

# agents/web_search_agent.py
from typing import List, Dict, Any
# U�yj �cie�ek wzgl�dnych do import�w
from ..tools.llm_clients import generate_completion
from ..tools.api_clients import search_firecrawl

class WebSearchAgent:
    def _generate_queries(self, subgraph: Any, prompt: str, num_queries: int = 3) -> List[str]:
        """Generuje zapytania do wyszukiwarki u�ywaj�c LLM."""
        # Przygotuj prompt dla LLM
        # TODO: Ulepszy� ekstrakcj� informacji z subgraph
        subgraph_str = str(subgraph) # Prosta konwersja na string, mo�na ulepszy�
        llm_prompt = f"""
        Na podstawie poni�szego podgrafu wiedzy i g��wnego zapytania u�ytkownika, wygeneruj {num_queries} r�norodnych zapyta� do og�lnej wyszukiwarki internetowej (np. Google).
        Zapytania powinny pom�c znale�� og�lne informacje, kontekst, wiadomo�ci i potencjalnie powi�zane koncepcje.
        Format odpowiedzi: Ka�de zapytanie w nowej linii, bez numeracji.

        Podgraf:
        {subgraph_str}

        G��wne zapytanie u�ytkownika:
        {prompt}

        Wygenerowane zapytania:
        """
        print("Generowanie zapyta� dla WebSearch u�ywaj�c LLM...")
        raw_queries = generate_completion(llm_prompt)

        if raw_queries.startswith("B��d:") or not raw_queries.strip():
             print(f"Nie uda�o si� wygenerowa� zapyta� przez LLM. U�ywanie domy�lnego zapytania. B��d: {raw_queries}")
             return [prompt] # Fallback

        # Przetwarzanie odpowiedzi LLM
        queries = [q.strip() for q in raw_queries.strip().split('\n') if q.strip()]
        print(f"Wygenerowane zapytania przez LLM: {queries}")
        return queries if queries else [prompt] # Zwr�� wygenerowane lub fallback

    def search(self, subgraph: Any, prompt: str, max_results_per_query: int = 3) -> List[Dict[str, Any]]:
        """Przeszukuje internet u�ywaj�c Firecrawl z zapytaniami generowanymi przez LLM."""
        queries = self._generate_queries(subgraph, prompt)
        all_results = []

        for query in queries:
            # U�yj funkcji z api_clients
            results = search_firecrawl(query, fetch_content=True, max_results=max_results_per_query)
            all_results.extend(results)
            # Opcjonalnie: Zastosuj LLM do podsumowania/ekstrakcji z 'content' wynik�w, je�li potrzebne
            # for result in results:
            #     if result.get('content'):
            #         summary_prompt = f"Podsumuj poni�szy tekst w kontek�cie zapytania '{query}':\n\n{result['content'][:2000]}" # Ogranicz d�ugo��
            #         summary = generate_completion(summary_prompt)
            #         result['llm_summary'] = summary # Dodaj podsumowanie do wyniku

        total_results = len(all_results)
        print(f"WebSearchAgent zako�czy� prac�, zwracaj�c {total_results} wynik�w.")
        # Mo�na doda� logik� deduplikacji wynik�w, je�li wiele zapyta� zwraca te same URL
        # unique_results = {r['url']: r for r in all_results}.values()
        # print(f"Po deduplikacji pozosta�o {len(unique_results)} wynik�w.")
        # return list(unique_results)
        return all_results