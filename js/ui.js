/**
 * Gemini Agentic Studio - UI Components, Reading Ergonomics, PDF Exports & Card Renderers
 */

import {
  escapeHtml,
  escapeHtmlAttr,
  isSafeUrl,
  sanitizeRenderedHtml
} from "./security.js";
import {
  buildTextFragmentUrl,
  highlightQuoteInAbstract
} from "./text-fragments.js";
import {
  THEME_STORAGE_KEY,
  FONT_STORAGE_KEY,
  FONT_SIZE_STORAGE_KEY,
  getDifficultyLabel,
  getReadingTypeLabel
} from "./config.js";

export let activeExportDocument = null;
export let currentTheme = (typeof localStorage !== "undefined" && localStorage.getItem(THEME_STORAGE_KEY)) || "slate";
export let currentFont = (typeof localStorage !== "undefined" && localStorage.getItem(FONT_STORAGE_KEY)) || "serif";
export let currentFontSize = (typeof localStorage !== "undefined" && localStorage.getItem(FONT_SIZE_STORAGE_KEY)) || "normal";

export function applyTheme(themeName) {
  currentTheme = themeName;
  if (typeof localStorage !== "undefined") {
    localStorage.setItem(THEME_STORAGE_KEY, themeName);
  }
  document.documentElement.setAttribute("data-theme", themeName);

  const colors = {
    sepia: "#F8F5EE",
    slate: "#020617",
    light: "#F9FAFB",
    oled: "#000000"
  };
  const metaColor = document.getElementById("metaThemeColor");
  if (metaColor) metaColor.setAttribute("content", colors[themeName] || "#020617");

  const btnIds = ["themeSepiaBtn", "themeSlateBtn", "themeLightBtn", "themeOledBtn"];
  btnIds.forEach(id => {
    const btn = document.getElementById(id);
    if (!btn) return;
    const match = id.toLowerCase().includes(themeName);
    if (match) {
      btn.classList.add("ring-2", "ring-cyan-400", "scale-105");
    } else {
      btn.classList.remove("ring-2", "ring-cyan-400", "scale-105");
    }
  });
}

export function applyFont(fontName) {
  currentFont = fontName;
  if (typeof localStorage !== "undefined") {
    localStorage.setItem(FONT_STORAGE_KEY, fontName);
  }
  document.documentElement.setAttribute("data-font-family", fontName);
  syncToolbarFontButtons(fontName);
}

export function applyFontSize(sizeName) {
  currentFontSize = sizeName;
  if (typeof localStorage !== "undefined") {
    localStorage.setItem(FONT_SIZE_STORAGE_KEY, sizeName);
  }
  document.documentElement.setAttribute("data-font-size", sizeName);
  syncToolbarSizeButtons(sizeName);
}

export function syncToolbarFontButtons(fontName) {
  document.querySelectorAll(".font-toggle-serif").forEach(b => {
    if (fontName === "serif") {
      b.classList.add("bg-cyan-500/20", "text-cyan-300", "border-cyan-500/50");
      b.classList.remove("text-slate-400");
    } else {
      b.classList.remove("bg-cyan-500/20", "text-cyan-300", "border-cyan-500/50");
      b.classList.add("text-slate-400");
    }
  });
  document.querySelectorAll(".font-toggle-sans").forEach(b => {
    if (fontName === "sans") {
      b.classList.add("bg-cyan-500/20", "text-cyan-300", "border-cyan-500/50");
      b.classList.remove("text-slate-400");
    } else {
      b.classList.remove("bg-cyan-500/20", "text-cyan-300", "border-cyan-500/50");
      b.classList.add("text-slate-400");
    }
  });
}

export function syncToolbarSizeButtons(sizeName) {
  const map = { small: ".size-toggle-small", normal: ".size-toggle-norm", large: ".size-toggle-large" };
  Object.entries(map).forEach(([key, sel]) => {
    document.querySelectorAll(sel).forEach(b => {
      if (sizeName === key) {
        b.classList.add("bg-cyan-500/20", "text-cyan-300", "border-cyan-500/50");
        b.classList.remove("text-slate-400");
      } else {
        b.classList.remove("bg-cyan-500/20", "text-cyan-300", "border-cyan-500/50");
        b.classList.add("text-slate-400");
      }
    });
  });
}

export function closeCitationDrawer() {
  const citationDrawer = document.getElementById("citationDrawer");
  const citationDrawerBackdrop = document.getElementById("citationDrawerBackdrop");
  if (citationDrawer) {
    citationDrawer.classList.remove("drawer-open");
    citationDrawer.classList.add("drawer-closed");
  }
  if (citationDrawerBackdrop) {
    citationDrawerBackdrop.classList.add("hidden");
  }
}

export function openCitationInspector(data, currentLang = "en") {
  const citationDrawer = document.getElementById("citationDrawer");
  const citationDrawerBackdrop = document.getElementById("citationDrawerBackdrop");
  if (!citationDrawer) return;
  const { title, authors, source, year, url, rawUrl, quote, abstract } = data;

  const drawerSourceBadge = document.getElementById("drawerSourceBadge");
  const drawerYear = document.getElementById("drawerYear");
  const drawerTitle = document.getElementById("drawerTitle");
  const drawerAuthors = document.getElementById("drawerAuthors");

  if (drawerSourceBadge) drawerSourceBadge.textContent = source || "Source";
  if (drawerYear) drawerYear.textContent = year || "";
  if (drawerTitle) drawerTitle.textContent = title || "Academic Source";
  if (drawerAuthors) drawerAuthors.textContent = authors || "";

  // Quote Section
  const drawerQuoteSection = document.getElementById("drawerQuoteSection");
  const drawerQuoteContainer = document.getElementById("drawerQuoteContainer");
  const drawerCopyQuoteBtn = document.getElementById("drawerCopyQuoteBtn");
  const drawerCopyQuoteText = document.getElementById("drawerCopyQuoteText");

  if (quote) {
    if (drawerQuoteSection) drawerQuoteSection.classList.remove("hidden");
    if (drawerQuoteContainer) {
      drawerQuoteContainer.textContent = `“${quote}”`;
      drawerQuoteContainer.classList.remove("hidden");
    }
    if (drawerCopyQuoteBtn) {
      drawerCopyQuoteBtn.classList.remove("hidden");
      if (drawerCopyQuoteText) {
        drawerCopyQuoteText.textContent = currentLang === "id" ? "Salin untuk CTRL+F" : "Copy for CTRL+F";
      }
      drawerCopyQuoteBtn.onclick = (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        navigator.clipboard.writeText(quote).then(() => {
          if (drawerCopyQuoteText) {
            drawerCopyQuoteText.textContent = currentLang === "id" ? "✓ Tersalin (CTRL+F)!" : "✓ Copied (CTRL+F)!";
            setTimeout(() => {
              drawerCopyQuoteText.textContent = currentLang === "id" ? "Salin untuk CTRL+F" : "Copy for CTRL+F";
            }, 2200);
          }
        });
      };
    }
  } else {
    if (drawerQuoteSection) drawerQuoteSection.classList.add("hidden");
    if (drawerQuoteContainer) drawerQuoteContainer.classList.add("hidden");
    if (drawerCopyQuoteBtn) drawerCopyQuoteBtn.classList.add("hidden");
  }

  // In-Context Verbatim Abstract Verification Section
  const drawerAbstractSection = document.getElementById("drawerAbstractSection");
  const drawerAbstractContent = document.getElementById("drawerAbstractContent");
  const drawerVerifyPill = document.getElementById("drawerVerifyPill");
  const drawerAbstractMatchBadge = document.getElementById("drawerAbstractMatchBadge");

  if (abstract && abstract.trim().length > 0) {
    if (drawerAbstractSection) drawerAbstractSection.classList.remove("hidden");
    const { html, found } = highlightQuoteInAbstract(abstract, quote);
    if (drawerAbstractContent) {
      drawerAbstractContent.innerHTML = sanitizeRenderedHtml(html);
    }
    if (found) {
      if (drawerVerifyPill) {
        drawerVerifyPill.textContent = currentLang === "id" ? "✓ Terverifikasi di Abstrak" : "✓ Verified in Abstract";
        drawerVerifyPill.className = "text-[10px] sm:text-xs font-semibold px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 inline-flex items-center gap-1";
      }
      if (drawerAbstractMatchBadge) {
        drawerAbstractMatchBadge.textContent = currentLang === "id" ? "✓ 100% Cocok Verbatim" : "✓ 100% Verbatim Match";
        drawerAbstractMatchBadge.className = "text-[10px] font-semibold text-emerald-400";
      }
    } else {
      if (drawerVerifyPill) {
        drawerVerifyPill.textContent = currentLang === "id" ? "ℹ️ Naskah Lengkap / Pre-print" : "ℹ️ Full-Text / Preprint";
        drawerVerifyPill.className = "text-[10px] sm:text-xs font-medium px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-500/40 inline-flex items-center gap-1";
      }
      if (drawerAbstractMatchBadge) {
        drawerAbstractMatchBadge.textContent = currentLang === "id" ? "ℹ️ Tidak di abstrak ringkas" : "ℹ️ Not in concise abstract";
        drawerAbstractMatchBadge.className = "text-[10px] font-medium text-amber-400";
      }
    }
  } else {
    if (drawerAbstractSection) drawerAbstractSection.classList.remove("hidden");
    if (drawerAbstractContent) {
      drawerAbstractContent.innerHTML = `<span class="italic text-slate-400">${currentLang === "id" ? "Hanya metadata bibliografi tersedia dalam indeks umum. Buka tautan makalah atau gunakan Google Scholar di bawah untuk memeriksa naskah lengkap." : "Only bibliographic metadata available in index. Open the paper link or search Google Scholar below to verify in full text."}</span>`;
    }
    if (drawerVerifyPill) {
      drawerVerifyPill.textContent = currentLang === "id" ? "📚 Sumber Bibliografi" : "📚 Bibliographic Source";
      drawerVerifyPill.className = "text-[10px] sm:text-xs font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-600 inline-flex items-center gap-1";
    }
    if (drawerAbstractMatchBadge) {
      drawerAbstractMatchBadge.textContent = "";
    }
  }

  // Actions Row
  const drawerActionLink = document.getElementById("drawerActionLink");
  if (drawerActionLink) {
    if (url && url !== "#" && !url.startsWith("#ref-")) {
      drawerActionLink.href = url;
      drawerActionLink.classList.remove("hidden");
      drawerActionLink.style.display = "flex";
    } else if (rawUrl && rawUrl !== "#" && !rawUrl.startsWith("#ref-")) {
      drawerActionLink.href = rawUrl;
      drawerActionLink.classList.remove("hidden");
      drawerActionLink.style.display = "flex";
    } else {
      drawerActionLink.classList.add("hidden");
      drawerActionLink.style.display = "none";
    }
  }

  // Google Scholar Fallback
  const drawerScholarBtn = document.getElementById("drawerScholarBtn");
  if (drawerScholarBtn) {
    const queryTerm = quote ? `"${quote.replace(/^["“'”]+|["“'”]+$/g, "").trim()}"` : `"${title}"`;
    drawerScholarBtn.href = `https://scholar.google.com/scholar?q=${encodeURIComponent(queryTerm)}`;
  }

  if (citationDrawerBackdrop) citationDrawerBackdrop.classList.remove("hidden");
  citationDrawer.classList.remove("drawer-closed");
  citationDrawer.classList.add("drawer-open");
}

let tooltipTimeout = null;

export function initCitationInteractions(container = document, currentLang = "en") {
  const citationTooltip = document.getElementById("citationTooltip");
  const tooltipSourceBadge = document.getElementById("tooltipSourceBadge");
  const tooltipYear = document.getElementById("tooltipYear");
  const tooltipTitle = document.getElementById("tooltipTitle");
  const tooltipAuthors = document.getElementById("tooltipAuthors");
  const tooltipActionLink = document.getElementById("tooltipActionLink");

  const citations = container.querySelectorAll(".citation-ref");
  citations.forEach(el => {
    const title = el.getAttribute("data-citation-title") || "Paper Reference";
    const authors = el.getAttribute("data-citation-authors") || "";
    const source = el.getAttribute("data-citation-source") || "Source";
    const year = el.getAttribute("data-citation-year") || "";
    const url = el.getAttribute("data-citation-url") || el.getAttribute("href");
    const rawUrl = el.getAttribute("data-citation-raw-url") || url;
    const num = el.getAttribute("data-citation-num") || "";
    const quote = el.getAttribute("data-citation-quote") || "";
    const abstract = el.getAttribute("data-citation-abstract") || "";

    const citationData = { title, authors, source, year, url, rawUrl, num, quote, abstract };

    // Desktop Hover Quick Tooltip
    el.addEventListener("mouseenter", () => {
      if (window.innerWidth < 640) return;
      clearTimeout(tooltipTimeout);
      if (!citationTooltip) return;

      if (tooltipSourceBadge) tooltipSourceBadge.textContent = source;
      if (tooltipYear) tooltipYear.textContent = year;
      if (tooltipTitle) tooltipTitle.textContent = title;
      if (tooltipAuthors) tooltipAuthors.textContent = authors;
      if (tooltipActionLink) {
        tooltipActionLink.href = url;
        tooltipActionLink.style.display = (url && url !== "#" && !url.startsWith("#ref-")) ? "inline-flex" : "none";
      }

      const tooltipQuoteContainer = document.getElementById("tooltipQuoteContainer");
      const tooltipCopyQuoteBtn = document.getElementById("tooltipCopyQuoteBtn");
      const tooltipInspectBtn = document.getElementById("tooltipInspectBtn");

      if (tooltipQuoteContainer) {
        if (quote) {
          tooltipQuoteContainer.textContent = `“${quote}”`;
          tooltipQuoteContainer.classList.remove("hidden");
        } else {
          tooltipQuoteContainer.classList.add("hidden");
        }
      }
      if (tooltipCopyQuoteBtn) {
        if (quote) {
          tooltipCopyQuoteBtn.classList.remove("hidden");
          const copyLabel = currentLang === "id" ? "Salin Kutipan" : "Copy Quote";
          tooltipCopyQuoteBtn.textContent = copyLabel;
          tooltipCopyQuoteBtn.onclick = (ev) => {
            ev.preventDefault();
            ev.stopPropagation();
            navigator.clipboard.writeText(quote).then(() => {
              tooltipCopyQuoteBtn.textContent = currentLang === "id" ? "✓ Tersalin!" : "✓ Copied!";
              setTimeout(() => {
                tooltipCopyQuoteBtn.textContent = copyLabel;
              }, 2000);
            });
          };
        } else {
          tooltipCopyQuoteBtn.classList.add("hidden");
        }
      }

      if (tooltipInspectBtn) {
        tooltipInspectBtn.onclick = (ev) => {
          ev.preventDefault();
          ev.stopPropagation();
          if (citationTooltip) citationTooltip.classList.add("hidden");
          openCitationInspector(citationData, currentLang);
        };
      }

      const rect = el.getBoundingClientRect();
      const top = window.scrollY + rect.bottom + 8;
      const left = Math.max(12, Math.min(window.innerWidth - 370, window.scrollX + rect.left - 100));

      citationTooltip.style.top = `${top}px`;
      citationTooltip.style.left = `${left}px`;
      citationTooltip.classList.remove("hidden");
    });

    el.addEventListener("mouseleave", () => {
      if (window.innerWidth < 640) return;
      tooltipTimeout = setTimeout(() => {
        if (citationTooltip) citationTooltip.classList.add("hidden");
      }, 300);
    });

    // Click Handling (Both Mobile and Desktop open Evidence Inspector)
    el.addEventListener("click", (e) => {
      e.preventDefault();
      if (citationTooltip) citationTooltip.classList.add("hidden");
      openCitationInspector(citationData, currentLang);
    });
  });

  if (citationTooltip) {
    citationTooltip.addEventListener("mouseenter", () => clearTimeout(tooltipTimeout));
    citationTooltip.addEventListener("mouseleave", () => {
      tooltipTimeout = setTimeout(() => {
        if (citationTooltip) citationTooltip.classList.add("hidden");
      }, 200);
    });
  }

  // Also attach inspect buttons inside references section
  const refInspectButtons = container.querySelectorAll(".ref-inspect-btn");
  refInspectButtons.forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const refNum = parseInt(btn.getAttribute("data-ref-num"), 10);
      const citRef = container.querySelector(`.citation-ref[data-citation-num='${refNum}']`);
      if (citRef) {
        citRef.click();
      }
    });
  });
}

export function initGlobalUIControls(currentLang = "en") {
  const closeDrawerBtn = document.getElementById("closeDrawerBtn");
  if (closeDrawerBtn) closeDrawerBtn.addEventListener("click", closeCitationDrawer);
  const citationDrawerBackdrop = document.getElementById("citationDrawerBackdrop");
  if (citationDrawerBackdrop) citationDrawerBackdrop.addEventListener("click", closeCitationDrawer);

  const closeFocusModalBtn = document.getElementById("closeFocusModalBtn");
  if (closeFocusModalBtn) closeFocusModalBtn.addEventListener("click", closeFocusReadingMode);

  const closePdfModalBtn = document.getElementById("closePdfModalBtn");
  if (closePdfModalBtn) closePdfModalBtn.addEventListener("click", closePdfExportModal);
  const cancelPdfModalBtn = document.getElementById("cancelPdfModalBtn");
  if (cancelPdfModalBtn) cancelPdfModalBtn.addEventListener("click", closePdfExportModal);

  const pdfExportModal = document.getElementById("pdfExportModal");
  if (pdfExportModal) {
    pdfExportModal.addEventListener("click", (e) => {
      if (e.target === pdfExportModal) {
        closePdfExportModal();
      }
    });
  }

  const pdfPrintVectorBtn = document.getElementById("pdfPrintVectorBtn");
  if (pdfPrintVectorBtn) {
    pdfPrintVectorBtn.addEventListener("click", () => {
      const opts = getPdfExportOptions();
      printDocumentViaIframe(activeExportDocument, opts, currentLang);
    });
  }

  const pdfDownloadDirectBtn = document.getElementById("pdfDownloadDirectBtn");
  if (pdfDownloadDirectBtn) {
    pdfDownloadDirectBtn.addEventListener("click", () => {
      const opts = getPdfExportOptions();
      downloadDocumentAsPdf(activeExportDocument, opts, currentLang);
    });
  }

  const focusDownloadMDBtn = document.getElementById("focusDownloadMDBtn");
  if (focusDownloadMDBtn) {
    focusDownloadMDBtn.addEventListener("click", () => {
      downloadMarkdownFile(activeExportDocument?.markdown || "", document.getElementById("topicInput")?.value || "");
    });
  }

  const focusExportPdfBtn = document.getElementById("focusExportPdfBtn");
  if (focusExportPdfBtn) {
    focusExportPdfBtn.addEventListener("click", () => {
      openPdfExportModal(activeExportDocument);
    });
  }

  const focusPrintBtn = document.getElementById("focusPrintBtn");
  if (focusPrintBtn) {
    focusPrintBtn.addEventListener("click", () => {
      openPdfExportModal(activeExportDocument);
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closePdfExportModal();
      closeFocusReadingMode();
      closeCitationDrawer();
    }
  });

  document.getElementById("focusFontSerifBtn")?.addEventListener("click", () => applyFont("serif"));
  document.getElementById("focusFontSansBtn")?.addEventListener("click", () => applyFont("sans"));
  document.getElementById("focusSizeMinusBtn")?.addEventListener("click", () => applyFontSize("small"));
  document.getElementById("focusSizeNormBtn")?.addEventListener("click", () => applyFontSize("normal"));
  document.getElementById("focusSizePlusBtn")?.addEventListener("click", () => applyFontSize("large"));

  document.getElementById("themeSepiaBtn")?.addEventListener("click", () => applyTheme("sepia"));
  document.getElementById("themeSlateBtn")?.addEventListener("click", () => applyTheme("slate"));
  document.getElementById("themeLightBtn")?.addEventListener("click", () => applyTheme("light"));
  document.getElementById("themeOledBtn")?.addEventListener("click", () => applyTheme("oled"));
}

export function openFocusReadingMode(htmlContent, title = "Zen View", markdownContent = null) {
  const modal = document.getElementById("focusReadingModal");
  const focusModalContent = document.getElementById("focusModalContent");
  const focusModalTitle = document.getElementById("focusModalTitle");
  const focusProgressBar = document.getElementById("focusProgressBar");

  if (!modal || !focusModalContent) return;
  focusModalContent.innerHTML = sanitizeRenderedHtml(htmlContent);
  if (focusModalTitle) focusModalTitle.textContent = title;

  initCitationInteractions(focusModalContent);
  modal.classList.remove("hidden");
  document.body.style.overflow = "hidden";

  focusModalContent.onscroll = () => {
    if (!focusProgressBar) return;
    const progress = (focusModalContent.scrollTop / (focusModalContent.scrollHeight - focusModalContent.clientHeight)) * 100;
    focusProgressBar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
  };
}

export function closeFocusReadingMode() {
  const modal = document.getElementById("focusReadingModal");
  if (modal) {
    modal.classList.add("hidden");
    document.body.style.overflow = "";
  }
}

export function extractDocumentTitle(markdownText, fallbackTopic = "") {
  if (!markdownText) return fallbackTopic || "Agentic_Studio_Document";
  const h1Match = markdownText.match(/^#\s+(.+)$/m);
  if (h1Match && h1Match[1].trim()) {
    return h1Match[1].replace(/[*_`]/g, "").trim();
  }
  return fallbackTopic || "Agentic_Studio_Document";
}

export function slugifyFilename(title, maxLength = 80) {
  if (!title) return "document";
  let slug = title
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .trim()
    .replace(/[\s_]+/g, "_");
  if (slug.length > maxLength) {
    slug = slug.substring(0, maxLength).replace(/_$/, "");
  }
  return slug || "document";
}

export function downloadMarkdownFile(markdownText, topic = "") {
  if (!markdownText) return;
  const title = extractDocumentTitle(markdownText, topic);
  const filename = `${slugifyFilename(title)}.md`;
  const blob = new Blob([markdownText], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function openPdfExportModal(docData = null) {
  const modal = document.getElementById("pdfExportModal");
  if (!modal) return;
  if (docData) activeExportDocument = docData;
  modal.classList.remove("hidden");
}

export function closePdfExportModal() {
  const modal = document.getElementById("pdfExportModal");
  if (modal) modal.classList.add("hidden");
}

export function getPdfExportOptions() {
  return {
    paperSize: document.getElementById("pdfPaperSize")?.value || "a4",
    orientation: document.getElementById("pdfOrientation")?.value || "portrait",
    margins: document.getElementById("pdfMargins")?.value || "standard",
    font: document.getElementById("pdfFont")?.value || "serif",
    fontSize: document.getElementById("pdfFontSize")?.value || "11pt",
    includeHeader: document.getElementById("pdfIncludeHeader")?.checked ?? true,
    smartBreaks: document.getElementById("pdfAvoidBreaks")?.checked ?? true
  };
}

export function prepareCleanPrintHtml(docData, options = {}, currentLang = "en") {
  const {
    paperSize = "a4",
    orientation = "portrait",
    margins = "standard",
    font = "serif",
    fontSize = "11pt",
    includeHeader = true
  } = options;

  const fontStack = font === "serif"
    ? "Charter, Georgia, Cambria, 'Times New Roman', serif"
    : "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";

  const marginMmMap = { standard: "15mm", narrow: "10mm", wide: "22mm" };
  const marginCss = marginMmMap[margins] || "15mm";

  let headerHtml = "";
  if (includeHeader) {
    const isId = currentLang === "id";
    const dateStr = new Date().toLocaleDateString(isId ? "id-ID" : "en-US", {
      year: "numeric", month: "long", day: "numeric"
    });
    const diffText = docData.metadata?.difficulty ? getDifficultyLabel(docData.metadata.difficulty, isId) : "";
    const typeText = docData.metadata?.readingType ? getReadingTypeLabel(docData.metadata.readingType, isId) : "";
    const scoreText = (docData.metadata?.score != null) ? `${Number(docData.metadata.score).toFixed(1)}/10` : "";

    headerHtml = `
      <div class="print-header-banner" style="margin-bottom: 24px; padding-bottom: 16px; border-bottom: 2px solid #e2e8f0;">
        <h1 style="margin: 0 0 10px 0; font-size: 22pt; font-weight: 800; color: #0f172a; line-height: 1.25;">
          ${escapeHtml(docData.title)}
        </h1>
        <div style="font-size: 9.5pt; color: #475569; display: flex; flex-wrap: wrap; gap: 14px; margin-top: 6px;">
          <span>📅 ${dateStr}</span>
          ${diffText ? `<span>🎯 <strong>${isId ? "Target" : "Audience"}:</strong> ${diffText}</span>` : ""}
          ${typeText ? `<span>📚 <strong>${isId ? "Genre" : "Type"}:</strong> ${typeText}</span>` : ""}
          ${scoreText ? `<span>🏆 <strong>${isId ? "Skor" : "Score"}:</strong> ${scoreText}</span>` : ""}
        </div>
      </div>
    `;
  }

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>${escapeHtml(docData.title)}</title>
  <style>
    @page { size: ${paperSize} ${orientation}; margin: ${marginCss}; }
    *, *::before, *::after { box-sizing: border-box; box-shadow: none !important; text-shadow: none !important; }
    body {
      margin: 0; padding: 0; background: #ffffff !important; color: #111827 !important;
      font-family: ${fontStack}; font-size: ${fontSize}; line-height: 1.65;
      text-rendering: optimizeLegibility; -webkit-font-smoothing: antialiased;
    }
    h1, h2, h3, h4, h5, h6 { color: #0f172a; font-family: ${fontStack}; font-weight: 700; margin-top: 1.5em; margin-bottom: 0.5em; page-break-after: avoid; break-after: avoid; }
    p, li, blockquote { orphans: 3; widows: 3; }
    blockquote, .verbatim-quote-block {
      margin: 1.2em 0; padding: 10px 16px; border-left: 3.5px solid #0284c7;
      background: #f8fafc; font-style: italic; page-break-inside: avoid; break-inside: avoid;
    }
    .reference-item { padding: 6px 0; border-bottom: 1px solid #f1f5f9; page-break-inside: avoid; break-inside: avoid; font-size: 0.9em; }
    .reading-toolbar, button, .no-print { display: none !important; }
  </style>
</head>
<body>
  ${headerHtml}
  <div class="document-content">
    ${sanitizeRenderedHtml(docData.html)}
  </div>
</body>
</html>`;
}

export function printDocumentViaIframe(docData, options = {}, currentLang = "en") {
  const fullHtml = prepareCleanPrintHtml(docData, options, currentLang);
  const iframe = document.createElement("iframe");
  iframe.style.position = "fixed";
  iframe.style.right = "0";
  iframe.style.bottom = "0";
  iframe.style.width = "0";
  iframe.style.height = "0";
  iframe.style.border = "0";
  iframe.id = "cleanPrintIframe";
  document.body.appendChild(iframe);

  const doc = iframe.contentWindow.document;
  doc.open();
  doc.write(fullHtml);
  doc.close();

  iframe.contentWindow.focus();
  setTimeout(() => {
    iframe.contentWindow.print();
    setTimeout(() => {
      if (iframe.parentNode) iframe.parentNode.removeChild(iframe);
      closePdfExportModal();
    }, 1000);
  }, 400);
}

export function downloadDocumentAsPdf(docData, options = {}, currentLang = "en") {
  const {
    paperSize = "a4",
    orientation = "portrait",
    margins = "standard",
    font = "serif",
    fontSize = "11pt",
    includeHeader = true
  } = options;

  const marginMmMap = { standard: 15, narrow: 10, wide: 22 };
  const marginMm = marginMmMap[margins] || 15;

  const fontStack = font === "serif"
    ? "Charter, Georgia, Cambria, 'Times New Roman', serif"
    : "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";

  const container = document.createElement("div");
  container.id = "tempPdfContainer";
  container.style.position = "absolute";
  container.style.left = "-9999px";
  container.style.top = "0";
  container.style.width = orientation === "landscape" ? "270mm" : "190mm";
  container.style.background = "#ffffff";
  container.style.color = "#111827";

  let headerHtml = "";
  if (includeHeader) {
    const isId = currentLang === "id";
    const dateStr = new Date().toLocaleDateString(isId ? "id-ID" : "en-US", {
      year: "numeric", month: "long", day: "numeric"
    });
    const diffText = docData.metadata?.difficulty ? getDifficultyLabel(docData.metadata.difficulty, isId) : "";
    const typeText = docData.metadata?.readingType ? getReadingTypeLabel(docData.metadata.readingType, isId) : "";
    const scoreText = (docData.metadata?.score != null) ? `${Number(docData.metadata.score).toFixed(1)}/10` : "";

    headerHtml = `
      <div style="margin-bottom: 24px; padding-bottom: 16px; border-bottom: 2px solid #e2e8f0;">
        <h1 style="margin: 0 0 10px 0; font-size: 24px; font-weight: 800; color: #0f172a; line-height: 1.25; font-family: ${fontStack};">
          ${escapeHtml(docData.title)}
        </h1>
        <div style="font-size: 12px; color: #475569; display: flex; flex-wrap: wrap; gap: 14px; margin-top: 6px;">
          <span>📅 ${dateStr}</span>
          ${diffText ? `<span>🎯 <strong>${isId ? "Target" : "Audience"}:</strong> ${diffText}</span>` : ""}
          ${typeText ? `<span>📚 <strong>${isId ? "Genre" : "Type"}:</strong> ${typeText}</span>` : ""}
          ${scoreText ? `<span>🏆 <strong>${isId ? "Skor" : "Score"}:</strong> ${scoreText}</span>` : ""}
        </div>
      </div>
    `;
  }

  container.innerHTML = `
    <div style="font-family: ${fontStack}; font-size: ${fontSize}; line-height: 1.65; color: #111827;">
      ${headerHtml}
      <div class="markdown-body" style="color: #111827; background: transparent;">
        ${sanitizeRenderedHtml(docData.html)}
      </div>
    </div>
  `;

  document.body.appendChild(container);

  if (typeof window.html2pdf !== "function") {
    document.body.removeChild(container);
    printDocumentViaIframe(docData, options, currentLang);
    return;
  }

  const opt = {
    margin: [marginMm, marginMm, marginMm, marginMm],
    filename: `${slugifyFilename(docData.title)}.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true, logging: false },
    jsPDF: { unit: 'mm', format: (paperSize === "executive") ? [184, 267] : paperSize, orientation: orientation },
    pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
  };

  const btn = document.getElementById("pdfDownloadDirectBtn");
  const origText = btn ? btn.innerHTML : "";
  if (btn) btn.innerHTML = `<span>⏳</span> <span>${currentLang === "id" ? "Memproses PDF..." : "Generating PDF..."}</span>`;

  window.html2pdf().set(opt).from(container).save()
    .then(() => {
      if (container.parentNode) container.parentNode.removeChild(container);
      if (btn) btn.innerHTML = origText;
      closePdfExportModal();
    })
    .catch((err) => {
      console.warn("html2pdf direct render error, falling back to clean print:", err);
      if (container.parentNode) container.parentNode.removeChild(container);
      if (btn) btn.innerHTML = origText;
      printDocumentViaIframe(docData, options, currentLang);
    });
}

/**
 * Prepares rich draft HTML with verbatim quote wrappers, rich citation anchors, and safe markdown rendering.
 * Strictly escapes quotes at source to prevent executable markup while keeping exact characters for CTRL+F matching.
 */
export function prepareDraftHtml(draftText, dossier = null, currentLang = "en") {
  if (!draftText) return "";
  let enriched = typeof draftText === "string" ? draftText : (Array.isArray(draftText) ? draftText.join("\n\n") : String(draftText));

  // Extract all verbatim quotes associated with citation numbers: quotesMap[num] = quoteText
  const quotesMap = {};
  const quoteRegex = /(?:["“])((?:[^"”\r\n]|\n(?!\n)){8,})(?:["”])\s*\[(\d+)\]/g;
  let qMatch;
  while ((qMatch = quoteRegex.exec(draftText)) !== null) {
    const qText = qMatch[1].trim();
    const num = parseInt(qMatch[2], 10);
    if (!quotesMap[num]) {
      quotesMap[num] = qText;
    }
  }

  // Also fallback to first sentence of abstract in dossier if no inline quote
  if (dossier && dossier.citations) {
    dossier.citations.forEach(c => {
      if (!quotesMap[c.num] && c.abstract) {
        const firstSent = c.abstract.split(/(?<=[.!?])\s+/)[0];
        if (firstSent && firstSent.length > 20) {
          quotesMap[c.num] = firstSent.trim();
        }
      }
    });
  }

  const linkifyCitations = (str) => {
    return str.replace(/\[(\d+)\]/g, (match, n) => {
      const num = parseInt(n, 10);
      const cit = dossier && dossier.citations ? (dossier.citations.find(c => c.num === num) || dossier.citations[num - 1]) : null;
      const citTitle = cit ? escapeHtmlAttr(cit.title) : (currentLang === "id" ? `Referensi [${num}]` : `Reference [${num}]`);
      const citAuthors = cit ? escapeHtmlAttr(cit.authors || cit.meta || "") : "";
      const citSource = cit ? escapeHtmlAttr(cit.source || "") : (currentLang === "id" ? "Rujukan Ilmiah" : "Scholarly Source");
      const citYear = cit ? escapeHtmlAttr(cit.year || "") : "";
      const citAbstract = cit ? (cit.abstract || "") : "";
      const quote = quotesMap[num] || "";
      const rawUrl = (cit && cit.url && cit.url !== "#") ? cit.url : `#ref-${num}`;
      const citUrl = (quote && rawUrl !== `#ref-${num}`) ? buildTextFragmentUrl(rawUrl, quote) : rawUrl;
      const tooltipTitle = cit ? escapeHtmlAttr(`[${num}] ${cit.title}`) : (currentLang === "id" ? `Lihat Referensi [${num}]` : `View Reference [${num}]`);
      const safeCitUrl = isSafeUrl(citUrl) ? escapeHtmlAttr(citUrl) : `#ref-${num}`;
      const safeRawUrl = isSafeUrl(rawUrl) ? escapeHtmlAttr(rawUrl) : `#ref-${num}`;

      return `<a href="#ref-${num}" class="citation-ref" data-citation-num="${num}" data-citation-title="${citTitle}" data-citation-authors="${citAuthors}" data-citation-source="${citSource}" data-citation-year="${citYear}" data-citation-url="${safeCitUrl}" data-citation-raw-url="${safeRawUrl}" data-citation-quote="${escapeHtmlAttr(quote)}" data-citation-abstract="${escapeHtmlAttr(citAbstract)}" title="${tooltipTitle}">[${num}]</a>`;
    });
  };

  // 1. Enrich references section: Ensure each [n] entry has a clickable markdown link
  const refHeaderMatch = enriched.match(/(##+\s*(?:📚\s*)?(?:Referensi|References|Sumber Terkutip|Cited Sources|Daftar Rujukan|Daftar Referensi)[^\n]*\n)([\s\S]*)$/i);
  if (refHeaderMatch) {
    const header = refHeaderMatch[1];
    let refBody = refHeaderMatch[2];

    // Format each reference line: [1] ... or 1. ... or - [1] ...
    refBody = refBody.replace(/^(?:[-*]\s*)?(\[(\d+)\]|\b(\d+)\.)\s+([^\n]+)$/gm, (fullLine, prefix, num1, num2, content) => {
      const num = parseInt(num1 || num2, 10);
      let updatedContent = content;

      // Check if markdown link already exists [text](url)
      const hasMarkdownLink = /\[[^\]]+\]\((https?:\/\/[^\s)]+)\)/.test(updatedContent);
      const rawUrlMatch = updatedContent.match(/(https?:\/\/[^\s<)]+)/);
      const linkLabel = currentLang === "id" ? "Buka Makalah / Sumber" : "Open Paper / Source";
      const quote = quotesMap[num] || "";

      if (!hasMarkdownLink && rawUrlMatch) {
        const rawUrl = rawUrlMatch[1];
        const highlightedUrl = quote ? buildTextFragmentUrl(rawUrl, quote) : rawUrl;
        updatedContent = updatedContent.replace(rawUrl, `[🔗 ${linkLabel}](${highlightedUrl})`);
      } else if (!hasMarkdownLink && !rawUrlMatch && dossier && dossier.citations) {
        const matchingCitation = dossier.citations.find(c => c.num === num) || dossier.citations[num - 1];
        if (matchingCitation && matchingCitation.url && matchingCitation.url !== "#") {
          const highlightedUrl = quote ? buildTextFragmentUrl(matchingCitation.url, quote) : matchingCitation.url;
          updatedContent += ` [🔗 ${linkLabel}](${highlightedUrl})`;
        }
      } else if (hasMarkdownLink && quote) {
        updatedContent = updatedContent.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (m, txt, linkUrl) => {
          return `[${txt}](${buildTextFragmentUrl(linkUrl, quote)})`;
        });
      }

      const inspectLabel = currentLang === "id" ? "Periksa Bukti" : "Inspect Evidence";
      const inspectBtnHtml = ` <button type="button" class="ref-inspect-btn text-xs text-cyan-400 hover:text-cyan-300 font-semibold inline-flex items-center gap-1 transition ml-1 px-2 py-0.5 rounded border border-cyan-800/40 bg-cyan-950/20" data-ref-num="${num}" title="${inspectLabel}"><span>🔍</span> <span>${inspectLabel}</span></button>`;
      return `<div id="ref-${num}" class="reference-item">\n\n**[${num}]** ${updatedContent}${inspectBtnHtml}\n\n</div>`;
    });

    let bodyPart = enriched.substring(0, refHeaderMatch.index);

    // Escape quoteText at the source before wrapping in HTML blockquote/span tags
    const formatQuotesInText = (text) => {
      text = text.replace(/(^|\n+)[ \t]*(?:>\s*)?(["“])((?:[^"”\r\n]|\n(?!\n)){8,})(["”])\s*(\[(\d+)\])[ \t]*(?=\n+|$)/g, 
        (m, leadNl, openQ, quoteText, closeQ, citeBracket, citeNum) => {
          return `${leadNl}<blockquote class="verbatim-quote-block"><p class="quote-text">&ldquo;${escapeHtml(quoteText.trim())}&rdquo; [${citeNum}]</p></blockquote>`;
        }
      );
      text = text.replace(/(:[ \t]*)(["“])((?:[^"”\r\n]|\n(?!\n)){60,})(["”])\s*(\[(\d+)\])[ \t]*(?=\n+|$)/g,
        (m, colonLead, openQ, quoteText, closeQ, citeBracket, citeNum) => {
          return `:\n\n<blockquote class="verbatim-quote-block"><p class="quote-text">&ldquo;${escapeHtml(quoteText.trim())}&rdquo; [${citeNum}]</p></blockquote>`;
        }
      );
      text = text.replace(/(["“])([^"”\r\n]{8,})(["”])\s*(\[(\d+)\])/g, 
        (m, openQ, quoteText, closeQ, citeBracket, citeNum) => {
          return `<span class="verbatim-quote">&ldquo;${escapeHtml(quoteText)}&rdquo;</span> [${citeNum}]`;
        }
      );
      return text;
    };

    bodyPart = formatQuotesInText(bodyPart);
    bodyPart = linkifyCitations(bodyPart);
    enriched = bodyPart + header + "\n" + refBody;
  } else {
    const formatQuotesInText = (text) => {
      text = text.replace(/(^|\n+)[ \t]*(?:>\s*)?(["“])((?:[^"”\r\n]|\n(?!\n)){8,})(["”])\s*(\[(\d+)\])[ \t]*(?=\n+|$)/g, 
        (m, leadNl, openQ, quoteText, closeQ, citeBracket, citeNum) => {
          return `${leadNl}<blockquote class="verbatim-quote-block"><p class="quote-text">&ldquo;${escapeHtml(quoteText.trim())}&rdquo; [${citeNum}]</p></blockquote>`;
        }
      );
      text = text.replace(/(:[ \t]*)(["“])((?:[^"”\r\n]|\n(?!\n)){60,})(["”])\s*(\[(\d+)\])[ \t]*(?=\n+|$)/g,
        (m, colonLead, openQ, quoteText, closeQ, citeBracket, citeNum) => {
          return `:\n\n<blockquote class="verbatim-quote-block"><p class="quote-text">&ldquo;${escapeHtml(quoteText.trim())}&rdquo; [${citeNum}]</p></blockquote>`;
        }
      );
      text = text.replace(/(["“])([^"”\r\n]{8,})(["”])\s*(\[(\d+)\])/g, 
        (m, openQ, quoteText, closeQ, citeBracket, citeNum) => {
          return `<span class="verbatim-quote">&ldquo;${escapeHtml(quoteText)}&rdquo;</span> [${citeNum}]`;
        }
      );
      return text;
    };
    enriched = formatQuotesInText(enriched);
    enriched = linkifyCitations(enriched);
  }

  const rawParsed = typeof window !== "undefined" && window.marked ? window.marked.parse(enriched) : enriched;
  return sanitizeRenderedHtml(rawParsed);
}

export function createReadingToolbarHtml(cardId, currentLang = "en") {
  const isId = currentLang === "id";
  const zenText = isId ? "📖 Mode Baca" : "📖 Zen View";
  return `
    <div class="reading-toolbar flex items-center justify-between flex-wrap gap-2 pt-2.5 pb-3 mb-4 border-b border-slate-800/80 text-xs">
      <div class="flex items-center gap-1.5 flex-wrap">
        <span class="text-[11px] text-slate-400 font-medium mr-1">${isId ? "Tampilan:" : "Reading:"}</span>
        <button type="button" class="zen-mode-btn px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition inline-flex items-center gap-1 font-medium shadow-sm">
          <span>${zenText}</span>
        </button>
        <div class="inline-flex rounded border border-slate-800 p-0.5 bg-slate-950/60 ml-1">
          <button type="button" class="font-toggle-serif px-2 py-0.5 rounded text-[11px] font-serif transition ${currentFont === 'serif' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50' : 'text-slate-400'}">Serif</button>
          <button type="button" class="font-toggle-sans px-2 py-0.5 rounded text-[11px] font-sans transition ${currentFont === 'sans' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50' : 'text-slate-400'}">Sans</button>
        </div>
        <div class="inline-flex rounded border border-slate-800 p-0.5 bg-slate-950/60">
          <button type="button" class="size-toggle-small px-1.5 py-0.5 rounded text-[10px] font-mono transition ${currentFontSize === 'small' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400'}">A-</button>
          <button type="button" class="size-toggle-norm px-1.5 py-0.5 rounded text-[11px] font-mono transition ${currentFontSize === 'normal' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400'}">A</button>
          <button type="button" class="size-toggle-large px-1.5 py-0.5 rounded text-[12px] font-mono transition ${currentFontSize === 'large' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400'}">A+</button>
        </div>
      </div>
      <div class="flex items-center gap-1.5 flex-wrap">
        <button type="button" class="download-md-btn px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition inline-flex items-center gap-1 text-[11px] font-medium shadow-sm">
          <span>📥</span> <span>MD</span>
        </button>
        <button type="button" class="export-pdf-btn px-2.5 py-1 rounded bg-cyan-950/80 hover:bg-cyan-900 text-cyan-300 border border-cyan-700/80 transition inline-flex items-center gap-1 text-[11px] font-medium shadow-sm">
          <span>📄</span> <span>PDF</span>
        </button>
      </div>
    </div>
  `;
}

export function renderWriterCard(turn, draftText, dossier = null, currentLang = "en", topic = "") {
  const outputContainer = document.getElementById("outputContainer");
  if (!outputContainer) return;

  const card = document.createElement("div");
  card.id = `turnCard-${turn}`;
  card.className = "bg-slate-900 border border-slate-800 rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-xl transition space-y-4";
  const title = currentLang === "id" ? `Agen Penulis &bull; Draf ${turn}` : `Writer Agent &bull; Draft ${turn}`;
  const statusLabel = currentLang === "id" ? "Selesai" : "Completed";
  const draftHtml = prepareDraftHtml(draftText, dossier, currentLang);

  card.innerHTML = `
    <div class="flex items-center justify-between mb-2 border-b border-slate-800 pb-3">
      <div class="flex items-center gap-2">
        <span class="w-3 h-3 rounded-full bg-emerald-400"></span>
        <span class="font-bold text-emerald-400 text-sm">${title}</span>
      </div>
      <span class="text-xs bg-emerald-950/80 text-emerald-300 border border-emerald-800/60 px-2.5 py-0.5 rounded-full font-mono">${statusLabel}</span>
    </div>
    ${createReadingToolbarHtml(`writer-${turn}`, currentLang)}
    <div class="markdown-body text-slate-200 text-sm">
      ${draftHtml}
    </div>
  `;
  outputContainer.appendChild(card);

  const docTitle = extractDocumentTitle(draftText, topic);
  activeExportDocument = {
    title: docTitle,
    markdown: draftText,
    html: draftHtml,
    metadata: {
      topic: topic,
      score: null,
      turns: turn,
      difficulty: document.getElementById("readingDifficultySelect")?.value || "undergraduate",
      readingType: document.getElementById("readingTypeSelect")?.value || "literature_review",
      model: document.getElementById("modelSelect")?.value || "gemini-3.8-flash"
    }
  };

  card.querySelector(".download-md-btn")?.addEventListener("click", () => {
    downloadMarkdownFile(draftText, topic);
  });
  card.querySelector(".export-pdf-btn")?.addEventListener("click", () => {
    openPdfExportModal(activeExportDocument);
  });
  card.querySelector(".font-toggle-serif")?.addEventListener("click", () => applyFont("serif"));
  card.querySelector(".font-toggle-sans")?.addEventListener("click", () => applyFont("sans"));
  card.querySelector(".size-toggle-small")?.addEventListener("click", () => applyFontSize("small"));
  card.querySelector(".size-toggle-norm")?.addEventListener("click", () => applyFontSize("normal"));
  card.querySelector(".size-toggle-large")?.addEventListener("click", () => applyFontSize("large"));
  card.querySelector(".zen-mode-btn")?.addEventListener("click", () => {
    openFocusReadingMode(draftHtml, title.replace("&bull;", "•"), draftText);
  });

  initCitationInteractions(card, currentLang);
  syncToolbarFontButtons(currentFont);
  syncToolbarSizeButtons(currentFontSize);
}

export function renderCriticCard(turn, critique, targetScore, currentLang = "en") {
  const outputContainer = document.getElementById("outputContainer");
  if (!outputContainer) return;

  const isApproved = critique.score >= targetScore;
  const card = document.createElement("div");
  card.className = `bg-slate-900 border ${isApproved ? "border-cyan-500/50" : "border-amber-500/40"} rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-xl transition`;
  
  const title = currentLang === "id" ? `Agen Pengkritik &bull; Tinjauan ${turn}` : `Critic Agent &bull; Review ${turn}`;
  const statusText = isApproved 
    ? (currentLang === "id" ? "✓ DISETUJUI" : "✓ APPROVED")
    : (currentLang === "id" ? "⏳ PERLU REVISI" : "⏳ NEEDS REVISION");
  const strengthsHeading = currentLang === "id" ? "Kelebihan / Kekuatan:" : "Strengths:";
  const weaknessesHeading = currentLang === "id" ? "Kelemahan Kritis:" : "Critical Weaknesses:";
  const revisionsHeading = currentLang === "id" ? "Tindakan Perbaikan yang Diperlukan:" : "Required Improvements:";
  const scoreLabel = currentLang === "id" ? "Skor:" : "Score:";
  const targetLabel = currentLang === "id" ? "Target:" : "Target:";

  const strengthsList = (critique.strengths || []).map(s => `<li>${escapeHtml(s)}</li>`).join("");
  const weaknessesList = (critique.weaknesses || []).map(w => `<li>${escapeHtml(w)}</li>`).join("");
  const actionsList = (critique.actionable_revisions || []).map(a => `<li>${escapeHtml(a)}</li>`).join("");

  card.innerHTML = `
    <div class="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
      <div class="flex items-center gap-2">
        <span class="w-3 h-3 rounded-full ${isApproved ? "bg-cyan-400" : "bg-amber-400"}"></span>
        <span class="font-bold ${isApproved ? "text-cyan-400" : "text-amber-400"} text-sm">${title}</span>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-xs font-mono font-semibold ${isApproved ? "text-cyan-300" : "text-amber-300"}">
          ${scoreLabel} <span class="text-sm font-bold">${critique.score.toFixed(1)}</span>/10 <span class="text-[10px] text-slate-400">(${targetLabel} ${targetScore.toFixed(1)})</span>
        </span>
        <span class="text-xs px-2.5 py-0.5 rounded-full font-mono font-semibold ${isApproved ? "bg-cyan-950 text-cyan-300 border border-cyan-800" : "bg-amber-950 text-amber-300 border border-amber-800"}">
          ${statusText}
        </span>
      </div>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-2.5 sm:gap-4 text-xs">
      <div class="bg-slate-950/70 p-3 sm:p-3.5 rounded-xl border border-slate-800/80">
        <div class="font-semibold text-emerald-400 mb-2 flex items-center gap-1.5">
          <span>✓</span> ${strengthsHeading}
        </div>
        <ul class="list-disc list-inside space-y-1 text-slate-300">
          ${strengthsList || `<li>${currentLang === "id" ? "Struktur argumen jelas" : "Clear structure"}</li>`}
        </ul>
      </div>
      <div class="bg-slate-950/70 p-3 sm:p-3.5 rounded-xl border border-slate-800/80">
        <div class="font-semibold text-amber-400 mb-2 flex items-center gap-1.5">
          <span>⚠</span> ${weaknessesHeading}
        </div>
        <ul class="list-disc list-inside space-y-1 text-slate-300">
          ${weaknessesList || `<li>${currentLang === "id" ? "Tidak ada kelemahan besar" : "None identified"}</li>`}
        </ul>
      </div>
      <div class="bg-slate-950/70 p-3 sm:p-3.5 rounded-xl border border-slate-800/80">
        <div class="font-semibold text-cyan-400 mb-2 flex items-center gap-1.5">
          <span>🔧</span> ${revisionsHeading}
        </div>
        <ul class="list-disc list-inside space-y-1 text-slate-300">
          ${actionsList || `<li>${currentLang === "id" ? "Siap dipoles lebih lanjut" : "Ready for polish"}</li>`}
        </ul>
      </div>
    </div>
  `;
  outputContainer.appendChild(card);
}

export function renderDossierCard(dossier, currentLang = "en") {
  const outputContainer = document.getElementById("outputContainer");
  if (!outputContainer || !dossier || !dossier.citations || dossier.citations.length === 0) return;

  const card = document.createElement("div");
  card.id = "finalScholarlyDossierCard";
  card.className = "bg-slate-900 border border-indigo-500/50 rounded-xl sm:rounded-2xl p-4 sm:p-5 shadow-xl transition space-y-3";

  const title = currentLang === "id" 
    ? "Dossier Riset Akademis & Referensi Terverifikasi" 
    : "Verified Academic & Reference Research Dossier";
  const desc = currentLang === "id"
    ? "Agen Penulis dan Pengkritik merujuk langsung pada literatur ilmiah, publikasi peer-review, tinjauan ensiklopedia, dan dokumen terverifikasi ini:"
    : "The Writer and Critic agents are strictly grounded in these verified scholarly preprints, papers, encyclopedic overviews, and documents:";
  const countBadge = currentLang === "id"
    ? `${dossier.citations.length} Sumber Rujukan Aktif`
    : `${dossier.citations.length} Grounding Source(s)`;

  const itemsHtml = dossier.citations.map(c => {
    const safeUrl = isSafeUrl(c.url) ? escapeHtmlAttr(c.url) : "";
    const safeSource = escapeHtml(c.source || "");
    const safeTitle = escapeHtml(c.title || "");
    const safeMeta = escapeHtml(c.meta || "");
    return `
    <div class="flex items-start justify-between gap-3 p-2.5 sm:p-3 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-indigo-500/30 transition">
      <div class="flex-1 min-w-0">
        <div class="flex flex-wrap items-center gap-2 mb-1">
          <span class="text-[10px] font-semibold px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">${safeSource}</span>
          ${safeUrl ? `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="text-xs font-semibold text-cyan-400 hover:underline flex items-center gap-1">${safeTitle} 🔗</a>` : `<span class="text-xs font-semibold text-slate-200">${safeTitle}</span>`}
        </div>
        <div class="text-[11px] text-slate-400 truncate">${safeMeta}</div>
      </div>
    </div>
  `;
  }).join("");

  card.innerHTML = `
    <div class="flex items-center justify-between mb-3 border-b border-slate-800 pb-2.5">
      <div class="flex items-center gap-2">
        <span class="text-lg">📚</span>
        <span class="font-bold text-indigo-300 text-sm">${title}</span>
      </div>
      <span class="text-xs bg-indigo-950 text-indigo-300 border border-indigo-800 px-2.5 py-0.5 rounded-full font-mono">
        ${countBadge}
      </span>
    </div>
    <p class="text-xs text-slate-400 mb-3">
      ${desc}
    </p>
    <div class="space-y-2.5">
      ${itemsHtml}
    </div>
  `;
  outputContainer.appendChild(card);
}

export function renderSourceAuditCard(auditResult, round, currentLang = "en") {
  const outputContainer = document.getElementById("outputContainer");
  if (!outputContainer || !auditResult) return;

  const cardId = `sourceAuditCard-turn-${round}`;
  const existing = document.getElementById(cardId);
  if (existing) existing.remove();

  const isId = currentLang === "id";
  const card = document.createElement("div");
  card.id = cardId;
  card.setAttribute("data-testid", "source-audit-card");
  card.className = `rounded-xl sm:rounded-2xl p-4 sm:p-5 shadow-xl transition space-y-4 border-2 ${
    auditResult.all_yes
      ? "bg-gradient-to-b from-emerald-950/40 to-slate-900 border-emerald-500/80 shadow-emerald-950/20"
      : "bg-gradient-to-b from-amber-950/40 to-slate-900 border-amber-500/80 shadow-amber-950/20"
  }`;

  const title = isId
    ? "Audit Integritas Publikasi (source-checking-guide.md)"
    : "Publication Integrity Audit (source-checking-guide.md)";
  const roundBadge = isId ? `Putaran Audit ${round}` : `Audit Round ${round}`;
  
  const yesCount = (auditResult.items || []).filter(it => it.answer === "YES" || it.answer === "YA").length;
  const totalCount = auditResult.items ? auditResult.items.length : 11;
  
  const bannerTitle = auditResult.all_yes
    ? (isId ? "🛡️ 100% Lolos Integritas Publikasi — Seluruh 11 Kriteria Terverifikasi (YA)" : "🛡️ 100% Publication & Understanding Integrity Clearance — All 11 Guide Criteria Verified (YES)")
    : (isId ? `⚠ Terdeteksi Ketidaksesuaian Integritas (${totalCount - yesCount} Butir) — Agen Penulis Membangun Ulang Teks...` : `⚠ Integrity Discrepancies Detected (${totalCount - yesCount} items) — Writer Agent Rebuilding Draft...`);
  
  const bannerDesc = auditResult.all_yes
    ? (isId 
        ? "Naskah telah diaudit ketat terhadap 3 lapisan: Tipe Sumber & Metadata (Lapisan 1), Kesesuaian Klaim & Tangga Kata Kerja (Lapisan 2), dan Koherensi Argumen Tanpa Lompatan (Lapisan 3)."
        : "The draft was rigorously verified against all 3 layers: Source Type & Metadata (Layer 1), Claim Match & Verb Ladder (Layer 2), and Argument Coherence without Uncited Leaps (Layer 3).")
    : (isId
        ? "Terdapat jawaban 'TIDAK' pada panduan. Sesuai aturan publikasi dan pemahaman integritas, naskah harus ditulis ulang secara mandiri oleh Agen Penulis hingga seluruh jawaban menjadi 'YA'."
        : "One or more guide criteria evaluated to 'NO'. Per publication integrity requirements, the text must be automatically rebuilt by the Writer Agent until all answers are 'YES'.");

  const layer1Items = (auditResult.items || []).filter(it => it.layer === 1);
  const layer2Items = (auditResult.items || []).filter(it => it.layer === 2);
  const layer3Items = (auditResult.items || []).filter(it => it.layer === 3);

  const renderLayerSection = (layerNum, layerTitle, items) => {
    return `
      <div class="bg-slate-950/80 rounded-xl p-3 sm:p-3.5 border border-slate-800">
        <div class="flex items-center justify-between mb-2 pb-1.5 border-b border-slate-800/80">
          <span class="text-xs font-semibold text-slate-200">${layerTitle}</span>
          <span class="text-[10px] font-mono px-2 py-0.5 rounded ${
            items.every(it => it.answer === "YES" || it.answer === "YA")
              ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
              : "bg-amber-950 text-amber-300 border border-amber-800"
          }">
            ${items.filter(it => it.answer === "YES" || it.answer === "YA").length} / ${items.length} ${isId ? "Lolos" : "Passed"}
          </span>
        </div>
        <div class="space-y-2">
          ${items.map(it => {
            const passed = it.answer === "YES" || it.answer === "YA";
            return `
              <div class="p-2 sm:p-2.5 rounded-lg ${passed ? "bg-slate-900/40 border border-emerald-900/30" : "bg-rose-950/20 border border-rose-900/40"} transition">
                <div class="flex items-start justify-between gap-2">
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-1.5 flex-wrap">
                      <span class="text-[11px] font-semibold text-slate-200">${it.title}</span>
                      <span class="text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold ${passed ? "bg-emerald-950 text-emerald-300 border border-emerald-800" : "bg-rose-950 text-rose-300 border border-rose-800"}">
                        ${passed ? (isId ? "✓ YA" : "✓ YES") : (isId ? "⚠ TIDAK" : "⚠ NO")}
                      </span>
                    </div>
                    <div class="text-[10px] text-slate-400 mt-0.5">${escapeHtml(it.question)}</div>
                    ${it.reason ? `<div class="text-[11px] text-slate-300 mt-1 pl-2 border-l-2 ${passed ? "border-emerald-700/60" : "border-rose-700"}">${escapeHtml(it.reason)}</div>` : ""}
                    ${it.offending_text ? `<div class="text-[10px] font-mono text-amber-300 bg-amber-950/40 p-1.5 rounded mt-1.5 border border-amber-900/50"><strong>${isId ? "Kutipan Discrepancy:" : "Discrepancy Passage:"}</strong> "${escapeHtml(it.offending_text)}"</div>` : ""}
                  </div>
                </div>
              </div>
            `;
          }).join("")}
        </div>
      </div>
    `;
  };

  const failureTagsHtml = (auditResult.failure_patterns_detected && auditResult.failure_patterns_detected.length > 0)
    ? `
      <div class="bg-rose-950/30 border border-rose-800/60 rounded-xl p-3 text-xs space-y-1.5">
        <span class="font-semibold text-rose-300 flex items-center gap-1">
          <span>⚠</span> ${isId ? "Pola Kegagalan Terdeteksi (Perlu Diperbaiki):" : "Failure Patterns Detected (Targeted for Rebuild):"}
        </span>
        <div class="flex flex-wrap gap-1.5 pt-1">
          ${auditResult.failure_patterns_detected.map(p => `
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-rose-900/50 text-rose-200 border border-rose-700 font-mono">${escapeHtml(p)}</span>
          `).join("")}
        </div>
      </div>
    `
    : "";

  card.innerHTML = `
    <div class="flex items-center justify-between mb-1 pb-2 border-b border-slate-800 flex-wrap gap-2">
      <div class="flex items-center gap-2">
        <span class="text-lg">🛡️</span>
        <span class="font-bold text-slate-100 text-sm sm:text-base">${title}</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-xs font-mono px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
          ${roundBadge}
        </span>
        <span class="text-xs font-mono font-bold px-2.5 py-0.5 rounded-full ${
          auditResult.all_yes 
            ? "bg-emerald-950 text-emerald-300 border border-emerald-700" 
            : "bg-amber-950 text-amber-300 border border-amber-700"
        }">
          ${yesCount} / ${totalCount} YES (${Math.round((yesCount / totalCount) * 100)}%)
        </span>
      </div>
    </div>

    <div class="rounded-xl p-3 sm:p-3.5 border ${
      auditResult.all_yes
        ? "bg-emerald-950/50 border-emerald-600/70 text-emerald-100"
        : "bg-amber-950/50 border-amber-600/70 text-amber-100"
    }">
      <div class="font-bold text-xs sm:text-sm flex items-center gap-1.5 mb-1">
        ${bannerTitle}
      </div>
      <div class="text-[11px] sm:text-xs text-slate-300 leading-relaxed">
        ${bannerDesc}
      </div>
    </div>

    ${failureTagsHtml}

    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
      ${renderLayerSection(1, isId ? "Lapisan 1: Apa Sumber Ini?" : "Layer 1: What Is This Source?", layer1Items)}
      ${renderLayerSection(2, isId ? "Lapisan 2: Kesesuaian Klaim & Tangga Verba" : "Layer 2: Claim Match & Verb Ladder", layer2Items)}
      ${renderLayerSection(3, isId ? "Lapisan 3: Ketahanan Argumen Utuh" : "Layer 3: Whole Argument Integrity", layer3Items)}
    </div>
  `;

  outputContainer.appendChild(card);
}

export function renderFinalApprovedCard(finalDraft, score, turns, dossier = null, difficulty = "undergraduate", readingType = "literature_review", auditResult = null, currentLang = "en", topic = "") {
  const outputContainer = document.getElementById("outputContainer");
  if (!outputContainer) return;

  const existing = document.getElementById("finalApprovedCard");
  if (existing) existing.remove();

  const card = document.createElement("div");
  card.id = "finalApprovedCard";
  card.className = "bg-gradient-to-b from-cyan-950/40 to-slate-900 border-2 border-cyan-400/80 rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-2xl transition";
  const title = currentLang === "id" ? "Hasil Akhir Disetujui" : "Final Polish Approved";
  const copyBtnText = currentLang === "id" ? "📋 Salin Markdown" : "📋 Copy Markdown";
  const downloadMDBtnText = currentLang === "id" ? "Unduh Markdown" : "Download Markdown";
  const exportPdfBtnText = currentLang === "id" ? "Ekspor PDF" : "Export PDF";
  const scoreLabel = currentLang === "id" ? "Skor Akhir:" : "Final Score:";
  const turnsLabel = currentLang === "id" ? "Selesai dalam:" : "Completed in:";
  const turnsUnit = currentLang === "id" ? "putaran" : "turn(s)";
  const draftHtml = prepareDraftHtml(finalDraft, dossier, currentLang);

  const finalDocTitle = extractDocumentTitle(finalDraft, topic);
  activeExportDocument = {
    title: finalDocTitle,
    markdown: finalDraft,
    html: draftHtml,
    metadata: {
      topic: topic,
      score: score,
      turns: turns,
      difficulty: difficulty,
      readingType: readingType,
      model: document.getElementById("modelSelect")?.value || "gemini-3.8-flash",
      auditResult: auditResult
    }
  };

  card.innerHTML = `
    <div class="flex items-center justify-between mb-2 border-b border-cyan-800/60 pb-3 flex-wrap gap-2">
      <div class="flex items-center gap-2 flex-wrap">
        <span class="text-xl">🏆</span>
        <span class="font-bold text-cyan-300 text-base">${title}</span>
        ${auditResult?.all_yes ? `<span id="finalIntegrityBadge" class="text-[11px] bg-emerald-950 text-emerald-300 border border-emerald-700 px-2.5 py-0.5 rounded-full font-semibold flex items-center gap-1 shadow-sm">🛡️ 100% Publication Integrity Verified</span>` : ""}
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <button id="copyArtifactBtn" class="text-xs bg-cyan-950/70 hover:bg-cyan-900 text-cyan-200 border border-cyan-700 px-3 py-1.5 rounded-lg transition">
          ${copyBtnText}
        </button>
        <button id="downloadMDBtn" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-600 px-3 py-1.5 rounded-lg transition inline-flex items-center gap-1 font-medium shadow-sm">
          <span>📥</span>
          <span>${downloadMDBtnText}</span>
        </button>
        <button id="exportPdfBtn" class="text-xs bg-cyan-600 hover:bg-cyan-500 text-white font-semibold px-3 py-1.5 rounded-lg transition inline-flex items-center gap-1 shadow-md shadow-cyan-900/40">
          <span>📄</span>
          <span>${exportPdfBtnText}</span>
        </button>
      </div>
    </div>
    <div class="text-xs text-slate-400 mb-2 flex items-center flex-wrap gap-2 sm:gap-4">
      <span>${scoreLabel} <strong class="text-emerald-400 font-mono">${score.toFixed(1)}/10</strong></span>
      <span>${turnsLabel} <strong class="text-slate-200 font-mono">${turns} ${turnsUnit}</strong></span>
      <span class="text-[11px] px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800">🎯 ${getDifficultyLabel(difficulty, currentLang === "id")}</span>
      <span class="text-[11px] px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800">📚 ${getReadingTypeLabel(readingType, currentLang === "id")}</span>
      ${auditResult?.all_yes ? `<span class="text-[11px] px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800">🛡️ source-checking-guide: 11/11 YES</span>` : ""}
    </div>
    ${createReadingToolbarHtml("final-approved", currentLang)}
    <div class="markdown-body text-slate-100 text-sm">
      ${draftHtml}
    </div>
  `;
  outputContainer.prepend(card);

  const copyBtn = card.querySelector("#copyArtifactBtn");
  copyBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(finalDraft).then(() => {
      copyBtn.textContent = currentLang === "id" ? "✓ Tersalin!" : "✓ Copied!";
      setTimeout(() => copyBtn.textContent = copyBtnText, 2000);
    });
  });

  const dlMdBtn = card.querySelector("#downloadMDBtn");
  if (dlMdBtn) {
    dlMdBtn.addEventListener("click", () => {
      downloadMarkdownFile(finalDraft, topic);
    });
  }

  const exportPdfBtn = card.querySelector("#exportPdfBtn");
  if (exportPdfBtn) {
    exportPdfBtn.addEventListener("click", () => {
      openPdfExportModal(activeExportDocument);
    });
  }

  card.querySelector(".download-md-btn")?.addEventListener("click", () => {
    downloadMarkdownFile(finalDraft, topic);
  });
  card.querySelector(".export-pdf-btn")?.addEventListener("click", () => {
    openPdfExportModal(activeExportDocument);
  });
  card.querySelector(".font-toggle-serif")?.addEventListener("click", () => applyFont("serif"));
  card.querySelector(".font-toggle-sans")?.addEventListener("click", () => applyFont("sans"));
  card.querySelector(".size-toggle-small")?.addEventListener("click", () => applyFontSize("small"));
  card.querySelector(".size-toggle-norm")?.addEventListener("click", () => applyFontSize("normal"));
  card.querySelector(".size-toggle-large")?.addEventListener("click", () => applyFontSize("large"));
  card.querySelector(".zen-mode-btn")?.addEventListener("click", () => {
    openFocusReadingMode(draftHtml, title, finalDraft);
  });

  initCitationInteractions(card, currentLang);
  syncToolbarFontButtons(currentFont);
  syncToolbarSizeButtons(currentFontSize);
}
