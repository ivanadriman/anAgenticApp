/**
 * Gemini Agentic Studio - Application Orchestrator & Entry Point
 * Native ES Module (No Build Step Required)
 */

import {
  STORAGE_KEY,
  LANG_STORAGE_KEY,
  ALL_MODELS,
  I18N,
  getModelDisplayName,
  getDifficultyLabel,
  getReadingTypeLabel
} from "./config.js";

import {
  configureMarked,
  escapeHtml,
  escapeHtmlAttr,
  isSafeUrl
} from "./security.js";

import {
  buildTextFragmentUrl,
  runDeterministicSanityChecks
} from "./text-fragments.js";

import {
  resolveMultilingualQueries,
  fetchArxivPapers,
  fetchCrossrefPapers,
  fetchSemanticScholarPapers,
  fetchOpenAlexWorks,
  fetchPubMedWorks,
  fetchWikipediaSummary,
  extractPdfText
} from "./fetchers.js";

import {
  callGemini,
  checkAllModelQuotas,
  probeGoogleSearchAvailability,
  runWriterDraft,
  runWriterRevision,
  runCriticReview,
  runSourceCheckingAudit,
  runWriterIntegrityRevision
} from "./gemini.js";

import {
  applyTheme,
  applyFont,
  applyFontSize,
  syncToolbarFontButtons,
  syncToolbarSizeButtons,
  openCitationInspector,
  closeCitationDrawer,
  initCitationInteractions,
  openFocusReadingMode,
  closeFocusReadingMode,
  openPdfExportModal,
  closePdfExportModal,
  getPdfExportOptions,
  printDocumentViaIframe,
  downloadDocumentAsPdf,
  downloadMarkdownFile,
  prepareDraftHtml,
  renderWriterCard,
  renderCriticCard,
  renderDossierCard,
  renderSourceAuditCard,
  renderFinalApprovedCard,
  initGlobalUIControls,
  activeExportDocument,
  currentTheme,
  currentFont,
  currentFontSize
} from "./ui.js";

// Initialize Marked configuration
configureMarked();

// Initialize PDF.js worker if library is present
if (typeof window !== "undefined" && window.pdfjsLib) {
  window.pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
}

// Global App State
let currentLang = (typeof localStorage !== "undefined" && localStorage.getItem(LANG_STORAGE_KEY)) || "en";
let uploadedDocument = null;

// DOM Element References
const langEnBtn = document.getElementById("langEnBtn");
const langIdBtn = document.getElementById("langIdBtn");
const apiKeyInput = document.getElementById("apiKeyInput");
const saveKeyBtn = document.getElementById("saveKeyBtn");
const toggleKeyVisibility = document.getElementById("toggleKeyVisibility");
const topicInput = document.getElementById("topicInput");
const modelSelect = document.getElementById("modelSelect");
const maxTurnsSelect = document.getElementById("maxTurnsSelect");
const targetScoreInput = document.getElementById("targetScoreInput");
const startPipelineBtn = document.getElementById("startPipelineBtn");
const startBtnText = document.getElementById("startBtnText");
const statusCard = document.getElementById("statusCard");
const statusText = document.getElementById("statusText");
const statusSpinner = document.getElementById("statusSpinner");
const stepCounter = document.getElementById("stepCounter");
const outputContainer = document.getElementById("outputContainer");

// Grounding Checkboxes
const arxivCheck = document.getElementById("arxivCheck");
const crossrefCheck = document.getElementById("crossrefCheck");
const semanticScholarCheck = document.getElementById("semanticScholarCheck");
const openAlexCheck = document.getElementById("openAlexCheck");
const pubmedCheck = document.getElementById("pubmedCheck");
const wikipediaCheck = document.getElementById("wikipediaCheck");
const docFileInput = document.getElementById("docFileInput");
const uploadDocBtn = document.getElementById("uploadDocBtn");
const docFileStatus = document.getElementById("docFileStatus");
const clearDocBtn = document.getElementById("clearDocBtn");

const checkQuotaBtn = document.getElementById("checkQuotaBtn");
const quotaStatusText = document.getElementById("quotaStatusText");

function updateHeaderPoweredBadge(modelId = null) {
  const selectedId = modelId || (modelSelect ? modelSelect.value : "gemini-3.8-flash");
  const modelName = getModelDisplayName(selectedId);
  const badgeEl = document.getElementById("headerPoweredBadge");
  if (!badgeEl) return;
  const prefix = currentLang === "id" ? "Didukung oleh:" : "Powered by:";
  badgeEl.innerHTML = `${prefix} <strong>${modelName}</strong>`;
}

function updateApiKeyCardState(hasKey) {
  const stateBadge = document.getElementById("apiKeySavedStateBadge");
  const formRow = document.getElementById("apiKeyFormRow");
  if (!stateBadge || !formRow) return;

  if (hasKey) {
    stateBadge.classList.remove("hidden");
    formRow.classList.add("hidden");
  } else {
    stateBadge.classList.add("hidden");
    formRow.classList.remove("hidden");
  }
}

function updateActiveSourcesUI() {
  const sources = [arxivCheck, semanticScholarCheck, pubmedCheck, openAlexCheck, crossrefCheck, wikipediaCheck];
  let active = 0;
  sources.forEach(box => {
    if (box && box.checked) active++;
  });
  const badge = document.getElementById("activeSourcesCountBadge");
  if (badge) {
    const unit = currentLang === "id" ? "aktif" : "active";
    badge.textContent = `${active} ${unit}`;
  }
}

function updateAdvancedOptionsSummary() {
  const badge = document.getElementById("advancedOptionsSummaryBadge");
  if (!badge) return;
  const isId = currentLang === "id";
  const diffEl = document.getElementById("readingDifficultySelect");
  const typeEl = document.getElementById("readingTypeSelect");
  const thinkingEl = document.getElementById("thinkingLevelSelect");
  const turnsEl = document.getElementById("maxTurnsSelect");
  const scoreEl = document.getElementById("targetScoreInput");
  const searchEl = document.getElementById("webSearchCheck");
  const auditEl = document.getElementById("strictSourceAuditCheck");

  const diff = diffEl?.value || "undergraduate";
  const type = typeEl?.value || "literature_review";
  const thinking = thinkingEl?.value || "medium";
  const turns = turnsEl?.value || "3";
  const score = scoreEl?.value || "9.5";
  const search = searchEl?.checked || false;
  const audit = auditEl?.checked ?? true;

  const diffMap = isId 
    ? { layman: "Awam", undergraduate: "Sarjana", expert: "Pakar", executive: "Eksekutif" }
    : { layman: "Layman", undergraduate: "Undergrad", expert: "Expert", executive: "Executive" };

  const typeMap = isId 
    ? { literature_review: "Lit Review", deep_dive_essay: "Esai", textbook_chapter: "Buku Teks", technical_whitepaper: "Whitepaper", executive_brief: "Brief" }
    : { literature_review: "Lit Review", deep_dive_essay: "Essay", textbook_chapter: "Textbook", technical_whitepaper: "Whitepaper", executive_brief: "Brief" };

  const thinkingMap = isId 
    ? { low: "Cepat", medium: "Sedang", high: "Mendalam" }
    : { low: "Fast", medium: "Medium", high: "Deep" };
  const turnsUnit = isId ? "Putaran" : "Turns";
  
  let parts = [
    `🎯 ${diffMap[diff] || diff}`,
    `📚 ${typeMap[type] || type}`,
    `🧠 ${thinkingMap[thinking] || thinking}`,
    `${turns} ${turnsUnit}`,
    `Target ${score}`
  ];
  if (search) parts.push("🌐 Search");
  if (audit) parts.push(isId ? "🛡️ Audit Panduan" : "🛡️ Guide Audit");
  badge.textContent = parts.join(" • ");
}

export function applyLanguage(lang) {
  currentLang = lang;
  if (typeof localStorage !== "undefined") {
    localStorage.setItem(LANG_STORAGE_KEY, lang);
  }
  const t = I18N[lang] || I18N.en;

  if (lang === "id") {
    if (langIdBtn) langIdBtn.className = "px-2.5 py-1 text-xs rounded-lg font-semibold transition bg-cyan-500/20 text-cyan-400 border border-cyan-500/40";
    if (langEnBtn) langEnBtn.className = "px-2.5 py-1 text-xs rounded-lg font-semibold transition text-slate-400 hover:text-slate-200 border border-transparent";
  } else {
    if (langEnBtn) langEnBtn.className = "px-2.5 py-1 text-xs rounded-lg font-semibold transition bg-cyan-500/20 text-cyan-400 border border-cyan-500/40";
    if (langIdBtn) langIdBtn.className = "px-2.5 py-1 text-xs rounded-lg font-semibold transition text-slate-400 hover:text-slate-200 border border-transparent";
  }

  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (t[key]) el.textContent = t[key];
  });

  document.querySelectorAll("[data-i18n-html]").forEach(el => {
    const key = el.getAttribute("data-i18n-html");
    if (t[key]) el.innerHTML = t[key];
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (t[key]) el.placeholder = t[key];
  });

  const optDiffLayman = document.getElementById("optDiffLayman");
  const optDiffUndergrad = document.getElementById("optDiffUndergrad");
  const optDiffExpert = document.getElementById("optDiffExpert");
  const optDiffExec = document.getElementById("optDiffExec");
  if (optDiffLayman) optDiffLayman.textContent = t.optDiffLayman;
  if (optDiffUndergrad) optDiffUndergrad.textContent = t.optDiffUndergrad;
  if (optDiffExpert) optDiffExpert.textContent = t.optDiffExpert;
  if (optDiffExec) optDiffExec.textContent = t.optDiffExec;

  const optTypeReview = document.getElementById("optTypeReview");
  const optTypeEssay = document.getElementById("optTypeEssay");
  const optTypeTextbook = document.getElementById("optTypeTextbook");
  const optTypeWhitepaper = document.getElementById("optTypeWhitepaper");
  const optTypeBrief = document.getElementById("optTypeBrief");
  if (optTypeReview) optTypeReview.textContent = t.optTypeReview;
  if (optTypeEssay) optTypeEssay.textContent = t.optTypeEssay;
  if (optTypeTextbook) optTypeTextbook.textContent = t.optTypeTextbook;
  if (optTypeWhitepaper) optTypeWhitepaper.textContent = t.optTypeWhitepaper;
  if (optTypeBrief) optTypeBrief.textContent = t.optTypeBrief;

  const optLow = document.getElementById("optThinkingLow");
  const optMed = document.getElementById("optThinkingMed");
  const optHigh = document.getElementById("optThinkingHigh");
  if (optLow) optLow.textContent = t.optThinkingLow;
  if (optMed) optMed.textContent = t.optThinkingMed;
  if (optHigh) optHigh.textContent = t.optThinkingHigh;

  const optT1 = document.getElementById("optTurn1");
  const optT2 = document.getElementById("optTurn2");
  const optT3 = document.getElementById("optTurn3");
  if (optT1) optT1.textContent = t.optTurn1;
  if (optT2) optT2.textContent = t.optTurn2;
  if (optT3) optT3.textContent = t.optTurn3;

  // PDF Export Modal translations
  const pdfModalHeading = document.getElementById("pdfModalHeading");
  const pdfModalSubheading = document.getElementById("pdfModalSubheading");
  const pdfPaperSizeLabel = document.getElementById("pdfPaperSizeLabel");
  const pdfOrientationLabel = document.getElementById("pdfOrientationLabel");
  const pdfMarginsLabel = document.getElementById("pdfMarginsLabel");
  const pdfFontLabel = document.getElementById("pdfFontLabel");
  const pdfFontSizeLabel = document.getElementById("pdfFontSizeLabel");
  const pdfIncludeHeaderLabel = document.getElementById("pdfIncludeHeaderLabel");
  const pdfAvoidBreaksLabel = document.getElementById("pdfAvoidBreaksLabel");
  const cancelPdfModalBtn = document.getElementById("cancelPdfModalBtn");
  const pdfPrintVectorBtnText = document.getElementById("pdfPrintVectorBtnText");
  const pdfDownloadDirectBtnText = document.getElementById("pdfDownloadDirectBtnText");

  if (pdfModalHeading) pdfModalHeading.textContent = t.pdfModalTitle;
  if (pdfModalSubheading) pdfModalSubheading.textContent = t.pdfModalSub;
  if (pdfPaperSizeLabel) pdfPaperSizeLabel.textContent = t.pdfPaperSizeLabel;
  if (pdfOrientationLabel) pdfOrientationLabel.textContent = t.pdfOrientationLabel;
  if (pdfMarginsLabel) pdfMarginsLabel.textContent = t.pdfMarginsLabel;
  if (pdfFontLabel) pdfFontLabel.textContent = t.pdfFontLabel;
  if (pdfFontSizeLabel) pdfFontSizeLabel.textContent = t.pdfFontSizeLabel;
  if (pdfIncludeHeaderLabel) pdfIncludeHeaderLabel.textContent = t.pdfIncludeHeaderLabel;
  if (pdfAvoidBreaksLabel) pdfAvoidBreaksLabel.textContent = t.pdfAvoidBreaksLabel;
  if (cancelPdfModalBtn) cancelPdfModalBtn.textContent = t.pdfCancelBtn;
  if (pdfPrintVectorBtnText) pdfPrintVectorBtnText.textContent = t.pdfPrintVectorBtn;
  if (pdfDownloadDirectBtnText) pdfDownloadDirectBtnText.textContent = t.pdfDownloadDirectBtn;

  if (topicInput && (topicInput.value === I18N.en.defaultTopic || topicInput.value === I18N.id.defaultTopic)) {
    topicInput.value = t.defaultTopic;
  }

  if (quotaStatusText && (quotaStatusText.textContent === "Ready" || quotaStatusText.textContent === "Siap")) {
    quotaStatusText.textContent = t.quotaReady;
  }

  updateHeaderPoweredBadge();
  updateAdvancedOptionsSummary();
  applyTheme(currentTheme);
  applyFont(currentFont);
  applyFontSize(currentFontSize);
}

// Progressive Lookup Card UI Builders
function initResearchProgressCard(activeSources, rawTopic, queries = {}) {
  const card = document.createElement("div");
  card.id = "liveResearchProgressCard";
  card.className = "bg-slate-900 border border-cyan-500/50 rounded-2xl p-5 shadow-2xl transition space-y-4";
  
  const rowsHtml = activeSources.map(s => `
    <div id="prog-row-${s.id}" class="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 transition">
      <div class="flex items-center justify-between mb-1.5">
        <div class="flex items-center gap-2">
          <span id="prog-dot-${s.id}" class="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping"></span>
          <span class="font-bold text-xs text-slate-100">${s.name}</span>
        </div>
        <span id="prog-badge-${s.id}" class="text-[10px] font-mono px-2.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/80">
          ${currentLang === "id" ? "⏳ Sedang mencari..." : "⏳ Searching..."}
        </span>
      </div>
      <div id="prog-msg-${s.id}" class="text-[11px] text-slate-400">
        ${currentLang === "id" ? "Menghubungkan ke repositori..." : "Initializing connection..."}
      </div>
      <div id="prog-list-${s.id}" class="mt-2.5 pt-2 border-t border-slate-800/60 hidden space-y-1.5"></div>
    </div>
  `).join("");

  const title = currentLang === "id" 
    ? "Progres Penelusuran Riset & Literatur Ilmiah Langsung" 
    : "Live Research & Literature Grounding Progress";
  const subtitle = currentLang === "id"
    ? "Menelusuri basis data akademis global &bull; Pembaruan pencarian multi-bahasa waktu nyata"
    : "Querying scholarly databases &bull; Real-time multilingual lookup progression";
  const initialCounter = currentLang === "id"
    ? `0 / ${activeSources.length} Selesai`
    : `0 / ${activeSources.length} Completed`;
  const topicLabel = currentLang === "id" ? "Topik Riset:" : "Search query:";
  const activeCountLabel = currentLang === "id" ? `${activeSources.length} sumber aktif` : `${activeSources.length} sources enabled`;
  const globalQuery = queries.global || rawTopic;

  card.innerHTML = `
    <div class="flex items-center justify-between border-b border-slate-800 pb-3">
      <div class="flex items-center gap-2.5">
        <span class="text-xl">🔍</span>
        <div>
          <div class="font-bold text-cyan-300 text-sm">${title}</div>
          <div class="text-[10px] text-slate-400">${subtitle}</div>
        </div>
      </div>
      <span id="researchProgressCounter" class="text-xs bg-slate-800 text-slate-300 border border-slate-700 px-3 py-1 rounded-full font-mono font-medium">
        ${initialCounter}
      </span>
    </div>
    <div class="text-xs text-slate-300 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
      <div>
        <span>${topicLabel} <strong class="text-cyan-300 font-mono">"${rawTopic}"</strong></span>
        ${globalQuery && globalQuery.toLowerCase() !== rawTopic.toLowerCase() ? `<span class="block sm:inline sm:ml-2 text-[11px] text-emerald-400 font-mono">🌐 ${currentLang === "id" ? "Penelusuran Global (STEM / Semua Bahasa)" : "Global STEM Search"}: "${globalQuery}"</span>` : `<span class="block sm:inline sm:ml-2 text-[11px] text-cyan-400 font-mono">🌐 ${currentLang === "id" ? "Penelusuran Literatur Global" : "Global Literature Search"}</span>`}
      </div>
      <span class="text-[10px] text-slate-400 font-mono whitespace-nowrap">${activeCountLabel}</span>
    </div>
    <div class="space-y-2.5">
      ${rowsHtml}
    </div>
  `;

  if (outputContainer) outputContainer.appendChild(card);
  return card;
}

function updateSourceProgressUI(sourceId, status, message, items = []) {
  const dot = document.getElementById(`prog-dot-${sourceId}`);
  const badge = document.getElementById(`prog-badge-${sourceId}`);
  const msg = document.getElementById(`prog-msg-${sourceId}`);
  const list = document.getElementById(`prog-list-${sourceId}`);
  if (!badge || !msg) return;

  if (status === "searching") {
    if (dot) { dot.className = "w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping"; }
    badge.className = "text-[10px] font-mono px-2.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/80";
    badge.textContent = currentLang === "id" ? "⏳ Sedang mencari..." : "⏳ Searching...";
    msg.textContent = message;
  } else if (status === "done") {
    if (dot) { dot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400"; }
    badge.className = "text-[10px] font-mono px-2.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/80";
    badge.textContent = message;
    msg.textContent = currentLang === "id" ? `Ditemukan ${items.length} catatan ilmiah relevan:` : `Found ${items.length} relevant record(s):`;

    if (list && items.length > 0) {
      list.classList.remove("hidden");
      list.innerHTML = items.map(it => {
        const safeUrl = isSafeUrl(it.url) ? escapeHtmlAttr(it.url) : "";
        const safeTitle = escapeHtml(it.title || "");
        const safeMeta = escapeHtml(it.meta || it.authors || "");
        return `
        <div class="flex items-start justify-between gap-2 text-xs bg-slate-900/60 p-2 rounded-lg border border-slate-800/60">
          <div class="flex-1 min-w-0">
            <div class="font-medium text-slate-200 truncate">
              ${safeUrl ? `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="text-cyan-400 hover:underline">📄 ${safeTitle}</a>` : `📄 ${safeTitle}`}
            </div>
            <div class="text-[10px] text-slate-400 mt-0.5 truncate">${safeMeta}</div>
          </div>
          ${safeUrl ? `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="text-[10px] text-slate-400 hover:text-cyan-300 whitespace-nowrap">🔗 Open</a>` : ""}
        </div>
      `;
      }).join("");
    }
  } else if (status === "empty") {
    if (dot) { dot.className = "w-2.5 h-2.5 rounded-full bg-slate-500"; }
    badge.className = "text-[10px] font-mono px-2.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700";
    badge.textContent = currentLang === "id" ? "✕ Tidak ditemukan" : "✕ None found";
    msg.textContent = message;
  }
}

async function collectScholarlyDossier(rawTopic, queries) {
  const activeSources = [];
  if (arxivCheck?.checked) activeSources.push({ id: "arxiv", name: "📚 arXiv API" });
  if (semanticScholarCheck?.checked) activeSources.push({ id: "semantic", name: "🔬 Semantic Scholar API" });
  if (pubmedCheck?.checked) activeSources.push({ id: "pubmed", name: "🧬 PubMed / Europe PMC" });
  if (openAlexCheck?.checked) activeSources.push({ id: "openalex", name: "🏛️ OpenAlex API" });
  if (crossrefCheck?.checked) activeSources.push({ id: "crossref", name: "🏷️ Crossref API" });
  if (wikipediaCheck?.checked) activeSources.push({ id: "wikipedia", name: "📖 Wikipedia Reference" });
  if (uploadedDocument) activeSources.push({ id: "doc", name: `📄 ${currentLang === "id" ? "Dokumen Lokal" : "Local Document"}: ${uploadedDocument.name}` });

  if (activeSources.length === 0) return null;

  initResearchProgressCard(activeSources, rawTopic, queries);
  const counterEl = document.getElementById("researchProgressCounter");

  let completedCount = 0;
  let sourceNum = 1;
  const citationList = [];
  let dossierMarkdown = currentLang === "id" 
    ? "## VERIFIED SCHOLARLY RESEARCH & REFERENCE DOSSIER (MULTI-BAHASA)\n\n"
    : "## VERIFIED SCHOLARLY RESEARCH & REFERENCE DOSSIER\n\n";

  for (const s of activeSources) {
    if (s.id === "arxiv") {
      const items = await fetchArxivPapers(queries, (st, msg, its) => updateSourceProgressUI("arxiv", st, msg, its), currentLang);
      if (items.length > 0) {
        dossierMarkdown += "### 📚 arXiv API:\n";
        items.forEach(p => {
          dossierMarkdown += `[Source ${sourceNum}] arXiv: "${p.title}" (${p.year})\n`;
          dossierMarkdown += `  Authors: ${p.authors}\n`;
          dossierMarkdown += `  Link: ${p.url}\n`;
          if (p.abstract) {
            dossierMarkdown += `  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  """\n  ${p.abstract}\n  """\n`;
          } else {
            dossierMarkdown += `  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [${sourceNum}].]\n`;
          }
          dossierMarkdown += "\n";
          citationList.push({ num: sourceNum, title: p.title, url: p.url, source: "arXiv API", authors: p.authors, year: p.year, meta: `${p.authors} (${p.year})`, abstract: p.abstract || "" });
          sourceNum++;
        });
      }
    } else if (s.id === "semantic") {
      const items = await fetchSemanticScholarPapers(queries, (st, msg, its) => updateSourceProgressUI("semantic", st, msg, its), currentLang);
      if (items.length > 0) {
        dossierMarkdown += "### 🔬 Semantic Scholar API:\n";
        items.forEach(p => {
          dossierMarkdown += `[Source ${sourceNum}] Semantic Scholar: "${p.title}" (${p.year})\n`;
          dossierMarkdown += `  Authors: ${p.authors}\n`;
          dossierMarkdown += `  Citations: ${p.citations}\n`;
          dossierMarkdown += `  Link/DOI: ${p.url}\n`;
          if (p.abstract) {
            dossierMarkdown += `  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  """\n  ${p.abstract}\n  """\n`;
          } else {
            dossierMarkdown += `  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [${sourceNum}].]\n`;
          }
          dossierMarkdown += "\n";
          citationList.push({ num: sourceNum, title: p.title, url: p.url, source: "Semantic Scholar API", authors: p.authors, year: p.year, meta: p.meta, abstract: p.abstract || "" });
          sourceNum++;
        });
      }
    } else if (s.id === "pubmed") {
      const items = await fetchPubMedWorks(queries, (st, msg, its) => updateSourceProgressUI("pubmed", st, msg, its), currentLang);
      if (items.length > 0) {
        dossierMarkdown += "### 🧬 PubMed / Europe PMC:\n";
        items.forEach(p => {
          dossierMarkdown += `[Source ${sourceNum}] PubMed/PMC: "${p.title}" (${p.year})\n`;
          dossierMarkdown += `  Authors: ${p.authors}\n`;
          dossierMarkdown += `  Article Link: ${p.url}\n`;
          if (p.abstract) {
            dossierMarkdown += `  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  """\n  ${p.abstract}\n  """\n`;
          } else {
            dossierMarkdown += `  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [${sourceNum}].]\n`;
          }
          dossierMarkdown += "\n";
          citationList.push({ num: sourceNum, title: p.title, url: p.url, source: "PubMed / Europe PMC", authors: p.authors, year: p.year, meta: p.meta, abstract: p.abstract || "" });
          sourceNum++;
        });
      }
    } else if (s.id === "openalex") {
      const items = await fetchOpenAlexWorks(queries, (st, msg, its) => updateSourceProgressUI("openalex", st, msg, its), currentLang);
      if (items.length > 0) {
        dossierMarkdown += "### 🏛️ OpenAlex API:\n";
        items.forEach(p => {
          dossierMarkdown += `[Source ${sourceNum}] OpenAlex: "${p.title}" (${p.year})\n`;
          dossierMarkdown += `  Venue: ${p.venue}\n`;
          dossierMarkdown += `  Authors: ${p.authors}\n`;
          dossierMarkdown += `  DOI/Link: ${p.url}\n`;
          if (p.abstract) {
            dossierMarkdown += `  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  """\n  ${p.abstract}\n  """\n`;
          } else {
            dossierMarkdown += `  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [${sourceNum}].]\n`;
          }
          dossierMarkdown += "\n";
          citationList.push({ num: sourceNum, title: p.title, url: p.url, source: p.source || "OpenAlex API", authors: p.authors, year: p.year, meta: p.meta, abstract: p.abstract || "" });
          sourceNum++;
        });
      }
    } else if (s.id === "crossref") {
      const items = await fetchCrossrefPapers(queries, (st, msg, its) => updateSourceProgressUI("crossref", st, msg, its), currentLang);
      if (items.length > 0) {
        dossierMarkdown += "### 🏷️ Crossref API:\n";
        items.forEach(p => {
          dossierMarkdown += `[Source ${sourceNum}] Crossref: "${p.title}" (${p.year})\n`;
          dossierMarkdown += `  Authors: ${p.authors}\n`;
          dossierMarkdown += `  DOI/Link: ${p.url}\n`;
          if (p.abstract) {
            dossierMarkdown += `  Verbatim Excerpt / Abstract (FOR EXACT CTRL+F QUOTING):\n  """\n  ${p.abstract}\n  """\n`;
          } else {
            dossierMarkdown += `  [Bibliographic Metadata Only - No Excerpt Available. Do NOT invent/fabricate a quotation. Cite purely as bibliographic attribution [${sourceNum}].]\n`;
          }
          dossierMarkdown += "\n";
          citationList.push({ num: sourceNum, title: p.title, url: p.url, source: "Crossref API", authors: p.authors, year: p.year, meta: p.meta, abstract: p.abstract || "" });
          sourceNum++;
        });
      }
    } else if (s.id === "wikipedia") {
      const wikiItems = await fetchWikipediaSummary(queries, (st, msg, its) => updateSourceProgressUI("wikipedia", st, msg, its), currentLang);
      if (wikiItems && wikiItems.length > 0) {
        wikiItems.forEach(item => {
          dossierMarkdown += `[Source ${sourceNum}] ${item.source} (${item.title}):\n`;
          dossierMarkdown += `  Reference URL: ${item.url}\n`;
          dossierMarkdown += `  Verbatim Encyclopedic Text (FOR EXACT CTRL+F QUOTING):\n  """\n  ${item.extract}\n  """\n\n`;
          citationList.push({ num: sourceNum, title: item.title, url: item.url, source: item.source, meta: item.meta, abstract: item.extract });
          sourceNum++;
        });
      }
    } else if (s.id === "doc" && uploadedDocument) {
      updateSourceProgressUI("doc", "done", currentLang === "id" ? `✓ Diproses (${uploadedDocument.charCount.toLocaleString()} karakter)` : `✓ Processed (${uploadedDocument.charCount.toLocaleString()} chars)`, [{ title: uploadedDocument.name, url: "#", meta: currentLang === "id" ? "Dokumen / PDF Lokal" : "Local PDF/Document" }]);
      dossierMarkdown += `[Source ${sourceNum}] User Document (${uploadedDocument.name}):\n`;
      dossierMarkdown += `  Verbatim Document Text (FOR EXACT CTRL+F QUOTING):\n  """\n  ${uploadedDocument.text.slice(0, 6000)}\n  """\n\n`;
      citationList.push({ num: sourceNum, title: uploadedDocument.name, url: "#", source: currentLang === "id" ? "Dokumen Lokal" : "Local Document", meta: `${uploadedDocument.charCount.toLocaleString()} ${currentLang === "id" ? "karakter" : "characters"}`, abstract: uploadedDocument.text.slice(0, 6000) });
      sourceNum++;
    }

    completedCount++;
    if (counterEl) {
      counterEl.textContent = currentLang === "id"
        ? `${completedCount} / ${activeSources.length} Selesai`
        : `${completedCount} / ${activeSources.length} Completed`;
    }
    await new Promise(r => setTimeout(r, 120));
  }

  if (counterEl) {
    counterEl.textContent = currentLang === "id"
      ? `✓ Seluruh ${activeSources.length} Sumber Terkumpul (${citationList.length} referensi)`
      : `✓ All ${activeSources.length} Sources Gathered (${citationList.length} references)`;
    counterEl.className = "text-xs bg-emerald-950 text-emerald-300 border border-emerald-800 px-3 py-1 rounded-full font-mono font-medium";
  }

  if (citationList.length === 0) return null;

  return {
    text: dossierMarkdown,
    citations: citationList
  };
}

// Event Bindings
if (langEnBtn) langEnBtn.addEventListener("click", () => applyLanguage("en"));
if (langIdBtn) langIdBtn.addEventListener("click", () => applyLanguage("id"));

if (modelSelect) {
  modelSelect.addEventListener("change", () => {
    updateHeaderPoweredBadge();
  });
}

// Check Quotas Button
if (checkQuotaBtn) {
  checkQuotaBtn.addEventListener("click", async () => {
    const key = apiKeyInput ? apiKeyInput.value.trim() : "";
    if (!key) {
      alert(currentLang === "id" ? "Masukkan Kunci API Gemini terlebih dahulu." : "Please enter your Gemini API Key first.");
      return;
    }
    if (quotaStatusText) {
      quotaStatusText.textContent = "Checking quotas...";
      quotaStatusText.className = "text-[11px] text-cyan-400 mt-1 animate-pulse";
    }

    const { available, exhausted } = await checkAllModelQuotas(key);
    if (modelSelect) {
      modelSelect.innerHTML = "";
      if (available.length > 0) {
        const availableGroup = document.createElement("optgroup");
        availableGroup.label = "✓ Available Quota";
        available.forEach((m, idx) => {
          const opt = document.createElement("option");
          opt.value = m.id;
          opt.textContent = `✓ ${m.label}`;
          if (idx === 0) opt.selected = true;
          availableGroup.appendChild(opt);
        });
        modelSelect.appendChild(availableGroup);
      }

      if (exhausted.length > 0) {
        const exhaustedGroup = document.createElement("optgroup");
        exhaustedGroup.label = "🔴 Quota Reached (Daily limit)";
        exhausted.forEach(m => {
          const opt = document.createElement("option");
          opt.value = m.id;
          opt.textContent = `✕ ${m.label} (Quota Exceeded)`;
          opt.disabled = true;
          exhaustedGroup.appendChild(opt);
        });
        modelSelect.appendChild(exhaustedGroup);
      }
      updateHeaderPoweredBadge();
    }

    if (available.length > 0) {
      const hasSearch = await probeGoogleSearchAvailability(key, available[0].id);
      const searchBadge = document.getElementById("searchQuotaBadge");
      const searchBox = document.getElementById("webSearchCheck");
      if (searchBox && searchBadge) {
        if (!hasSearch) {
          searchBox.checked = false;
          searchBox.disabled = true;
          searchBadge.classList.remove("hidden");
          searchBadge.textContent = currentLang === "id"
            ? "⚠️ Kuota pencarian web habis (nonaktifkan untuk menjalankan LLM murni)"
            : "⚠️ Search quota reached (uncheck to run pure LLM)";
          searchBadge.className = "text-[10px] text-amber-400 pl-6 block font-medium";
        } else {
          searchBox.disabled = false;
          searchBadge.classList.remove("hidden");
          searchBadge.textContent = currentLang === "id"
            ? "✓ Kuota pencarian web tersedia"
            : "✓ Search quota available";
          searchBadge.className = "text-[10px] text-emerald-400 pl-6 block";
        }
      }
    }

    if (quotaStatusText) {
      if (available.length > 0) {
        quotaStatusText.textContent = `Active models: ${available.length}/${ALL_MODELS.length}`;
        quotaStatusText.className = "text-[11px] text-emerald-400 mt-1 font-semibold";
      } else {
        quotaStatusText.textContent = "All model quotas exhausted for this key.";
        quotaStatusText.className = "text-[11px] text-rose-400 mt-1 font-semibold";
      }
    }
  });
}

// API Key Storage & Handling
if (typeof localStorage !== "undefined") {
  const savedKey = localStorage.getItem(STORAGE_KEY);
  if (savedKey && apiKeyInput) {
    apiKeyInput.value = savedKey;
    updateApiKeyCardState(true);
    checkAllModelQuotas(savedKey).then(({ available }) => {
      if (available.length > 0 && quotaStatusText) {
        quotaStatusText.textContent = `Active models: ${available.length}/${ALL_MODELS.length}`;
        quotaStatusText.className = "text-[11px] text-emerald-400 mt-1 font-semibold";
      }
    });
  }
}

if (toggleKeyVisibility && apiKeyInput) {
  toggleKeyVisibility.addEventListener("click", () => {
    if (apiKeyInput.type === "password") {
      apiKeyInput.type = "text";
      toggleKeyVisibility.textContent = currentLang === "id" ? "Sembunyikan" : "Hide";
    } else {
      apiKeyInput.type = "password";
      toggleKeyVisibility.textContent = currentLang === "id" ? "Lihat" : "Show";
    }
  });
}

if (saveKeyBtn && apiKeyInput) {
  saveKeyBtn.addEventListener("click", () => {
    const key = apiKeyInput.value.trim();
    if (key) {
      localStorage.setItem(STORAGE_KEY, key);
      updateApiKeyCardState(true);
      alert(currentLang === "id" ? "Kunci API berhasil disimpan!" : "API Key saved successfully!");
      if (checkQuotaBtn) checkQuotaBtn.click();
    } else {
      localStorage.removeItem(STORAGE_KEY);
      updateApiKeyCardState(false);
      alert(currentLang === "id" ? "Kunci API dihapus." : "API Key removed.");
    }
  });
}

document.getElementById("editApiKeyBtn")?.addEventListener("click", () => {
  updateApiKeyCardState(false);
  apiKeyInput?.focus();
});

const selectAllSourcesBtn = document.getElementById("selectAllSourcesBtn");
const clearAllSourcesBtn = document.getElementById("clearAllSourcesBtn");
if (selectAllSourcesBtn) {
  selectAllSourcesBtn.addEventListener("click", () => {
    [arxivCheck, semanticScholarCheck, pubmedCheck, openAlexCheck, crossrefCheck, wikipediaCheck].forEach(box => {
      if (box) box.checked = true;
    });
    updateActiveSourcesUI();
  });
}
if (clearAllSourcesBtn) {
  clearAllSourcesBtn.addEventListener("click", () => {
    [arxivCheck, semanticScholarCheck, pubmedCheck, openAlexCheck, crossrefCheck, wikipediaCheck].forEach(box => {
      if (box) box.checked = false;
    });
    updateActiveSourcesUI();
  });
}
[arxivCheck, semanticScholarCheck, pubmedCheck, openAlexCheck, crossrefCheck, wikipediaCheck].forEach(box => {
  box?.addEventListener("change", updateActiveSourcesUI);
});

["readingDifficultySelect", "readingTypeSelect", "thinkingLevelSelect", "maxTurnsSelect", "targetScoreInput", "webSearchCheck", "forceAllTurnsCheck", "strictSourceAuditCheck"].forEach(id => {
  const el = document.getElementById(id);
  el?.addEventListener("change", updateAdvancedOptionsSummary);
  el?.addEventListener("input", updateAdvancedOptionsSummary);
});

const advancedOptionsDetailsEl = document.getElementById("advancedOptionsDetails");
if (advancedOptionsDetailsEl) {
  advancedOptionsDetailsEl.open = window.innerWidth >= 768;
}

// Document Upload Handling
if (uploadDocBtn && docFileInput) {
  uploadDocBtn.addEventListener("click", () => docFileInput.click());
}

if (docFileInput) {
  docFileInput.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (docFileStatus) {
      docFileStatus.textContent = "Parsing document...";
      docFileStatus.className = "text-xs text-cyan-400 truncate max-w-[180px] animate-pulse";
    }

    try {
      const extractedText = await extractPdfText(file);
      const charCount = extractedText.length;
      if (charCount === 0) {
        throw new Error("Document appears empty or contains only scanned images.");
      }

      uploadedDocument = {
        name: file.name,
        text: extractedText,
        charCount: charCount
      };

      if (docFileStatus) {
        docFileStatus.textContent = `✓ ${file.name} (${charCount.toLocaleString()} chars)`;
        docFileStatus.className = "text-xs text-emerald-400 font-medium truncate max-w-[180px]";
      }
      if (clearDocBtn) clearDocBtn.classList.remove("hidden");
    } catch (err) {
      console.error("Document read error:", err);
      alert(`Failed to extract text from document: ${err.message}`);
      if (docFileStatus) {
        docFileStatus.textContent = "Error reading file";
        docFileStatus.className = "text-xs text-rose-400 truncate max-w-[180px]";
      }
    }
  });
}

if (clearDocBtn) {
  clearDocBtn.addEventListener("click", () => {
    uploadedDocument = null;
    if (docFileInput) docFileInput.value = "";
    if (docFileStatus) {
      docFileStatus.textContent = "No document selected";
      docFileStatus.className = "text-xs text-slate-400 truncate max-w-[180px]";
    }
    clearDocBtn.classList.add("hidden");
  });
}

// Modal & Export Button Bindings
document.getElementById("closeCitationDrawerBtn")?.addEventListener("click", closeCitationDrawer);
document.getElementById("citationDrawerBackdrop")?.addEventListener("click", closeCitationDrawer);
document.getElementById("closeFocusModalBtn")?.addEventListener("click", closeFocusReadingMode);
document.getElementById("closePdfModalBtn")?.addEventListener("click", closePdfExportModal);
document.getElementById("cancelPdfModalBtn")?.addEventListener("click", closePdfExportModal);

const pdfExportModal = document.getElementById("pdfExportModal");
if (pdfExportModal) {
  pdfExportModal.addEventListener("click", (e) => {
    if (e.target === pdfExportModal) closePdfExportModal();
  });
}

document.getElementById("pdfPrintVectorBtn")?.addEventListener("click", () => {
  const opts = getPdfExportOptions();
  printDocumentViaIframe(activeExportDocument, opts, currentLang);
});
document.getElementById("pdfDownloadDirectBtn")?.addEventListener("click", () => {
  const opts = getPdfExportOptions();
  downloadDocumentAsPdf(activeExportDocument, opts, currentLang);
});

document.getElementById("focusDownloadMDBtn")?.addEventListener("click", () => {
  downloadMarkdownFile(activeExportDocument?.markdown || "", topicInput?.value || "");
});
document.getElementById("focusExportPdfBtn")?.addEventListener("click", () => {
  openPdfExportModal(activeExportDocument);
});
document.getElementById("focusPrintBtn")?.addEventListener("click", () => {
  openPdfExportModal(activeExportDocument);
});

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

// Main Pipeline Orchestration
if (startPipelineBtn) {
  startPipelineBtn.addEventListener("click", async () => {
    const apiKey = apiKeyInput ? apiKeyInput.value.trim() : "";
    if (!apiKey) {
      alert(currentLang === "id" ? "Silakan masukkan Kunci API Google Gemini terlebih dahulu!" : "Please enter a Google Gemini API Key first!");
      apiKeyInput?.focus();
      return;
    }
    localStorage.setItem(STORAGE_KEY, apiKey);

    const topic = topicInput ? topicInput.value.trim() : "";
    if (!topic) {
      alert(currentLang === "id" ? "Silakan tentukan topik atau instruksi target." : "Please provide a topic or prompt.");
      topicInput?.focus();
      return;
    }

    const selectedModel = modelSelect?.value || "gemini-3.8-flash";
    updateHeaderPoweredBadge(selectedModel);
    const selectedDifficulty = document.getElementById("readingDifficultySelect")?.value || "undergraduate";
    const selectedReadingType = document.getElementById("readingTypeSelect")?.value || "literature_review";
    const diffLabel = getDifficultyLabel(selectedDifficulty, currentLang === "id");
    const typeLabel = getReadingTypeLabel(selectedReadingType, currentLang === "id");
    const selectedThinking = document.getElementById("thinkingLevelSelect")?.value || "medium";
    const maxTurns = parseInt(maxTurnsSelect?.value || "3", 10) || 3;
    
    const rawScoreStr = (targetScoreInput?.value || "9.5").trim().replace(",", ".");
    let targetScore = parseFloat(rawScoreStr);
    if (isNaN(targetScore)) targetScore = 9.5;

    const forceAllTurns = document.getElementById("forceAllTurnsCheck")?.checked || false;
    const enableWebSearch = document.getElementById("webSearchCheck")?.checked || false;

    // Reset UI
    if (outputContainer) outputContainer.innerHTML = "";
    if (statusCard) statusCard.classList.remove("hidden");
    if (startPipelineBtn) {
      startPipelineBtn.disabled = true;
      startPipelineBtn.classList.add("opacity-50", "cursor-not-allowed");
    }
    if (startBtnText) {
      startBtnText.textContent = currentLang === "id" ? "Agen Sedang Bekerja..." : "Agents Working...";
    }

    let currentDraft = "";
    let latestCritique = null;
    let scholarlyDossier = null;

    try {
      // Step 0: Formulate Multilingual Search Queries & Collect Grounding Dossier
      const anyScholarly = (arxivCheck && arxivCheck.checked) || 
                           (crossrefCheck && crossrefCheck.checked) || 
                           (semanticScholarCheck && semanticScholarCheck.checked) || 
                           (openAlexCheck && openAlexCheck.checked) || 
                           (pubmedCheck && pubmedCheck.checked) || 
                           (wikipediaCheck && wikipediaCheck.checked) || 
                           uploadedDocument;
      if (anyScholarly) {
        if (statusText) {
          statusText.textContent = currentLang === "id" 
            ? "Menganalisis kueri & menelusuri repositori akademis global..." 
            : "Formulating queries & querying verified academic repositories...";
        }
        
        const queries = await resolveMultilingualQueries(topic, apiKey, selectedModel, callGemini, currentLang);
        scholarlyDossier = await collectScholarlyDossier(topic, queries);
        if (scholarlyDossier) {
          renderDossierCard(scholarlyDossier, currentLang);
        }
      }

      for (let turn = 1; turn <= maxTurns; turn++) {
        if (stepCounter) {
          stepCounter.textContent = currentLang === "id" ? `Putaran ${turn} dari ${maxTurns}` : `Turn ${turn} of ${maxTurns}`;
        }

        // Step 1: Writer
        if (statusText) {
          statusText.textContent = currentLang === "id"
            ? `Putaran ${turn}: Agen Penulis (${selectedModel} | 🎯 ${diffLabel} | 📚 ${typeLabel} | 🧠 ${selectedThinking}${enableWebSearch ? " | 🌐 Web Search" : ""}${scholarlyDossier ? " | 📚 Rujukan Ilmiah" : ""}) sedang menyusun draf...`
            : `Turn ${turn}: Writer Agent (${selectedModel} | 🎯 ${diffLabel} | 📚 ${typeLabel} | 🧠 ${selectedThinking}${enableWebSearch ? " | 🌐 Search" : ""}${scholarlyDossier ? " | 📚 Scholarly Grounded" : ""}) is composing...`;
        }
        
        if (turn === 1) {
          currentDraft = await runWriterDraft(apiKey, topic, selectedModel, enableWebSearch, selectedThinking, scholarlyDossier, selectedDifficulty, selectedReadingType, currentLang);
        } else {
          currentDraft = await runWriterRevision(apiKey, topic, currentDraft, latestCritique, turn - 1, selectedModel, enableWebSearch, selectedThinking, scholarlyDossier, selectedDifficulty, selectedReadingType, currentLang);
        }
        renderWriterCard(turn, currentDraft, scholarlyDossier, currentLang, topic);

        // Step 2: Critic
        if (statusText) {
          statusText.textContent = currentLang === "id"
            ? `Putaran ${turn}: Agen Pengkritik (${selectedModel} | 🧠 ${selectedThinking}) sedang mengevaluasi draf...`
            : `Turn ${turn}: Critic Agent (${selectedModel} | 🧠 ${selectedThinking}) is evaluating...`;
        }
        
        latestCritique = await runCriticReview(apiKey, topic, currentDraft, turn, selectedModel, selectedThinking, scholarlyDossier, selectedDifficulty, selectedReadingType, currentLang);
        renderCriticCard(turn, latestCritique, targetScore, currentLang);

        const isApproved = latestCritique.score >= targetScore;
        const shouldFinalize = (isApproved && !forceAllTurns) || (turn === maxTurns);

        if (shouldFinalize) {
          let auditResult = null;
          const strictSourceAudit = document.getElementById("strictSourceAuditCheck")?.checked ?? true;
          if (strictSourceAudit) {
            let auditTurn = 1;
            const maxAuditTurns = 3;
            while (auditTurn <= maxAuditTurns) {
              if (statusText) {
                statusText.textContent = currentLang === "id"
                  ? `🛡️ Putaran Audit Integritas ${auditTurn}: Menilai naskah berdasarkan Panduan Integritas Publikasi 3-Lapisan (source-checking-guide.md)...`
                  : `🛡️ Integrity Audit Round ${auditTurn}: Evaluating draft against 3-Layer Publication Integrity Guide (source-checking-guide.md)...`;
              }
              
              auditResult = await runSourceCheckingAudit(apiKey, topic, currentDraft, selectedModel, selectedThinking, scholarlyDossier, currentLang);
              renderSourceAuditCard(auditResult, auditTurn, currentLang);

              if (auditResult.all_yes) {
                if (statusText) {
                  statusText.textContent = currentLang === "id"
                    ? `🛡️ 100% Lolos Integritas Publikasi! Seluruh 11 kriteria panduan terjawab YA.`
                    : `🛡️ 100% Publication Integrity Clearance! All 11 guide criteria answered YES.`;
                }
                break;
              } else {
                if (auditTurn < maxAuditTurns) {
                  const failCount = (auditResult.items || []).filter(i => i.answer === "NO").length || (auditResult.discrepancies?.length || 1);
                  if (statusText) {
                    statusText.textContent = currentLang === "id"
                      ? `🛡️ Ditemukan ${failCount} ketidaksesuaian integritas. Agen Penulis sedang menyusun ulang teks (Putaran Audit ${auditTurn + 1})...`
                      : `🛡️ Integrity discrepancies detected (${failCount} items). Writer Agent is rebuilding text (Audit Round ${auditTurn + 1})...`;
                  }
                  
                  currentDraft = await runWriterIntegrityRevision(apiKey, topic, currentDraft, auditResult, auditTurn, selectedModel, enableWebSearch, selectedThinking, scholarlyDossier, selectedDifficulty, selectedReadingType, currentLang);
                  renderWriterCard(`Integrity-Rev-${auditTurn}`, currentDraft, scholarlyDossier, currentLang, topic);
                  auditTurn++;
                } else {
                  if (statusText) {
                    statusText.textContent = currentLang === "id"
                      ? `Menyelesaikan putaran audit integritas maksimum (${maxAuditTurns}).`
                      : `Completed maximum integrity audit rounds (${maxAuditTurns}).`;
                  }
                  break;
                }
              }
            }
          }

          if (statusText) {
            statusText.textContent = currentLang === "id"
              ? `Selesai! Draf telah dipoles & diverifikasi (Skor Pengkritik: ${latestCritique.score.toFixed(1)}${auditResult?.all_yes ? " • 🛡️ 100% Integritas Terverifikasi" : ""}).`
              : `Completed! Draft polished & verified (Critic score: ${latestCritique.score.toFixed(1)}${auditResult?.all_yes ? " • 🛡️ 100% Integrity Verified" : ""}).`;
          }
          renderFinalApprovedCard(currentDraft, latestCritique.score, turn, scholarlyDossier, selectedDifficulty, selectedReadingType, auditResult, currentLang, topic);
          break;
        } else if (isApproved && forceAllTurns) {
          if (statusText) {
            statusText.textContent = currentLang === "id"
              ? `Putaran ${turn} bernilai ${latestCritique.score.toFixed(1)} (>= ${targetScore.toFixed(1)}), lanjut ke putaran berikutnya (Mode paksa aktif)...`
              : `Turn ${turn} scored ${latestCritique.score.toFixed(1)} (>= ${targetScore.toFixed(1)}), continuing next turn (Force mode active)...`;
          }
        }
      }
    } catch (err) {
      console.error(err);
      let userMsg = err.message;
      if (userMsg.includes("quota") || userMsg.includes("429")) {
        userMsg += currentLang === "id" 
          ? "\n\n💡 Petunjuk: Jika 'Pencarian Web Google' aktif, hapus centangnya. Google menerapkan kuota terpisah untuk pencarian web."
          : "\n\n💡 Tip: If 'Google Web Search' is checked, uncheck it to use standard model reasoning. Google imposes a separate quota on web search grounding.";
      }
      alert(`Pipeline Error: ${userMsg}`);
      if (statusText) statusText.textContent = `Error: ${userMsg}`;
    } finally {
      if (statusSpinner) statusSpinner.classList.add("hidden");
      if (startPipelineBtn) {
        startPipelineBtn.disabled = false;
        startPipelineBtn.classList.remove("opacity-50", "cursor-not-allowed");
      }
      if (startBtnText) {
        startBtnText.textContent = I18N[currentLang]?.startBtnText || "Run Agentic Pipeline";
      }
    }
  });
}

// Window Bridge for Automated Testing & Playwright Evaluation Compatibility
if (typeof window !== "undefined") {
  window.buildTextFragmentUrl = buildTextFragmentUrl;
  window.renderWriterCard = (turn, draft, dossier) => renderWriterCard(turn, draft, dossier, currentLang, topicInput?.value || "");
  window.renderCriticCard = (turn, critique, targetScore) => renderCriticCard(turn, critique, targetScore, currentLang);
  window.renderSourceAuditCard = (auditResult, round) => renderSourceAuditCard(auditResult, round, currentLang);
  window.renderFinalApprovedCard = (finalDraft, score, turns, dossier, diff, type, auditResult) => renderFinalApprovedCard(finalDraft, score, turns, dossier, diff, type, auditResult, currentLang, topicInput?.value || "");
  window.runDeterministicSanityChecks = runDeterministicSanityChecks;
  window.prepareDraftHtml = (draftText, dossier) => prepareDraftHtml(draftText, dossier, currentLang);
  window.openCitationInspector = (data) => openCitationInspector(data, currentLang);
  window.closeCitationDrawer = closeCitationDrawer;
  window.applyTheme = applyTheme;
  window.applyFont = applyFont;
  window.applyFontSize = applyFontSize;
  window.applyLanguage = applyLanguage;
}

// Initialize on page load
initGlobalUIControls(currentLang);
applyLanguage(currentLang);

