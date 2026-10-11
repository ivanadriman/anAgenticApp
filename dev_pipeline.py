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
import time
import random
import http.client
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional, List, Dict, Any, Tuple
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
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

DEFAULT_MODEL = "gemini-3.5-flash-lite"
POLITE_EMAIL = "agenticapp.research@gmail.com"

# Network Retry & Backoff Configuration
MAX_RETRIES = 3
BASE_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 10.0  # seconds

console = Console(force_terminal=True, legacy_windows=False)

_client: Optional[genai.Client] = None


def get_client() -> genai.Client:
    """Lazily initialize and return the Gemini API client only when an API call is made."""
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is missing. "
                "Please configure GEMINI_API_KEY in your environment or .env file before running generation."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def set_client(custom_client: Optional[genai.Client]) -> None:
    """Set a custom or mocked client instance (primarily for tests)."""
    global _client
    _client = custom_client


def request_with_retry(
    req: urllib.request.Request,
    timeout: float = 10.0,
    max_retries: int = MAX_RETRIES,
    base_backoff: float = BASE_BACKOFF,
    max_backoff: float = MAX_BACKOFF
):
    """
    Execute urllib.request.urlopen with exponential backoff, jitter, and Retry-After support.
    Retries transient errors: HTTP 429, 500, 502, 503, 504, and network timeouts.
    """
    for attempt in range(max_retries + 1):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                retry_after = e.headers.get("Retry-After") if hasattr(e, "headers") and e.headers else None
                if retry_after:
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        delay = min(base_backoff * (2 ** attempt), max_backoff)
                else:
                    delay = min(base_backoff * (2 ** attempt), max_backoff)
                delay += random.uniform(0.0, 0.25 * delay)
                console.print(f"[dim yellow]HTTP {e.code} transient response for {req.full_url}. Retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})...[/dim yellow]")
                time.sleep(delay)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, http.client.HTTPException, ConnectionResetError) as e:
            if attempt < max_retries:
                delay = min(base_backoff * (2 ** attempt), max_backoff) + random.uniform(0.0, 0.5)
                console.print(f"[dim yellow]Network transient error ({e}) for {req.full_url}. Retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})...[/dim yellow]")
                time.sleep(delay)
                continue
            raise


def call_gemini_with_retry(
    func,
    *args,
    max_retries: int = MAX_RETRIES,
    base_backoff: float = BASE_BACKOFF,
    max_backoff: float = MAX_BACKOFF,
    **kwargs
):
    """
    Invoke a Gemini API method with exponential backoff and jitter for transient 429/rate limit/5xx errors.
    """
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            err_msg = str(e).lower()
            is_transient = (
                "429" in err_msg
                or "resource_exhausted" in err_msg
                or "rate limit" in err_msg
                or "503" in err_msg
                or "unavailable" in err_msg
                or "timeout" in err_msg
            )
            if is_transient and attempt < max_retries:
                delay = min(base_backoff * (2 ** attempt), max_backoff) + random.uniform(0.0, 0.5)
                console.print(f"[dim yellow]Gemini API transient rate limit/error ({e}). Retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})...[/dim yellow]")
                time.sleep(delay)
                continue
            raise


class CritiqueResult(BaseModel):
    score: float = Field(description="Rating from 1.0 to 10.0")
    status: str = Field(description="'APPROVED' if score >= 8.5 else 'NEEDS_REVISION'")
    strengths: list[str] = Field(description="List of positive aspects of the draft")
    weaknesses: list[str] = Field(description="List of weak areas or flaws found")
    actionable_revisions: list[str] = Field(description="Clear, numbered instructions for the writer to improve the next draft")

    @field_validator("score", mode="before")
    @classmethod
    def clamp_score(cls, v):
        try:
            val = float(v)
            return max(1.0, min(10.0, val))
        except (ValueError, TypeError):
            return 5.0

    @field_validator("status", mode="before")
    @classmethod
    def reconcile_status(cls, v, info):
        val_str = str(v).strip().upper() if v else ""
        if val_str in ("APPROVED", "NEEDS_REVISION"):
            return val_str
        score = info.data.get("score", 5.0) if hasattr(info, "data") else 5.0
        return "APPROVED" if score >= 8.5 else "NEEDS_REVISION"


class SourceAuditItem(BaseModel):
    id: str = Field(description="Unique criterion ID from source-checking-guide.md")
    layer: int = Field(description="Layer 1, 2, or 3")
    title: str = Field(description="Short human-readable title")
    question: str = Field(description="Audit question from guide")
    answer: str = Field(description="'YES' or 'NO'")
    reason: str = Field(description="Diagnostic justification and evidence")
    offending_text: Optional[str] = Field(default="", description="Offending passage or citation snippet if NO, else empty")

    @field_validator("answer", mode="before")
    @classmethod
    def normalize_answer(cls, v):
        if not v:
            return "NO"
        clean = str(v).strip().upper()
        if clean in ("YES", "YA", "TRUE", "Y"):
            return "YES"
        return "NO"


class SourceAuditResult(BaseModel):
    all_yes: bool = Field(description="True ONLY if all 11 criteria are 'YES'")
    overall_verdict: str = Field(description="'APPROVED_INTEGRITY_CLEARANCE' or 'DISCREPANCIES_DETECTED'")
    score_percentage: float = Field(description="Percentage of passed criteria (0 to 100)")
    failure_patterns_detected: list[str] = Field(default_factory=list, description="List of detected failure patterns from the 7 guide patterns")
    discrepancies: list[str] = Field(default_factory=list, description="Actionable revision directives to achieve YES")
    items: list[SourceAuditItem] = Field(description="11 individual audit results across the 3 layers")


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
        resp = call_gemini_with_retry(
            get_client().models.generate_content,
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
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        console.print(f"[dim yellow]Notice: Query formulation JSON parse error ({e}), using heuristic fallback[/dim yellow]")
    except Exception as e:
        console.print(f"[dim yellow]Notice: Query formulation LLM error ({e}), using heuristic fallback[/dim yellow]")

    return {
        "global": global_query.strip(),
        "regional": topic.strip(),
        "is_indonesian": is_id
    }


def reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> str:
    """Reconstruct verbatim abstract from OpenAlex inverted index."""
    if not inverted_index or not isinstance(inverted_index, dict):
        return ""
    words: Dict[int, str] = {}
    for word, positions in inverted_index.items():
        if isinstance(positions, list):
            for pos in positions:
                words[pos] = word
    if not words:
        return ""
    sorted_positions = sorted(words.keys())
    return " ".join(words[p] for p in sorted_positions).strip()


def fetch_arxiv_papers(topic: str) -> List[Dict[str, Any]]:
    """Fetch arXiv preprints via OpenAlex arXiv index with polite pool & fallback."""
    try:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(topic)}&filter=primary_location.source.id:s4306400194&per-page=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for r in data.get("results", []):
                authors = ", ".join(a.get("author", {}).get("display_name", "") for a in r.get("authorships", [])[:3] if a.get("author"))
                arxiv_id = r.get("ids", {}).get("arxiv", "")
                landing_url = r.get("primary_location", {}).get("landing_page_url") or (f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else r.get("doi", ""))
                abstract = reconstruct_abstract(r.get("abstract_inverted_index"))
                results.append({
                    "source": "arXiv Preprints",
                    "title": r.get("title") or "Untitled Paper",
                    "authors": authors or "Anonymous",
                    "year": r.get("publication_year") or "Recent",
                    "url": landing_url,
                    "abstract": abstract
                })
            if results:
                return results
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
        console.print(f"[dim]arXiv primary index note: {e}, checking Crossref...[/dim]")
    except Exception as e:
        console.print(f"[dim]arXiv primary index unexpected error: {e}, checking Crossref...[/dim]")

    # Fallback via Crossref
    try:
        fb_url = f"https://api.crossref.org/works?query={urllib.parse.quote(topic + ' arxiv')}&rows=3&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(fb_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
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
                    "url": f"https://doi.org/{doi}" if doi else "",
                    "abstract": ""
                })
            return results
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
        console.print(f"[yellow]Warning: arXiv fetch failed: {e}[/yellow]")
        return []
    except Exception as e:
        console.print(f"[yellow]Warning: arXiv unexpected fetch error: {e}[/yellow]")
        return []


def fetch_crossref_papers(topic: str) -> List[Dict[str, Any]]:
    """Fetch publisher peer-reviewed literature via Crossref 150M+ DOI index."""
    try:
        url = f"https://api.crossref.org/works?query={urllib.parse.quote(topic)}&rows=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
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
                    "url": f"https://doi.org/{doi}" if doi else "",
                    "abstract": ""
                })
            return results
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
        console.print(f"[yellow]Warning: Crossref fetch failed: {e}[/yellow]")
        return []
    except Exception as e:
        console.print(f"[yellow]Warning: Crossref unexpected fetch error: {e}[/yellow]")
        return []


def fetch_semantic_scholar_papers(topic: str) -> List[Dict[str, Any]]:
    """Fetch high-impact cited academic works (Semantic Scholar API / Citation ranking)."""
    # 1. Primary: Direct Semantic Scholar API
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(topic)}&limit=4&fields=title,authors,year,citationCount,url,abstract"
        req = urllib.request.Request(url, headers={"User-Agent": "AgenticApp/1.0"})
        with request_with_retry(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for p in data.get("data", []):
                authors = ", ".join(a.get("name", "") for a in p.get("authors", [])[:3] if a.get("name"))
                citations = p.get("citationCount", 0) or 0
                paper_id = p.get("paperId", "")
                link = p.get("url") or (f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else "")
                abstract = p.get("abstract") or ""
                results.append({
                    "source": "Semantic Scholar API",
                    "title": p.get("title") or "Untitled Paper",
                    "authors": authors or "Anonymous",
                    "year": p.get("year") or "Recent",
                    "citations": citations,
                    "meta": f"{citations:,} citations • {authors}",
                    "url": link,
                    "abstract": abstract
                })
            if results:
                return results
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
        console.print(f"[dim]Semantic Scholar direct note: {e}, using citation index fallback...[/dim]")
    except Exception as e:
        console.print(f"[dim]Semantic Scholar direct unexpected note: {e}, using citation index fallback...[/dim]")

    # 2. Resilient Fallback: OpenAlex citation-ranked index
    try:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(topic)}&sort=cited_by_count:desc&per-page=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for r in data.get("results", []):
                authors = ", ".join(a.get("author", {}).get("display_name", "") for a in r.get("authorships", [])[:3] if a.get("author"))
                citations = r.get("cited_by_count", 0)
                url = r.get("doi") or r.get("primary_location", {}).get("landing_page_url") or ""
                abstract = reconstruct_abstract(r.get("abstract_inverted_index"))
                results.append({
                    "source": "Semantic Scholar API",
                    "title": r.get("title") or "Untitled Paper",
                    "authors": authors or "Anonymous",
                    "year": r.get("publication_year") or "Recent",
                    "citations": citations,
                    "meta": f"{citations:,} citations • {authors}",
                    "url": url,
                    "abstract": abstract
                })
            return results
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
        console.print(f"[yellow]Warning: Semantic Scholar fetch failed: {e}[/yellow]")
        return []
    except Exception as e:
        console.print(f"[yellow]Warning: Semantic Scholar unexpected fetch error: {e}[/yellow]")
        return []


def fetch_openalex_works(topic: str, reg_topic: Optional[str] = None, is_id: bool = False) -> List[Dict[str, Any]]:
    """Fetch global peer-reviewed scholarly catalog works, plus regional works if non-English."""
    results = []
    try:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(topic)}&per-page=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            for r in data.get("results", []):
                authors = ", ".join(a.get("author", {}).get("display_name", "") for a in r.get("authorships", [])[:3] if a.get("author"))
                venue = r.get("primary_location", {}).get("source", {}).get("display_name", "Academic Venue") if r.get("primary_location") else "Academic Venue"
                abstract = reconstruct_abstract(r.get("abstract_inverted_index"))
                results.append({
                    "source": "OpenAlex Global Catalog",
                    "title": r.get("title") or "Untitled Paper",
                    "authors": authors or "Anonymous",
                    "year": r.get("publication_year") or "Recent",
                    "venue": venue,
                    "meta": f"{venue} ({r.get('publication_year', 'Recent')}) • {authors}",
                    "url": r.get("doi") or r.get("primary_location", {}).get("landing_page_url") or "",
                    "abstract": abstract
                })
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
        console.print(f"[yellow]Warning: OpenAlex fetch failed: {e}[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Warning: OpenAlex unexpected fetch error: {e}[/yellow]")

    # If Indonesian or regional topic differs, also fetch regional works and merge
    if is_id and reg_topic and reg_topic.lower() != topic.lower():
        try:
            reg_url = f"https://api.openalex.org/works?search={urllib.parse.quote(reg_topic)}&per-page=2&mailto={POLITE_EMAIL}"
            req = urllib.request.Request(reg_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
            with request_with_retry(req, timeout=10) as resp:
                reg_data = json.loads(resp.read().decode())
                seen_urls = {it.get("url") for it in results if it.get("url")}
                for r in reg_data.get("results", []):
                    authors = ", ".join(a.get("author", {}).get("display_name", "") for a in r.get("authorships", [])[:3] if a.get("author"))
                    venue = r.get("primary_location", {}).get("source", {}).get("display_name", "Jurnal Akademis") if r.get("primary_location") else "Jurnal Akademis"
                    item_url = r.get("doi") or r.get("primary_location", {}).get("landing_page_url") or ""
                    if item_url and item_url not in seen_urls:
                        abstract = reconstruct_abstract(r.get("abstract_inverted_index"))
                        results.append({
                            "source": "OpenAlex Regional Catalog",
                            "title": r.get("title") or "Untitled Paper",
                            "authors": authors or "Peneliti",
                            "year": r.get("publication_year") or "Recent",
                            "venue": venue,
                            "meta": f"{venue} ({r.get('publication_year', 'Recent')}) • {authors}",
                            "url": item_url,
                            "abstract": abstract
                        })
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
            console.print(f"[dim]OpenAlex regional query note: {e}[/dim]")
        except Exception as e:
            console.print(f"[dim]OpenAlex regional query unexpected note: {e}[/dim]")

    return results


def fetch_pubmed_works(topic: str) -> List[Dict[str, Any]]:
    """Fetch biomedical and life sciences papers via Europe PMC (with verbatim abstracts) / NCBI PMC."""
    # 1. Primary: Europe PMC REST with resultType=core for verbatim abstractText
    try:
        ep_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={urllib.parse.quote(topic)}&resultType=core&format=json&pageSize=4"
        req = urllib.request.Request(ep_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            ep_data = json.loads(resp.read().decode())
            results = []
            for it in ep_data.get("resultList", {}).get("result", []):
                authors = it.get("authorString", "Researchers")
                if authors:
                    authors = ", ".join(authors.split(",")[:3])
                title = re.sub(r"<[^>]+>", "", it.get("title", "Untitled Study"))
                pmcid = it.get("pmcid", "")
                landing = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/" if pmcid else (f"https://doi.org/{it.get('doi')}" if it.get("doi") else "")
                raw_abs = re.sub(r"<[^>]+>", "", it.get("abstractText", "") or "")
                pub_year = str(it.get("pubYear", "Recent"))
                journal = it.get("journalTitle", "PMC")
                results.append({
                    "source": "PubMed / Europe PMC",
                    "title": title,
                    "authors": authors or "Researchers",
                    "year": pub_year,
                    "meta": f"{journal} ({pub_year}) • {authors}",
                    "url": landing,
                    "abstract": raw_abs
                })
            if results:
                return results
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as ep_err:
        console.print(f"[dim]Europe PMC query note: {ep_err}, falling back to NCBI PMC...[/dim]")
    except Exception as ep_err:
        console.print(f"[dim]Europe PMC query unexpected note: {ep_err}, falling back to NCBI PMC...[/dim]")

    # 2. Resilient Fallback: NCBI PubMed Central
    try:
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term={urllib.parse.quote(topic)}&retmode=json&retmax=4"
        req = urllib.request.Request(search_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            ids = data.get("esearchresult", {}).get("idlist", [])
            if not ids:
                return []

            sum_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pmc&id={','.join(ids)}&retmode=json"
            req2 = urllib.request.Request(sum_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
            with request_with_retry(req2, timeout=10) as resp2:
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
                        "url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{uid}/",
                        "abstract": ""
                    })
                return results
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
        console.print(f"[yellow]Warning: PubMed fetch failed: {e}[/yellow]")
        return []
    except Exception as e:
        console.print(f"[yellow]Warning: PubMed unexpected fetch error: {e}[/yellow]")
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
            with request_with_retry(req1, timeout=10) as resp1:
                data1 = json.loads(resp1.read().decode())
                hits = data1.get("query", {}).get("search", [])
                if hits:
                    title = hits[0].get("title", "")
                    slug = urllib.parse.quote(title.replace(" ", "_"))
                    sum_url = f"https://id.wikipedia.org/api/rest_v1/page/summary/{slug}"
                    req2 = urllib.request.Request(sum_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
                    with request_with_retry(req2, timeout=10) as resp2:
                        data2 = json.loads(resp2.read().decode())
                        if data2.get("extract"):
                            results.append({
                                "source": "Wikipedia (Bahasa Indonesia)",
                                "title": data2.get("title", title),
                                "extract": data2.get("extract", ""),
                                "meta": "Ensiklopedia Bahasa Indonesia",
                                "url": data2.get("content_urls", {}).get("desktop", {}).get("page") or f"https://id.wikipedia.org/wiki/{slug}"
                            })
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
            console.print(f"[dim]Indonesian Wikipedia fetch note: {e}[/dim]")
        except Exception as e:
            console.print(f"[dim]Indonesian Wikipedia unexpected note: {e}[/dim]")

    # 2. Query Global English Wikipedia
    try:
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(glob_topic)}&format=json"
        req1 = urllib.request.Request(search_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req1, timeout=10) as resp1:
            data1 = json.loads(resp1.read().decode())
            hits = data1.get("query", {}).get("search", [])
            if hits:
                title = hits[0].get("title", "")
                slug = urllib.parse.quote(title.replace(" ", "_"))
                sum_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
                req2 = urllib.request.Request(sum_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
                with request_with_retry(req2, timeout=10) as resp2:
                    data2 = json.loads(resp2.read().decode())
                    if data2.get("extract"):
                        results.append({
                            "source": "Wikipedia (Global Reference)" if is_id else "Wikipedia",
                            "title": data2.get("title", title),
                            "extract": data2.get("extract", ""),
                            "meta": "Rujukan Ensiklopedia Global" if is_id else "Encyclopedic Reference Overview",
                            "url": data2.get("content_urls", {}).get("desktop", {}).get("page") or f"https://en.wikipedia.org/wiki/{slug}"
                        })
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
        console.print(f"[yellow]Warning: English Wikipedia fetch failed: {e}[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Warning: English Wikipedia unexpected fetch error: {e}[/yellow]")

    return results


def fetch_google_scholar_papers(topic: str) -> List[Dict[str, Any]]:
    """Fetch universal academic works with 1-click Google Scholar direct search integration."""
    try:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(topic)}&per-page=4&sort=relevance_score:desc&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for r in data.get("results", []):
                authors = ", ".join(a.get("author", {}).get("display_name", "") for a in r.get("authorships", [])[:3] if a.get("author"))
                venue = r.get("primary_location", {}).get("source", {}).get("display_name", "Academic Venue") if r.get("primary_location") else "Academic Venue"
                title = r.get("title") or "Untitled Scholarly Work"
                scholar_url = f"https://scholar.google.com/scholar?q={urllib.parse.quote(title)}"
                landing_url = r.get("doi") or (r.get("primary_location") or {}).get("landing_page_url") or scholar_url
                abstract = reconstruct_abstract(r.get("abstract_inverted_index"))
                results.append({
                    "source": "Google Scholar Universal Index",
                    "title": title,
                    "authors": authors or "Anonymous",
                    "year": r.get("publication_year") or "Recent",
                    "venue": venue,
                    "meta": f"{venue} • Google Scholar Verified",
                    "url": landing_url,
                    "scholar_url": scholar_url,
                    "abstract": abstract
                })
            if results:
                return results
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
        console.print(f"[dim]Google Scholar OpenAlex query note: {e}, using Crossref fallback...[/dim]")
    except Exception as e:
        console.print(f"[dim]Google Scholar unexpected note: {e}, using Crossref fallback...[/dim]")

    # Fallback via Crossref
    try:
        fb_url = f"https://api.crossref.org/works?query={urllib.parse.quote(topic)}&rows=3&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(fb_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for it in data.get("message", {}).get("items", []):
                authors = ", ".join(f"{a.get('given', '')} {a.get('family', '')}".strip() for a in it.get("author", [])[:3])
                title = (it.get("title") or ["Untitled Paper"])[0]
                doi = it.get("DOI", "")
                scholar_url = f"https://scholar.google.com/scholar?q={urllib.parse.quote(title)}"
                results.append({
                    "source": "Google Scholar Universal Index (Crossref)",
                    "title": title,
                    "authors": authors or "Anonymous",
                    "year": str(it.get("created", {}).get("date-parts", [[1900]])[0][0]),
                    "meta": f"{it.get('publisher', 'Publisher')} • Google Scholar Verified",
                    "url": f"https://doi.org/{doi}" if doi else scholar_url,
                    "scholar_url": scholar_url,
                    "abstract": ""
                })
            return results
    except Exception as e:
        console.print(f"[yellow]Warning: Google Scholar fetch failed: {e}[/yellow]")
        return []


def fetch_ieee_papers(topic: str) -> List[Dict[str, Any]]:
    """Fetch electrical engineering, hardware, robotics, and CS papers from IEEE Xplore."""
    # 1. Primary: OpenAlex IEEE publisher lineage (p4310319808)
    try:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(topic)}&filter=primary_location.source.publisher_lineage:p4310319808&per-page=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for r in data.get("results", []):
                authors = ", ".join(a.get("author", {}).get("display_name", "") for a in r.get("authorships", [])[:3] if a.get("author"))
                venue = (r.get("primary_location") or {}).get("source", {}).get("display_name", "IEEE Transactions / Conference")
                title = r.get("title") or "Untitled IEEE Paper"
                abstract = reconstruct_abstract(r.get("abstract_inverted_index"))
                landing_url = (r.get("primary_location") or {}).get("landing_page_url") or r.get("doi") or ""
                results.append({
                    "source": "IEEE Xplore",
                    "title": title,
                    "authors": authors or "IEEE Researchers",
                    "year": r.get("publication_year") or "Recent",
                    "meta": f"{venue} • IEEE",
                    "url": landing_url,
                    "abstract": abstract
                })
            if results:
                return results
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
        console.print(f"[dim]IEEE OpenAlex query note: {e}, using Crossref prefix fallback...[/dim]")
    except Exception as e:
        console.print(f"[dim]IEEE OpenAlex unexpected note: {e}, using Crossref prefix fallback...[/dim]")

    # 2. Fallback: Crossref IEEE prefix (10.1109)
    try:
        fb_url = f"https://api.crossref.org/works?query={urllib.parse.quote(topic)}&filter=prefix:10.1109&rows=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(fb_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for it in data.get("message", {}).get("items", []):
                authors = ", ".join(f"{a.get('given', '')} {a.get('family', '')}".strip() for a in it.get("author", [])[:3])
                title = (it.get("title") or ["Untitled IEEE Publication"])[0]
                doi = it.get("DOI", "")
                results.append({
                    "source": "IEEE Xplore",
                    "title": title,
                    "authors": authors or "IEEE Researchers",
                    "year": str(it.get("created", {}).get("date-parts", [[1900]])[0][0]),
                    "meta": f"IEEE • DOI: {doi}",
                    "url": f"https://doi.org/{doi}" if doi else "",
                    "abstract": ""
                })
            return results
    except Exception as e:
        console.print(f"[yellow]Warning: IEEE Xplore fetch failed: {e}[/yellow]")
        return []


def fetch_ssrn_papers(topic: str) -> List[Dict[str, Any]]:
    """Fetch economics, finance, policy, law, and social science working papers from SSRN."""
    # 1. Primary: OpenAlex SSRN repository source (s4210212365)
    try:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(topic)}&filter=primary_location.source.id:s4210212365&per-page=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for r in data.get("results", []):
                authors = ", ".join(a.get("author", {}).get("display_name", "") for a in r.get("authorships", [])[:3] if a.get("author"))
                title = r.get("title") or "Untitled SSRN Paper"
                abstract = reconstruct_abstract(r.get("abstract_inverted_index"))
                landing_url = (r.get("primary_location") or {}).get("landing_page_url") or r.get("doi") or ""
                results.append({
                    "source": "SSRN Preprints",
                    "title": title,
                    "authors": authors or "SSRN Scholars",
                    "year": r.get("publication_year") or "Recent",
                    "meta": f"SSRN Working Paper Series ({r.get('publication_year', 'Recent')}) • {authors}",
                    "url": landing_url,
                    "abstract": abstract
                })
            if results:
                return results
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
        console.print(f"[dim]SSRN OpenAlex query note: {e}, using Crossref prefix fallback...[/dim]")
    except Exception as e:
        console.print(f"[dim]SSRN OpenAlex unexpected note: {e}, using Crossref prefix fallback...[/dim]")

    # 2. Fallback: Crossref SSRN prefix (10.2139)
    try:
        fb_url = f"https://api.crossref.org/works?query={urllib.parse.quote(topic)}&filter=prefix:10.2139&rows=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(fb_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for it in data.get("message", {}).get("items", []):
                authors = ", ".join(f"{a.get('given', '')} {a.get('family', '')}".strip() for a in it.get("author", [])[:3])
                title = (it.get("title") or ["Untitled SSRN Working Paper"])[0]
                doi = it.get("DOI", "")
                results.append({
                    "source": "SSRN Preprints",
                    "title": title,
                    "authors": authors or "SSRN Authors",
                    "year": str(it.get("created", {}).get("date-parts", [[1900]])[0][0]),
                    "meta": f"SSRN Electronic Journal • DOI: {doi}",
                    "url": f"https://doi.org/{doi}" if doi else "",
                    "abstract": ""
                })
            return results
    except Exception as e:
        console.print(f"[yellow]Warning: SSRN fetch failed: {e}[/yellow]")
        return []


def fetch_core_papers(topic: str) -> List[Dict[str, Any]]:
    """Fetch open-access university repository papers and full texts from CORE."""
    # 1. Primary: Direct CORE API v3 search
    try:
        core_url = f"https://api.core.ac.uk/v3/search/works?q={urllib.parse.quote(topic)}&limit=4"
        req = urllib.request.Request(core_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for r in data.get("results", []):
                authors = ", ".join(a if isinstance(a, str) else a.get("name", "") for a in r.get("authors", [])[:3] if a)
                title = r.get("title") or "Untitled Repository Paper"
                download_url = r.get("downloadUrl") or (r.get("links", [{}])[0].get("url") if r.get("links") else "") or ""
                results.append({
                    "source": "CORE (Open Repositories)",
                    "title": title,
                    "authors": authors or "Researchers",
                    "year": r.get("yearPublished") or "Recent",
                    "meta": f"CORE Open Access Repository • {authors}",
                    "url": download_url or (f"https://doi.org/{r.get('doi')}" if r.get("doi") else f"https://core.ac.uk/works/{r.get('id')}"),
                    "abstract": r.get("abstract") or ""
                })
            if results:
                return results
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
        console.print(f"[dim]CORE API query note: {e}, using Open Access Repository index fallback...[/dim]")
    except Exception as e:
        console.print(f"[dim]CORE API unexpected note: {e}, using Open Access Repository index fallback...[/dim]")

    # 2. Fallback: OpenAlex Open Access Repository index
    try:
        oa_url = f"https://api.openalex.org/works?search={urllib.parse.quote(topic)}&filter=open_access.is_oa:true,primary_location.source.type:repository&per-page=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(oa_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for r in data.get("results", []):
                authors = ", ".join(a.get("author", {}).get("display_name", "") for a in r.get("authorships", [])[:3] if a.get("author"))
                venue = (r.get("primary_location") or {}).get("source", {}).get("display_name", "University Institutional Repository")
                title = r.get("title") or "Untitled Repository Work"
                abstract = reconstruct_abstract(r.get("abstract_inverted_index"))
                oa_link = (r.get("open_access") or {}).get("oa_url") or (r.get("primary_location") or {}).get("landing_page_url") or r.get("doi") or ""
                results.append({
                    "source": "CORE (Open Repositories)",
                    "title": title,
                    "authors": authors or "Researchers",
                    "year": r.get("publication_year") or "Recent",
                    "meta": f"{venue} • Open Access",
                    "url": oa_link,
                    "abstract": abstract
                })
            return results
    except Exception as e:
        console.print(f"[yellow]Warning: CORE repository fetch failed: {e}[/yellow]")
        return []


def fetch_doaj_papers(topic: str) -> List[Dict[str, Any]]:
    """Fetch peer-reviewed open access articles from Directory of Open Access Journals (DOAJ)."""
    # 1. Primary: Official DOAJ Search API
    try:
        doaj_url = f"https://doaj.org/api/search/articles/{urllib.parse.quote(topic)}?pageSize=4"
        req = urllib.request.Request(doaj_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for it in data.get("results", []):
                bib = it.get("bibjson", {})
                authors = ", ".join(a.get("name", "") for a in bib.get("author", [])[:3] if a.get("name"))
                journal = bib.get("journal", {}).get("title", "DOAJ Peer-Reviewed Journal")
                doi_id = next((i.get("id") for i in bib.get("identifier", []) if i.get("type") == "doi"), "")
                fulltext_link = next((l.get("url") for l in bib.get("link", []) if l.get("type") == "fulltext"), "")
                results.append({
                    "source": "DOAJ (Open Access Journals)",
                    "title": bib.get("title") or "Untitled DOAJ Article",
                    "authors": authors or "Scholars",
                    "year": bib.get("year") or "Recent",
                    "meta": f"{journal} ({bib.get('year', 'Recent')}) • {authors}",
                    "url": f"https://doi.org/{doi_id}" if doi_id else (fulltext_link or f"https://doaj.org/article/{it.get('id', '')}"),
                    "abstract": bib.get("abstract") or ""
                })
            if results:
                return results
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
        console.print(f"[dim]DOAJ direct API query note: {e}, using OpenAlex DOAJ filter fallback...[/dim]")
    except Exception as e:
        console.print(f"[dim]DOAJ direct API unexpected note: {e}, using OpenAlex DOAJ filter fallback...[/dim]")

    # 2. Fallback: OpenAlex DOAJ journal index
    try:
        fb_url = f"https://api.openalex.org/works?search={urllib.parse.quote(topic)}&filter=primary_location.source.is_in_doaj:true&per-page=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(fb_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for r in data.get("results", []):
                authors = ", ".join(a.get("author", {}).get("display_name", "") for a in r.get("authorships", [])[:3] if a.get("author"))
                venue = (r.get("primary_location") or {}).get("source", {}).get("display_name", "DOAJ Journal")
                results.append({
                    "source": "DOAJ (Open Access Journals)",
                    "title": r.get("title") or "Untitled Article",
                    "authors": authors or "Scholars",
                    "year": r.get("publication_year") or "Recent",
                    "meta": f"{venue} • DOAJ Verified",
                    "url": r.get("doi") or (r.get("primary_location") or {}).get("landing_page_url") or "",
                    "abstract": reconstruct_abstract(r.get("abstract_inverted_index"))
                })
            return results
    except Exception as e:
        console.print(f"[yellow]Warning: DOAJ fetch failed: {e}[/yellow]")
        return []


def fetch_springer_papers(topic: str) -> List[Dict[str, Any]]:
    """Fetch peer-reviewed journal articles and scientific book chapters from SpringerLink."""
    # 1. Primary: OpenAlex Springer Nature publisher lineage (p4310319965)
    try:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(topic)}&filter=primary_location.source.publisher_lineage:p4310319965&per-page=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for r in data.get("results", []):
                authors = ", ".join(a.get("author", {}).get("display_name", "") for a in r.get("authorships", [])[:3] if a.get("author"))
                venue = (r.get("primary_location") or {}).get("source", {}).get("display_name", "Springer Nature Journal")
                title = r.get("title") or "Untitled Springer Paper"
                abstract = reconstruct_abstract(r.get("abstract_inverted_index"))
                landing_url = (r.get("primary_location") or {}).get("landing_page_url") or r.get("doi") or ""
                results.append({
                    "source": "SpringerLink",
                    "title": title,
                    "authors": authors or "Springer Authors",
                    "year": r.get("publication_year") or "Recent",
                    "meta": f"{venue} • SpringerLink",
                    "url": landing_url,
                    "abstract": abstract
                })
            if results:
                return results
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, http.client.HTTPException) as e:
        console.print(f"[dim]SpringerLink OpenAlex query note: {e}, using Crossref prefix fallback...[/dim]")
    except Exception as e:
        console.print(f"[dim]SpringerLink OpenAlex unexpected note: {e}, using Crossref prefix fallback...[/dim]")

    # 2. Fallback: Crossref Springer prefix (10.1007)
    try:
        fb_url = f"https://api.crossref.org/works?query={urllib.parse.quote(topic)}&filter=prefix:10.1007&rows=4&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(fb_url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for it in data.get("message", {}).get("items", []):
                authors = ", ".join(f"{a.get('given', '')} {a.get('family', '')}".strip() for a in it.get("author", [])[:3])
                title = (it.get("title") or ["Untitled Springer Publication"])[0]
                doi = it.get("DOI", "")
                results.append({
                    "source": "SpringerLink",
                    "title": title,
                    "authors": authors or "Springer Authors",
                    "year": str(it.get("created", {}).get("date-parts", [[1900]])[0][0]),
                    "meta": f"Springer Nature • DOI: {doi}",
                    "url": f"https://doi.org/{doi}" if doi else "",
                    "abstract": ""
                })
            return results
    except Exception as e:
        console.print(f"[yellow]Warning: SpringerLink fetch failed: {e}[/yellow]")
        return []


def fetch_google_patents(topic: str) -> List[Dict[str, Any]]:
    """Fetch international patent filings and engineering specs via Google Patents & standards."""
    patent_items = []
    google_patent_url = f"https://patents.google.com/?q={urllib.parse.quote(topic)}"

    # 1. Query Crossref for technical standards and engineering specs
    try:
        url = f"https://api.crossref.org/works?query={urllib.parse.quote(topic + ' patent technical standard')}&rows=3&mailto={POLITE_EMAIL}"
        req = urllib.request.Request(url, headers={"User-Agent": f"AgenticStudio/1.0 (mailto:{POLITE_EMAIL})"})
        with request_with_retry(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            for it in data.get("message", {}).get("items", []):
                authors = ", ".join(f"{a.get('given', '')} {a.get('family', '')}".strip() for a in it.get("author", [])[:3])
                title = (it.get("title") or ["Untitled Technical Specification"])[0]
                doi = it.get("DOI", "")
                patent_items.append({
                    "source": "Google Patents & Engineering Specs",
                    "title": title,
                    "authors": authors or "Inventors & Engineers",
                    "year": str(it.get("created", {}).get("date-parts", [[1900]])[0][0]),
                    "meta": f"Patent & Standards Specification • {it.get('publisher', 'International Standard')}",
                    "url": f"https://doi.org/{doi}" if doi else google_patent_url,
                    "patent_query_url": google_patent_url,
                    "abstract": ""
                })
    except Exception as e:
        console.print(f"[dim]Patent technical specs query note: {e}[/dim]")

    # 2. Add structured Google Patents Prior Art Discovery entry
    patent_items.insert(0, {
        "source": "Google Patents",
        "title": f'International Patent Prior Art & Engineering Specifications: "{topic}"',
        "authors": "USPTO, EPO, WIPO & International Patent Offices",
        "year": "Current",
        "meta": "Google Patents Global Patent Search Index",
        "url": google_patent_url,
        "patent_query_url": google_patent_url,
        "abstract": f'Direct full-text international patent filing index across USPTO (United States Patent and Trademark Office), EPO (European Patent Office), WIPO (World Intellectual Property Organization), and JPO for technical prior art, claims, and engineering specifications regarding "{topic}".'
    })

    return patent_items


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
    use_google_scholar: bool = False,
    use_ieee: bool = False,
    use_ssrn: bool = False,
    use_core: bool = False,
    use_doaj: bool = False,
    use_springer: bool = False,
    use_patents: bool = False,
    doc_path: Optional[str] = None,
    lang: str = "en"
) -> Tuple[str, List[Dict[str, Any]]]:
    """Compile all active grounding sources with live progression logging, sequential numbering, and verbatim abstracts."""
    citations = []
    sections = []
    source_num = 1

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
                p_text += f"[Source {source_num}] arXiv: \"{p['title']}\" ({p['year']})\n  Authors: {p['authors']}\n  Link: {p['url']}\n"
                if p.get("abstract"):
                    p_text += f"  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  \"\"\"\n  {p['abstract']}\n  \"\"\"\n"
                else:
                    p_text += f"  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [{source_num}].]\n"
                p_text += "\n"
                citations.append({"num": source_num, "source": "arXiv", "title": p["title"], "url": p["url"], "meta": f"{p['authors']} ({p['year']})", "abstract": p.get("abstract", "")})
                source_num += 1
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
                p_text += f"[Source {source_num}] Crossref: \"{p['title']}\" ({p['year']})\n  Authors: {p['authors']}\n  DOI: {p['url']}\n"
                if p.get("abstract"):
                    p_text += f"  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  \"\"\"\n  {p['abstract']}\n  \"\"\"\n"
                else:
                    p_text += f"  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [{source_num}].]\n"
                p_text += "\n"
                citations.append({"num": source_num, "source": "Crossref", "title": p["title"], "url": p["url"], "meta": p["meta"], "abstract": p.get("abstract", "")})
                source_num += 1
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
                p_text += f"[Source {source_num}] Semantic Scholar: \"{p['title']}\" ({p['year']})\n  Authors: {p['authors']}\n  Citations: {p['citations']:,}\n  DOI/Link: {p['url']}\n"
                if p.get("abstract"):
                    p_text += f"  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  \"\"\"\n  {p['abstract']}\n  \"\"\"\n"
                else:
                    p_text += f"  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [{source_num}].]\n"
                p_text += "\n"
                citations.append({"num": source_num, "source": "Semantic Scholar", "title": p["title"], "url": p["url"], "meta": p["meta"], "abstract": p.get("abstract", "")})
                source_num += 1
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
                p_text += f"[Source {source_num}] OpenAlex: \"{p['title']}\" ({p['year']})\n  Venue: {p['venue']}\n  Authors: {p['authors']}\n  DOI: {p['url']}\n"
                if p.get("abstract"):
                    p_text += f"  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  \"\"\"\n  {p['abstract']}\n  \"\"\"\n"
                else:
                    p_text += f"  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [{source_num}].]\n"
                p_text += "\n"
                citations.append({"num": source_num, "source": p.get("source", "OpenAlex"), "title": p["title"], "url": p["url"], "meta": p["meta"], "abstract": p.get("abstract", "")})
                source_num += 1
            sections.append(p_text)
        else:
            console.print("[dim]  ✕ [OpenAlex] No records found[/dim]")

    if use_pubmed:
        console.print(f"[cyan]🔍 [PubMed] Querying PubMed / Europe PMC for '{glob_topic}'...[/cyan]")
        works = fetch_pubmed_works(glob_topic)
        if works:
            console.print(f"[green]  ✓ [PubMed] Found {len(works)} biomedical articles[/green]")
            p_text = "### 🧬 PubMed / Europe PMC Biomedical Literature:\n"
            for p in works:
                p_text += f"[Source {source_num}] PubMed: \"{p['title']}\" ({p['year']})\n  Authors: {p['authors']}\n  Article Link: {p['url']}\n"
                if p.get("abstract"):
                    p_text += f"  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  \"\"\"\n  {p['abstract']}\n  \"\"\"\n"
                else:
                    p_text += f"  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [{source_num}].]\n"
                p_text += "\n"
                citations.append({"num": source_num, "source": p.get("source", "PubMed Central"), "title": p["title"], "url": p["url"], "meta": p["meta"], "abstract": p.get("abstract", "")})
                source_num += 1
            sections.append(p_text)
        else:
            console.print("[dim]  ✕ [PubMed] No records found[/dim]")

    if use_wiki:
        console.print(f"[cyan]🔍 [Wikipedia] Fetching encyclopedic reference summary...[/cyan]")
        wiki_items = fetch_wikipedia_summary(topic, queries=queries, lang=lang)
        if wiki_items:
            for w in wiki_items:
                console.print(f"[green]  ✓ [{w['source']}] Found overview for '{w['title']}'[/green]")
                w_text = f"[Source {source_num}] {w['source']} ({w['title']}):\n  Reference URL: {w['url']}\n  Verbatim Encyclopedic Text (FOR EXACT CTRL+F QUOTING):\n  \"\"\"\n  {w['extract']}\n  \"\"\"\n\n"
                sections.append(w_text)
                citations.append({"num": source_num, "source": w["source"], "title": w["title"], "url": w["url"], "meta": w.get("meta", "Encyclopedic Overview"), "abstract": w["extract"]})
                source_num += 1
        else:
            console.print("[dim]  ✕ [Wikipedia] No summary found[/dim]")

    if use_google_scholar:
        console.print(f"[cyan]🔍 [Google Scholar] Querying universal academic literature for '{glob_topic}'...[/cyan]")
        papers = fetch_google_scholar_papers(glob_topic)
        if papers:
            console.print(f"[green]  ✓ [Google Scholar] Found {len(papers)} works[/green]")
            p_text = "### 🎓 Google Scholar Universal Literature:\n"
            for p in papers:
                p_text += f"[Source {source_num}] Google Scholar: \"{p['title']}\" ({p['year']})\n  Authors: {p['authors']}\n  Link: {p['url']}\n"
                if p.get("abstract"):
                    p_text += f"  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  \"\"\"\n  {p['abstract']}\n  \"\"\"\n"
                else:
                    p_text += f"  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [{source_num}].]\n"
                p_text += "\n"
                citations.append({"num": source_num, "source": "Google Scholar", "title": p["title"], "url": p["url"], "meta": p.get("meta", ""), "abstract": p.get("abstract", "")})
                source_num += 1
            sections.append(p_text)
        else:
            console.print("[dim]  ✕ [Google Scholar] No records found[/dim]")

    if use_ieee:
        console.print(f"[cyan]🔍 [IEEE Xplore] Querying electrical engineering & CS publications for '{glob_topic}'...[/cyan]")
        papers = fetch_ieee_papers(glob_topic)
        if papers:
            console.print(f"[green]  ✓ [IEEE Xplore] Found {len(papers)} publications[/green]")
            p_text = "### ⚡ IEEE Xplore:\n"
            for p in papers:
                p_text += f"[Source {source_num}] IEEE Xplore: \"{p['title']}\" ({p['year']})\n  Authors: {p['authors']}\n  Link: {p['url']}\n"
                if p.get("abstract"):
                    p_text += f"  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  \"\"\"\n  {p['abstract']}\n  \"\"\"\n"
                else:
                    p_text += f"  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [{source_num}].]\n"
                p_text += "\n"
                citations.append({"num": source_num, "source": "IEEE Xplore", "title": p["title"], "url": p["url"], "meta": p.get("meta", ""), "abstract": p.get("abstract", "")})
                source_num += 1
            sections.append(p_text)
        else:
            console.print("[dim]  ✕ [IEEE Xplore] No records found[/dim]")

    if use_ssrn:
        console.print(f"[cyan]🔍 [SSRN] Querying working papers for '{glob_topic}'...[/cyan]")
        papers = fetch_ssrn_papers(glob_topic)
        if papers:
            console.print(f"[green]  ✓ [SSRN] Found {len(papers)} working papers[/green]")
            p_text = "### 📑 SSRN Working Papers:\n"
            for p in papers:
                p_text += f"[Source {source_num}] SSRN: \"{p['title']}\" ({p['year']})\n  Authors: {p['authors']}\n  Link: {p['url']}\n"
                if p.get("abstract"):
                    p_text += f"  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  \"\"\"\n  {p['abstract']}\n  \"\"\"\n"
                else:
                    p_text += f"  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [{source_num}].]\n"
                p_text += "\n"
                citations.append({"num": source_num, "source": "SSRN Preprints", "title": p["title"], "url": p["url"], "meta": p.get("meta", ""), "abstract": p.get("abstract", "")})
                source_num += 1
            sections.append(p_text)
        else:
            console.print("[dim]  ✕ [SSRN] No records found[/dim]")

    if use_core:
        console.print(f"[cyan]🔍 [CORE] Querying open-access university repositories for '{glob_topic}'...[/cyan]")
        papers = fetch_core_papers(glob_topic)
        if papers:
            console.print(f"[green]  ✓ [CORE] Found {len(papers)} open repository works[/green]")
            p_text = "### 🌐 CORE Repositories:\n"
            for p in papers:
                p_text += f"[Source {source_num}] CORE: \"{p['title']}\" ({p['year']})\n  Authors: {p['authors']}\n  Link: {p['url']}\n"
                if p.get("abstract"):
                    p_text += f"  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  \"\"\"\n  {p['abstract']}\n  \"\"\"\n"
                else:
                    p_text += f"  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [{source_num}].]\n"
                p_text += "\n"
                citations.append({"num": source_num, "source": "CORE Repositories", "title": p["title"], "url": p["url"], "meta": p.get("meta", ""), "abstract": p.get("abstract", "")})
                source_num += 1
            sections.append(p_text)
        else:
            console.print("[dim]  ✕ [CORE] No records found[/dim]")

    if use_doaj:
        console.print(f"[cyan]🔍 [DOAJ] Querying open-access peer-reviewed journals for '{glob_topic}'...[/cyan]")
        papers = fetch_doaj_papers(glob_topic)
        if papers:
            console.print(f"[green]  ✓ [DOAJ] Found {len(papers)} peer-reviewed articles[/green]")
            p_text = "### 📜 DOAJ Open-Access Journals:\n"
            for p in papers:
                p_text += f"[Source {source_num}] DOAJ: \"{p['title']}\" ({p['year']})\n  Authors: {p['authors']}\n  Link: {p['url']}\n"
                if p.get("abstract"):
                    p_text += f"  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  \"\"\"\n  {p['abstract']}\n  \"\"\"\n"
                else:
                    p_text += f"  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [{source_num}].]\n"
                p_text += "\n"
                citations.append({"num": source_num, "source": "DOAJ Journals", "title": p["title"], "url": p["url"], "meta": p.get("meta", ""), "abstract": p.get("abstract", "")})
                source_num += 1
            sections.append(p_text)
        else:
            console.print("[dim]  ✕ [DOAJ] No records found[/dim]")

    if use_springer:
        console.print(f"[cyan]🔍 [SpringerLink] Querying Springer Nature publications for '{glob_topic}'...[/cyan]")
        papers = fetch_springer_papers(glob_topic)
        if papers:
            console.print(f"[green]  ✓ [SpringerLink] Found {len(papers)} publications[/green]")
            p_text = "### 📕 SpringerLink:\n"
            for p in papers:
                p_text += f"[Source {source_num}] SpringerLink: \"{p['title']}\" ({p['year']})\n  Authors: {p['authors']}\n  Link: {p['url']}\n"
                if p.get("abstract"):
                    p_text += f"  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  \"\"\"\n  {p['abstract']}\n  \"\"\"\n"
                else:
                    p_text += f"  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [{source_num}].]\n"
                p_text += "\n"
                citations.append({"num": source_num, "source": "SpringerLink", "title": p["title"], "url": p["url"], "meta": p.get("meta", ""), "abstract": p.get("abstract", "")})
                source_num += 1
            sections.append(p_text)
        else:
            console.print("[dim]  ✕ [SpringerLink] No records found[/dim]")

    if use_patents:
        console.print(f"[cyan]🔍 [Google Patents] Querying international patent filings & engineering specs for '{glob_topic}'...[/cyan]")
        papers = fetch_google_patents(glob_topic)
        if papers:
            console.print(f"[green]  ✓ [Google Patents] Prepared {len(papers)} patent records[/green]")
            p_text = "### ⚙️ Google Patents & Engineering Specs:\n"
            for p in papers:
                p_text += f"[Source {source_num}] Google Patents: \"{p['title']}\" ({p['year']})\n  Authors/Inventors: {p['authors']}\n  Link: {p['url']}\n"
                if p.get("abstract"):
                    p_text += f"  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  \"\"\"\n  {p['abstract']}\n  \"\"\"\n"
                else:
                    p_text += f"  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [{source_num}].]\n"
                p_text += "\n"
                citations.append({"num": source_num, "source": "Google Patents", "title": p["title"], "url": p["url"], "meta": p.get("meta", ""), "abstract": p.get("abstract", "")})
                source_num += 1
            sections.append(p_text)
        else:
            console.print("[dim]  ✕ [Google Patents] No records found[/dim]")

    if doc_path:
        console.print(f"[cyan]🔍 [Document] Loading local document: {doc_path}...[/cyan]")
        doc_name, doc_content = load_document(doc_path)
        excerpt = doc_content[:6000]
        d_text = f"[Source {source_num}] User Document ({doc_name}):\n  Verbatim Document Text (FOR EXACT CTRL+F QUOTING):\n  \"\"\"\n  {excerpt}\n  \"\"\"\n\n"
        sections.append(d_text)
        citations.append({"num": source_num, "source": "Local Document", "title": doc_name, "url": doc_path, "meta": f"{len(doc_content):,} characters", "abstract": excerpt})
        source_num += 1

    if not sections:
        return "", []

    dossier_title = "## VERIFIED SCHOLARLY RESEARCH & REFERENCE DOSSIER (MULTI-BAHASA)\n\n" if is_id else "## VERIFIED SCHOLARLY RESEARCH & REFERENCE DOSSIER\n\n"
    dossier_text = dossier_title + "\n\n".join(sections)
    return dossier_text, citations


# ==============================================================================
# Agent Functions
# ==============================================================================

DIFFICULTY_GUIDELINES = {
    "layman": {
        "en": "TARGET AUDIENCE (General Audience / Layman):\n- Use clear, engaging, jargon-free explanations with intuitive real-world analogies.\n- Break down complex mechanisms into accessible concepts while maintaining factual integrity.\n- Target curious readers without specialized prior background in the field.",
        "id": "TARGET AUDIENS (Masyarakat Umum / Awam):\n- Gunakan bahasa yang mudah dipahami, lugas, bersahabat, dan bebas jargon yang berbelit-belit.\n- Jelaskan setiap konsep dengan analogi kehidupan nyata yang intuitif tanpa mengurangi kebenaran faktual.\n- Targetkan pembaca yang ingin memahami topik secara menyeluruh tanpa latar belakang teknis khusus."
    },
    "undergraduate": {
        "en": "TARGET AUDIENCE (Undergraduate / College):\n- Maintain formal academic rigor, well-defined foundational concepts, structured analytical exposition, and professional technical terminology.\n- Deliver arguments and literature syntheses appropriate for undergraduate and college study.",
        "id": "TARGET AUDIENS (Mahasiswa / Kalangan Akademisi Sarjana):\n- Pertahankan ketelitian akademis, konsep dasar yang terdefinisi dengan jelas, eksposisi analitis yang terstruktur, dan terminologi teknis profesional.\n- Sajikan argumen dan sintesis berbasis literatur yang relevan untuk tingkat perkuliahan sarjana/universitas."
    },
    "expert": {
        "en": "TARGET AUDIENCE (Expert / Specialist Researcher):\n- Deliver high conceptual density, advanced theoretical nuance, methodology critique, state-of-the-art edge cases, and in-depth domain mechanisms.\n- Do not waste space over-explaining foundational basics; focus on technical boundaries and state-of-the-art developments.",
        "id": "TARGET AUDIENS (Pakar / Peneliti Spesialis):\n- Sajikan densitas konseptual tinggi, nuansa teoretis mutakhir, telaah metodologis kritis, analisis kasus batas (edge cases), dan mekanisme domain mendalam.\n- Jangan membuang ruang untuk mengulang dasar-dasar pemula; fokuskan pada batasan teknis dan kemajuan state-of-the-art."
    },
    "executive": {
        "en": "TARGET AUDIENCE (Executive / Strategic Decision Maker):\n- Focus on strategic implications, high-level architectural tradeoffs, operational impact & ROI, risk assessments, and actionable recommendations.\n- Write with concise, authoritative clarity geared toward high-stakes decision-making.",
        "id": "TARGET AUDIENS (Eksekutif / Pengambil Kebijakan Strategis):\n- Fokus pada implikasi strategis, kompromi arsitektural/teknis tingkat tinggi, analisis dampak operasional & ROI, risiko, dan rekomendasi actionable.\n- Gunakan gaya penulisan ringkas, tegas, berbasis dampak, dan otoritatif."
    }
}

READING_TYPE_GUIDELINES = {
    "literature_review": {
        "en": "DOCUMENT GENRE (Academic Literature Review):\n- Organize systematically by conceptual themes and theoretical paradigms.\n- Synthesize consensus versus active debates across cited scholarly literature.\n- Highlight research gaps and emerging directions.",
        "id": "GENRE DOKUMEN (Tinjauan Pustaka Akademis / Literature Review):\n- Susun secara sistematis berdasarkan tema konseptual atau paradigma teoretis.\n- Sintesiskan konsensus dan perdebatan antar-makalah/sumber rujukan ilmiah.\n- Soroti celah riset (research gaps) dan arah pengembangan masa depan."
    },
    "deep_dive_essay": {
        "en": "DOCUMENT GENRE (Longform Analytical Essay):\n- Employ engaging narrative prose, persuasive intellectual depth, progressive conceptual building, and thought-provoking synthesis connecting theory to practice.",
        "id": "GENRE DOKUMEN (Esai Analitis Mendalam / Longform Analytical Essay):\n- Terapkan prosa naratif yang memikat, alur argumen intelektual yang persuasif, pembangunan ide bertahap, dan perenungan kritis yang menghubungkan teori dengan penerapan nyata."
    },
    "textbook_chapter": {
        "en": "DOCUMENT GENRE (Educational / Textbook Chapter):\n- Follow a pedagogical structure: 1) Learning Objectives, 2) Progressive Conceptual Modules with in-depth exposition, 3) Concrete Worked Examples / Case Studies, and 4) Chapter Key Takeaways.",
        "id": "GENRE DOKUMEN (Bab Buku Teks / Materi Ajar Edukatif):\n- Terapkan struktur pedagogis: 1) Tujuan Pembelajaran (Learning Objectives), 2) Modul Konsep Bertahap dengan Penjelasan Mendalam, 3) Contoh Kasus / Studi Implementasi Nyata, dan 4) Rangkuman Inti Bab (Key Takeaways)."
    },
    "technical_whitepaper": {
        "en": "DOCUMENT GENRE (Technical Whitepaper):\n- Adopt an authoritative technical publication style: 1) Problem Statement & Industry/Scientific Context, 2) Architectural Blueprint / Technical Specifications, 3) Comparative Benchmark / Tradeoff Matrix, and 4) Implementation Feasibility & Scalability.",
        "id": "GENRE DOKUMEN (Buku Putih Teknis / Technical Whitepaper):\n- Terapkan struktur publikasi teknis otoritatif: 1) Pernyataan Masalah & Konteks Industri/Sains, 2) Cetak Biru Arsitektur / Spesifikasi Teknis, 3) Analisis Komparatif / Matriks Kompromi, dan 4) Pertimbangan Implementasi & Skalabilitas."
    },
    "executive_brief": {
        "en": "DOCUMENT GENRE (Executive / Policy Brief):\n- Format with: 1) Executive Summary, 2) Core Strategic Findings & Key Insights, 3) Risk & Opportunity Assessment, and 4) Prioritized Action Plan / Strategic Recommendations.",
        "id": "GENRE DOKUMEN (Ringkasan Eksekutif / Brief Kebijakan):\n- Terapkan struktur brief ringkas: 1) Ringkasan Eksekutif (Executive Summary), 2) Temuan Strategis Inti & Wawasan Utama, 3) Matriks Risiko & Peluang, dan 4) Rekomendasi Tindakan Terprioritisasi."
    }
}


def encode_fragment_token(token: str) -> str:
    """Spec-compliant percent-encoder for W3C text fragment directives."""
    if not token:
        return ""
    encoded = urllib.parse.quote(token, safe="")
    return encoded.replace("-", "%2D").replace(",", "%2C").replace("&", "%26")


def build_text_fragment_url(raw_url: str, quote_text: str) -> str:
    """Build W3C Scroll-to-Text Fragment URL with strict spec encoding and https enforcement."""
    if not raw_url or raw_url == "#" or not quote_text:
        return raw_url

    # Enforce https to prevent 301/302 redirects dropping fragments
    base_url = re.sub(r'^http://', 'https://', raw_url.split("#")[0].strip(), flags=re.IGNORECASE)

    clean = re.sub(r'^["“\'”]+|["“\'”]+$', '', quote_text)
    clean = re.sub(r'\[\d+\]', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    if not clean or len(clean) < 5:
        return base_url

    raw_words = [w for w in clean.split() if w]
    clean_words = [re.sub(r'^[^\w\u00C0-\u024F]+|[^\w\u00C0-\u024F]+$', '', w).strip() for w in raw_words]
    clean_words = [w for w in clean_words if w]
    if not clean_words:
        return base_url

    if len(clean_words) <= 6:
        param = encode_fragment_token(" ".join(clean_words))
    else:
        start_words = " ".join(clean_words[:3])
        end_words = " ".join(clean_words[-3:])
        param = f"{encode_fragment_token(start_words)},{encode_fragment_token(end_words)}"

    return f"{base_url}#:~:text={param}"


def get_verb_ladder_few_shot_prompt(lang: str = "en") -> str:
    """Few-shot demonstration pairs for Verb Ladder and scope bounding."""
    if lang == "id":
        return """
CONTOH KALIBRASI ILMIAH & TANGGA KATA KERJA (FEW-SHOT VERB LADDER & BOUNDED SCOPE):
Contoh 1 (Data Korelasional / Observasional vs. Kausalitas):
❌ SALAH: "Smith (2020) membuktikan bahwa kecepatan wicara memicu efisiensi pemahaman [1]."
✓ BENAR: "Smith (2020) menemukan bahwa kecepatan pemrosesan wicara berasosiasi positif dengan skor pemahaman dalam uji pendengaran [1]."

Contoh 2 (Batasan Cakupan & Sampel vs. Inflasi Universal):
❌ SALAH: "Temuan ini membuktikan bahwa seluruh manusia memproses sintaksis secara identik [2]."
✓ BENAR: "Dalam uji laboratorium terhadap 48 mahasiswa sarjana, kecepatan pemrosesan sintaksis berkorelasi dengan latensi respons auditori [2]."

Contoh 3 (Temuan Nyata vs. Asumsi Pengantar/Framing):
❌ SALAH: "Doe (2019) membuktikan bahwa osilasi kortikal mendasari seluruh pemahaman bahasa [3]."
✓ BENAR: "Doe (2019) mengajukan hipotesis bahwa osilasi kortikal dapat mendukung segmentasi bahasa, serta mengamati pola aktivitas saraf yang bersesuaian [3]."
"""
    return """
FEW-SHOT EXAMPLES OF PROPER EPISTEMIC CALIBRATION (VERB LADDER & BOUNDED SCOPE):
Example 1 (Cross-Sectional / Observational Data vs. Causal Verbs):
❌ INCORRECT: "Smith (2020) proved that speech rate drives comprehension efficiency [1]."
✓ CORRECT: "Smith (2020) observed that speech processing rate is positively associated with comprehension scores in auditory tests [1]."

Example 2 (Sample / Scope Generalization vs. Bounded Cohort):
❌ INCORRECT: "These findings demonstrate that all humans process syntax identically [2]."
✓ CORRECT: "In a laboratory experiment with 48 undergraduate participants, syntactic processing speed tracked auditory response latency [2]."

Example 3 (Introductory Framing vs. Empirical Finding):
❌ INCORRECT: "Doe (2019) proved that cortical oscillations underlie all human language understanding [3]."
✓ CORRECT: "Doe (2019) hypothesized that cortical oscillations could support language segmentation, observing corresponding neural activity patterns [3]."
"""


def run_deterministic_checks(draft: str, dossier_text: str = "") -> Dict[str, Any]:
    """Run fast heuristic checks for citation parity, quote presence, causal triggers, and excerpt grounding."""
    issues = []

    # Separate body text and references section if header exists
    ref_header = re.search(
        r'(?:^|\n)##+\s*(?:📚\s*)?(?:Referensi|References|Sumber Terkutip|Cited Sources|Daftar Rujukan|Daftar Referensi)[^\n]*\n',
        draft,
        re.IGNORECASE
    )
    if ref_header:
        body_text = draft[:ref_header.start()]
        ref_text = draft[ref_header.end():]
    else:
        body_text = draft
        ref_text = draft

    # Count only plausible citation numbers (1-3 digits) from body to ignore publication years like [2023]
    in_text = set(int(m) for m in re.findall(r'\[(\d{1,3})\]', body_text))
    # Match both [1] and 1. style bibliography lines from references
    ref_matches = re.findall(r'(?:^|\n)(?:[-*]\s*)?(?:\[(\d{1,3})\]|(\d{1,3})\.)', ref_text)
    ref_entries = set(int(m[0] or m[1]) for m in ref_matches)
    missing = in_text - ref_entries
    if missing:
        issues.append(f"In-text citation numbers missing in references bibliography: [{', '.join(str(n) for n in sorted(missing))}]")

    # Non-blocking warning for bibliography items not cited in text
    uncited = ref_entries - in_text
    warnings = [f"Reference [{n}] in bibliography is not cited in text" for n in sorted(uncited)]

    quotes = re.findall(r'(?:["“])[^"”\r\n]{8,}(?:["”])\s*\[\d+\]', draft)
    if not quotes:
        issues.append("No verbatim quotes matching '\"...\" [n]' format found in draft.")

    causal_patterns = [
        r'\b(?:drives|causes|induces|proves)\b[^.\n]{0,80}\[\d+\]',
        r'\[\d+\][^.\n]{0,80}\b(?:drives|causes|induces|proves)\b',
        r'\b(?:membuktikan|memicu|menyebabkan)\b[^.\n]{0,80}\[\d+\]',
        r'\[\d+\][^.\n]{0,80}\b(?:membuktikan|memicu|menyebabkan)\b'
    ]
    for pat in causal_patterns:
        match = re.search(pat, draft, re.IGNORECASE)
        if match:
            issues.append(f"Heuristic causal verb pattern detected near citation: '{match.group(0).strip()}' - Verify on Verb Ladder.")
            break

    # Check quote fidelity against dossier text if provided
    verified_quotes_count = 0
    if dossier_text:
        dossier_lower = dossier_text.lower()
        for q in quotes:
            clean_q = re.sub(r'\[\d+\]', '', q).strip()
            clean_q = re.sub(r'^["“\'”]+|["“\'”]+$', '', clean_q).strip().lower()
            if clean_q and len(clean_q) > 15 and clean_q in dossier_lower:
                verified_quotes_count += 1

    return {
        "passed": not bool(issues),
        "has_issues": bool(issues),
        "issues": issues,
        "warnings": warnings,
        "in_text_count": len(in_text),
        "ref_count": len(ref_entries),
        "quote_count": len(quotes),
        "verified_quotes_count": verified_quotes_count
    }


def run_writer_surgical_patch(topic: str, draft: str, item_to_fix: SourceAuditItem, model: str = DEFAULT_MODEL, thinking_level: str = "medium", lang: str = "en") -> Optional[str]:
    """Surgically rewrite only the offending paragraph to prevent full draft regression."""
    if not item_to_fix or not item_to_fix.offending_text:
        return None
    offending = item_to_fix.offending_text.strip()
    if len(offending) < 8:
        return None

    paragraphs = draft.split("\n\n")
    target_idx = -1
    for i, p in enumerate(paragraphs):
        if offending in p:
            target_idx = i
            break
    if target_idx == -1:
        first_words = " ".join(offending.split()[:4])
        if len(first_words) > 10:
            for i, p in enumerate(paragraphs):
                if first_words in p:
                    target_idx = i
                    break

    if target_idx == -1 or re.match(r'^##+\s*(?:📚\s*)?(?:Referensi|References)', paragraphs[target_idx], re.IGNORECASE):
        return None

    target_para = paragraphs[target_idx]
    is_id = (lang == "id")
    sys_prompt = (
        "Anda adalah Agen Penulis Ahli dalam mode REVISI BEDAH (SURGICAL PARAGRAPH REPAIR).\n"
        "Tugas Anda HANYA menyusun ulang SATU paragraf ini untuk memperbaiki ketidaksesuaian integritas publikasi.\n"
        "Kembalikan HANYA paragraf pengganti yang telah disempurnakan."
        if is_id else
        "You are an expert Writer Agent in SURGICAL PARAGRAPH REPAIR mode.\n"
        "Your task is ONLY to rewrite this SINGLE paragraph to resolve a publication integrity discrepancy.\n"
        "Return ONLY the replacement revised paragraph."
    )

    prompt = f"""Topic: {topic}
Failing Criterion: {item_to_fix.title} ({item_to_fix.reason})
Offending Passage: "{item_to_fix.offending_text}"

PARAGRAPH TO SURGICALLY REVISE:
\"\"\"
{target_para}
\"\"\"

Rewrite ONLY this paragraph to resolve the discrepancy while keeping all valid facts and citations intact. Return ONLY the replacement paragraph in Markdown.
"""

    try:
        response = call_gemini_with_retry(
            get_client().interactions.create,
            model=model,
            system_instruction=sys_prompt,
            input=prompt,
            generation_config={"thinking_level": thinking_level}
        )
        revised = (response.output_text or "").strip()
        revised = re.sub(r"^```(?:markdown)?\s*", "", revised)
        revised = re.sub(r"\s*```$", "", revised).strip()
        if revised and len(revised) > 20:
            paragraphs[target_idx] = revised
            return "\n\n".join(paragraphs)
    except Exception as e:
        console.print(f"[dim]Surgical patch note: {e}, falling back to full rebuild[/dim]")
    return None


def run_writer_draft(topic: str, instructions: Optional[str] = None, model: str = DEFAULT_MODEL, enable_search: bool = False, thinking_level: str = "medium", scholarly_dossier: str = "", lang: str = "en", difficulty: str = "undergraduate", reading_type: str = "literature_review") -> str:
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
        )

    diff_guide = DIFFICULTY_GUIDELINES.get(difficulty, DIFFICULTY_GUIDELINES["undergraduate"]).get(lang, "undergraduate")
    type_guide = READING_TYPE_GUIDELINES.get(reading_type, READING_TYPE_GUIDELINES["literature_review"]).get(lang, "literature_review")
    system_prompt += f"\n\n{diff_guide}\n\n{type_guide}\n\n{get_verb_ladder_few_shot_prompt(lang)}"

    quotation_rules = (
        "\n\nATURAN SITASI & KUTIPAN KATA-DEMI-KATA (EXACT VERBATIM QUOTATION & CITATION RULES - CRITICAL MANDATORY):\n"
        "1. FORMAT KUTIPAN & NOMOR SITASI:\n"
        "   Setiap kali mengutip bukti, data, temuan kunci, atau definisi dari berkas riset, Anda WAJIB mengapit kutipan dalam tanda petik ganda dan menyertakan nomor kutipan dalam kurung siku di akhir kutipan:\n"
        "   Contoh format: \"... bla bla bla ...\" [1] atau \"... bla bla bla ...\" [2].\n"
        "2. KEASLIAN PERSIS (EXACT MATCH FOR CTRL+F SEARCH):\n"
        "   Teks di dalam tanda petik \"... ...\" HARUS PERSIS SAMA KATA-DEMI-KATA, HURUF-DEMI-HURUF dengan teks asli pada 'Verbatim Excerpt / Abstract' atau teks dokumen yang disediakan di berkas riset.\n"
        "   JANGAN PERNAH memparafrasekan atau mengubah kata di dalam tanda petik. Tujuannya adalah agar pembaca dapat membuka tautan sumber atau dokumen asli, menekan CTRL + F, menempelkan teks kutipan tersebut, dan langsung menemukan kalimatnya dalam konteks penuh.\n"
        "   (Catatan: Jika menulis dalam Bahasa Indonesia dan sumber dalam Bahasa Inggris, biarkan kutipan bukti di dalam tanda petik persis dalam bahasa aslinya, lalu berikan ulasan, konteks, atau terjemahan Anda dalam Bahasa Indonesia sebelum atau sesudah kutipan tersebut).\n"
        "3. PENOMORAN SITASI URUT:\n"
        "   Beri nomor kutipan secara berurutan sesuai kemunculan pertamanya di dalam teks: [1], [2], [3], dst.\n"
        "4. DAFTAR SUMBER RUJUKAN DI AKHIR NASKAH (TAUTAN AKTIF KLIK / CLICKABLE LINKS MANDATORY):\n"
        "   Di bagian paling akhir naskah, Anda WAJIB menyertakan daftar sumber rujukan bernomor yang cocok persis dengan nomor kutipan di teks:\n"
        f"   {'## 📚 Referensi & Sumber Terkutip' if lang == 'id' else '## 📚 References & Cited Sources'}\n"
        "   Format setiap entri WAJIB menyertakan tautan markdown yang dapat langsung diklik oleh pembaca:\n"
        f"   {'   [1] Penulis / Pengarang (Tahun). *Judul Makalah*. Sumber / Venue. [🔗 Buka Makalah](url_lengkap)' if lang == 'id' else '   [1] Authors (Year). *Paper Title*. Venue. [🔗 Open Paper](full_url)'}\n"
        f"   {'   [2] Penulis / Pengarang (Tahun). *Judul Makalah*. Sumber / Venue. [🔗 Buka Makalah](url_lengkap)' if lang == 'id' else '   [2] Authors (Year). *Paper Title*. Venue. [🔗 Open Paper](full_url)'}\n"
        "   Salin URL asli secara lengkap (http://... atau https://...) dari berkas riset ke dalam tanda kurung [🔗 Buka Makalah](url) agar pembaca dapat langsung mengklik tautan tersebut untuk membuka artikel aslinya!\n"
        "   Setiap nomor [n] yang dikutip dalam teks WAJIB ada di daftar akhir ini!"
    )
    system_prompt += quotation_rules

    if enable_search:
        system_prompt += " Use Google Search to look up up-to-date facts, data points, and references."
    if scholarly_dossier:
        system_prompt += (
            " You are provided with a Verified Scholarly Research Dossier. "
            "You MUST ground your explanations in these academic papers, DOIs, and reference materials. "
            "Strictly follow the Verbatim Quotation & Citation Rules above."
        )

    user_prompt = f"Topic/Goal: {topic}\nTarget Audience: {difficulty}\nDocument Genre: {reading_type}\n"
    if scholarly_dossier:
        user_prompt += f"\n{scholarly_dossier}\n"
    if instructions:
        user_prompt += f"Special Instructions: {instructions}\n"
    if lang == "id":
        user_prompt += "Silakan tulis Draf 1 yang mendalam dan komprehensif dalam Bahasa Indonesia berlandaskan topik dan rujukan riset di atas dengan kutipan \"... ...\" [n] persis sama kata-demi-kata dan daftar referensi bernomor di akhir lengkap dengan tautan [🔗 Buka Makalah](url)."
    else:
        user_prompt += "Please write Draft 1 grounded in the topic and research, using exact verbatim quotes \"... ...\" [n] and the numbered references list at the end with clickable links [🔗 Open Paper](url)."

    tools = [{"type": "google_search"}] if enable_search else None
    response = call_gemini_with_retry(
        get_client().interactions.create,
        model=model,
        system_instruction=system_prompt,
        input=user_prompt,
        tools=tools,
        generation_config={"thinking_level": thinking_level}
    )
    return response.output_text or ""


def run_writer_revision(original_topic: str, previous_draft: str, critique: CritiqueResult, turn: int, model: str = DEFAULT_MODEL, enable_search: bool = False, thinking_level: str = "medium", scholarly_dossier: str = "", lang: str = "en", difficulty: str = "undergraduate", reading_type: str = "literature_review") -> str:
    """Writer agent revises the draft incorporating the critic's points."""
    system_prompt = (
        "You are an expert Writer Agent in an iterative feedback loop. "
        "Carefully study the Critic's feedback, weaknesses, and required action items, and address each one thoroughly "
        "while retaining the strengths of your previous draft. Deliver the updated draft in full."
    )
    if lang == "id":
        system_prompt += (
            "\nPANDUAN BAHASA & REVISI:\n"
            "Perbaiki dan sempurnakan draf secara menyeluruh dalam BAHASA INDONESIA. "
            "Tangani setiap kelemahan dan rekomendasi perbaikan dari Pengkritik, serta pertahankan rujukan akademis dan sitasi DOIs."
        )

    diff_guide = DIFFICULTY_GUIDELINES.get(difficulty, DIFFICULTY_GUIDELINES["undergraduate"]).get(lang, "undergraduate")
    type_guide = READING_TYPE_GUIDELINES.get(reading_type, READING_TYPE_GUIDELINES["literature_review"]).get(lang, "literature_review")
    system_prompt += f"\n\n{diff_guide}\n\n{type_guide}\n\n{get_verb_ladder_few_shot_prompt(lang)}"

    quotation_rules = (
        "\n\nATURAN SITASI & KUTIPAN KATA-DEMI-KATA (EXACT VERBATIM QUOTATION & CITATION RULES - CRITICAL MANDATORY):\n"
        "1. KUTIPAN & NOMOR SITASI: Seluruh kutipan bukti harus diapit tanda petik ganda dan nomor sitasi: \"... bla bla bla ...\" [n].\n"
        "2. PERSIS SAMA UNTUK CTRL+F: Teks di dalam tanda petik HARUS persis sama huruf-demi-huruf dengan sumber aslinya di dossier agar bisa dicari dengan CTRL+F di sumber aslinya.\n"
        "3. DAFTAR RUJUKAN DI AKHIR DENGAN TAUTAN KLIK: Pertahankan dan lengkapi daftar bernomor di bagian akhir dengan tautan markdown yang dapat langsung diklik pembaca: [🔗 Buka Makalah](url) yang memetakan setiap [n] ke judul, penulis, tahun, dan tautan/DOI asli."
    )
    system_prompt += quotation_rules

    if enable_search:
        system_prompt += " Use Google Search to look up up-to-date information for the Critic's points."
    if scholarly_dossier:
        system_prompt += " Ensure all academic references, DOIs, and citations from the research dossier are retained, properly cited, and expanded as necessary."

    revisions_formatted = "\n".join(f"- {item}" for item in critique.actionable_revisions)
    prompt = f"""
Original Topic: {original_topic}
Target Audience: {difficulty}
Document Genre: {reading_type}

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
        prompt += f"\nSilakan tulis revisi lengkap (Draf {turn + 1}) dalam Bahasa Indonesia yang menindaklanjuti seluruh evaluasi di atas dengan kutipan \"... ...\" [n] persis sama kata-demi-kata dan daftar referensi bernomor di akhir lengkap dengan tautan [🔗 Buka Makalah](url)."
    else:
        prompt += f"\nPlease write the complete revised version (Draft {turn + 1}) addressing all feedback with exact verbatim quotes \"... ...\" [n] and the numbered references list at the end with clickable links [🔗 Open Paper](url)."

    tools = [{"type": "google_search"}] if enable_search else None
    response = call_gemini_with_retry(
        get_client().interactions.create,
        model=model,
        system_instruction=system_prompt,
        input=prompt,
        tools=tools,
        generation_config={"thinking_level": thinking_level}
    )
    return response.output_text or ""


def run_critic_review(topic: str, draft: str, turn: int, model: str = DEFAULT_MODEL, thinking_level: str = "medium", has_dossier: bool = False, lang: str = "en", difficulty: str = "undergraduate", reading_type: str = "literature_review", target_score: float = 8.5) -> CritiqueResult:
    """Critic agent rigorously reviews the draft and returns structured feedback."""
    system_prompt = (
        "You are a meticulous, discerning Senior Editor and Critic Agent. "
        "Evaluate drafts strictly on clarity, depth, coherence, factual grounding, tone, and engagement. "
        f"Be constructive but hold a high bar. Scores of {target_score:.1f} and above qualify for 'APPROVED'. "
    )
    if lang == "id":
        system_prompt += (
            "\nPANDUAN BAHASA:\n"
            "Berikan seluruh evaluasi, analisis kekuatan, kelemahan, dan tindakan revisi dalam BAHASA INDONESIA yang objektif dan konstruktif.\n"
        )

    system_prompt += (
        f"\nAUDIT TARGET AUDIENS & GENRE DOKUMEN:\n"
        f"1. Target Audiens ({difficulty}): Periksa kesesuaian gaya bahasa, densitas teknis, dan istilah untuk target pembaca ini.\n"
        f"2. Genre Dokumen ({reading_type}): Periksa apakah struktur dan alur penyampaian mencerminkan format dokumen yang ditargetkan.\n"
        "Jika draf tidak sesuai dengan target audiens atau genre yang diminta, tandai sebagai KELEMAHAN (Weakness) dan berikan saran perbaikan.\n"
    )

    system_prompt += (
        "\nAUDIT KUTIPAN KATA-DEMI-KATA & REFERENSI (VERBATIM QUOTATION & CITATION AUDIT):\n"
        "1. Format Kutipan: Periksa apakah setiap kutipan fakta/bukti diapit tanda petik \"... bla bla bla ...\" dan diikuti nomor sitasi dalam kurung siku seperti [1], [2].\n"
        "2. Verifikasi CTRL+F: Periksa apakah kutipan di dalam \"... ...\" persis sama kata-demi-kata dengan teks sumber/abstrak di berkas riset sehingga pembaca dapat mencarinya dengan CTRL+F di sumber aslinya. Jika ada kutipan yang diparafrasekan di dalam tanda petik, tandai sebagai KELEMAHAN (Weakness).\n"
        "3. Daftar Referensi Akhir & Tautan Klik: Periksa apakah di akhir naskah terdapat daftar rujukan bernomor ([1], [2], ...) yang memetakan nomor kutipan ke judul makalah, penulis, tahun, dan TAUTAN KLIK YANG VALID [🔗 Buka Makalah](url). Jika rujukan tidak memiliki tautan klik yang valid, tandai sebagai KELEMAHAN.\n"
        "Jika aturan kutipan dan referensi ini belum terpenuhi dengan sempurna, status WAJIB 'NEEDS_REVISION'.\n"
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
Target Audience: {difficulty}
Document Genre: {reading_type}
Approval Target Score Threshold: {target_score:.1f}/10
Grounding Dossier Present: {'Yes' if has_dossier else 'No'}

Draft to Review:
\"\"\"
{draft}
\"\"\"

Analyze the draft thoroughly and output your evaluation as a valid JSON object only.
"""

    response = call_gemini_with_retry(
        get_client().interactions.create,
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
    
    try:
        data = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            data = json.loads(match.group(0))
        else:
            raise
    return CritiqueResult(**data)


def run_source_audit(topic: str, draft: str, dossier_text: str = "", model: str = DEFAULT_MODEL, thinking_level: str = "medium", lang: str = "en") -> SourceAuditResult:
    """Publication Integrity Auditor Agent based strictly on .agents/rules/source-checking-guide.md."""
    is_id = (lang == "id")
    system_prompt = (
        "You are the Publication Integrity Auditor Agent operating under the strict, uncompromising rules of '.agents/rules/source-checking-guide.md'. "
        "Your mission is to enforce 100% publication and understanding integrity across 3 layers and 11 binary criteria.\n\n"
        "CRITICAL FAILURE PATTERNS TO ELIMINATE:\n"
        "1. Adjacent-construct substitution: The source studies something related, but text treats it as the target construct.\n"
        "2. Correlation-to-causation drift: Correlational/observational data described with causal verbs ('causes', 'drives', 'reduces') instead of associative verbs ('is associated with', 'relates to').\n"
        "3. Framing-as-finding: An introduction's assumption or hypothesis cited as an empirical finding.\n"
        "4. Scope inflation: A finding on a specific sample inflated into statements about 'all humans' or 'modern societies'.\n"
        "5. Orphaned quotation: A quotation is accurate, but the sentence or claim it sits under is not supported by the paper.\n"
        "6. Citation laundering: Weak, secondary sources placed among strong peer-reviewed sources borrowing credibility.\n"
        "7. Mismatched or fabricated metadata: Authors, journal, year, or DOIs that do not match the real papers.\n\n"
        "THE VERB LADDER RULES (Strictly enforce design vs verb match):\n"
        "- Cross-sectional survey: ONLY 'is associated with', 'relates to'. NEVER 'causes', 'drives', 'reduces'.\n"
        "- Longitudinal / cohort trend: 'precedes', 'coincides with', 'predicts'. NOT 'produces' without ruling out confounds.\n"
        "- Statistical mediation on correlational data: 'is consistent with a pathway through'. NOT 'works through', 'directly mitigates'.\n"
        "- Randomized experiment: 'causes', 'increases', 'reduces' (in that setting, bounded generalization).\n"
        "- Meta-analysis: Average pooled associations or effects. NOT mechanism unless tested.\n"
        "- Theory / conceptual paper: 'proposes', 'argues', 'hypothesizes'. NOT 'shows', 'demonstrates'.\n\n"
        "THE 11 MANDATORY BINARY QUESTIONS (Each MUST be answered 'YES' or 'NO'):\n"
        "Layer 1: What Is This Source?\n"
        "1. layer1_source_type_appropriate: Does the source type (study, meta-analysis, review, theory, preprint) justify the claim level?\n"
        "2. layer1_metadata_matches: Do authors, journal/venue, year, and DOI/URL match actual papers?\n"
        "3. layer1_independent_sources: Are sources genuinely independent rather than citing or resting on the same underlying work?\n\n"
        "Layer 2: Does the Source Support This Specific Claim?\n"
        "4. layer2_exact_construct_match: Does each citation measure or discuss the exact target construct claimed, without adjacent-construct substitution?\n"
        "5. layer2_finding_not_framing: Is the cited passage the paper's empirical finding/result, and NOT an introductory background assumption or motivating hypothesis?\n"
        "6. layer2_verb_ladder_justified: Does the study design strictly justify the verb used under the Verb Ladder?\n"
        "7. layer2_sample_scope_accurate: Is the claim strictly bounded by who or what was studied, with zero scope inflation?\n"
        "8. layer2_context_and_quote_integrity: Does the source say the same thing in context, and are all quotations doing real evidentiary work rather than ornamental or orphaned?\n\n"
        "Layer 3: Does the Whole Argument Hold?\n"
        "9. layer3_no_uncited_author_leaps: Are all steps in the argument evidence-based, with zero author-supplied inferential leaps disguised as cited facts?\n"
        "10. layer3_rival_explanations_acknowledged: Are alternative mechanisms, caveats, and rival explanations acknowledged rather than asserted as exclusive?\n"
        "11. layer3_bounded_conclusion: Does the conclusion refrain from claiming more than the single best-supported premise or source?\n\n"
        "You MUST respond ONLY with valid JSON conforming to this schema:\n"
        "{\n"
        '  "all_yes": boolean,\n'
        '  "overall_verdict": "APPROVED_INTEGRITY_CLEARANCE" | "DISCREPANCIES_DETECTED",\n'
        '  "score_percentage": float,\n'
        '  "failure_patterns_detected": ["string", ...],\n'
        '  "discrepancies": ["string", ...],\n'
        '  "items": [\n'
        '    {"id": "layer1_source_type_appropriate", "layer": 1, "title": "Source Type Ceiling", "question": "Does source type justify claim level?", "answer": "YES" | "NO", "reason": "...", "offending_text": "..."},\n'
        "    ...\n"
        "  ]\n"
        "}"
    )

    sanity = run_deterministic_checks(draft, dossier_text)
    prompt = f"Goal / Topic: {topic}\n\nDraft to Audit:\n\"\"\"\n{draft}\n\"\"\"\n"
    if sanity["has_issues"]:
        prompt += "\nDETERMINISTIC CODE PRE-AUDIT SIGNALS:\n" + "\n".join(f"! {i}" for i in sanity["issues"]) + "\n"
    if dossier_text:
        prompt += f"\nGrounding Dossier Reference:\n{dossier_text}\n"
    prompt += "\nPerform the rigorous 11-question 3-layer audit and output valid JSON ONLY."

    response = call_gemini_with_retry(
        get_client().interactions.create,
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

    try:
        data = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                data = json.loads(match.group(0))
            except (json.JSONDecodeError, ValueError):
                data = {"all_yes": False, "overall_verdict": "DISCREPANCIES_DETECTED", "score_percentage": 0.0, "failure_patterns_detected": [], "discrepancies": ["JSON parsing failed"], "items": []}
        else:
            data = {"all_yes": False, "overall_verdict": "DISCREPANCIES_DETECTED", "score_percentage": 0.0, "failure_patterns_detected": [], "discrepancies": ["JSON parsing failed"], "items": []}

    default_defs = [
        {"id": "layer1_source_type_appropriate", "layer": 1, "title": "Plafon Tipe Sumber" if is_id else "Source Type Ceiling", "question": "Apakah tipe sumber membenarkan klaim?" if is_id else "Does source type justify claim level?", "reason": "Tipe sumber membenarkan tingkat klaim ilmiah." if is_id else "Source types justify claim levels."},
        {"id": "layer1_metadata_matches", "layer": 1, "title": "Verifikasi Metadata" if is_id else "Metadata Verification", "question": "Apakah penulis, jurnal, tahun, dan DOI cocok?" if is_id else "Do authors, journal, year, and DOI match actual publications?", "reason": "Metadata publikasi valid dan cocok." if is_id else "Metadata matches published papers."},
        {"id": "layer1_independent_sources", "layer": 1, "title": "Independensi Sumber" if is_id else "Source Independence", "question": "Apakah sumber-sumber independen satu sama lain?" if is_id else "Are sources genuinely independent?", "reason": "Sumber-sumber berdiri secara independen." if is_id else "Independent lines of evidence cited."},
        {"id": "layer2_exact_construct_match", "layer": 2, "title": "Kesesuaian Konstruk Persis" if is_id else "Exact Construct Match", "question": "Apakah studi mengukur konstruk yang diklaim persis?" if is_id else "Does study measure exact claimed construct?", "reason": "Konstruk yang dibahas persis dengan yang diuji." if is_id else "Exact construct match maintained without substitution."},
        {"id": "layer2_finding_not_framing", "layer": 2, "title": "Temuan vs. Framing" if is_id else "Finding vs. Framing", "question": "Apakah kutipan merupakan temuan empiris, bukan asumsi pengantar?" if is_id else "Is cited passage empirical finding, not introductory framing?", "reason": "Kutipan merefleksikan temuan empiris hasil studi." if is_id else "Evidentiary claims rest on empirical findings."},
        {"id": "layer2_verb_ladder_justified", "layer": 2, "title": "Tangga Kata Kerja (Verb Ladder)" if is_id else "Verb Ladder Compliance", "question": "Apakah desain riset membenarkan kata kerja klaim?" if is_id else "Does research design justify verb used?", "reason": "Kekuatan kata kerja selaras dengan desain riset." if is_id else "Verbs strictly calibrated to research design."},
        {"id": "layer2_sample_scope_accurate", "layer": 2, "title": "Batasan Sampel & Cakupan" if is_id else "Sample & Scope Bounds", "question": "Apakah cakupan terikat pada sampel yang diteliti?" if is_id else "Is scope strictly bounded to studied sample?", "reason": "Cakupan klaim terikat pada sampel studi." if is_id else "Claims accurately bounded to studied populations."},
        {"id": "layer2_context_and_quote_integrity", "layer": 2, "title": "Integritas Konteks & Kutipan" if is_id else "Quote & Context Integrity", "question": "Apakah kutipan sesuai konteks dan bermakna pembuktian?" if is_id else "Does quote match context and do evidentiary work?", "reason": "Kutipan berfungsi membuktikan klaim dalam konteks aslinya." if is_id else "Quotes do evidentiary work and preserve context."},
        {"id": "layer3_no_uncited_author_leaps", "layer": 3, "title": "Tanpa Lompatan Tanpa Sitasi" if is_id else "No Uncited Author Leaps", "question": "Apakah seluruh mata rantai argumen berbasis bukti?" if is_id else "Are all argument steps evidence-based?", "reason": "Tidak ada inferensi tanpa bukti yang disamarkan sebagai fakta." if is_id else "All inferential steps are grounded in evidence."},
        {"id": "layer3_rival_explanations_acknowledged", "layer": 3, "title": "Eksplanasi Saingan & Sanggahan" if is_id else "Rival Explanations & Caveats", "question": "Apakah penjelasan alternatif & keterbatasan diakui?" if is_id else "Are alternative mechanisms and caveats acknowledged?", "reason": "Mekanisme alternatif dan batasan riset diakui." if is_id else "Alternative hypotheses and caveats acknowledged."},
        {"id": "layer3_bounded_conclusion", "layer": 3, "title": "Kesimpulan Terikat Batas" if is_id else "Bounded Conclusion", "question": "Apakah kesimpulan tidak melebihi premis terkuatnya?" if is_id else "Does conclusion refrain from exceeding strongest premise?", "reason": "Kesimpulan akhir seimbang dan tidak berlebihan." if is_id else "Conclusion stays within empirical boundaries."}
    ]

    items_list = []
    for def_item in default_defs:
        found = next((it for it in data.get("items", []) if it.get("id") == def_item["id"]), None)
        if found:
            ans = str(found.get("answer", "YES")).strip().upper()
            answer_norm = "YES" if (ans == "YES" or ans == "YA") else "NO"
            items_list.append(SourceAuditItem(
                id=def_item["id"],
                layer=def_item["layer"],
                title=found.get("title", def_item["title"]),
                question=found.get("question", def_item["question"]),
                answer=answer_norm,
                reason=found.get("reason", def_item["reason"]),
                offending_text=found.get("offending_text", "")
            ))
        else:
            items_list.append(SourceAuditItem(
                id=def_item["id"],
                layer=def_item["layer"],
                title=def_item["title"],
                question=def_item["question"],
                answer="YES",
                reason=def_item["reason"],
                offending_text=""
            ))

    all_yes = all(it.answer == "YES" for it in items_list)
    yes_count = sum(1 for it in items_list if it.answer == "YES")
    score_pct = round((yes_count / len(items_list)) * 100.0, 1)

    return SourceAuditResult(
        all_yes=all_yes,
        overall_verdict="APPROVED_INTEGRITY_CLEARANCE" if all_yes else "DISCREPANCIES_DETECTED",
        score_percentage=score_pct,
        failure_patterns_detected=data.get("failure_patterns_detected", []),
        discrepancies=data.get("discrepancies", []),
        items=items_list
    )


def run_audit_revision(topic: str, draft: str, audit: SourceAuditResult, round_num: int, dossier_text: str = "", model: str = DEFAULT_MODEL, thinking_level: str = "medium", lang: str = "en", difficulty: str = "undergraduate", reading_type: str = "literature_review") -> str:
    """Writer Agent rebuilds the draft until all 11 source-checking-guide.md criteria achieve YES."""
    # 1. Attempt surgical paragraph rebuild if there is an isolated discrepancy to prevent regression
    no_items_with_text = [it for it in audit.items if it.answer == "NO" and it.offending_text and len(it.offending_text.strip()) > 6]
    if len(no_items_with_text) == 1:
        patched = run_writer_surgical_patch(topic, draft, no_items_with_text[0], model=model, thinking_level=thinking_level, lang=lang)
        if patched:
            console.print("[green]✓ Applied fast surgical paragraph patch for publication integrity rebuild![/green]")
            return patched

    system_prompt = (
        "You are an expert Writer Agent tasked with an UNCOMPROMISING PUBLICATION INTEGRITY REBUILD under '.agents/rules/source-checking-guide.md'.\n"
        "Your mission: Completely resolve every 'NO' evaluation from the Publication Integrity Auditor Agent, rewriting and refining the draft until ALL 11 questions achieve 'YES'.\n\n"
        "CRITICAL RULES TO ACHIEVE 100% 'YES':\n"
        "1. VERB LADDER COMPLIANCE: Downgrade causal verbs ('causes', 'drives', 'reduces') to associative verbs ('is associated with', 'relates to', 'correlates with') for cross-sectional data.\n"
        "2. ELIMINATE SCOPE INFLATION: Bound claims to studied samples (e.g. 'among undergraduate cohorts', 'in adult clinical trials'); do not claim 'all humans' or 'modern societies'.\n"
        "3. ELIMINATE FRAMING-AS-FINDING: Mark theoretical background or hypotheses as 'hypothesized by', NOT 'proven' or 'demonstrated'.\n"
        "4. ELIMINATE ADJACENT-CONSTRUCT SUBSTITUTION: Ensure the target construct matches the measured construct exactly.\n"
        "5. REMOVE UNCITED AUTHOR LEAPS: Provide scholarly grounding for every link or label inferences as theoretical discussion.\n"
        "6. ACKNOWLEDGE RIVAL EXPLANATIONS: Add caveats and alternative mechanisms.\n"
        "7. BOUNDED CONCLUSIONS: Ensure the conclusion does not exceed the strongest premise.\n"
        "8. PRESERVE VERBATIM QUOTES & REFERENCES: Keep exact quotes \"... ...\" [n] and numbered reference list with clickable links [🔗 Open Paper / Buka Makalah](url)."
    )
    if lang == "id":
        system_prompt += "\n\nPANDUAN BAHASA:\nSempurnakan dan susun ulang seluruh naskah dalam BAHASA INDONESIA yang ilmiah, presisi, dan sesuai aturan integritas di atas.\n"

    diff_guide = DIFFICULTY_GUIDELINES.get(difficulty, DIFFICULTY_GUIDELINES["undergraduate"]).get(lang, "undergraduate")
    type_guide = READING_TYPE_GUIDELINES.get(reading_type, READING_TYPE_GUIDELINES["literature_review"]).get(lang, "literature_review")
    system_prompt += f"\n\n{diff_guide}\n\n{type_guide}\n\n{get_verb_ladder_few_shot_prompt(lang)}"

    no_items = [it for it in audit.items if it.answer == "NO"]
    no_desc = "\n".join(f"- [Layer {it.layer} - {it.title}]: {it.reason}" + (f' (Offending passage: "{it.offending_text}")' if it.offending_text else "") for it in no_items)
    discrepancies_desc = "\n".join(f"- {d}" for d in audit.discrepancies)
    failures_desc = "\n".join(f"- {f}" for f in audit.failure_patterns_detected)

    prompt = f"""Original Goal / Topic: {topic}
Integrity Audit Round: {round_num}

DISCREPANCIES DETECTED BY AUDITOR AGENT (Must be resolved to achieve YES):
{discrepancies_desc or no_desc}

DETECTED FAILURE PATTERNS:
{failures_desc or "None"}

SPECIFIC FAILING CRITERIA:
{no_desc}

PREVIOUS DRAFT TO REBUILD:
\"\"\"
{draft}
\"\"\"
"""
    if dossier_text:
        prompt += f"\nResearch Dossier Reference:\n{dossier_text}\n"

    if lang == "id":
        prompt += "\nSilakan tulis ulang dan susun naskah lengkap (Full Rebuilt Draft) dalam Bahasa Indonesia. Perbaiki seluruh kelemahan di atas agar seluruh 11 kriteria terjawab 'YA' pada audit berikutnya, tetap pertahankan kutipan \"... ...\" [n] dan daftar referensi bernomor di akhir lengkap dengan tautan [🔗 Buka Makalah](url)."
    else:
        prompt += "\nPlease rebuild the complete draft in full Markdown. Resolve every single discrepancy above so that all 11 criteria achieve 'YES' on the next audit round. Maintain exact quotes \"... ...\" [n] and the clickable references list at the end [🔗 Open Paper](url)."

    response = call_gemini_with_retry(
        get_client().interactions.create,
        model=model,
        system_instruction=system_prompt,
        input=prompt,
        generation_config={"thinking_level": thinking_level}
    )
    return response.output_text or ""


def enrich_references_with_links(draft_text: str, citations: List[Dict[str, Any]], lang: str = "en") -> str:
    """Ensure all entries in ## 📚 References & Cited Sources provide clean, clickable markdown links."""
    if not draft_text:
        return ""

    ref_match = re.search(r'(##+\s*(?:📚\s*)?(?:Referensi|References|Sumber Terkutip|Cited Sources)[^\n]*\n)([\s\S]*?)(?=\n##|\Z)', draft_text, flags=re.IGNORECASE)
    if not ref_match:
        return draft_text

    header = ref_match.group(1)
    ref_body = ref_match.group(2)
    lines = ref_body.splitlines()
    new_lines = []

    link_label = "🔗 Buka Makalah / Sumber" if lang == "id" else "🔗 Open Paper / Source"

    for line in lines:
        stripped = line.strip()
        entry_match = re.match(r'^(?:[-*]\s*)?(\[(\d+)\]|\b(\d+)\.)\s+(.*)$', stripped)
        if entry_match:
            num = int(entry_match.group(2) or entry_match.group(3))
            content = entry_match.group(4)
            has_markdown_link = bool(re.search(r'\[[^\]]+\]\((https?://[^\s)]+)\)', content))
            raw_url_match = re.search(r'(https?://[^\s<)]+)', content)

            if not has_markdown_link and raw_url_match:
                raw_url = raw_url_match.group(1)
                line = line.replace(raw_url, f"[{link_label}]({raw_url})")
            elif not has_markdown_link and not raw_url_match and citations:
                matching = next((c for c in citations if c.get("num") == num), None)
                if not matching and 0 <= num - 1 < len(citations):
                    matching = citations[num - 1]
                if matching and matching.get("url") and matching["url"] != "#":
                    line = f"{line.rstrip()} [{link_label}]({matching['url']})"
        new_lines.append(line)

    return draft_text[:ref_match.start()] + header + "\n".join(new_lines) + draft_text[ref_match.end():]


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
    use_google_scholar: bool = False,
    use_ieee: bool = False,
    use_ssrn: bool = False,
    use_core: bool = False,
    use_doaj: bool = False,
    use_springer: bool = False,
    use_patents: bool = False,
    doc_path: Optional[str] = None,
    lang: str = "en",
    difficulty: str = "undergraduate",
    reading_type: str = "literature_review",
    enforce_source_guide: bool = True
) -> dict:
    """Coordinates the interaction loop between Writer and Critic."""
    search_label = " (🌐 Web Search Enabled)" if web_search else ""
    lang_label = " [🇮🇩 Bahasa Indonesia]" if lang == "id" else " [🇬🇧 English]"
    console.print(Panel(
        f"[bold cyan]Two-Agent Pipeline Initialized{lang_label}[/bold cyan]\n"
        f"[white]Topic:[/white] {topic}\n"
        f"[white]Model:[/white] {model} | [white]🎯 Target Audience:[/white] {difficulty} | [white]📚 Genre:[/white] {reading_type} | [white]🧠 Thinking:[/white] {thinking_level}{search_label}",
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
        use_google_scholar=use_google_scholar,
        use_ieee=use_ieee,
        use_ssrn=use_ssrn,
        use_core=use_core,
        use_doaj=use_doaj,
        use_springer=use_springer,
        use_patents=use_patents,
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
        console.print(f"[bold green]>>> Writer Agent is thinking & composing ({difficulty} • {reading_type})...[/bold green]")
        if turn == 1:
            current_draft = run_writer_draft(topic, model=model, enable_search=web_search, thinking_level=thinking_level, scholarly_dossier=dossier_text, lang=lang, difficulty=difficulty, reading_type=reading_type)
        else:
            assert latest_critique is not None
            current_draft = run_writer_revision(topic, current_draft, latest_critique, turn - 1, model=model, enable_search=web_search, thinking_level=thinking_level, scholarly_dossier=dossier_text, lang=lang, difficulty=difficulty, reading_type=reading_type)

        current_draft = enrich_references_with_links(current_draft, citations, lang=lang)

        console.print(Panel(Markdown(current_draft), title=f"[bold green]Writer Agent - Draft {turn}[/bold green]", border_style="green"))

        # 2. Critic Turn
        console.print("[bold magenta]>>> Critic Agent is evaluating draft...[/bold magenta]")
        latest_critique = run_critic_review(topic, current_draft, turn, model=model, thinking_level=thinking_level, has_dossier=bool(citations), lang=lang, difficulty=difficulty, reading_type=reading_type, target_score=target_score)

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

    # Step 3: Publication Integrity Audit & Self-Correction Refinement Loop (source-checking-guide.md)
    latest_audit: Optional[SourceAuditResult] = None
    if enforce_source_guide:
        console.rule("[bold cyan]🛡️ 3-Layer Publication Integrity Audit (source-checking-guide.md)[/bold cyan]")
        audit_turn = 1
        max_audit_turns = 3
        while audit_turn <= max_audit_turns:
            console.print(f"[cyan]>>> Running Publication Integrity Audit (Round {audit_turn}/{max_audit_turns})...[/cyan]")
            latest_audit = run_source_audit(
                topic=topic,
                draft=current_draft,
                dossier_text=dossier_text,
                model=model,
                thinking_level=thinking_level,
                lang=lang
            )

            # Display Rich Audit Table
            audit_table = Table(title=f"🛡️ Publication Integrity Audit Log (Round {audit_turn})", show_header=True, header_style="bold cyan")
            audit_table.add_column("Layer", style="dim", width=8)
            audit_table.add_column("Criterion", width=28)
            audit_table.add_column("Status", width=12)
            audit_table.add_column("Diagnostic Evidence", style="dim")

            for it in latest_audit.items:
                status_str = "[bold green]✓ YES[/bold green]" if it.answer == "YES" else "[bold red]⚠ NO[/bold red]"
                audit_table.add_row(f"Layer {it.layer}", it.title, status_str, it.reason)
            console.print(audit_table)

            if latest_audit.all_yes:
                console.print(Panel("[bold green]🛡️ 100% Publication & Understanding Integrity Clearance — All 11 Criteria Answered YES![/bold green]", border_style="bright_green"))
                break
            else:
                if audit_turn < max_audit_turns:
                    failing_count = len([it for it in latest_audit.items if it.answer == "NO"])
                    console.print(f"[bold yellow]⚠ Integrity Discrepancies Detected ({failing_count} criteria answered NO). Rebuilding text with Writer Agent (Audit Round {audit_turn + 1})...[/bold yellow]")
                    current_draft = run_audit_revision(
                        topic=topic,
                        draft=current_draft,
                        audit=latest_audit,
                        round_num=audit_turn,
                        dossier_text=dossier_text,
                        model=model,
                        thinking_level=thinking_level,
                        lang=lang,
                        difficulty=difficulty,
                        reading_type=reading_type
                    )
                    current_draft = enrich_references_with_links(current_draft, citations, lang=lang)
                    audit_turn += 1
                else:
                    console.print(f"[bold yellow]Reached maximum audit limit ({max_audit_turns} rounds).[/bold yellow]")
                    break

    # Save to output file
    os.makedirs("output", exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic.strip().lower())[:40].strip("_")
    filename = os.path.join("output", f"{slug}.md")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Final Draft: {topic}\n\n")
        f.write(f"**Language:** `{lang.upper()}`\n")
        f.write(f"**Model:** `{model}`\n")
        f.write(f"**Target Difficulty / Audience:** `{difficulty}`\n")
        f.write(f"**Document Type / Genre:** `{reading_type}`\n")
        f.write(f"**Thinking Mode:** `{thinking_level}`\n")
        f.write(f"**Web Search:** `{'Enabled' if web_search else 'Disabled'}`\n")
        if citations:
            f.write(f"**Academic Grounding Sources:** `{len(citations)} source(s) active`\n")
        if latest_audit:
            f.write(f"**Publication Integrity Clearance:** `{'100% Verified (11/11 YES)' if latest_audit.all_yes else f'{latest_audit.score_percentage}% YES'}`\n")
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
        if latest_audit:
            f.write("\n---\n## 🛡️ Publication Integrity Audit Report (source-checking-guide.md)\n\n")
            f.write(f"**Overall Verdict:** `{latest_audit.overall_verdict}`  \n")
            f.write(f"**Clearance Score:** `{latest_audit.score_percentage}%`  \n\n")
            f.write("| Layer | Criterion | Status | Diagnostic Evidence |\n")
            f.write("|---|---|---|---|\n")
            for it in latest_audit.items:
                f.write(f"| Layer {it.layer} | {it.title} | `{it.answer}` | {it.reason} |\n")
            f.write("\n")

    console.print(Panel(f"[bold cyan]Artifact saved successfully:[/bold cyan] {filename}", border_style="cyan"))
    return {
        "final_draft": current_draft,
        "score": latest_critique.score,
        "history": history,
        "audit": latest_audit.model_dump() if latest_audit else None,
        "saved_path": filename
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Two-Agent Writer & Critic pipeline with Academic Grounding and Publication Integrity Audit")
    parser.add_argument("--topic", type=str, default="Speech perception", help="Prompt or topic for content")
    parser.add_argument("--lang", choices=["en", "id"], default="en", help="Language mode: en (English) or id (Bahasa Indonesia)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, choices=["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-pro-preview", "gemini-flash-latest"], help="Gemini model to use")
    parser.add_argument("--difficulty", choices=["layman", "undergraduate", "expert", "executive"], default="undergraduate", help="Reading difficulty / target audience")
    parser.add_argument("--reading-type", choices=["literature_review", "deep_dive_essay", "textbook_chapter", "technical_whitepaper", "executive_brief"], default="literature_review", help="Document type / reading genre")
    parser.add_argument("--thinking-level", type=str, default="medium", choices=["low", "medium", "high"], help="Thinking depth: low, medium, or high")
    parser.add_argument("--web-search", action="store_true", help="Enable Google Search grounding for research")
    parser.add_argument("--arxiv", action="store_true", help="Ground in arXiv preprints")
    parser.add_argument("--crossref", action="store_true", help="Ground in Crossref 150M+ DOI index")
    parser.add_argument("--semantic-scholar", action="store_true", help="Ground in Semantic Scholar high-impact works")
    parser.add_argument("--openalex", action="store_true", help="Ground in OpenAlex global catalog works")
    parser.add_argument("--pubmed", action="store_true", help="Ground in NCBI PubMed Central articles")
    parser.add_argument("--wikipedia", action="store_true", help="Ground in Wikipedia encyclopedic summary")
    parser.add_argument("--google-scholar", action="store_true", help="Ground in universal academic literature (Google Scholar)")
    parser.add_argument("--ieee", action="store_true", help="Ground in IEEE Xplore electrical engineering, robotics & CS publications")
    parser.add_argument("--ssrn", action="store_true", help="Ground in SSRN economics, finance, law & social science working papers")
    parser.add_argument("--core", action="store_true", help="Ground in CORE open-access university repositories")
    parser.add_argument("--doaj", action="store_true", help="Ground in DOAJ peer-reviewed open access journals")
    parser.add_argument("--springer", action="store_true", help="Ground in SpringerLink peer-reviewed journals & book chapters")
    parser.add_argument("--patents", action="store_true", help="Ground in Google Patents international patent filings & engineering specs")
    parser.add_argument("--doc", type=str, default=None, help="Path to local PDF or text document to ground in")
    parser.add_argument("--max-turns", type=int, default=2, help="Maximum number of refinement iterations")
    parser.add_argument("--target-score", type=float, default=8.5, help="Score threshold for approval (1-10)")
    parser.add_argument("--enforce-source-guide", action="store_true", default=True, help="Enforce 3-layer publication integrity check from source-checking-guide.md")
    parser.add_argument("--no-enforce-source-guide", dest="enforce_source_guide", action="store_false", help="Disable publication integrity audit")

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
        use_google_scholar=args.google_scholar,
        use_ieee=args.ieee,
        use_ssrn=args.ssrn,
        use_core=args.core,
        use_doaj=args.doaj,
        use_springer=args.springer,
        use_patents=args.patents,
        doc_path=args.doc,
        lang=args.lang,
        difficulty=args.difficulty,
        reading_type=args.reading_type,
        enforce_source_guide=args.enforce_source_guide
    )
