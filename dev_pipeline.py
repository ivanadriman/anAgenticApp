"""
Two-Agent Writer & Critic Pipeline Prototype.
Demonstrates iterative multi-agent collaboration using Gemini models with
multi-source academic and scholarly grounding (arXiv, Crossref, Semantic Scholar, OpenAlex, PubMed, Wikipedia, PDF/Docs).
"""

import os
import sys
import re
import json
import argparse
import urllib.request
import urllib.parse
from typing import Optional, List, Dict, Any, Tuple
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Load environment variables
load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is missing. Check your .env file.")

DEFAULT_MODEL = "gemini-3.5-flash-lite"
console = Console(force_terminal=True, legacy_windows=False)
client = genai.Client(api_key=API_KEY)

POLITE_EMAIL = "agenticapp.research@gmail.com"


class CritiqueResult(BaseModel):
    score: float = Field(description="Rating from 1.0 to 10.0")
    status: str = Field(description="'APPROVED' if score >= 8.5 else 'NEEDS_REVISION'")
    strengths: list[str] = Field(description="List of positive aspects of the draft")
    weaknesses: list[str] = Field(description="List of weak areas or flaws found")
    actionable_revisions: list[str] = Field(description="Clear, numbered instructions for the writer to improve the next draft")


# ==============================================================================
# Scholarly Grounding & Document Reading Helpers
# ==============================================================================

def resolve_multilingual_queries(topic: str, lang: str = "en") -> Dict[str, Any]:
    """Formulate global STEM search keywords and regional keywords.
    When Indonesian or non-English input is provided, global literature databases
    (arXiv, PubMed, Semantic Scholar, Crossref, OpenAlex) require English scientific terms
    to return rich literature, while regional encyclopedias and local indices benefit from native terms.
    """
    dict_map = {
        "persepsi wicara": "speech perception",
        "persepsi suara": "sound perception",
        "pemrosesan auditori": "auditory processing",
        "kecerdasan buatan": "artificial intelligence",
        "pembelajaran mesin": "machine learning",
        "pembelajaran mendalam": "deep learning",
        "jaringan saraf": "neural networks",
        "komputasi kuantum": "quantum computing",
        "kriptografi kuantum": "quantum cryptography",
        "keamanan siber": "cybersecurity",
        "rekayasa perangkat lunak": "software engineering",
        "pemrosesan bahasa alami": "natural language processing",
        "diagnosis medis": "medical diagnosis",
        "pelayanan kesehatan": "healthcare medicine",
        "penyakit kardiovaskular": "cardiovascular disease",
        "perubahan iklim": "climate change",
        "energi terbarukan": "renewable energy",
        "komputasi awan": "cloud computing",
        "arsitektur mikroservis": "microservices architecture",
        "biologi molekuler": "molecular biology",
        "ilmu saraf": "neuroscience"
    }

    lower = topic.lower()
    global_query = topic
    is_id = (lang == "id")

    for id_term, en_term in dict_map.items():
        if id_term in lower:
            global_query = re.sub(re.escape(id_term), en_term, global_query, flags=re.IGNORECASE)
            is_id = True

    id_words = ["yang", "dan", "di", "dari", "untuk", "pada", "adalah", "dengan", "dalam", "bagaimana", "cara", "dampak", "pengaruh", "analisis", "tentang", "wicara", "persepsi"]
    if any(w in lower.split() for w in id_words):
        is_id = True

    # Try LLM query formulation if available
    try:
        prompt = f"""Task: Formulate global STEM academic query.
Topic: "{topic}"
If the topic is in Indonesian or non-English, extract 2-4 concise English scientific keywords for arXiv, PubMed, and Semantic Scholar.
Respond ONLY with JSON:
{{"global_stem": "...", "regional": "{topic}", "is_indonesian": {str(is_id).lower()}}}"""
        resp = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
        )
        if resp.text:
            cleaned = resp.text.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            if data.get("global_stem"):
                return {
                    "global": data["global_stem"].strip(),
                    "regional": data.get("regional", topic).strip(),
                    "is_indonesian": is_id or data.get("is_indonesian", False)
                }
    except Exception:
        pass

    return {
        "global": global_query.strip(),
        "regional": topic.strip(),
        "is_indonesian": is_id
    }


def fetch_arxiv_papers(topic: str) -> List[Dict[str, Any]]:
    """Fetch arXiv preprints via OpenAlex arXiv index with polite pool & fallback."""
    try:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(topic)}&filter=primary_location.source.id:s4306400194&per-page=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for r in data.get("results", []):
                authors = ", ".join(a.get("author", {}).get("display_name", "") for a in r.get("authorships", [])[:3] if a.get("author"))
                arxiv_id = r.get("ids", {}).get("arxiv", "")
                landing_url = r.get("primary_location", {}).get("landing_page_url") or (f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else r.get("doi", ""))
                results.append({
                    "source": "arXiv Preprints",
                    "title": r.get("title") or "Untitled Paper",
                    "authors": authors or "Anonymous",
                    "year": r.get("publication_year") or "Recent",
                    "url": landing_url
                })
            if results:
                return results
    except Exception as e:
        console.print(f"[dim]arXiv primary index note: {e}, checking Crossref...[/dim]")

    # Fallback via Crossref
    try:
        fb_url = f"https://api.crossref.org/works?query={urllib.parse.quote(topic + ' arxiv')}&rows=3&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(fb_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for it in data.get("message", {}).get("items", []):
                authors = ", ".join(f"{a.get('given','')} {a.get('family','')}".strip() for a in it.get("author", [])[:3])
                doi = it.get("DOI", "")
                results.append({
                    "source": "arXiv Preprints (Crossref)",
                    "title": (it.get("title") or ["Untitled Paper"])[0],
                    "authors": authors or "Anonymous",
                    "year": it.get("created", {}).get("date-parts", [[ "Recent" ]])[0][0],
                    "url": f"https://doi.org/{doi}" if doi else ""
                })
            return results
    except Exception as e:
        console.print(f"[yellow]Warning: arXiv fetch failed: {e}[/yellow]")
        return []


def fetch_crossref_papers(topic: str) -> List[Dict[str, Any]]:
    """Fetch publisher peer-reviewed literature via Crossref 150M+ DOI index."""
    try:
        url = f"https://api.crossref.org/works?query={urllib.parse.quote(topic)}&rows=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for it in data.get("message", {}).get("items", []):
                authors = ", ".join(f"{a.get('given','')} {a.get('family','')}".strip() for a in it.get("author", [])[:3])
                doi = it.get("DOI", "")
                publisher = it.get("publisher", "Publisher")
                year = it.get("created", {}).get("date-parts", [[ "Recent" ]])[0][0]
                results.append({
                    "source": "Crossref DOI Index",
                    "title": (it.get("title") or ["Untitled Paper"])[0],
                    "authors": authors or "Anonymous",
                    "year": year,
                    "meta": f"{publisher} • DOI: {doi}",
                    "url": f"https://doi.org/{doi}" if doi else ""
                })
            return results
    except Exception as e:
        console.print(f"[yellow]Warning: Crossref fetch failed: {e}[/yellow]")
        return []


def fetch_semantic_scholar_papers(topic: str) -> List[Dict[str, Any]]:
    """Fetch high-impact cited academic works (Semantic Scholar API / Citation ranking)."""
    # 1. Primary: Direct Semantic Scholar API
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(topic)}&limit=4&fields=title,authors,year,citationCount,url"
        req = urllib.request.Request(url, headers={"User-Agent": "AgenticApp/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for p in data.get("data", []):
                authors = ", ".join(a.get("name", "") for a in p.get("authors", [])[:3] if a.get("name"))
                citations = p.get("citationCount", 0) or 0
                paper_id = p.get("paperId", "")
                link = p.get("url") or (f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else "")
                results.append({
                    "source": "Semantic Scholar API",
                    "title": p.get("title") or "Untitled Paper",
                    "authors": authors or "Anonymous",
                    "year": p.get("year") or "Recent",
                    "citations": citations,
                    "meta": f"{citations:,} citations • {authors}",
                    "url": link
                })
            if results:
                return results
    except Exception as e:
        console.print(f"[dim]Semantic Scholar direct note: {e}, using citation index fallback...[/dim]")

    # 2. Resilient Fallback: OpenAlex citation-ranked index
    try:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(topic)}&sort=cited_by_count:desc&per-page=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for r in data.get("results", []):
                authors = ", ".join(a.get("author", {}).get("display_name", "") for a in r.get("authorships", [])[:3] if a.get("author"))
                citations = r.get("cited_by_count", 0)
                url = r.get("doi") or r.get("primary_location", {}).get("landing_page_url") or ""
                results.append({
                    "source": "Semantic Scholar API",
                    "title": r.get("title") or "Untitled Paper",
                    "authors": authors or "Anonymous",
                    "year": r.get("publication_year") or "Recent",
                    "citations": citations,
                    "meta": f"{citations:,} citations • {authors}",
                    "url": url
                })
            return results
    except Exception as e:
        console.print(f"[yellow]Warning: Semantic Scholar fetch failed: {e}[/yellow]")
        return []


def fetch_openalex_works(topic: str, reg_topic: Optional[str] = None, is_id: bool = False) -> List[Dict[str, Any]]:
    """Fetch global peer-reviewed scholarly catalog works, plus regional works if non-English."""
    results = []
    try:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(topic)}&per-page=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            for r in data.get("results", []):
                authors = ", ".join(a.get("author", {}).get("display_name", "") for a in r.get("authorships", [])[:3] if a.get("author"))
                venue = r.get("primary_location", {}).get("source", {}).get("display_name", "Academic Venue") if r.get("primary_location") else "Academic Venue"
                results.append({
                    "source": "OpenAlex Global Catalog",
                    "title": r.get("title") or "Untitled Paper",
                    "authors": authors or "Anonymous",
                    "year": r.get("publication_year") or "Recent",
                    "venue": venue,
                    "meta": f"{venue} ({r.get('publication_year', 'Recent')}) • {authors}",
                    "url": r.get("doi") or r.get("primary_location", {}).get("landing_page_url") or ""
                })
    except Exception as e:
        console.print(f"[yellow]Warning: OpenAlex fetch failed: {e}[/yellow]")

    # If Indonesian or regional topic differs, also fetch regional works and merge
    if is_id and reg_topic and reg_topic.lower() != topic.lower():
        try:
            reg_url = f"https://api.openalex.org/works?search={urllib.parse.quote(reg_topic)}&per-page=2&mailto={POLITE_EMAIL}"
            req = urllib.request.Request(reg_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                reg_data = json.loads(resp.read().decode())
                seen_urls = {it.get("url") for it in results if it.get("url")}
                for r in reg_data.get("results", []):
                    authors = ", ".join(a.get("author", {}).get("display_name", "") for a in r.get("authorships", [])[:3] if a.get("author"))
                    venue = r.get("primary_location", {}).get("source", {}).get("display_name", "Jurnal Akademis") if r.get("primary_location") else "Jurnal Akademis"
                    item_url = r.get("doi") or r.get("primary_location", {}).get("landing_page_url") or ""
                    if item_url and item_url not in seen_urls:
                        results.append({
                            "source": "OpenAlex Regional Catalog",
                            "title": r.get("title") or "Untitled Paper",
                            "authors": authors or "Peneliti",
                            "year": r.get("publication_year") or "Recent",
                            "venue": venue,
                            "meta": f"{venue} ({r.get('publication_year', 'Recent')}) • {authors}",
                            "url": item_url
                        })
        except Exception as e:
            console.print(f"[dim]OpenAlex regional query note: {e}[/dim]")

    return results


def fetch_pubmed_works(topic: str) -> List[Dict[str, Any]]:
    """Fetch biomedical and life sciences papers via NCBI PubMed Central."""
    try:
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term={urllib.parse.quote(topic)}&retmode=json&retmax=4"
        req = urllib.request.Request(search_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            ids = data.get("esearchresult", {}).get("idlist", [])
            if not ids:
                return []

            sum_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pmc&id={','.join(ids)}&retmode=json"
            req2 = urllib.request.Request(sum_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
            with urllib.request.urlopen(req2, timeout=10) as resp2:
                data2 = json.loads(resp2.read().decode())
                results = []
                for uid in ids:
                    doc = data2.get("result", {}).get(uid, {})
                    title = re.sub(r"<[^>]+>", "", doc.get("title", "Untitled Study"))
                    authors = ", ".join(a.get("name", "") for a in doc.get("authors", [])[:3] if a.get("name"))
                    pubdate = doc.get("pubdate", "Recent").split(" ")[0]
                    source = doc.get("source", "PMC")
                    results.append({
                        "source": "PubMed Central (PMC)",
                        "title": title,
                        "authors": authors or "Researchers",
                        "year": pubdate,
                        "meta": f"{source} • {authors}",
                        "url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{uid}/"
                    })
                return results
    except Exception as e:
        console.print(f"[yellow]Warning: PubMed fetch failed: {e}[/yellow]")
        return []


def fetch_wikipedia_summary(topic: str, queries: Optional[Dict[str, Any]] = None, lang: str = "en") -> List[Dict[str, Any]]:
    """Fetch Wikipedia encyclopedic summary for reference in both regional and global editions."""
    results = []
    reg_topic = queries.get("regional", topic) if queries else topic
    glob_topic = queries.get("global", topic) if queries else topic
    is_id = (lang == "id") or bool(queries and queries.get("is_indonesian"))

    # 1. If Indonesian mode, query Indonesian Wikipedia first
    if is_id:
        try:
            search_url = f"https://id.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(reg_topic)}&format=json"
            req1 = urllib.request.Request(search_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
            with urllib.request.urlopen(req1, timeout=10) as resp1:
                data1 = json.loads(resp1.read().decode())
                hits = data1.get("query", {}).get("search", [])
                if hits:
                    title = hits[0].get("title", "")
                    slug = urllib.parse.quote(title.replace(" ", "_"))
                    sum_url = f"https://id.wikipedia.org/api/rest_v1/page/summary/{slug}"
                    req2 = urllib.request.Request(sum_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
                    with urllib.request.urlopen(req2, timeout=10) as resp2:
                        data2 = json.loads(resp2.read().decode())
                        if data2.get("extract"):
                            results.append({
                                "source": "Wikipedia (Bahasa Indonesia)",
                                "title": data2.get("title", title),
                                "extract": data2.get("extract", ""),
                                "meta": "Ensiklopedia Bahasa Indonesia",
                                "url": data2.get("content_urls", {}).get("desktop", {}).get("page") or f"https://id.wikipedia.org/wiki/{slug}"
                            })
        except Exception as e:
            console.print(f"[dim]Indonesian Wikipedia fetch note: {e}[/dim]")

    # 2. Query Global English Wikipedia
    try:
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(glob_topic)}&format=json"
        req1 = urllib.request.Request(search_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with urllib.request.urlopen(req1, timeout=10) as resp1:
            data1 = json.loads(resp1.read().decode())
            hits = data1.get("query", {}).get("search", [])
            if hits:
                title = hits[0].get("title", "")
                slug = urllib.parse.quote(title.replace(" ", "_"))
                sum_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
                req2 = urllib.request.Request(sum_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
                with urllib.request.urlopen(req2, timeout=10) as resp2:
                    data2 = json.loads(resp2.read().decode())
                    if data2.get("extract"):
                        results.append({
                            "source": "Wikipedia (Global Reference)" if is_id else "Wikipedia",
                            "title": data2.get("title", title),
                            "extract": data2.get("extract", ""),
                            "meta": "Rujukan Ensiklopedia Global" if is_id else "Encyclopedic Reference Overview",
                            "url": data2.get("content_urls", {}).get("desktop", {}).get("page") or f"https://en.wikipedia.org/wiki/{slug}"
                        })
    except Exception as e:
        console.print(f"[yellow]Warning: English Wikipedia fetch failed: {e}[/yellow]")

    return results


def load_document(doc_path: str) -> Tuple[str, str]:
    """Read a local PDF or text document."""
    if not os.path.exists(doc_path):
        raise FileNotFoundError(f"Document file not found at: {doc_path}")

    filename = os.path.basename(doc_path)
    if doc_path.lower().endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(doc_path)
            pages_text = []
            max_pages = min(len(reader.pages), 15)
            for i in range(max_pages):
                pages_text.append(f"[Page {i+1}]\n" + reader.pages[i].extract_text())
            full_text = "\n\n".join(pages_text)
            return filename, full_text
        except ImportError:
            raise ImportError("pypdf is required to parse PDF documents. Install via: pip install pypdf")
    else:
        with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
            return filename, f.read()


def build_scholarly_dossier(
    topic: str,
    use_arxiv: bool,
    use_crossref: bool,
    use_semantic: bool,
    use_openalex: bool,
    use_pubmed: bool,
    use_wiki: bool,
    doc_path: Optional[str],
    lang: str = "en"
) -> Tuple[str, List[Dict[str, Any]]]:
    """Compile all active grounding sources with live progression logging and cross-lingual querying."""
    citations = []
    sections = []

    # Resolve multilingual query representations
    queries = resolve_multilingual_queries(topic, lang=lang)
    glob_topic = queries["global"]
    reg_topic = queries["regional"]
    is_id = queries["is_indonesian"] or (lang == "id")

    console.print(Panel(
        f"[bold cyan]Cross-Lingual Literature Grounding Active[/bold cyan]\n"
        f"[white]Original Query:[/white] {topic}\n"
        f"[white]Global STEM Keywords:[/white] [green]{glob_topic}[/green]\n"
        f"[white]Regional Context:[/white] {reg_topic} (Mode: {'Bahasa Indonesia' if is_id else 'English'})",
        border_style="cyan"
    ))

    if use_arxiv:
        console.print(f"[cyan]🔍 [arXiv] Querying open preprints for '{glob_topic}'...[/cyan]")
        papers = fetch_arxiv_papers(glob_topic)
        if papers:
            console.print(f"[green]  ✓ [arXiv] Found {len(papers)} preprints[/green]")
            p_text = "### 📚 arXiv Preprints:\n"
            for p in papers:
                p_text += f"- Title: \"{p['title']}\" ({p['year']})\n  Authors: {p['authors']}\n  Link: {p['url']}\n"
                citations.append({"source": "arXiv", "title": p["title"], "url": p["url"], "meta": f"{p['authors']} ({p['year']})"})
            sections.append(p_text)
        else:
            console.print("[dim]  ✕ [arXiv] No preprints found[/dim]")

    if use_crossref:
        console.print(f"[cyan]🔍 [Crossref] Querying 150M+ verified DOI index for '{glob_topic}'...[/cyan]")
        papers = fetch_crossref_papers(glob_topic)
        if papers:
            console.print(f"[green]  ✓ [Crossref] Found {len(papers)} publisher DOIs[/green]")
            p_text = "### 🏷️ Crossref Verified DOIs:\n"
            for p in papers:
                p_text += f"- Title: \"{p['title']}\" ({p['year']})\n  Authors: {p['authors']}\n  DOI: {p['url']}\n"
                citations.append({"source": "Crossref", "title": p["title"], "url": p["url"], "meta": p["meta"]})
            sections.append(p_text)
        else:
            console.print("[dim]  ✕ [Crossref] No records found[/dim]")

    if use_semantic:
        console.print(f"[cyan]🔍 [Semantic Scholar] Fetching citation rankings for '{glob_topic}'...[/cyan]")
        papers = fetch_semantic_scholar_papers(glob_topic)
        if papers:
            console.print(f"[green]  ✓ [Semantic Scholar] Found {len(papers)} high-impact papers[/green]")
            p_text = "### 🔬 High-Impact Academic Works (Semantic Scholar):\n"
            for p in papers:
                p_text += f"- Title: \"{p['title']}\" ({p['year']})\n  Authors: {p['authors']}\n  Citations: {p['citations']:,}\n  DOI/Link: {p['url']}\n"
                citations.append({"source": "Semantic Scholar", "title": p["title"], "url": p["url"], "meta": p["meta"]})
            sections.append(p_text)
        else:
            console.print("[dim]  ✕ [Semantic Scholar] No records found[/dim]")

    if use_openalex:
        console.print(f"[cyan]🔍 [OpenAlex] Fetching global catalog works for '{glob_topic}'...[/cyan]")
        works = fetch_openalex_works(glob_topic, reg_topic=reg_topic, is_id=is_id)
        if works:
            console.print(f"[green]  ✓ [OpenAlex] Found {len(works)} peer-reviewed works[/green]")
            p_text = "### 🏛️ OpenAlex Global Scholarly Catalog:\n"
            for p in works:
                p_text += f"- Title: \"{p['title']}\" ({p['year']})\n  Venue: {p['venue']}\n  Authors: {p['authors']}\n  DOI: {p['url']}\n"
                citations.append({"source": p.get("source", "OpenAlex"), "title": p["title"], "url": p["url"], "meta": p["meta"]})
            sections.append(p_text)
        else:
            console.print("[dim]  ✕ [OpenAlex] No records found[/dim]")

    if use_pubmed:
        console.print(f"[cyan]🔍 [PubMed] Querying NCBI PubMed Central for '{glob_topic}'...[/cyan]")
        works = fetch_pubmed_works(glob_topic)
        if works:
            console.print(f"[green]  ✓ [PubMed] Found {len(works)} biomedical articles[/green]")
            p_text = "### 🧬 PubMed Central (PMC) Biomedical Literature:\n"
            for p in works:
                p_text += f"- Title: \"{p['title']}\" ({p['year']})\n  Authors: {p['authors']}\n  Article Link: {p['url']}\n"
                citations.append({"source": "PubMed Central", "title": p["title"], "url": p["url"], "meta": p["meta"]})
            sections.append(p_text)
        else:
            console.print("[dim]  ✕ [PubMed] No records found[/dim]")

    if use_wiki:
        console.print(f"[cyan]🔍 [Wikipedia] Fetching encyclopedic reference summary...[/cyan]")
        wiki_items = fetch_wikipedia_summary(topic, queries=queries, lang=lang)
        if wiki_items:
            for w in wiki_items:
                console.print(f"[green]  ✓ [{w['source']}] Found overview for '{w['title']}'[/green]")
                w_text = f"### 📖 {w['source']} ({w['title']}):\n{w['extract']}\nReference URL: {w['url']}\n"
                sections.append(w_text)
                citations.append({"source": w["source"], "title": w["title"], "url": w["url"], "meta": w.get("meta", "Encyclopedic Overview")})
        else:
            console.print("[dim]  ✕ [Wikipedia] No summary found[/dim]")

    if doc_path:
        console.print(f"[cyan]🔍 [Document] Loading local document: {doc_path}...[/cyan]")
        doc_name, doc_content = load_document(doc_path)
        excerpt = doc_content[:6000]
        d_text = f"### 📄 User-Supplied Document ({doc_name}):\n\"\"\"\n{excerpt}\n\"\"\"\n"
        sections.append(d_text)
        citations.append({"source": "Local Document", "title": doc_name, "url": doc_path, "meta": f"{len(doc_content):,} characters"})

    if not sections:
        return "", []

    dossier_title = "## VERIFIED SCHOLARLY RESEARCH & REFERENCE DOSSIER (MULTI-BAHASA)\n\n" if is_id else "## VERIFIED SCHOLARLY RESEARCH & REFERENCE DOSSIER\n\n"
    dossier_text = dossier_title + "\n\n".join(sections)
    return dossier_text, citations


# ==============================================================================
# Agent Functions
# ==============================================================================

def run_writer_draft(topic: str, instructions: Optional[str] = None, model: str = DEFAULT_MODEL, enable_search: bool = False, thinking_level: str = "medium", scholarly_dossier: str = "", lang: str = "en") -> str:
    """Writer agent creates the first draft."""
    system_prompt = (
        "You are an expert, engaging, and articulate Writer Agent. "
        "Your goal is to produce well-structured, clear, and compelling content based on the user's prompt. "
        "Use Markdown formatting with headings and bullet points where appropriate."
    )
    if lang == "id":
        system_prompt += (
            "\n\nPANDUAN BAHASA & SINTESIS:\n"
            "Anda WAJIB menulis seluruh naskah dan draf secara komprehensif dalam BAHASA INDONESIA yang baku, ilmiah, mengalir, dan profesional.\n"
            "Sintesiskan semua temuan dari literatur ilmiah internasional dan regional (arXiv, Semantic Scholar, PubMed, OpenAlex, Crossref, Wikipedia) ke dalam Bahasa Indonesia dengan runtut.\n"
            "Rujuk nama penulis dan tahun penelitian di dalam teks.\n"
            "Wajib sertakan bagian penutup: '## 📚 Referensi & Sitasi Akademis' dengan tautan dan DOI lengkap."
        )
    if enable_search:
        system_prompt += " Use Google Search to look up up-to-date facts, data points, and references."
    if scholarly_dossier:
        system_prompt += (
            " You are provided with a Verified Scholarly Research Dossier. "
            "You MUST ground your explanations in these academic papers, DOIs, and reference materials. "
            "Cite the authors and dates in the text, and include a dedicated '## 📚 Scholarly References & Citations' "
            "section at the end with markdown links and DOIs."
        )

    user_prompt = f"Topic/Goal: {topic}\n"
    if scholarly_dossier:
        user_prompt += f"\n{scholarly_dossier}\n"
    if instructions:
        user_prompt += f"Special Instructions: {instructions}\n"
    if lang == "id":
        user_prompt += "Silakan tulis Draf 1 yang mendalam dan komprehensif dalam Bahasa Indonesia berlandaskan topik dan rujukan riset di atas."
    else:
        user_prompt += "Please write Draft 1 grounded in the topic and research."

    tools = [{"type": "google_search"}] if enable_search else None
    response = client.interactions.create(
        model=model,
        system_instruction=system_prompt,
        input=user_prompt,
        tools=tools,
        generation_config={"thinking_level": thinking_level}
    )
    return response.output_text or ""


def run_writer_revision(original_topic: str, previous_draft: str, critique: CritiqueResult, turn: int, model: str = DEFAULT_MODEL, enable_search: bool = False, thinking_level: str = "medium", scholarly_dossier: str = "", lang: str = "en") -> str:
    """Writer agent revises the draft incorporating the critic's points."""
    system_prompt = (
        "You are an expert Writer Agent in an iterative feedback loop. "
        "Carefully study the Critic's feedback, weaknesses, and required action items, and address each one thoroughly "
        "while retaining the strengths of your previous draft. Deliver the updated draft in full."
    )
    if lang == "id":
        system_prompt += (
            "\n\nPANDUAN BAHASA & REVISI:\n"
            "Perbaiki dan sempurnakan draf secara menyeluruh dalam BAHASA INDONESIA. "
            "Tangani setiap kelemahan dan rekomendasi perbaikan dari Pengkritik, serta pertahankan rujukan akademis dan sitasi DOIs."
        )
    if enable_search:
        system_prompt += " Use Google Search to look up up-to-date information for the Critic's points."
    if scholarly_dossier:
        system_prompt += " Ensure all academic references, DOIs, and citations from the research dossier are retained and accurately cited."

    revisions_formatted = "\n".join(f"- {item}" for item in critique.actionable_revisions)
    prompt = f"""
Original Topic: {original_topic}

Your Previous Draft (Draft {turn}):
\"\"\"
{previous_draft}
\"\"\"

Critic Feedback (Score: {critique.score}/10):
Weaknesses:
{chr(10).join(f"- {w}" for w in critique.weaknesses)}

Required Improvements:
{revisions_formatted}
"""
    if scholarly_dossier:
        prompt += f"\nResearch Dossier Reference:\n{scholarly_dossier}\n"

    if lang == "id":
        prompt += f"\nSilakan tulis revisi lengkap (Draf {turn + 1}) dalam Bahasa Indonesia yang menindaklanjuti seluruh evaluasi di atas."
    else:
        prompt += f"\nPlease write the complete revised version (Draft {turn + 1}) addressing all feedback."

    tools = [{"type": "google_search"}] if enable_search else None
    response = client.interactions.create(
        model=model,
        system_instruction=system_prompt,
        input=prompt,
        tools=tools,
        generation_config={"thinking_level": thinking_level}
    )
    return response.output_text or ""


def run_critic_review(topic: str, draft: str, turn: int, model: str = DEFAULT_MODEL, thinking_level: str = "medium", has_dossier: bool = False, lang: str = "en") -> CritiqueResult:
    """Critic agent rigorously reviews the draft and returns structured feedback."""
    system_prompt = (
        "You are a meticulous, discerning Senior Editor and Critic Agent. "
        "Evaluate drafts strictly on clarity, depth, coherence, factual grounding, tone, and engagement. "
        "Be constructive but hold a high bar. Scores above 8.5 qualify for 'APPROVED'. "
    )
    if lang == "id":
        system_prompt += (
            "\nPANDUAN BAHASA:\n"
            "Berikan seluruh evaluasi, analisis kekuatan, kelemahan, dan tindakan revisi dalam BAHASA INDONESIA yang objektif dan konstruktif."
        )
    if has_dossier:
        system_prompt += " Verify that the draft properly incorporates facts from the provided research dossier and includes valid academic citations and links. "

    system_prompt += (
        "You MUST respond ONLY with valid JSON conforming to this schema:\n"
        "{\n"
        '  "score": float (1.0 to 10.0),\n'
        '  "status": "APPROVED" | "NEEDS_REVISION",\n'
        '  "strengths": ["string", ...],\n'
        '  "weaknesses": ["string", ...],\n'
        '  "actionable_revisions": ["string", ...]\n'
        "}"
    )

    prompt = f"""
Goal / Prompt: {topic}
Iteration Turn: {turn}
Grounding Dossier Present: {'Yes' if has_dossier else 'No'}

Draft to Review:
\"\"\"
{draft}
\"\"\"

Analyze the draft thoroughly and output your evaluation as a valid JSON object only.
"""

    response = client.interactions.create(
        model=model,
        system_instruction=system_prompt,
        input=prompt,
        generation_config={"thinking_level": thinking_level}
    )

    raw_text = response.output_text or ""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    
    data = json.loads(cleaned)
    return CritiqueResult(**data)


# ==============================================================================
# Pipeline Orchestrator
# ==============================================================================

def orchestrate_pipeline(
    topic: str,
    max_turns: int = 2,
    target_score: float = 8.5,
    model: str = DEFAULT_MODEL,
    web_search: bool = False,
    thinking_level: str = "medium",
    use_arxiv: bool = False,
    use_crossref: bool = False,
    use_semantic: bool = False,
    use_openalex: bool = False,
    use_pubmed: bool = False,
    use_wiki: bool = False,
    doc_path: Optional[str] = None,
    lang: str = "en"
) -> dict:
    """Coordinates the interaction loop between Writer and Critic."""
    search_label = " (🌐 Web Search Enabled)" if web_search else ""
    lang_label = " [🇮🇩 Bahasa Indonesia]" if lang == "id" else " [🇬🇧 English]"
    console.print(Panel(
        f"[bold cyan]Two-Agent Pipeline Initialized{lang_label}[/bold cyan]\n"
        f"[white]Topic:[/white] {topic}\n"
        f"[white]Model:[/white] {model} | [white]🧠 Thinking:[/white] {thinking_level}{search_label}",
        border_style="cyan"
    ))

    # Step 0: Gather scholarly grounding if requested
    dossier_text, citations = build_scholarly_dossier(
        topic,
        use_arxiv=use_arxiv,
        use_crossref=use_crossref,
        use_semantic=use_semantic,
        use_openalex=use_openalex,
        use_pubmed=use_pubmed,
        use_wiki=use_wiki,
        doc_path=doc_path,
        lang=lang
    )

    if citations:
        table = Table(title="Verified Academic & Reference Sources Loaded", border_style="cyan")
        table.add_column("Source", style="bold magenta", width=18)
        table.add_column("Title / Document", style="white")
        table.add_column("Details", style="dim", width=34)
        for c in citations:
            table.add_row(c["source"], c["title"], c["meta"])
        console.print(table)

    history = []
    current_draft = ""
    latest_critique: Optional[CritiqueResult] = None

    for turn in range(1, max_turns + 1):
        console.rule(f"[bold yellow]Iteration {turn} / {max_turns}[/bold yellow]")

        # 1. Writer Turn
        console.print("[bold green]>>> Writer Agent is thinking & composing...[/bold green]")
        if turn == 1:
            current_draft = run_writer_draft(topic, model=model, enable_search=web_search, thinking_level=thinking_level, scholarly_dossier=dossier_text, lang=lang)
        else:
            assert latest_critique is not None
            current_draft = run_writer_revision(topic, current_draft, latest_critique, turn - 1, model=model, enable_search=web_search, thinking_level=thinking_level, scholarly_dossier=dossier_text, lang=lang)

        console.print(Panel(Markdown(current_draft), title=f"[bold green]Writer Agent - Draft {turn}[/bold green]", border_style="green"))

        # 2. Critic Turn
        console.print("[bold magenta]>>> Critic Agent is evaluating draft...[/bold magenta]")
        latest_critique = run_critic_review(topic, current_draft, turn, model=model, thinking_level=thinking_level, has_dossier=bool(citations), lang=lang)

        critique_md = (
            f"**Score:** {latest_critique.score:.1f}/10.0  \n"
            f"**Status:** `{'APPROVED' if latest_critique.score >= target_score else 'NEEDS_REVISION'}`  \n\n"
            f"**Strengths:**\n" + "\n".join(f"- {s}" for s in latest_critique.strengths) + "\n\n"
            f"**Weaknesses:**\n" + "\n".join(f"- {w}" for w in latest_critique.weaknesses) + "\n\n"
            f"**Actionable Revisions:**\n" + "\n".join(f"- {r}" for r in latest_critique.actionable_revisions)
        )
        border = "bright_green" if latest_critique.score >= target_score else "bright_yellow"
        console.print(Panel(Markdown(critique_md), title=f"[bold magenta]Critic Review (Draft {turn})[/bold magenta]", border_style=border))

        history.append({
            "turn": turn,
            "draft": current_draft,
            "score": latest_critique.score,
            "status": latest_critique.status,
            "strengths": latest_critique.strengths,
            "weaknesses": latest_critique.weaknesses,
            "actionable_revisions": latest_critique.actionable_revisions,
        })

        if latest_critique.score >= target_score:
            console.print(f"\n[bold green]✓ Approved by Critic with score {latest_critique.score:.1f} >= {target_score}![/bold green]\n")
            break
        elif turn == max_turns:
            console.print(f"\n[bold yellow]Reached maximum limit of {max_turns} iterations.[/bold yellow]\n")

    # Save to output file
    os.makedirs("output", exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic.strip().lower())[:40].strip("_")
    filename = os.path.join("output", f"{slug}.md")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Final Draft: {topic}\n\n")
        f.write(f"**Language:** `{lang.upper()}`\n")
        f.write(f"**Model:** `{model}`\n")
        f.write(f"**Thinking Mode:** `{thinking_level}`\n")
        f.write(f"**Web Search:** `{'Enabled' if web_search else 'Disabled'}`\n")
        if citations:
            f.write(f"**Academic Grounding Sources:** `{len(citations)} source(s) active`\n")
        f.write(f"**Final Score:** {latest_critique.score:.1f}/10.0\n")
        f.write(f"**Total Iterations:** {len(history)}\n\n")
        f.write("## Content\n\n")
        f.write(current_draft)
        f.write("\n\n---\n## Revision History & Critic Log\n\n")
        for h in history:
            f.write(f"### Draft {h['turn']} (Score: {h['score']:.1f}/10)\n")
            f.write(f"**Critic Status:** `{h['status']}`\n")
            f.write("**Actionable Feedback:**\n")
            for item in h["actionable_revisions"]:
                f.write(f"- {item}\n")
            f.write("\n")

    console.print(Panel(f"[bold cyan]Artifact saved successfully:[/bold cyan] {filename}", border_style="cyan"))
    return {
        "final_draft": current_draft,
        "score": latest_critique.score,
        "history": history,
        "saved_path": filename
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Two-Agent Writer & Critic pipeline with Academic Grounding")
    parser.add_argument("--topic", type=str, default="Speech perception", help="Prompt or topic for content")
    parser.add_argument("--lang", choices=["en", "id"], default="en", help="Language mode: en (English) or id (Bahasa Indonesia)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, choices=["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-pro-preview", "gemini-flash-latest"], help="Gemini model to use")
    parser.add_argument("--thinking-level", type=str, default="medium", choices=["low", "medium", "high"], help="Thinking depth: low, medium, or high")
    parser.add_argument("--web-search", action="store_true", help="Enable Google Search grounding for research")
    parser.add_argument("--arxiv", action="store_true", help="Ground in arXiv preprints")
    parser.add_argument("--crossref", action="store_true", help="Ground in Crossref 150M+ DOI index")
    parser.add_argument("--semantic-scholar", action="store_true", help="Ground in Semantic Scholar high-impact works")
    parser.add_argument("--openalex", action="store_true", help="Ground in OpenAlex global catalog works")
    parser.add_argument("--pubmed", action="store_true", help="Ground in NCBI PubMed Central articles")
    parser.add_argument("--wikipedia", action="store_true", help="Ground in Wikipedia encyclopedic summary")
    parser.add_argument("--doc", type=str, default=None, help="Path to local PDF or text document to ground in")
    parser.add_argument("--max-turns", type=int, default=2, help="Maximum number of refinement iterations")
    parser.add_argument("--target-score", type=float, default=8.5, help="Score threshold for approval (1-10)")

    args = parser.parse_args()
    orchestrate_pipeline(
        topic=args.topic,
        max_turns=args.max_turns,
        target_score=args.target_score,
        model=args.model,
        web_search=args.web_search,
        thinking_level=args.thinking_level,
        use_arxiv=args.arxiv,
        use_crossref=args.crossref,
        use_semantic=args.semantic_scholar,
        use_openalex=args.openalex,
        use_pubmed=args.pubmed,
        use_wiki=args.wikipedia,
        doc_path=args.doc,
        lang=args.lang
    )
