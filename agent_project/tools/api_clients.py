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
        print("Ostrze�enie: Klucz API Firecrawl nie jest dost�pny. Klient nieaktywny.")
except ImportError:
    firecrawl_client = None
    print("Ostrze�enie: Biblioteka firecrawl-py nie jest zainstalowana.")


def search_firecrawl(query: str, fetch_content: bool = True, max_results: int = 5) -> List[Dict[str, Any]]:
    """Wykonuje wyszukiwanie za pomoc� Firecrawl."""
    if not firecrawl_client:
        print("B��d: Klient Firecrawl jest nieaktywny.")
        return []
    try:
        print(f"Wysy�anie zapytania do Firecrawl: {query}")
        # Wywo�anie API Firecrawl - BEZ limitowania wynik�w tutaj, je�li API go nie wspiera bezpo�rednio
        # (parametr max_results tutaj jest tylko dla informacji, nie u�ywamy go do krojenia poni�ej)
        results = firecrawl_client.search(
            query,
            params={'pageOptions': {'fetchPageContent': fetch_content}}
        )
        # Sprawd� typ wyniku na wszelki wypadek
        if not isinstance(results, list):
             print(f"Ostrze�enie: Firecrawl API zwr�ci�o nieoczekiwany typ danych ({type(results)}), oczekiwano listy.")
             # Spr�buj obs�u�y�, je�li to mo�liwe, lub zwr�� pust� list�
             if isinstance(results, dict) and 'data' in results and isinstance(results['data'], list):
                  results = results['data'] # Pr�ba odzyskania listy z typowej struktury API
             else:
                  return [] # Zwr�� pust� list�, je�li nie mo�na przetworzy�

        print(f"Otrzymano {len(results)} wynik�w z Firecrawl dla zapytania '{query}'")

        formatted_results = []
        # Iteruj po WSZYSTKICH wynikach zwr�conych przez API
        for res in results: # <--- Iterujemy po results_list
            if isinstance(res, dict):
                # U�yj 'title' je�li jest, inaczej spr�buj 'name' (standardowo Firecrawl zwraca 'title')
                # U�yj 'description' je�li jest, inaczej spr�buj 'snippet'
                # U�yj 'markdown' lub 'content' je�li jest, inaczej None
                title = res.get('title') or res.get('name')
                snippet = res.get('description') or res.get('snippet')
                content = None
                if fetch_content:
                    content = res.get('markdown') or res.get('content') # Dodaj inne mo�liwe klucze tre�ci, je�li znasz

                formatted_results.append({
                    'url': res.get('url'),
                    'title': title,
                    'snippet': snippet,
                    'content': content,
                    'source': 'firecrawl_search'
                })
            else:
                 print(f"Ostrze�enie: Pomi�to nieprawid�owy element wyniku Firecrawl: {res}")

        return formatted_results
    except Exception as e:
        print(f"B��d podczas wyszukiwania w Firecrawl dla zapytania '{query}': {e}")
        # Dodajmy traceback dla lepszego debugowania
        import traceback
        traceback.print_exc()
        return []

# --- PubMed (Entrez) Client ---
try:
    from Bio import Entrez
    Entrez.email = settings.PUBMED_EMAIL
    if not Entrez.email or Entrez.email == "wiktortobota13@gmail.com":
        print("Ostrze�enie: Nie ustawiono prawid�owego adresu email dla PubMed Entrez w .env (PUBMED_EMAIL).")
        entrez_active = False
    else:
         print(f"Klient PubMed Entrez skonfigurowany z emailem: {Entrez.email}")
         entrez_active = True

except ImportError:
    Entrez = None
    entrez_active = False
    print("Ostrze�enie: Biblioteka biopython nie jest zainstalowana. PubMed Entrez nie b�dzie dzia�a�.")


def search_pubmed_entrez(query: str, max_results: int = 5) -> Optional[List[Dict[str, Any]]]:
    """Wyszukuje w PubMed u�ywaj�c Bio.Entrez."""
    if not entrez_active or not Entrez:
        print("Nie mo�na u�y� PubMed API (Entrez): Klient nieaktywny lub brak biblioteki/emaila.")
        return None # Zwr�� None, aby wskaza� problem z t� metod�

    try:
        print(f"Wysy�anie zapytania do PubMed (Entrez): {query}")
        handle = Entrez.esearch(db="pubmed", term=query, retmax=str(max_results), api_key=settings.PUBMED_API_KEY) # Dodano opcjonalny klucz API
        record = Entrez.read(handle)
        handle.close()
        pmids = record["IdList"]

        if not pmids:
            print("PubMed (Entrez): Nie znaleziono artyku��w.")
            return [] # Zwr�� pust� list�, je�li nie ma wynik�w

        print(f"PubMed (Entrez): Znaleziono {len(pmids)} ID artyku��w.")
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
             title = article_info.get('ArticleTitle', 'Brak tytu�u')
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
        print(f"PubMed (Entrez): Pomy�lnie przetworzono {len(articles)} artyku��w.")
        return articles

    except Exception as e:
        print(f"B��d podczas wyszukiwania w PubMed (Entrez): {e}")
        # Mo�na logowa� szczeg�y b��du
        # Sprawdzenie specyficznych b��d�w Entrez (np. 429 Too Many Requests)
        if "HTTP Error 429" in str(e):
             print("B��d Entrez: Przekroczono limit zapyta�. Spr�buj ponownie p�niej.")
        return None # Zwr�� None w przypadku b��du