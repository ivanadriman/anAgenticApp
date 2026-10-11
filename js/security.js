/**
 * Gemini Agentic Studio - Security & Sanitization Utilities
 */

export function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function escapeHtmlAttr(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

export function isSafeUrl(url) {
  if (!url) return false;
  // Strip control characters, tabs, newlines, and surrounding spaces used for protocol obfuscation
  const sanitized = String(url).replace(/[\u0000-\u001F\u007F-\u009F\s]+/g, "");
  if (!sanitized) return false;
  if (sanitized.startsWith("#")) return true;

  // Explicitly reject dangerous script / execution schemes
  if (/^(?:javascript|data|vbscript):/i.test(sanitized)) {
    return false;
  }

  try {
    const parsed = new URL(sanitized, typeof window !== "undefined" ? window.location.href : "https://localhost");
    return parsed.protocol === "http:" || parsed.protocol === "https:" || parsed.protocol === "mailto:";
  } catch (e) {
    return false;
  }
}

export const DOMPURIFY_CONFIG = {
  USE_PROFILES: { html: true },
  ADD_TAGS: ["mark", "button"],
  ADD_ATTR: [
    "target",
    "rel",
    "class",
    "id",
    "type",
    "style",
    "data-citation-num",
    "data-citation-title",
    "data-citation-authors",
    "data-citation-source",
    "data-citation-year",
    "data-citation-url",
    "data-citation-raw-url",
    "data-citation-quote",
    "data-citation-abstract",
    "data-ref-num"
  ],
  ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$)|#)/i
};

// Install DOMPurify hooks once if available in window environment
if (typeof window !== "undefined" && window.DOMPurify && typeof window.DOMPurify.addHook === "function") {
  window.DOMPurify.addHook("afterSanitizeAttributes", function(node) {
    if (node.tagName === "A" && node.getAttribute("target") === "_blank") {
      node.setAttribute("rel", "noopener noreferrer");
    }
  });
}

export function sanitizeRenderedHtml(rawHtml) {
  if (typeof window !== "undefined" && window.DOMPurify && typeof window.DOMPurify.sanitize === "function") {
    return window.DOMPurify.sanitize(rawHtml, DOMPURIFY_CONFIG);
  }
  return rawHtml;
}

export function configureMarked() {
  if (typeof window === "undefined" || !window.marked) return;

  window.marked.use({
    gfm: true,
    breaks: true,
    renderer: {
      link(arg1, arg2, arg3) {
        let href = "";
        let title = "";
        let text = "";
        if (typeof arg1 === "object" && arg1 !== null) {
          href = arg1.href || "";
          title = arg1.title || "";
          text = arg1.text || href;
        } else {
          href = arg1 || "";
          title = arg2 || "";
          text = arg3 || href;
        }

        // Reject unsafe protocols (javascript:, data:, vbscript:)
        const safeHref = isSafeUrl(href) ? escapeHtmlAttr(href) : "#";
        const isExternal = href.startsWith("http://") || href.startsWith("https://") || href.startsWith("//");
        const targetAttr = isExternal ? ' target="_blank" rel="noopener noreferrer"' : '';
        const titleAttr = title ? ` title="${escapeHtmlAttr(title)}"` : '';

        // Check if this is a link to an external paper or reference action
        const isPaperAction = /buka|open|paper|makalah|doi|arxiv|pmc|pubmed|link|tautan|source|sumber/i.test(text) ||
                              href.includes("doi.org") || href.includes("arxiv.org") || href.includes("ncbi.nlm.nih.gov") || href.includes("semanticscholar.org");

        if (isPaperAction) {
          const cleanText = text.replace(/^🔗\s*/, "");
          return `<a href="${safeHref}"${targetAttr}${titleAttr} class="inline-flex items-center gap-1.5 px-3 py-1 my-1 text-xs font-semibold rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-700/80 hover:bg-cyan-900 hover:text-white hover:border-cyan-400 transition shadow-sm no-underline group"><span class="text-cyan-400 group-hover:scale-110 transition-transform">🔗</span> <span>${cleanText}</span> <span class="text-[10px] text-cyan-400 opacity-80">↗</span></a>`;
        }

        return `<a href="${safeHref}"${targetAttr}${titleAttr} class="text-cyan-400 hover:text-cyan-300 underline underline-offset-2 hover:underline transition inline-flex items-center gap-1 font-medium">${text} <span class="text-[10px] text-cyan-500 no-underline">↗</span></a>`;
      }
    }
  });
}
