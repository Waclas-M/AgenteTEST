# -*- coding: cp1252 -*- 

# agents/context_builder_agent.py
from typing import Dict, Any, List # Dodano List
# U�yj �cie�ek wzgl�dnych
from .web_search_agent import WebSearchAgent
from .sls_agent import SLSAgent
# Importujemy LLM client bezpo�rednio tutaj, bo b�dziemy go u�ywa�
from ..tools.llm_clients import generate_completion
# from .kg_agent import KnowledgeGraphConstructorAgent # Placeholder

class ContextBuilderAgent:
    def __init__(self):
        print("Inicjalizacja ContextBuilderAgent...")
        # Inicjalizacja specjalistycznych agent�w (bez Aggregatora)
        self.web_searcher = WebSearchAgent()
        self.sls_searcher = SLSAgent(use_pubmed_api=True)
        # self.kg_constructor = KnowledgeGraphConstructorAgent()
        # Usuni�to self.aggregator
        print("Agenci podrz�dni (Web, SLS) zainicjalizowani.") # Usuni�to Aggregator z logu

    # --- Metody skopiowane z ContextAggregatorAgent ---

    def _prepare_llm_prompt(self, context_data: Dict[str, Any]) -> str:
        """Przygotowuje prompt dla LLM na podstawie zebranych danych."""

        initial_text = context_data.get('initial_input_text', 'Brak tekstu wej�ciowego.')

        web_info_parts = []
        # Zak�adamy, �e web_search_results jest pust� list�, ale zostawiamy logik� na przysz�o��
        for res in context_data.get('web_search_results', []):
            info = res.get('title') if res.get('title') else res.get('snippet')
            url = res.get('url', 'N/A')
            if info:
                web_info_parts.append(f"- {info} (URL: {url})")
        web_info_str = "\n".join(web_info_parts) if web_info_parts else "Brak wynik�w z wyszukiwania w internecie (funkcjonalno�� wy��czona lub brak wynik�w)." # Zaktualizowano komunikat

        literature_abstracts = []
        for res in context_data.get('scientific_literature_results', []):
            abstract = res.get('abstract')
            title = res.get('title')
            url = res.get('url', 'N/A')
            pmid = res.get('pmid', 'N/A')
            if abstract:
                # U�ywamy \n dla nowej linii w f-string, spacja mo�e nie by� potrzebna
                literature_abstracts.append(f"- {title} (PMID: {pmid}, URL: {url}):\n{abstract}")
            elif title:
                 literature_abstracts.append(f"- {title} (PMID: {pmid}, URL: {url}) (brak abstraktu)")
        literature_info_str = "\n\n".join(literature_abstracts) if literature_abstracts else "Brak wynik�w z literatury naukowej."

        llm_prompt = f"""
        Zadanie: Jeste� specjalist� analizuj�cym dane biomedyczne. Na podstawie poni�szego **Tekstu Wej�ciowego** oraz dodatkowych informacji znalezionych w **Internecie** i **Literaturze Naukowej**, wygeneruj szczeg�owe, ustrukturyzowane i obiektywne podsumowanie kontekstu w j�zyku angielskim. Zachowaj neutralny ton. Odpowied� powinna �ci�le trzyma� si� dostarczonych informacji i mie� nast�puj�c� struktur�:

        **1. Analizowany Temat:**
        (Kr�tkie, 1-2 zdaniowe podsumowanie g��wnych poj�� i relacji opisanych w Tek�cie Wej�ciowym.)

        **2. Kluczowe Definicje:**
        (Wylistuj definicje poj�� zawarte w Tek�cie Wej�ciowym. Je�li definicji brakuje w tek�cie wej�ciowym, ale zosta�a znaleziona w �r�d�ach, mo�esz j� doda� z adnotacj� �r�d�a, np. [wg. PubMed: ID].)
        - Poj�cie 1: Definicja...
        - Poj�cie 2: Definicja...
        - ...

        **3. G��wne Powi�zania/Mechanizmy Opisane w Tek�cie Wej�ciowym:**
        (Wylistuj i opisz zwi�le relacje wspomniane w Tek�cie Wej�ciowym. Mo�esz wzbogaci� opis o 1-2 zdania kontekstu z znalezionych �r�de�, je�li bezpo�rednio dotycz� tej relacji.)
        - Relacja 1 (np. Zapalenie zwi�ksza Amyloid Beta): Opis relacji... (ewentualne wzbogacenie ze �r�de�)
        - Relacja 2 (np. Amyloid Beta akumuluje si� w Ch. Alzheimera): Opis...
        - ...

        **4. Kontekst z Literatury Naukowej:**
        (Syntetyczny przegl�d najwa�niejszych informacji i wniosk�w z abstrakt�w naukowych. Pogrupuj informacje tematycznie, je�li to mo�liwe. Unikaj bezpo�redniego cytowania poszczeg�lnych artyku��w, skup si� na zagregowanej wiedzy.)

        **5. Kontekst z Og�lnego Internetu:**
        (Podsumowanie relevantnych informacji z tytu��w/snippet�w znalezionych w Internecie. Wska� g��wne punkty lub perspektywy. Pomi� t� sekcj�, je�li brak wynik�w lub informacji.)

        **6. Synteza i Wnioski Og�lne:**
        (Kr�tkie, 2-4 zdaniowe podsumowanie ��cz�ce wszystkie zebrane informacje. Jakie s� g��wne wnioski p�yn�ce z analizy tekstu wej�ciowego w �wietle znalezionego kontekstu?)

        --- Dane Wej�ciowe dla LLM ---

        **Tekst Wej�ciowy do Analizy:**
        ```
        {initial_text}
        ```

        **Informacje z Internetu (Tytu�y/Fragmenty):**
        ```
        {web_info_str}
        ```

        **Informacje z Literatury Naukowej (Tytu�y/Abstrakty):**
        ```
        {literature_info_str}
        ```

        --- Koniec Danych Wej�ciowych ---

        Wygenerowane Podsumowanie Kontekstu (w formacie opisanym powy�ej):
        """
        return llm_prompt

    def generate_aggregated_context(self, context_data: Dict[str, Any]) -> str:
        """Generuje zagregowany kontekst tekstowy u�ywaj�c LLM."""
        print("ContextBuilderAgent: Generowanie zagregowanego kontekstu...") # Zmieniono nazw� agenta w logu

        has_literature_results = bool(context_data.get('scientific_literature_results'))
        # Mo�na te� sprawdzi� web_search_results, je�li zostan� w��czone i naprawione
        # has_web_results = bool(context_data.get('web_search_results'))
        # if not has_literature_results and not has_web_results:

        if not has_literature_results: # Na razie sprawdzamy tylko literatur�
             print("Ostrze�enie (ContextBuilderAgent): Brak wynik�w z literatury. Zwracam podstawowy kontekst.")
             return f"Analiza tekstu wej�ciowego wykaza�a nast�puj�ce poj�cia i relacje:\n{context_data.get('initial_input_text', '')}\nNie znaleziono dodatkowego kontekstu w dost�pnych �r�d�ach (Literatura Naukowa, Internet)."

        llm_prompt = self._prepare_llm_prompt(context_data)
        print("\n--- Prompt dla generowania zagregowanego kontekstu ---") # Zmieniono nazw� logu
        print(llm_prompt)
        print("--- Koniec Promptu dla generowania zagregowanego kontekstu ---\n")

        # Wywo�ujemy generate_completion bezpo�rednio
        aggregated_context = generate_completion(llm_prompt, model_preference="gemini", max_tokens=3000)

        if aggregated_context.startswith("B��d:") or not aggregated_context.strip():
            print(f"B��d (ContextBuilderAgent): LLM nie zwr�ci� poprawnego kontekstu. B��d: {aggregated_context}")
            return f"Wyst�pi� b��d podczas generowania zagregowanego kontekstu przez LLM: {aggregated_context}"
        else:
            print("ContextBuilderAgent: Pomy�lnie wygenerowano zagregowany kontekst.")
            return aggregated_context.strip()

    # --- G��wna metoda build_context ---

    def build_context(self, input_text: str) -> Dict[str, Any]:
        """Buduje kontekst, w tym zagregowane podsumowanie tekstowe."""
        print("\n=== ContextBuilderAgent: Rozpoczynanie budowania kontekstu ===")

        # Web search jest wy��czony zgodnie z ustaleniami
        # print("\n--- Uruchamianie WebSearchAgent ---")
        # web_results = self.web_searcher.search(input_text=input_text)
        web_results = []
        print(f"ContextBuilderAgent: Pomini�to WebSearchAgent (web_results ustawione na pust� list�).")

        print("\n--- Uruchamianie SLSAgent ---")
        scientific_results = self.sls_searcher.search_papers(input_text=input_text)
        print(f"ContextBuilderAgent: Otrzymano {len(scientific_results)} wynik�w z SLSAgent.")

        # --- Tutaj mo�na doda� wywo�anie KG Agenta ---

        # Stworzenie wst�pnego kontekstu
        context = {
            "initial_input_text": input_text,
            "web_search_results": web_results, # Pusta lista
            "scientific_literature_results": scientific_results,
            # "knowledge_graph": kg_results
        }

        # --- Generowanie Zagregowanego Kontekstu (bezpo�rednie wywo�anie metody) ---
        # print("\n--- Uruchamianie ContextAggregatorAgent ---") # Usuni�to log o osobnym agencie
        # Zamiast: aggregated_context_text = self.aggregator.generate_aggregated_context(context)
        # U�ywamy:
        aggregated_context_text = self.generate_aggregated_context(context) # <--- BEZPO�REDNIE WYWO�ANIE
        context['aggregated_context'] = aggregated_context_text # Dodajemy wynik do s�ownika

        print("\n=== ContextBuilderAgent: Zako�czono budowanie kontekstu (z agregacj�) ===")
        return context