# -*- coding: cp1252 -*-
# tools/api_clients.py
from typing import List, Dict, Any, Optional
from ..config import settings

# --- Firecrawl Client ---
try:
    from firecrawl import FirecrawlApp
    if settings.FIRECRAWL_API_KEY:
        firecrawl_client = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)
        print("Klient Firecrawl zainicjalizowany.")
    else:
        firecrawl_clie/home/wiktor/hackathon/hackathon/langgraph/Zespol_EjAjownt = None
        print("Ostrze¿enie: Klucz API Firecrawl nie jest dostêpny. Klient nieaktywny.")
except ImportError:
    firecrawl_client = None
    print("Ostrze¿enie: Biblioteka firecrawl-py nie jest zainstalowana.")


def search_firecrawl(query: str, fetch_content: bool = True, max_results: int = 5) -> List[Dict[str, Any]]:
    """Wykonuje wyszukiwanie za pomoc¹ Firecrawl."""
    if not firecrawl_client:
        print("B³¹d: Klient Firecrawl jest nieaktywny.")
        return []
    try:
        print(f"Wysy³anie zapytania do Firecrawl: {query}")
        # Wywo³anie API Firecrawl - BEZ limitowania wyników tutaj, jeœli API go nie wspiera bezpoœrednio
        # (parametr max_results tutaj jest tylko dla informacji, nie u¿ywamy go do krojenia poni¿ej)
        results = firecrawl_client.search(
            query,
            params={'pageOptions': {'fetchPageContent': fetch_content}}
        )
        # SprawdŸ typ wyniku na wszelki wypadek
        if not isinstance(results, list):
             print(f"Ostrze¿enie: Firecrawl API zwróci³o nieoczekiwany typ danych ({type(results)}), oczekiwano listy.")
             # Spróbuj obs³u¿yæ, jeœli to mo¿liwe, lub zwróæ pust¹ listê
             if isinstance(results, dict) and 'data' in results and isinstance(results['data'], list):
                  results = results['data'] # Próba odzyskania listy z typowej struktury API
             else:
                  return [] # Zwróæ pust¹ listê, jeœli nie mo¿na przetworzyæ

        print(f"Otrzymano {len(results)} wyników z Firecrawl dla zapytania '{query}'")

        formatted_results = []
        # Iteruj po WSZYSTKICH wynikach zwróconych przez API
        for res in results: # <--- Iterujemy po results_list
            if isinstance(res, dict):
                # U¿yj 'title' jeœli jest, inaczej spróbuj 'name' (standardowo Firecrawl zwraca 'title')
                # U¿yj 'description' jeœli jest, inaczej spróbuj 'snippet'
                # U¿yj 'markdown' lub 'content' jeœli jest, inaczej None
                title = res.get('title') or res.get('name')
                snippet = res.get('description') or res.get('snippet')
                content = None
                if fetch_content:
                    content = res.get('markdown') or res.get('content') # Dodaj inne mo¿liwe klucze treœci, jeœli znasz

                formatted_results.append({
                    'url': res.get('url'),
                    'title': title,
                    'snippet': snippet,
                    'content': content,
                    'source': 'firecrawl_search'
                })
            else:
                 print(f"Ostrze¿enie: Pomiêto nieprawid³owy element wyniku Firecrawl: {res}")

        return formatted_results
    except Exception as e:
        print(f"B³¹d podczas wyszukiwania w Firecrawl dla zapytania '{query}': {e}")
        # Dodajmy traceback dla lepszego debugowania
        import traceback
        traceback.print_exc()
        return []

# --- PubMed (Entrez) Client ---
try:
    from Bio import Entrez
    Entrez.email = settings.PUBMED_EMAIL
    if not Entrez.email or Entrez.email == "wiktortobota13@gmail.com":
        print("Ostrze¿enie: Nie ustawiono prawid³owego adresu email dla PubMed Entrez w .env (PUBMED_EMAIL).")
        entrez_active = False
    else:
         print(f"Klient PubMed Entrez skonfigurowany z emailem: {Entrez.email}")
         entrez_active = True

except ImportError:
    Entrez = None
    entrez_active = False
    print("Ostrze¿enie: Biblioteka biopython nie jest zainstalowana. PubMed Entrez nie bêdzie dzia³aæ.")


def search_pubmed_entrez(query: str, max_results: int = 5) -> Optional[List[Dict[str, Any]]]:
    """Wyszukuje w PubMed u¿ywaj¹c Bio.Entrez."""
    if not entrez_active or not Entrez:
        print("Nie mo¿na u¿yæ PubMed API (Entrez): Klient nieaktywny lub brak biblioteki/emaila.")
        return None # Zwróæ None, aby wskazaæ problem z t¹ metod¹

    try:
        print(f"Wysy³anie zapytania do PubMed (Entrez): {query}")
        handle = Entrez.esearch(db="pubmed", term=query, retmax=str(max_results), api_key=settings.PUBMED_API_KEY) # Dodano opcjonalny klucz API
        record = Entrez.read(handle)
        handle.close()
        pmids = record["IdList"]

        if not pmids:
            print("PubMed (Entrez): Nie znaleziono artyku³ów.")
            return [] # Zwróæ pust¹ listê, jeœli nie ma wyników

        print(f"PubMed (Entrez): Znaleziono {len(pmids)} ID artyku³ów.")
        handle = Entrez.efetch(db="pubmed", id=pmids, rettype="medline", retmode="xml", api_key=settings.PUBMED_API_KEY) # Dodano opcjonalny klucz API
        records = Entrez.read(handle)
        handle.close()

        articles = []
        pubmed_articles = records.get('PubmedArticle', [])
        if isinstance(pubmed_articles, dict): pubmed_articles = [pubmed_articles]

        for article_data in pubmed_articles:
             medline_citation = article_data.get('MedlineCitation')
             if not medline_citation: continue
             article_info = medline_citation.get('Article', {})
             title = article_info.get('ArticleTitle', 'Brak tytu³u')
             abstract_dict = article_info.get('Abstract', {})
             abstract = abstract_dict.get('AbstractText', [''])[0]

             doi = None
             article_ids = article_info.get('ELocationID', [])
             if not isinstance(article_ids, list): article_ids = [article_ids]
             for identifier in article_ids:
                  if identifier.attributes.get('EIdType') == 'doi':
                       doi = str(identifier)
                       break
             if not doi:
                  pubmed_data = article_data.get('PubmedData', {})
                  article_id_list = pubmed_data.get('ArticleIdList', [])
                  if isinstance(article_id_list, dict): article_id_list = article_id_list.get('ArticleId', [])
                  if not isinstance(article_id_list, list): article_id_list = [article_id_list]
                  for identifier in article_id_list:
                       if identifier.attributes.get('IdType') == 'doi':
                            doi = str(identifier)
                            break

             pmid = medline_citation.get('PMID', '')
             authors_list = article_info.get('AuthorList', [])
             authors = []
             if authors_list:
                  for author_entry in authors_list:
                       if isinstance(author_entry, dict):
                            lastname = author_entry.get('LastName', '')
                            forename = author_entry.get('ForeName', '')
                            if lastname and forename: authors.append(f"{forename} {lastname}")

             articles.append({
                 'title': str(title), 'authors': authors, 'abstract': str(abstract),
                 'doi': doi, 'pmid': str(pmid),
                 'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                 'source': 'pubmed_entrez'
             })
        print(f"PubMed (Entrez): Pomyœlnie przetworzono {len(articles)} artyku³ów.")
        return articles

    except Exception as e:
        print(f"B³¹d podczas wyszukiwania w PubMed (Entrez): {e}")
        # Mo¿na logowaæ szczegó³y b³êdu
        # Sprawdzenie specyficznych b³êdów Entrez (np. 429 Too Many Requests)
        if "HTTP Error 429" in str(e):
             print("B³¹d Entrez: Przekroczono limit zapytañ. Spróbuj ponownie póŸniej.")
        return None # Zwróæ None w przypadku b³êdu