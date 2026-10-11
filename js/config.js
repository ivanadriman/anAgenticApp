/**
 * Gemini Agentic Studio - Configuration, Constants & i18n
 */

export const STORAGE_KEY = "gemini_agentic_studio_key";
export const LANG_STORAGE_KEY = "gemini_agentic_studio_lang";
export const THEME_STORAGE_KEY = "gemini_agentic_studio_theme";
export const FONT_STORAGE_KEY = "gemini_agentic_studio_font";
export const FONT_SIZE_STORAGE_KEY = "gemini_agentic_studio_font_size";

export const ALL_MODELS = [
  { id: "gemini-3.5-flash-lite", label: "gemini-3.5-flash-lite (Ultra Fast)" },
  { id: "gemini-3.5-flash", label: "gemini-3.5-flash (Balanced)" },
  { id: "gemini-3-flash-preview", label: "gemini-3-flash-preview" },
  { id: "gemini-3.8-flash", label: "gemini-3.8-flash (Recommended)" },
  { id: "gemini-flash-latest", label: "gemini-flash-latest" },
  { id: "gemini-3.1-pro-preview", label: "gemini-3.1-pro-preview (Deep Reasoning)" }
];

export const MODEL_DISPLAY_NAMES = {
  "gemini-3.5-flash-lite": "Gemini 3.5 Flash Lite",
  "gemini-3.5-flash": "Gemini 3.5 Flash",
  "gemini-3-flash-preview": "Gemini 3 Flash Preview",
  "gemini-3.8-flash": "Gemini 3.8 Flash",
  "gemini-flash-latest": "Gemini Flash Latest",
  "gemini-3.1-pro-preview": "Gemini 3.1 Pro Preview"
};

export function getModelDisplayName(modelId) {
  if (!modelId) return "Gemini";
  if (MODEL_DISPLAY_NAMES[modelId]) return MODEL_DISPLAY_NAMES[modelId];
  return modelId
    .replace(/^models\//, "")
    .split("-")
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export const I18N = {
  en: {
    headerTitle: "Gemini Agentic Studio",
    headerSubtitle: "Two-Agent Autonomous \"Writer & Critic\" Pipeline",
    headerPowered: "Powered by: <strong>Gemini 3.8 Flash</strong>",
    apiKeyLabel: "🔑 Google Gemini API Key (Stored locally in your browser only)",
    apiKeyPlaceholder: "AIzaSy... or paste your Gemini API key",
    toggleKeyVisibility: "Show",
    saveKeyBtn: "Save Key",
    apiKeyNote: "🔒 Your key is stored in your browser's <code class=\"text-cyan-400\">localStorage</code> and sent directly to Google's API via secure <code class=\"text-cyan-400\">x-goog-api-key</code> headers (never in URLs or to third parties). Need a free key? Get one at <a href=\"https://aistudio.google.com/app/apikey\" target=\"_blank\" rel=\"noopener noreferrer\" class=\"text-cyan-400 hover:underline\">Google AI Studio</a>.",
    topicLabel: "Target Topic or Goal:",
    topicPlaceholder: "e.g., Explain microservices vs monoliths for junior developers with real-world tradeoffs",
    defaultTopic: "Explain how Agentic AI architectures work to software engineers with a concrete example",
    modelLabel: "Gemini Model:",
    checkQuotaBtn: "🔄 Check Quota",
    quotaReady: "Ready",
    difficultyLabel: "🎯 Target Difficulty / Audience:",
    readingTypeLabel: "📚 Document Type / Reading Genre:",
    optDiffLayman: "General Audience / Layman",
    optDiffUndergrad: "Undergraduate / College",
    optDiffExpert: "Expert / Specialist Researcher",
    optDiffExec: "Executive / Strategic Decision Maker",
    optTypeReview: "Academic Literature Review",
    optTypeEssay: "Longform Analytical Essay",
    optTypeTextbook: "Educational / Textbook Chapter",
    optTypeWhitepaper: "Technical Whitepaper",
    optTypeBrief: "Executive / Policy Brief",
    thinkingLabel: "🧠 Thinking Mode:",
    optThinkingLow: "Low (Fast Response)",
    optThinkingMed: "Medium (Balanced Reasoning)",
    optThinkingHigh: "High (Deep Strategic Reasoning)",
    iterationLabel: "Iteration Mode:",
    optTurn1: "1 Turn (Single Draft)",
    optTurn2: "2 Turns (Draft → Critique → Revise)",
    optTurn3: "3 Turns (Full Multi-Round Polish)",
    targetScoreLabel: "Approval Target Score (1-10):",
    forceTurnsLabel: "Force all turns",
    webSearchLabel: "🌐 Google Web Search",
    strictSourceAuditLabel: "🛡️ Strict Publication Integrity Audit (source-checking-guide)",
    groundingHeaderTitle: "Scholarly & Reference Grounding Sources",
    groundingHeaderSub: "Independent academic literature & encyclopedic sources • Free & Uncapped",
    arxivTitle: "📚 arXiv API",
    arxivSub: "2.4M+ STEM papers (AI, CS, Physics, Math, Bio)",
    semanticTitle: "🔬 Semantic Scholar API",
    semanticSub: "200M+ papers with citation graphs & metrics",
    pubmedTitle: "🧬 PubMed / Europe PMC",
    pubmedSub: "36M+ biomedical citations (NCBI E-utilities)",
    openAlexTitle: "🏛️ OpenAlex API",
    openAlexSub: "250M+ scholarly works, authors & open access",
    crossrefTitle: "🏷️ Crossref API",
    crossrefSub: "150M+ verified peer-reviewed publications & DOIs",
    wikipediaTitle: "📖 Wikipedia Reference",
    wikipediaSub: "Curated encyclopedic summaries",
    googleScholarTitle: "🎓 Google Scholar",
    googleScholarSub: "Universal academic literature, conference papers & dissertations",
    ieeeTitle: "⚡ IEEE Xplore",
    ieeeSub: "Specialized electrical engineering, robotics & CS papers",
    ssrnTitle: "📑 SSRN Preprints",
    ssrnSub: "Economics, finance, law & social science working papers",
    coreTitle: "🌐 CORE Repositories",
    coreSub: "Open-access full texts from global university repositories",
    doajTitle: "📜 DOAJ Journals",
    doajSub: "Directory of peer-reviewed open access journals",
    springerTitle: "📕 SpringerLink",
    springerSub: "Peer-reviewed journal articles and scientific book chapters",
    googlePatentsTitle: "⚙️ Google Patents",
    googlePatentsSub: "International patent filings & engineering specs",
    docUploadTitle: "Ground on Local Document / PDF",
    docUploadSub: "Client-side text parsing with PDF.js • 100% private, zero uploads to external servers",
    uploadDocBtn: "📁 Choose File",
    docFileStatus: "No document selected",
    startBtnText: "Run Agentic Pipeline",
    apiKeySavedLabel: "Gemini API Key Configured",
    editApiKeyText: "Edit Key",
    advancedOptionsTitle: "Advanced Pipeline Options",
    selectAllBtn: "Select All",
    clearAllBtn: "Clear",
    footerText1: "Autonomous Agentic App Demo • Powered by Google Gemini API",
    footerText2: "100% Client-side on GitHub Pages • No API keys stored on servers",
    downloadMarkdownBtn: "📥 Download Markdown",
    exportPdfBtn: "📄 Export PDF",
    pdfModalTitle: "Export Document as PDF",
    pdfModalSub: "Configure paper size, orientation, and layout",
    pdfPaperSizeLabel: "Paper Size:",
    pdfOrientationLabel: "Orientation:",
    pdfMarginsLabel: "Margins:",
    pdfFontLabel: "Typography:",
    pdfFontSizeLabel: "Body Font Size:",
    pdfIncludeHeaderLabel: "Include Title & Research Metadata Cover Banner",
    pdfAvoidBreaksLabel: "Smart Page Breaks (prevent breaking quotes, tables & citations across pages)",
    pdfCancelBtn: "Cancel",
    pdfPrintVectorBtn: "Print / Vector PDF",
    pdfDownloadDirectBtn: "Download PDF",
    pdfOptionA4: "A4 (210 × 297 mm) — Standard Academic & International",
    pdfOptionLetter: "US Letter (8.5 × 11 in) — North American Standard",
    pdfOptionA5: "A5 (148 × 210 mm) — Compact Handbook / Booklet",
    pdfOptionLegal: "US Legal (8.5 × 14 in) — Extended Format",
    pdfOptionExecutive: "Executive (7.25 × 10.5 in) — Compact Executive Report",
    pdfOptionPortrait: "Portrait (Vertical)",
    pdfOptionLandscape: "Landscape (Horizontal)",
    pdfOptionMarginStandard: "Standard (15 mm / 0.6 in)",
    pdfOptionMarginNarrow: "Narrow (10 mm / 0.4 in)",
    pdfOptionMarginWide: "Spacious (22 mm / 0.9 in)",
    pdfOptionFontSerif: "Academic Serif (Charter / Georgia)",
    pdfOptionFontSans: "Modern Sans (Inter / System UI)",
    pdfOptionSizeStandard: "Standard (11 pt / 14.5 px)",
    pdfOptionSizeCompact: "Compact (10 pt / 13 px)",
    pdfOptionSizeLarge: "Comfortable (12 pt / 16 px)",
    copyQuoteBtn: "📋 Copy Quote",
    quoteCopied: "✓ Copied!",
    tooltipHint: "Click citation for full inspector",
    tooltipInspectBtn: "Inspect Evidence",
    drawerQuoteLabel: "Verbatim Quote Cited in Text:",
    drawerAbstractLabel: "Official Source Abstract (Primary Text Evidence):",
    drawerAbstractMatchVerbatim: "✓ 100% Verbatim Match",
    drawerAbstractMatchNotice: "ℹ️ Full-Text / Preprint Article",
    drawerVerifiedInAbstract: "✓ Verified in Abstract",
    drawerFullTextNotice: "ℹ️ Full-Text / Preprint Article",
    drawerBibliographicSource: "📚 Bibliographic Source",
    drawerOpenPaper: "🔗 Open Paper (Deep Highlight)",
    drawerCopyQuoteBtn: "Salin untuk CTRL+F",
    drawerCopyQuoteText: "Copy for CTRL+F",
    drawerCopyQuoteCopied: "✓ Copied (CTRL+F)!",
    drawerScholarBtn: "Google Scholar",
    drawerAbstractNoticeText: "Note: Subscription publishers (DOI) often strip browser automatic highlights during cross-origin redirects. If the destination page does not highlight automatically, use 'Copy for CTRL+F' or 'Google Scholar' below to find the open full text."
  },
  id: {
    headerTitle: "Gemini Agentic Studio",
    headerSubtitle: "Pipeline Otonom Dua Agen \"Penulis & Pengkritik\"",
    headerPowered: "Didukung oleh: <strong>Gemini 3.8 Flash</strong>",
    apiKeyLabel: "🔑 Kunci API Google Gemini (Hanya tersimpan secara lokal di peramban Anda)",
    apiKeyPlaceholder: "AIzaSy... atau tempel kunci API Gemini Anda",
    toggleKeyVisibility: "Lihat",
    saveKeyBtn: "Simpan Kunci",
    apiKeyNote: "🔒 Kunci Anda tersimpan di <code class=\"text-cyan-400\">localStorage</code> peramban dan dikirim langsung ke API Google melalui header aman <code class=\"text-cyan-400\">x-goog-api-key</code> (tidak pernah melalui URL atau pihak ketiga). Perlu kunci gratis? Dapatkan di <a href=\"https://aistudio.google.com/app/apikey\" target=\"_blank\" rel=\"noopener noreferrer\" class=\"text-cyan-400 hover:underline\">Google AI Studio</a>.",
    topicLabel: "Topik atau Tujuan Target:",
    topicPlaceholder: "contoh: Jelaskan persepsi wicara dan mekanisme pemrosesan auditori pada otak manusia",
    defaultTopic: "Jelaskan bagaimana arsitektur Agentic AI bekerja kepada software engineer dengan contoh konkret",
    modelLabel: "Model Gemini:",
    checkQuotaBtn: "🔄 Cek Kuota",
    quotaReady: "Siap",
    difficultyLabel: "🎯 Target Kesulitan / Audiens:",
    readingTypeLabel: "📚 Jenis Dokumen / Genre Bacaan:",
    optDiffLayman: "Masyarakat Umum / Awam",
    optDiffUndergrad: "Mahasiswa / Sarjana",
    optDiffExpert: "Pakar / Peneliti Spesialis",
    optDiffExec: "Eksekutif / Pengambil Kebijakan Strategis",
    optTypeReview: "Tinjauan Pustaka Akademis (Lit Review)",
    optTypeEssay: "Esai Analitis Mendalam (Deep Dive)",
    optTypeTextbook: "Bab Buku Teks / Materi Ajar Edukatif",
    optTypeWhitepaper: "Buku Putih Teknis (Whitepaper)",
    optTypeBrief: "Ringkasan Eksekutif / Brief Kebijakan",
    thinkingLabel: "🧠 Mode Berpikir (Thinking Mode):",
    optThinkingLow: "Rendah (Respon Cepat)",
    optThinkingMed: "Sedang (Penalaran Seimbang)",
    optThinkingHigh: "Tinggi (Penalaran Strategis Mendalam)",
    iterationLabel: "Mode Iterasi:",
    optTurn1: "1 Putaran (Draf Tunggal)",
    optTurn2: "2 Putaran (Draf → Kritik → Revisi)",
    optTurn3: "3 Putaran (Penyempurnaan Multi-Putaran Penuh)",
    targetScoreLabel: "Target Skor Persetujuan (1-10):",
    forceTurnsLabel: "Jalankan semua putaran",
    webSearchLabel: "🌐 Pencarian Web Google",
    strictSourceAuditLabel: "🛡️ Audit Ketat Integritas Publikasi (source-checking-guide)",
    groundingHeaderTitle: "Sumber Rujukan Ilmiah & Akademis",
    groundingHeaderSub: "Literatur akademis independen & sumber ensiklopedia • Gratis & Tanpa Batas",
    arxivTitle: "📚 arXiv API",
    arxivSub: "2.4M+ Makalah STEM (AI, Ilmu Komputer, Fisika, Matematika, Biologi)",
    semanticTitle: "🔬 Semantic Scholar API",
    semanticSub: "200M+ Makalah dengan grafik sitasi & metrik dampak",
    pubmedTitle: "🧬 PubMed / Europe PMC",
    pubmedSub: "36M+ Sitasi biomedis & kesehatan (NCBI E-utilities)",
    openAlexTitle: "🏛️ OpenAlex API",
    openAlexSub: "250M+ Karya ilmiah global, penulis & akses terbuka",
    crossrefTitle: "🏷️ Crossref API",
    crossrefSub: "150M+ Publikasi peer-review & DOI penerbit terverifikasi",
    wikipediaTitle: "📖 Wikipedia Reference",
    wikipediaSub: "Ringkasan ensiklopedia terkurasi (ID & Global)",
    googleScholarTitle: "🎓 Google Scholar",
    googleScholarSub: "Literatur akademis universal, makalah konferensi & disertasi",
    ieeeTitle: "⚡ IEEE Xplore",
    ieeeSub: "Makalah teknik elektro, robotika & ilmu komputer spesifik",
    ssrnTitle: "📑 SSRN Preprints",
    ssrnSub: "Makalah kerja ekonomi, keuangan, hukum & ilmu sosial",
    coreTitle: "🌐 CORE Repositories",
    coreSub: "Naskah teks lengkap terbuka dari repositori universitas global",
    doajTitle: "📜 DOAJ Journals",
    doajSub: "Direktori jurnal akses terbuka telaah sejawat terverifikasi",
    springerTitle: "📕 SpringerLink",
    springerSub: "Artikel jurnal telaah sejawat dan bab buku ilmiah",
    googlePatentsTitle: "⚙️ Google Patents",
    googlePatentsSub: "Berkas paten internasional & spesifikasi rekayasa",
    docUploadTitle: "Rujukan Dokumen / PDF Lokal",
    docUploadSub: "Ekstraksi teks di peramban dengan PDF.js • 100% privat tanpa unggah ke server",
    uploadDocBtn: "📁 Pilih Berkas",
    docFileStatus: "Belum ada berkas dipilih",
    startBtnText: "Jalankan Pipeline Agen",
    apiKeySavedLabel: "Kunci API Gemini Terpasang",
    editApiKeyText: "Ubah Kunci",
    advancedOptionsTitle: "Pengaturan Lanjutan",
    selectAllBtn: "Pilih Semua",
    clearAllBtn: "Hapus",
    footerText1: "Demo Aplikasi Agen Otonom • Didukung oleh Google Gemini API",
    footerText2: "100% Sisi Klien di GitHub Pages • Tidak ada kunci API yang disimpan di server",
    downloadMarkdownBtn: "📥 Unduh Markdown",
    exportPdfBtn: "📄 Ekspor PDF",
    pdfModalTitle: "Ekspor Dokumen ke PDF",
    pdfModalSub: "Atur ukuran kertas, orientasi, dan tata letak",
    pdfPaperSizeLabel: "Ukuran Kertas:",
    pdfOrientationLabel: "Orientasi:",
    pdfMarginsLabel: "Margin:",
    pdfFontLabel: "Tipografi:",
    pdfFontSizeLabel: "Ukuran Font Teks:",
    pdfIncludeHeaderLabel: "Sertakan Judul & Banner Metadata Riset",
    pdfAvoidBreaksLabel: "Pemisah Halaman Cerdas (cegah kutipan & tabel terpotong)",
    pdfCancelBtn: "Batal",
    pdfPrintVectorBtn: "Cetak / Vektor PDF",
    pdfDownloadDirectBtn: "Unduh PDF",
    pdfOptionA4: "A4 (210 × 297 mm) — Standar Akademis & Internasional",
    pdfOptionLetter: "US Letter (8.5 × 11 in) — Standar Amerika Utara",
    pdfOptionA5: "A5 (148 × 210 mm) — Buku Saku / Buklet Ringkas",
    pdfOptionLegal: "US Legal (8.5 × 14 in) — Format Dokumen Panjang",
    pdfOptionExecutive: "Executive (7.25 × 10.5 in) — Laporan Eksekutif Ringkas",
    pdfOptionPortrait: "Potret (Vertikal)",
    pdfOptionLandscape: "Lanskap (Horizontal)",
    pdfOptionMarginStandard: "Standar (15 mm / 0.6 in)",
    pdfOptionMarginNarrow: "Sempit (10 mm / 0.4 in)",
    pdfOptionMarginWide: "Lapang (22 mm / 0.9 in)",
    pdfOptionFontSerif: "Serif Akademis (Charter / Georgia)",
    pdfOptionFontSans: "Sans Modern (Inter / System UI)",
    pdfOptionSizeStandard: "Standar (11 pt / 14.5 px)",
    pdfOptionSizeCompact: "Kompak (10 pt / 13 px)",
    pdfOptionSizeLarge: "Nyaman (12 pt / 16 px)",
    copyQuoteBtn: "📋 Salin Kutipan",
    quoteCopied: "✓ Tersalin!",
    tooltipHint: "Klik sitasi untuk inspeksi penuh",
    tooltipInspectBtn: "Periksa Bukti",
    drawerQuoteLabel: "Kutipan yang Dirujuk dalam Teks:",
    drawerAbstractLabel: "Teks Abstrak Sumber Resmi (Bukti Kontekstual):",
    drawerAbstractMatchVerbatim: "✓ 100% Cocok Verbatim",
    drawerAbstractMatchNotice: "ℹ️ Tidak di abstrak ringkas",
    drawerVerifiedInAbstract: "✓ Terverifikasi di Abstrak",
    drawerFullTextNotice: "ℹ️ Naskah Lengkap / Pre-print",
    drawerBibliographicSource: "📚 Sumber Bibliografi",
    drawerOpenPaper: "🔗 Buka Makalah (Deep Highlight)",
    drawerCopyQuoteBtn: "Salin untuk CTRL+F",
    drawerCopyQuoteText: "Salin untuk CTRL+F",
    drawerCopyQuoteCopied: "✓ Tersalin (CTRL+F)!",
    drawerScholarBtn: "Google Scholar",
    drawerAbstractNoticeText: "Catatan: Penerbit jurnal berbayar (DOI) sering memblokir highlight otomatis peramban saat pengalihan domain. Jika halaman tujuan tidak langsung menyorot teks, gunakan tombol 'Salin untuk CTRL+F' atau 'Google Scholar' di bawah ini untuk menemukan naskah lengkap terbuka."
  }
};

export function getDifficultyGuidance(diffKey, isId) {
  const guides = {
    layman: isId
      ? "TARGET AUDIENS (Masyarakat Umum / Awam):\n- Gunakan bahasa yang mudah dipahami, lugas, bersahabat, dan bebas jargon yang berbelit-belit.\n- Jelaskan setiap konsep dengan analogi kehidupan nyata yang intuitif tanpa mengurangi kebenaran faktual.\n- Targetkan pembaca yang ingin memahami topik secara menyeluruh tanpa latar belakang teknis khusus."
      : "TARGET AUDIENCE (General Audience / Layman):\n- Use clear, engaging, jargon-free explanations with intuitive real-world analogies.\n- Break down complex mechanisms into accessible concepts while maintaining factual integrity.\n- Target curious readers without specialized prior background in the field.",
    undergraduate: isId
      ? "TARGET AUDIENS (Mahasiswa / Kalangan Akademisi Sarjana):\n- Pertahankan ketelitian akademis, konsep dasar yang terdefinisi dengan jelas, eksposisi analitis yang terstruktur, dan terminologi teknis profesional.\n- Sajikan argumen dan sintesis berbasis literatur yang relevan untuk tingkat perkuliahan sarjana/universitas."
      : "TARGET AUDIENCE (Undergraduate / College):\n- Maintain formal academic rigor, well-defined foundational concepts, structured analytical exposition, and professional technical terminology.\n- Deliver arguments and literature syntheses appropriate for undergraduate and college study.",
    expert: isId
      ? "TARGET AUDIENS (Pakar / Peneliti Spesialis):\n- Sajikan densitas konseptual tinggi, nuansa teoretis mutakhir, telaah metodologis kritis, analisis kasus batas (edge cases), dan mekanisme domain mendalam.\n- Jangan membuang ruang untuk mengulang dasar-dasar pemula; fokuskan pada batasan teknis dan kemajuan state-of-the-art."
      : "TARGET AUDIENCE (Expert / Specialist Researcher):\n- Deliver high conceptual density, advanced theoretical nuance, methodology critique, state-of-the-art edge cases, and in-depth domain mechanisms.\n- Do not waste space over-explaining foundational basics; focus on technical boundaries and state-of-the-art developments.",
    executive: isId
      ? "TARGET AUDIENS (Eksekutif / Pengambil Kebijakan Strategis):\n- Fokus pada implikasi strategis, kompromi arsitektural/teknis tingkat tinggi, analisis dampak operasional & ROI, risiko, dan rekomendasi actionable.\n- Gunakan gaya penulisan ringkas, tegas, berbasis dampak, dan otoritatif."
      : "TARGET AUDIENCE (Executive / Strategic Decision Maker):\n- Focus on strategic implications, high-level architectural tradeoffs, operational impact & ROI, risk assessments, and actionable recommendations.\n- Write with concise, authoritative clarity geared toward high-stakes decision-making."
  };
  return guides[diffKey] || guides.undergraduate;
}

export function getReadingTypeGuidance(typeKey, isId) {
  const guides = {
    literature_review: isId
      ? "GENRE DOKUMEN (Tinjauan Pustaka Akademis / Literature Review):\n- Susun secara sistematis berdasarkan tema konseptual atau paradigma teoretis.\n- Sintesiskan konsensus dan perdebatan antar-makalah/sumber rujukan ilmiah.\n- Soroti celah riset (research gaps) dan arah pengembangan masa depan."
      : "DOCUMENT GENRE (Academic Literature Review):\n- Organize systematically by conceptual themes and theoretical paradigms.\n- Synthesize consensus versus active debates across cited scholarly literature.\n- Highlight research gaps and emerging directions.",
    deep_dive_essay: isId
      ? "GENRE DOKUMEN (Esai Analitis Mendalam / Longform Analytical Essay):\n- Terapkan prosa naratif yang memikat, alur argumen intelektual yang persuasif, pembangunan ide bertahap, dan perenungan kritis yang menghubungkan teori dengan penerapan nyata."
      : "DOCUMENT GENRE (Longform Analytical Essay):\n- Employ engaging narrative prose, persuasive intellectual depth, progressive conceptual building, and thought-provoking synthesis connecting theory to practice.",
    textbook_chapter: isId
      ? "GENRE DOKUMEN (Bab Buku Teks / Materi Ajar Edukatif):\n- Terapkan struktur pedagogis: 1) Tujuan Pembelajaran (Learning Objectives), 2) Modul Konsep Bertahap dengan Penjelasan Mendalam, 3) Contoh Kasus / Studi Implementasi Nyata, dan 4) Rangkuman Inti Bab (Key Takeaways)."
      : "DOCUMENT GENRE (Educational / Textbook Chapter):\n- Follow a pedagogical structure: 1) Learning Objectives, 2) Progressive Conceptual Modules with in-depth exposition, 3) Concrete Worked Examples / Case Studies, and 4) Chapter Key Takeaways.",
    technical_whitepaper: isId
      ? "GENRE DOKUMEN (Buku Putih Teknis / Technical Whitepaper):\n- Terapkan struktur publikasi teknis otoritatif: 1) Pernyataan Masalah & Konteks Industri/Sains, 2) Cetak Biru Arsitektur / Spesifikasi Teknis, 3) Analisis Komparatif / Matriks Kompromi, dan 4) Pertimbangan Implementasi & Skalabilitas."
      : "DOCUMENT GENRE (Technical Whitepaper):\n- Adopt an authoritative technical publication style: 1) Problem Statement & Industry/Scientific Context, 2) Architectural Blueprint / Technical Specifications, 3) Comparative Benchmark / Tradeoff Matrix, and 4) Implementation Feasibility & Scalability.",
    executive_brief: isId
      ? "GENRE DOKUMEN (Ringkasan Eksekutif / Brief Kebijakan):\n- Terapkan struktur brief ringkas: 1) Ringkasan Eksekutif (Executive Summary), 2) Temuan Strategis Inti & Wawasan Utama, 3) Matriks Risiko & Peluang, dan 4) Rekomendasi Tindakan Terprioritisasi."
      : "DOCUMENT GENRE (Executive / Policy Brief):\n- Format with: 1) Executive Summary, 2) Core Strategic Findings & Key Insights, 3) Risk & Opportunity Assessment, and 4) Prioritized Action Plan / Strategic Recommendations."
  };
  return guides[typeKey] || guides.literature_review;
}

export function getDifficultyLabel(diffKey, isId) {
  const map = isId 
    ? { layman: "Masyarakat Umum / Awam", undergraduate: "Mahasiswa / Sarjana", expert: "Pakar / Peneliti", executive: "Eksekutif" }
    : { layman: "General / Layman", undergraduate: "Undergraduate", expert: "Expert Researcher", executive: "Executive" };
  return map[diffKey] || map.undergraduate;
}

export function getReadingTypeLabel(typeKey, isId) {
  const map = isId
    ? { literature_review: "Tinjauan Pustaka", deep_dive_essay: "Esai Analitis", textbook_chapter: "Bab Buku Teks", technical_whitepaper: "Buku Putih Teknis", executive_brief: "Ringkasan Eksekutif" }
    : { literature_review: "Literature Review", deep_dive_essay: "Analytical Essay", textbook_chapter: "Textbook Chapter", technical_whitepaper: "Technical Whitepaper", executive_brief: "Executive Brief" };
  return map[typeKey] || map.literature_review;
}

export function getVerbLadderFewShotPrompt(isId) {
  if (isId) {
    return `
CONTOH KALIBRASI ILMIAH & TANGGA KATA KERJA (FEW-SHOT VERB LADDER & BOUNDED SCOPE):
Contoh 1 (Data Korelasional / Observasional vs. Kausalitas):
❌ SALAH (Pelanggaran kausalitas): "Smith (2020) membuktikan bahwa kecepatan wicara memicu efisiensi pemahaman [1]."
✓ BENAR (Asosiatif terkalibrasi): "Smith (2020) menemukan bahwa kecepatan pemrosesan wicara berasosiasi positif dengan skor pemahaman dalam uji pendengaran [1]."

Contoh 2 (Batasan Cakupan & Sampel vs. Inflasi Universal):
❌ SALAH (Generalisasi berlebih): "Temuan ini membuktikan bahwa seluruh manusia memproses sintaksis secara identik [2]."
✓ BENAR (Terikat sampel): "Dalam uji laboratorium terhadap 48 mahasiswa sarjana, kecepatan pemrosesan sintaksis berkorelasi dengan latensi respons auditori [2]."

Contoh 3 (Temuan Nyata vs. Asumsi Pengantar/Framing):
❌ SALAH (Mengutip pengantar seolah temuan): "Doe (2019) membuktikan bahwa osilasi kortikal mendasari seluruh pemahaman bahasa [3]."
✓ BENAR (Framing akurat): "Doe (2019) mengajukan hipotesis bahwa osilasi kortikal dapat mendukung segmentasi bahasa, serta mengamati pola aktivitas saraf yang bersesuaian [3]."
`;
  } else {
    return `
FEW-SHOT EXAMPLES OF PROPER EPISTEMIC CALIBRATION (VERB LADDER & BOUNDED SCOPE):
Example 1 (Cross-Sectional / Observational Data vs. Causal Verbs):
❌ INCORRECT (Causal violation): "Smith (2020) proved that speech rate drives comprehension efficiency [1]."
✓ CORRECT (Calibrated association): "Smith (2020) observed that speech processing rate is positively associated with comprehension scores in auditory tests [1]."

Example 2 (Sample / Scope Generalization vs. Bounded Cohort):
❌ INCORRECT (Scope inflation): "These findings demonstrate that all humans process syntax identically [2]."
✓ CORRECT (Bounded sample): "In a laboratory experiment with 48 undergraduate participants, syntactic processing speed tracked auditory response latency [2]."

Example 3 (Introductory Framing vs. Empirical Finding):
❌ INCORRECT (Treating intro background as finding): "Doe (2019) proved that cortical oscillations underlie all human language understanding [3]."
✓ CORRECT (Accurate epistemic framing): "Doe (2019) hypothesized that cortical oscillations could support language segmentation, observing corresponding neural activity patterns [3]."
`;
  }
}
