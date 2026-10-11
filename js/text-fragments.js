/**
 * Gemini Agentic Studio - W3C Scroll-to-Text Fragments & Abstract Reconstructors
 */

import { escapeHtml } from "./security.js";

/**
 * Spec-compliant percent-encoder for W3C Scroll-to-Text Fragment directives.
 * Encodes characters including '-', ',', '&' which serve as syntax delimiters in fragment directives.
 */
export function encodeFragmentToken(token) {
  if (!token) return "";
  return encodeURIComponent(token)
    .replace(/-/g, "%2D")
    .replace(/,/g, "%2C")
    .replace(/&/g, "%26");
}

/**
 * Build W3C Scroll-to-Text Fragment URL with strict syntax and https enforcement.
 */
export function buildTextFragmentUrl(rawUrl, quoteText) {
  if (!rawUrl || rawUrl === "#" || rawUrl.startsWith("#ref-")) return rawUrl;
  if (!quoteText || typeof quoteText !== "string") return rawUrl;

  // Clean base url and enforce https to prevent 301/302 redirects dropping fragments
  let baseUrl = rawUrl.split("#")[0].trim().replace(/^http:\/\//i, "https://");

  // Clean up quote text: strip surrounding quotes, citation brackets, and extra spaces
  let clean = quoteText
    .replace(/^["“'”]+|["“'”]+$/g, "")
    .replace(/\[\d+\]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  if (!clean || clean.length < 5) return baseUrl;

  // Extract alphanumeric token words, stripping edge punctuation
  const rawWords = clean.split(/\s+/).filter(Boolean);
  const cleanWords = rawWords
    .map(w => w.replace(/^[^\w\u00C0-\u024F]+|[^\w\u00C0-\u024F]+$/g, "").trim())
    .filter(w => w.length > 0);

  if (cleanWords.length === 0) return baseUrl;

  let textParam = "";
  if (cleanWords.length <= 6) {
    // Short quotes: exact phrase
    textParam = encodeFragmentToken(cleanWords.join(" "));
  } else {
    // Longer quotes: 3 start words, 3 end words range syntax
    const startWords = cleanWords.slice(0, 3).join(" ");
    const endWords = cleanWords.slice(-3).join(" ");
    textParam = `${encodeFragmentToken(startWords)},${encodeFragmentToken(endWords)}`;
  }

  return `${baseUrl}#:~:text=${textParam}`;
}

/**
 * Highlight verbatim quote inside source abstract with <mark> tag safely.
 */
export function highlightQuoteInAbstract(abstractText, quoteText) {
  if (!abstractText) return { html: "", found: false };
  if (!quoteText) return { html: escapeHtml(abstractText), found: false };

  const cleanQuote = quoteText
    .replace(/^["“'”]+|["“'”]+$/g, "")
    .replace(/\[\d+\]/g, "")
    .trim();
  if (!cleanQuote || cleanQuote.length < 5) {
    return { html: escapeHtml(abstractText), found: false };
  }

  // 1. Direct case-insensitive substring search
  const lowerAbs = abstractText.toLowerCase();
  const lowerQuote = cleanQuote.toLowerCase();
  const exactIdx = lowerAbs.indexOf(lowerQuote);
  if (exactIdx !== -1) {
    const before = escapeHtml(abstractText.substring(0, exactIdx));
    const matched = escapeHtml(abstractText.substring(exactIdx, exactIdx + cleanQuote.length));
    const after = escapeHtml(abstractText.substring(exactIdx + cleanQuote.length));
    return {
      html: `${before}<mark class="bg-amber-400 text-slate-950 font-bold px-1 rounded shadow-sm">${matched}</mark>${after}`,
      found: true
    };
  }

  // 2. Token-boundary regex search (ignores minor punctuation / whitespace differences)
  const qWords = cleanQuote.split(/\s+/).filter(w => w.length > 2);
  if (qWords.length >= 3) {
    const startRegex = qWords.slice(0, 3).map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join("\\s+");
    const endRegex = qWords.slice(-3).map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join("\\s+");
    try {
      const rx = new RegExp(`(${startRegex}[\\s\\S]*?${endRegex})`, "i");
      const m = abstractText.match(rx);
      if (m && m.index !== undefined) {
        const before = escapeHtml(abstractText.substring(0, m.index));
        const matched = escapeHtml(m[0]);
        const after = escapeHtml(abstractText.substring(m.index + m[0].length));
        return {
          html: `${before}<mark class="bg-amber-400 text-slate-950 font-bold px-1 rounded shadow-sm">${matched}</mark>${after}`,
          found: true
        };
      }
    } catch (e) {}
  }

  return { html: escapeHtml(abstractText), found: false };
}

/**
 * Reconstruct verbatim abstract text from OpenAlex inverted index.
 */
export function reconstructAbstract(invertedIndex) {
  if (!invertedIndex || typeof invertedIndex !== "object") return "";
  const words = [];
  for (const [word, positions] of Object.entries(invertedIndex)) {
    if (Array.isArray(positions)) {
      for (const pos of positions) {
        words[pos] = word;
      }
    }
  }
  return words.join(" ").replace(/\s+/g, " ").trim();
}

/**
 * Deterministic Sanity Checks (Citation parity, quote format, heuristic verb triggers, and uncited warnings).
 */
export function runDeterministicSanityChecks(draft, dossier = null) {
  const issues = [];

  // Separate body text and references section if header exists
  const refHeaderMatch = (draft || "").match(/(?:^|\n)##+\s*(?:📚\s*)?(?:Referensi|References|Sumber Terkutip|Cited Sources|Daftar Rujukan|Daftar Referensi)[^\n]*\n/i);
  let bodyText = draft || "";
  let refText = draft || "";
  if (refHeaderMatch && refHeaderMatch.index !== undefined) {
    bodyText = draft.substring(0, refHeaderMatch.index);
    refText = draft.substring(refHeaderMatch.index);
  }

  // 1. In-text citations (1-3 digits) from body vs references section
  const inTextCitations = new Set();
  const citeRegex = /\[(\d{1,3})\]/g;
  let m;
  while ((m = citeRegex.exec(bodyText)) !== null) {
    inTextCitations.add(parseInt(m[1], 10));
  }

  // Match both [1] and 1. style bibliography lines from references
  const refRegex = /(?:^|\n)(?:[-*]\s*)?(?:\[(\d{1,3})\]|(\d{1,3})\.)/g;
  const refNumbers = new Set();
  while ((m = refRegex.exec(refText)) !== null) {
    refNumbers.add(parseInt(m[1] || m[2], 10));
  }

  const missingRefs = [...inTextCitations].filter(n => !refNumbers.has(n));
  if (missingRefs.length > 0) {
    issues.push(`In-text citation numbers missing in references list: [${missingRefs.join("], [")}]`);
  }

  // Non-blocking warning for bibliography items not cited in text
  const uncitedRefs = [...refNumbers].filter(n => !inTextCitations.has(n));
  const warnings = uncitedRefs.sort((a, b) => a - b).map(n => `Reference [${n}] in bibliography is not cited in text`);

  // 2. Check for verbatim quotes presence
  const quoteMatches = (draft || "").match(/(?:["“])[^"”\r\n]{8,}(?:["”])\s*\[\d+\]/g) || [];
  if (quoteMatches.length === 0) {
    issues.push("No verbatim quotes matching '\"...\" [n]' format found in draft.");
  }

  // 3. Scan for aggressive causal verbs near citations
  const aggressiveCausalPatterns = [
    /\b(?:drives|causes|induces|proves)\b[^.\n]{0,80}\[\d+\]/i,
    /\[\d+\][^.\n]{0,80}\b(?:drives|causes|induces|proves)\b/i,
    /\b(?:membuktikan|memicu|menyebabkan)\b[^.\n]{0,80}\[\d+\]/i,
    /\[\d+\][^.\n]{0,80}\b(?:membuktikan|memicu|menyebabkan)\b/i
  ];
  for (const pat of aggressiveCausalPatterns) {
    const found = (draft || "").match(pat);
    if (found) {
      issues.push(`Heuristic causal verb pattern detected near citation: "${found[0].trim()}" - Verify against research design on Verb Ladder.`);
      break;
    }
  }

  // 4. Quote fidelity against dossier abstracts
  let verifiedQuotesCount = 0;
  if (dossier && dossier.citations && Array.isArray(dossier.citations)) {
    const quoteWithNumRegex = /(?:["“])((?:[^"”\r\n]|\n(?!\n)){8,})(?:["”])\s*\[(\d+)\]/g;
    let qm;
    while ((qm = quoteWithNumRegex.exec(draft || "")) !== null) {
      const qText = qm[1].trim();
      const num = parseInt(qm[2], 10);
      const cit = dossier.citations.find(c => c.num === num) || dossier.citations[num - 1];
      if (cit && cit.abstract) {
        const cleanQ = qText.toLowerCase().replace(/[^\w\s]/g, "");
        const cleanAbs = cit.abstract.toLowerCase().replace(/[^\w\s]/g, "");
        if (cleanAbs.includes(cleanQ) || cleanQ.split(/\s+/).slice(0, 5).join(" ") && cleanAbs.includes(cleanQ.split(/\s+/).slice(0, 5).join(" "))) {
          verifiedQuotesCount++;
        }
      }
    }
  }

  return {
    passed: issues.length === 0,
    hasIssues: issues.length > 0,
    issues: issues,
    warnings: warnings,
    inTextCount: inTextCitations.size,
    refCount: refNumbers.size,
    quoteCount: quoteMatches.length,
    verifiedQuotesCount: verifiedQuotesCount
  };
}

