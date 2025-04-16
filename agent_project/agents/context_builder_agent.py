# -*- coding: cp1252 -*- 

# agents/context_builder_agent.py
from typing import Dict, Any, List # Dodano List
# U¿yj œcie¿ek wzglêdnych
from .web_search_agent import WebSearchAgent
from .sls_agent import SLSAgent
# Importujemy LLM client bezpoœrednio tutaj, bo bêdziemy go u¿ywaæ
from ..tools.llm_clients import generate_completion
# from .kg_agent import KnowledgeGraphConstructorAgent # Placeholder

class ContextBuilderAgent:
    def __init__(self):
        print("Inicjalizacja ContextBuilderAgent...")
        # Inicjalizacja specjalistycznych agentów (bez Aggregatora)
        self.web_searcher = WebSearchAgent()
        self.sls_searcher = SLSAgent(use_pubmed_api=True)
        # self.kg_constructor = KnowledgeGraphConstructorAgent()
        # Usuniêto self.aggregator
        print("Agenci podrzêdni (Web, SLS) zainicjalizowani.") # Usuniêto Aggregator z logu

    # --- Metody skopiowane z ContextAggregatorAgent ---

    def _prepare_llm_prompt(self, context_data: Dict[str, Any]) -> str:
        """Przygotowuje prompt dla LLM na podstawie zebranych danych."""

        initial_text = context_data.get('initial_input_text', 'Brak tekstu wejœciowego.')

        web_info_parts = []
        # Zak³adamy, ¿e web_search_results jest pust¹ list¹, ale zostawiamy logikê na przysz³oœæ
        for res in context_data.get('web_search_results', []):
            info = res.get('title') if res.get('title') else res.get('snippet')
            url = res.get('url', 'N/A')
            if info:
                web_info_parts.append(f"- {info} (URL: {url})")
        web_info_str = "\n".join(web_info_parts) if web_info_parts else "Brak wyników z wyszukiwania w internecie (funkcjonalnoœæ wy³¹czona lub brak wyników)." # Zaktualizowano komunikat

        literature_abstracts = []
        for res in context_data.get('scientific_literature_results', []):
            abstract = res.get('abstract')
            title = res.get('title')
            url = res.get('url', 'N/A')
            pmid = res.get('pmid', 'N/A')
            if abstract:
                # U¿ywamy \n dla nowej linii w f-string, spacja mo¿e nie byæ potrzebna
                literature_abstracts.append(f"- {title} (PMID: {pmid}, URL: {url}):\n{abstract}")
            elif title:
                 literature_abstracts.append(f"- {title} (PMID: {pmid}, URL: {url}) (brak abstraktu)")
        literature_info_str = "\n\n".join(literature_abstracts) if literature_abstracts else "Brak wyników z literatury naukowej."

        llm_prompt = f"""
        Zadanie: Jesteœ specjalist¹ analizuj¹cym dane biomedyczne. Na podstawie poni¿szego **Tekstu Wejœciowego** oraz dodatkowych informacji znalezionych w **Internecie** i **Literaturze Naukowej**, wygeneruj szczegó³owe, ustrukturyzowane i obiektywne podsumowanie kontekstu w jêzyku angielskim. Zachowaj neutralny ton. OdpowiedŸ powinna œciœle trzymaæ siê dostarczonych informacji i mieæ nastêpuj¹c¹ strukturê:

        **1. Analizowany Temat:**
        (Krótkie, 1-2 zdaniowe podsumowanie g³ównych pojêæ i relacji opisanych w Tekœcie Wejœciowym.)

        **2. Kluczowe Definicje:**
        (Wylistuj definicje pojêæ zawarte w Tekœcie Wejœciowym. Jeœli definicji brakuje w tekœcie wejœciowym, ale zosta³a znaleziona w Ÿród³ach, mo¿esz j¹ dodaæ z adnotacj¹ Ÿród³a, np. [wg. PubMed: ID].)
        - Pojêcie 1: Definicja...
        - Pojêcie 2: Definicja...
        - ...

        **3. G³ówne Powi¹zania/Mechanizmy Opisane w Tekœcie Wejœciowym:**
        (Wylistuj i opisz zwiêŸle relacje wspomniane w Tekœcie Wejœciowym. Mo¿esz wzbogaciæ opis o 1-2 zdania kontekstu z znalezionych Ÿróde³, jeœli bezpoœrednio dotycz¹ tej relacji.)
        - Relacja 1 (np. Zapalenie zwiêksza Amyloid Beta): Opis relacji... (ewentualne wzbogacenie ze Ÿróde³)
        - Relacja 2 (np. Amyloid Beta akumuluje siê w Ch. Alzheimera): Opis...
        - ...

        **4. Kontekst z Literatury Naukowej:**
        (Syntetyczny przegl¹d najwa¿niejszych informacji i wniosków z abstraktów naukowych. Pogrupuj informacje tematycznie, jeœli to mo¿liwe. Unikaj bezpoœredniego cytowania poszczególnych artyku³ów, skup siê na zagregowanej wiedzy.)

        **5. Kontekst z Ogólnego Internetu:**
        (Podsumowanie relevantnych informacji z tytu³ów/snippetów znalezionych w Internecie. Wska¿ g³ówne punkty lub perspektywy. Pomiñ tê sekcjê, jeœli brak wyników lub informacji.)

        **6. Synteza i Wnioski Ogólne:**
        (Krótkie, 2-4 zdaniowe podsumowanie ³¹cz¹ce wszystkie zebrane informacje. Jakie s¹ g³ówne wnioski p³yn¹ce z analizy tekstu wejœciowego w œwietle znalezionego kontekstu?)

        --- Dane Wejœciowe dla LLM ---

        **Tekst Wejœciowy do Analizy:**
        ```
        {initial_text}
        ```

        **Informacje z Internetu (Tytu³y/Fragmenty):**
        ```
        {web_info_str}
        ```

        **Informacje z Literatury Naukowej (Tytu³y/Abstrakty):**
        ```
        {literature_info_str}
        ```

        --- Koniec Danych Wejœciowych ---

        Wygenerowane Podsumowanie Kontekstu (w formacie opisanym powy¿ej):
        """
        return llm_prompt

    def generate_aggregated_context(self, context_data: Dict[str, Any]) -> str:
        """Generuje zagregowany kontekst tekstowy u¿ywaj¹c LLM."""
        print("ContextBuilderAgent: Generowanie zagregowanego kontekstu...") # Zmieniono nazwê agenta w logu

        has_literature_results = bool(context_data.get('scientific_literature_results'))
        # Mo¿na te¿ sprawdziæ web_search_results, jeœli zostan¹ w³¹czone i naprawione
        # has_web_results = bool(context_data.get('web_search_results'))
        # if not has_literature_results and not has_web_results:

        if not has_literature_results: # Na razie sprawdzamy tylko literaturê
             print("Ostrze¿enie (ContextBuilderAgent): Brak wyników z literatury. Zwracam podstawowy kontekst.")
             return f"Analiza tekstu wejœciowego wykaza³a nastêpuj¹ce pojêcia i relacje:\n{context_data.get('initial_input_text', '')}\nNie znaleziono dodatkowego kontekstu w dostêpnych Ÿród³ach (Literatura Naukowa, Internet)."

        llm_prompt = self._prepare_llm_prompt(context_data)
        print("\n--- Prompt dla generowania zagregowanego kontekstu ---") # Zmieniono nazwê logu
        print(llm_prompt)
        print("--- Koniec Promptu dla generowania zagregowanego kontekstu ---\n")

        # Wywo³ujemy generate_completion bezpoœrednio
        aggregated_context = generate_completion(llm_prompt, model_preference="gemini", max_tokens=3000)

        if aggregated_context.startswith("B³¹d:") or not aggregated_context.strip():
            print(f"B³¹d (ContextBuilderAgent): LLM nie zwróci³ poprawnego kontekstu. B³¹d: {aggregated_context}")
            return f"Wyst¹pi³ b³¹d podczas generowania zagregowanego kontekstu przez LLM: {aggregated_context}"
        else:
            print("ContextBuilderAgent: Pomyœlnie wygenerowano zagregowany kontekst.")
            return aggregated_context.strip()

    # --- G³ówna metoda build_context ---

    def build_context(self, input_text: str) -> Dict[str, Any]:
        """Buduje kontekst, w tym zagregowane podsumowanie tekstowe."""
        print("\n=== ContextBuilderAgent: Rozpoczynanie budowania kontekstu ===")

        # Web search jest wy³¹czony zgodnie z ustaleniami
        # print("\n--- Uruchamianie WebSearchAgent ---")
        # web_results = self.web_searcher.search(input_text=input_text)
        web_results = []
        print(f"ContextBuilderAgent: Pominiêto WebSearchAgent (web_results ustawione na pust¹ listê).")

        print("\n--- Uruchamianie SLSAgent ---")
        scientific_results = self.sls_searcher.search_papers(input_text=input_text)
        print(f"ContextBuilderAgent: Otrzymano {len(scientific_results)} wyników z SLSAgent.")

        # --- Tutaj mo¿na dodaæ wywo³anie KG Agenta ---

        # Stworzenie wstêpnego kontekstu
        context = {
            "initial_input_text": input_text,
            "web_search_results": web_results, # Pusta lista
            "scientific_literature_results": scientific_results,
            # "knowledge_graph": kg_results
        }

        # --- Generowanie Zagregowanego Kontekstu (bezpoœrednie wywo³anie metody) ---
        # print("\n--- Uruchamianie ContextAggregatorAgent ---") # Usuniêto log o osobnym agencie
        # Zamiast: aggregated_context_text = self.aggregator.generate_aggregated_context(context)
        # U¿ywamy:
        aggregated_context_text = self.generate_aggregated_context(context) # <--- BEZPOŒREDNIE WYWO£ANIE
        context['aggregated_context'] = aggregated_context_text # Dodajemy wynik do s³ownika

        print("\n=== ContextBuilderAgent: Zakoñczono budowanie kontekstu (z agregacj¹) ===")
        return context