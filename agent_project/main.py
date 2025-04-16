# -*- coding: cp1252 -*-

# main.py
import json
# Importuj z odpowiednich modu³ów u¿ywaj¹c struktury pakietu
from agent_project.agents.context_builder_agent import ContextBuilderAgent
from .config import settings # Aby sprawdziæ czy klucze s¹ za³adowane



def run_context_building():
    """G³ówna funkcja uruchamiaj¹ca proces budowania kontekstu."""

    print("="*50)
    print(" Rozpoczynanie procesu budowania kontekstu")
    print("="*50)

    # Sprawdzenie kluczy (opcjonalne)
    if not settings.FIRECRAWL_API_KEY:
        print("OSTRZE¯ENIE: Brak klucza API Firecrawl! Wyszukiwanie mo¿e nie dzia³aæ.")
    if not settings.GEMINI_API_KEY and not settings.OPENAI_API_KEY:
        print("OSTRZE¯ENIE: Brak kluczy API LLM! Generowanie zapytañ bêdzie ograniczone.")
    if not settings.PUBMED_EMAIL or settings.PUBMED_EMAIL == "default.email@example.com":
        print("OSTRZE¯ENIE: Brak prawid³owego emaila dla PubMed Entrez! Wyszukiwanie w PubMed mo¿e nie dzia³aæ.")

    # Przyk³adowy subgraph i prompt
   # example_subgraph = {
   #     "nodes": [{"id": "1", "name": "Chronic Kidney Disease"}, {"id": "2", "name": "Anemia"}],
   #     "edges": [{"source": "1", "target": "2", "relation": "associated_with"}]
   # }
    #with open('/home/wiktor/hackathon/hackathon/sample_subgraph.json', 'r') as f:
    #    example_subgraph = json.load(f)

    #example_prompt = "Investigate how inflammation influences the development of Alzheimer’s disease by analyzing the mechanisms related to amyloid beta accumulation, the role of tau protein, and microglial activation, as illustrated in the provided knowledge graph."

    analysis_text = """# Ontologist Analysis
                    {
                    ### Definitions:
                    - **Inflammation**: A biological response of body tissues to harmful stimuli, such as pathogens, damaged cells, or irritants. It involves immune cell activation, blood vessel dilation, and the release of various molecules that promote healing.
                    - **Amyloid Beta**: A peptide that is produced in the brain through the breakdown of a larger protein called amyloid precursor protein (APP). Accumulation of amyloid beta in the brain is commonly associated with neurodegenerative diseases, especially Alzheimer's disease.
                    - **Alzheimer's Disease**: A progressive neurological disorder characterized by cognitive decline, memory loss, and changes in behavior and personality. It is associated with the accumulation of amyloid beta plaques and neurofibrillary tangles in the brain.

                    ### Relationships
                    - **Inflammation increases Amyloid Beta**: This relationship indicates that the presence of inflammation in the brain can lead to an increase in the production or aggregation of amyloid beta peptides. This connection suggests that inflammatory processes might play a crucial role in the pathogenesis of Alzheimer's disease by enhancing the toxic effects of amyloid beta.
                      
                    - **Amyloid Beta accumulates in Alzheimer's Disease**: This relationship illustrates how the accumulation of amyloid beta is a defining feature of Alzheimer's disease. In patients with Alzheimer’s, there is a significant build-up of amyloid beta plaques in the brain, which is believed to contribute to the neurodegenerative processes observed in the disorder, such as synaptic dysfunction and neuronal death.
                    }"""

    print("\nDane wejœciowe:")
    #print(f"  Subgraph: {json.dumps(example_subgraph, indent=2)}")
    #print(f"  Prompt: {example_prompt}")
    print(f" Tekst wejœciowy analizy: {analysis_text}")
    # Utworzenie i uruchomienie g³ównego agenta
    context_builder = ContextBuilderAgent()
    final_context = context_builder.build_context(input_text=analysis_text)

    print("\n" + "="*50)
    print(" Finalny Kontekst Zosta³ Zbudowany")
    print("="*50)

    # Wyœwietlenie podsumowania wyników
    print(f"Liczba wyników z wyszukiwania web: {len(final_context.get('web_search_results', []))}")
    print(f"Liczba wyników z literatury naukowej: {len(final_context.get('scientific_literature_results', []))}")

    # Opcjonalnie: Zapisz kontekst do pliku JSON
    try:
        output_filename = "final_context.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(final_context, f, indent=4, ensure_ascii=False)
        print(f"\nPe³ny kontekst zapisano do pliku: {output_filename}")
    except Exception as e:
        print(f"\nB³¹d podczas zapisywania kontekstu do pliku: {e}")

    # Mo¿esz tutaj dodaæ kod do dalszego przetwarzania `final_context`

if __name__ == "__main__":
    run_context_building()