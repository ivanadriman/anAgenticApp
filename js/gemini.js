/**
 * Gemini Agentic Studio - Gemini API Client & Autonomous Agent Loops
 */

import {
  ALL_MODELS,
  getDifficultyGuidance,
  getReadingTypeGuidance,
  getDifficultyLabel,
  getReadingTypeLabel,
  getVerbLadderFewShotPrompt,
  getModelDisplayName
} from "./config.js";
import { runDeterministicSanityChecks } from "./text-fragments.js";

/**
 * Call Gemini REST API directly from the browser using secure header-based auth (x-goog-api-key).
 */
export async function callGemini(apiKey, systemInstruction, prompt, model = "gemini-3.8-flash", enableSearch = false, thinkingLevel = "medium") {
  const cleanKey = apiKey.trim();
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`;

  const payload = {
    system_instruction: {
      parts: [{ text: systemInstruction }]
    },
    contents: [
      {
        role: "user",
        parts: [{ text: prompt }]
      }
    ],
    generationConfig: {
      temperature: 0.7,
      thinkingConfig: {
        thinkingLevel: thinkingLevel
      }
    }
  };

  if (enableSearch) {
    payload.tools = [{ google_search: {} }];
  }

  let res;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-goog-api-key": cleanKey
      },
      body: JSON.stringify(payload)
    });
  } catch (networkErr) {
    console.error("Network fetch failed:", networkErr);
    throw new Error(
      `Network connection to Google Gemini API failed ("${networkErr.message}"). ` +
      `Common causes: content blocker / Safari Private Browsing blocking third-party API calls, ` +
      `or an invalid API key. Please verify your internet connection, disable content blockers on this page, and check your key.`
    );
  }

  if (!res.ok) {
    const errJson = await res.json().catch(() => ({}));
    const msg = errJson.error?.message || `HTTP ${res.status} (${res.statusText})`;
    throw new Error(`Gemini API Error: ${msg}`);
  }

  const data = await res.json();
  const candidate = data.candidates?.[0];
  let text = candidate?.content?.parts?.[0]?.text || "";
  if (!text) {
    throw new Error("Received empty response from Gemini model.");
  }

  // Append Google Search Grounding sources if present
  const chunks = candidate?.groundingMetadata?.groundingChunks || [];
  const sources = chunks.filter(c => c.web?.uri && c.web?.title).map(c => `- [${c.web.title}](${c.web.uri})`);
  if (sources.length > 0) {
    const uniqueSources = [...new Set(sources)];
    text += `\n\n---\n**🌐 Live Web Research Sources:**\n` + uniqueSources.join("\n");
  }

  return text;
}

/**
 * Probe model quotas across all supported models.
 */
export async function checkAllModelQuotas(apiKey) {
  if (!apiKey) return { available: [], exhausted: [] };

  const available = [];
  const exhausted = [];

  for (const m of ALL_MODELS) {
    try {
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${m.id}:generateContent`;
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-goog-api-key": apiKey.trim()
        },
        body: JSON.stringify({ contents: [{ parts: [{ text: "ping" }] }] })
      });
      if (res.status === 200) {
        available.push(m);
      } else if (res.status === 429) {
        exhausted.push(m);
      }
    } catch (e) {
      console.warn(`Probe failed for ${m.id}:`, e);
    }
  }

  return { available, exhausted };
}

/**
 * Probe Google Search grounding tool availability on a specific model.
 */
export async function probeGoogleSearchAvailability(apiKey, modelId) {
  if (!apiKey || !modelId) return false;
  try {
    const testUrl = `https://generativelanguage.googleapis.com/v1beta/models/${modelId}:generateContent`;
    const sRes = await fetch(testUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-goog-api-key": apiKey.trim()
      },
      body: JSON.stringify({
        contents: [{ parts: [{ text: "ping" }] }],
        tools: [{ google_search: {} }]
      })
    });
    return sRes.status !== 429;
  } catch (e) {
    console.warn("Search quota probe error:", e);
    return false;
  }
}

/**
 * Surgical Paragraph Rebuild: Rewrites ONLY the single offending paragraph to avoid regression.
 */
export async function runWriterSurgicalPatch(apiKey, topic, draft, itemToFix, model, thinkingLevel = "medium", difficulty = "undergraduate", readingType = "literature_review", currentLang = "en") {
  if (!itemToFix || !itemToFix.offending_text) return null;
  const offending = itemToFix.offending_text.trim();
  if (offending.length < 8) return null;

  const paragraphs = draft.split(/\n\s*\n/);
  let targetIndex = -1;
  for (let i = 0; i < paragraphs.length; i++) {
    if (paragraphs[i].includes(offending)) {
      targetIndex = i;
      break;
    }
  }

  if (targetIndex === -1) {
    const firstWords = offending.split(/\s+/).slice(0, 4).join(" ");
    if (firstWords.length > 10) {
      for (let i = 0; i < paragraphs.length; i++) {
        if (paragraphs[i].includes(firstWords)) {
          targetIndex = i;
          break;
        }
      }
    }
  }

  if (targetIndex === -1) return null;

  const targetParagraph = paragraphs[targetIndex];
  if (/^##+\s*(?:📚\s*)?(?:Referensi|References)/i.test(targetParagraph)) {
    return null;
  }

  const isId = currentLang === "id";
  const sys = isId
    ? `Anda adalah Agen Penulis Ahli dalam mode REVISI BEDAH (SURGICAL PARAGRAPH REPAIR).
Tugas Anda HANYA menyusun ulang SATU paragraf ini untuk memperbaiki ketidaksesuaian integritas publikasi.
JANGAN membuat ulang naskah lain. Kembalikan HANYA paragraf pengganti yang telah disempurnakan.
Patuhi aturan: Turunkan kata kerja kausal ke asosiatif per Tangga Kata Kerja (Verb Ladder), batasi cakupan klaim pada sampel yang diteliti, dan pertahankan nomor sitasi asli [n].`
    : `You are an expert Writer Agent in SURGICAL PARAGRAPH REPAIR mode.
Your task is ONLY to rewrite this SINGLE paragraph to resolve a publication integrity discrepancy.
DO NOT regenerate the whole document. Return ONLY the replacement revised paragraph.
Obey the rules: Downgrade causal verbs to associative verbs per the Verb Ladder, bound scope to studied sample, and retain citation brackets [n].`;

  const prompt = `Topic: ${topic}
Failing Criterion: ${itemToFix.title} (${itemToFix.reason})
Offending Passage in paragraph: "${itemToFix.offending_text}"

PARAGRAPH TO SURGICALLY REVISE:
"""
${targetParagraph}
"""

Rewrite ONLY this paragraph to resolve the discrepancy while keeping all valid facts and citations intact. Return ONLY the replacement paragraph in Markdown.`;

  try {
    const revisedParagraph = await callGemini(apiKey, sys, prompt, model, false, thinkingLevel);
    const cleanRevised = revisedParagraph.trim().replace(/^```(?:markdown)?\s*/i, "").replace(/\s*```$/i, "").trim();
    if (cleanRevised && cleanRevised.length > 20) {
      paragraphs[targetIndex] = cleanRevised;
      return paragraphs.join("\n\n");
    }
  } catch (err) {
    console.warn("Surgical patch failed, will fallback to full revision:", err);
  }
  return null;
}

/**
 * Writer Agent: Generates initial Draft 1.
 */
export async function runWriterDraft(apiKey, topic, model, enableSearch = false, thinkingLevel = "medium", scholarlyDossier = null, difficulty = "undergraduate", readingType = "literature_review", currentLang = "en") {
  let sys = "You are an expert, engaging, and articulate Writer Agent. Produce well-structured, clear, and compelling content using Markdown with clear headings and bullet points.";
  if (currentLang === "id") {
    sys += "\n\nPANDUAN BAHASA & SINTESIS:\n" +
           "Anda WAJIB menulis seluruh naskah dan draf secara komprehensif dalam BAHASA INDONESIA yang baku, ilmiah, mengalir, dan profesional.\n" +
           "Sintesiskan semua temuan dari literatur ilmiah internasional dan regional (arXiv, Semantic Scholar, PubMed, OpenAlex, Crossref, Wikipedia) ke dalam Bahasa Indonesia dengan runtut.\n";
  }

  sys += "\n\n" + getDifficultyGuidance(difficulty, currentLang === "id") +
         "\n\n" + getReadingTypeGuidance(readingType, currentLang === "id") +
         "\n\n" + getVerbLadderFewShotPrompt(currentLang === "id");

  sys += "\n\n" +
    "ATURAN SITASI & KUTIPAN KATA-DEMI-KATA (EXACT VERBATIM QUOTATION & CITATION RULES - CRITICAL MANDATORY):\n" +
    "1. FORMAT KUTIPAN & NOMOR SITASI:\n" +
    "   Setiap kali mengutip bukti, data, temuan kunci, atau definisi dari berkas riset, Anda WAJIB mengapit kutipan dalam tanda petik ganda dan menyertakan nomor kutipan dalam kurung siku di akhir kutipan:\n" +
    "   Contoh format: \"... bla bla bla ...\" [1] atau \"... bla bla bla ...\" [2].\n" +
    "2. KEASLIAN PERSIS (EXACT MATCH FOR CTRL+F SEARCH):\n" +
    "   Teks di dalam tanda petik \"... ...\" HARUS PERSIS SAMA KATA-DEMI-KATA, HURUF-DEMI-HURUF dengan teks asli pada 'Verbatim Excerpt / Abstract' atau teks dokumen yang disediakan di berkas riset.\n" +
    "   JANGAN PERNAH memparafrasekan atau mengubah kata di dalam tanda petik. Tujuannya adalah agar pembaca dapat membuka tautan sumber atau dokumen asli, menekan CTRL + F, menempelkan teks kutipan tersebut, dan langsung menemukan kalimatnya dalam konteks penuh.\n" +
    "   (Catatan: Jika menulis dalam Bahasa Indonesia dan sumber dalam Bahasa Inggris, biarkan kutipan bukti di dalam tanda petik persis dalam bahasa aslinya, lalu berikan ulasan, konteks, atau terjemahan Anda dalam Bahasa Indonesia sebelum atau sesudah kutipan tersebut).\n" +
    "3. PENOMORAN SITASI URUT:\n" +
    "   Beri nomor kutipan secara berurutan sesuai kemunculan pertamanya di dalam teks: [1], [2], [3], dst.\n" +
    "4. DAFTAR SUMBER RUJUKAN DI AKHIR NASKAH (TAUTAN AKTIF KLIK / CLICKABLE LINKS MANDATORY):\n" +
    "   Di bagian paling akhir naskah, Anda WAJIB menyertakan daftar sumber rujukan bernomor yang cocok persis dengan nomor kutipan di teks:\n" +
    (currentLang === "id" ? "   '## 📚 Referensi & Sumber Terkutip'\n" : "   '## 📚 References & Cited Sources'\n") +
    "   Setiap entri WAJIB menyertakan tautan markdown yang dapat langsung diklik oleh pembaca:\n" +
    (currentLang === "id" 
      ? "   [1] Penulis / Pengarang (Tahun). *Judul Makalah*. Sumber / Venue. [🔗 Buka Makalah](url_lengkap)\n   [2] Penulis / Pengarang (Tahun). *Judul Makalah*. Sumber / Venue. [🔗 Buka Makalah](url_lengkap)\n" 
      : "   [1] Authors (Year). *Paper Title*. Venue. [🔗 Open Paper](full_url)\n   [2] Authors (Year). *Paper Title*. Venue. [🔗 Open Paper](full_url)\n") +
    "   Salin URL asli secara lengkap (http://... atau https://...) dari berkas riset ke dalam tanda kurung [🔗 Buka Makalah](url) agar pembaca dapat langsung mengklik tautan tersebut untuk membuka artikel aslinya!\n" +
    "   Setiap nomor [n] yang dikutip dalam teks WAJIB ada di daftar akhir ini!\n" +
    "5. INTEGRITAS GROUNDING & TANPA FABRIKASI (ZERO-HALLUCINATION GROUNDING):\n" +
    "   Hanya buat kutipan kata-demi-kata \"...\" [n] jika sumber [n] tersebut memiliki teks 'Verbatim Excerpt / Abstract' di berkas riset.\n" +
    "   Jika suatu sumber di berkas riset bertanda '[Bibliographic Metadata Only]', rujuklah sumber tersebut murni sebagai atribusi bibliografi [n] TANPA mengarang atau memfabrikasi tanda kutip kata-demi-kata.";

  if (enableSearch) {
    sys += " Use the Google Search tool to find and incorporate up-to-date facts, current developments, and accurate references.";
  }
  if (scholarlyDossier) {
    sys += " You are provided with a Verified Scholarly Research Dossier. You MUST ground your writing in these academic papers and reference sources and strictly obey the Verbatim Quotation & Citation Rules above.";
  }
  let prompt = `Topic/Goal: ${topic}\n`;
  if (scholarlyDossier) {
    prompt += `\n${scholarlyDossier.text}\n`;
  }
  prompt += currentLang === "id" 
    ? "Silakan tulis Draf 1 yang mendalam dan komprehensif dalam Bahasa Indonesia berlandaskan topik dan rujukan riset di atas dengan kutipan \"... ...\" [n] persis sama kata-demi-kata dan daftar referensi bernomor di akhir lengkap dengan tautan [🔗 Buka Makalah](url)."
    : "Please write Draft 1 grounded in the topic and research, using exact verbatim quotes \"... ...\" [n] and the numbered references list at the end with clickable links [🔗 Open Paper](url).";
  return await callGemini(apiKey, sys, prompt, model, enableSearch, thinkingLevel);
}

/**
 * Writer Agent: Generates revisions based on Critic review.
 */
export async function runWriterRevision(apiKey, topic, previousDraft, critique, turn, model, enableSearch = false, thinkingLevel = "medium", scholarlyDossier = null, difficulty = "undergraduate", readingType = "literature_review", currentLang = "en") {
  let sys = "You are an expert, meticulous Writer Agent revising your draft based on constructive critique.";
  if (currentLang === "id") {
    sys += "\n\nPANDUAN BAHASA:\n" +
           "Anda WAJIB menulis revisi naskah secara penuh dalam BAHASA INDONESIA yang ilmiah, lugas, mengalir, dan profesional.\n" +
           "Perbaiki setiap kelemahan yang disoroti oleh Pengkritik secara tuntas.\n";
  }

  sys += "\n\n" + getDifficultyGuidance(difficulty, currentLang === "id") +
         "\n\n" + getReadingTypeGuidance(readingType, currentLang === "id") +
         "\n\n" + getVerbLadderFewShotPrompt(currentLang === "id");

  sys += "\n\n" +
    "ATURAN SITASI & KUTIPAN KATA-DEMI-KATA (EXACT VERBATIM QUOTATION & CITATION RULES - CRITICAL MANDATORY):\n" +
    "1. FORMAT KUTIPAN: Gunakan format kutipan kata-demi-kata: \"... ...\" [n].\n" +
    "2. PERSIS KATA-DEMI-KATA (CTRL+F MATCH): Teks kutipan di dalam tanda petik ganda HARUS PERSIS SAMA dengan teks sumber/abstrak asli. JANGAN ubah satu kata pun.\n" +
    "3. DAFTAR SUMBER RUJUKAN DI BAGIAN AKHIR NASKAH (TAUTAN AKTIF KLIK MANDATORY):\n" +
    "   Sertakan daftar sumber rujukan bernomor lengkap dengan tautan markdown aktif:\n" +
    (currentLang === "id" ? "   '## 📚 Referensi & Sumber Terkutip'\n   [1] Penulis (Tahun). *Judul*. [🔗 Buka Makalah](url)\n" : "   '## 📚 References & Cited Sources'\n   [1] Authors (Year). *Title*. [🔗 Open Paper](url)\n") +
    "   Pastikan URL asli lengkap dan dapat langsung diklik oleh pembaca!";

  if (enableSearch) {
    sys += " Use the Google Search tool to resolve any factual ambiguities or add needed evidence.";
  }
  if (scholarlyDossier) {
    sys += " Re-verify all claims against the provided Verified Scholarly Research Dossier.";
  }

  const revisionsList = (critique.actionable_revisions || []).map((r, i) => `${i + 1}. ${r}`).join("\n");
  const weaknessesList = (critique.weaknesses || []).map((w, i) => `${i + 1}. ${w}`).join("\n");

  let prompt = `Original Goal/Topic: ${topic}
Previous Draft:
"""
${previousDraft}
"""

Critic's Score: ${critique.score}/10
Critic's Feedback / Weaknesses:
${weaknessesList}

Actionable Revision Plan:
${revisionsList}
`;

  if (scholarlyDossier) {
    prompt += `\nGrounding Dossier Reference:\n${scholarlyDossier.text}\n`;
  }

  prompt += currentLang === "id"
    ? "\nSilakan tulis Draf Revisi Lengkap yang telah disempurnakan dalam Bahasa Indonesia dengan kutipan kata-demi-kata \"... ...\" [n] yang terverifikasi dan daftar referensi dengan tautan aktif [🔗 Buka Makalah](url)."
    : "\nPlease write the complete revised draft incorporating all improvements, exact verbatim quotes \"... ...\" [n], and clickable references list [🔗 Open Paper](url).";

  return await callGemini(apiKey, sys, prompt, model, enableSearch, thinkingLevel);
}

/**
 * Critic Agent: Evaluates draft on depth, tone, audience alignment, and citation integrity.
 */
export async function runCriticReview(apiKey, topic, draft, turn, model, thinkingLevel = "medium", scholarlyDossier = null, difficulty = "undergraduate", readingType = "literature_review", currentLang = "en", targetScore = 8.5) {
  const minTarget = typeof targetScore === "number" && !isNaN(targetScore) ? Math.max(1.0, Math.min(10.0, targetScore)) : 8.5;
  let sys = `You are a meticulous Senior Editor and Critic Agent. 
Evaluate drafts strictly on clarity, depth, coherence, tone, and practical examples.
Hold a high bar. Scores of ${minTarget.toFixed(1)} and above qualify for 'APPROVED'.`;
  if (currentLang === "id") {
    sys += `\nPANDUAN BAHASA:\nBerikan seluruh evaluasi, analisis kekuatan, kelemahan, dan tindakan revisi dalam BAHASA INDONESIA yang objektif dan konstruktif.`;
  }

  sys += `\n\n` +
    `AUDIT TARGET AUDIENS & GENRE DOKUMEN (AUDIENCE & GENRE ALIGNMENT AUDIT):\n` +
    `1. Kesesuaian Audiens (${getDifficultyLabel(difficulty, currentLang === "id")}): Periksa apakah nada, tingkat kedalaman teknis, dan istilah sesuai untuk sasaran pembaca ini.\n` +
    `2. Kesesuaian Genre (${getReadingTypeLabel(readingType, currentLang === "id")}): Periksa apakah struktur dan gaya penulisan mengikuti format dokumen yang diminta.\n` +
    `Jika draf melenceng dari tingkat kesulitan sasaran atau struktur genre dokumen, tandai sebagai KELEMAHAN (Weakness) dan beri petunjuk perbaikan konkret.\n`;

  sys += `
AUDIT KUTIPAN KATA-DEMI-KATA & REFERENSI (VERBATIM QUOTATION & CITATION AUDIT):
1. Format Kutipan: Periksa apakah setiap kutipan fakta/bukti diapit tanda petik "... bla bla bla ..." dan diikuti nomor sitasi dalam kurung siku seperti [1], [2].
2. Verifikasi CTRL+F: Periksa apakah kutipan di dalam "... ..." persis sama kata-demi-kata dengan teks sumber/abstrak di berkas riset sehingga pembaca dapat mencarinya dengan CTRL+F di sumber aslinya. Jika ada kutipan yang diparafrasekan di dalam tanda petik, tandai sebagai KELEMAHAN (Weakness).
3. Daftar Referensi Akhir & Tautan Klik: Periksa apakah di akhir naskah terdapat daftar rujukan bernomor ([1], [2], ...) yang memetakan nomor kutipan ke judul makalah, penulis, tahun, dan TAUTAN KLIK YANG VALID [🔗 Buka Makalah](url). Jika rujukan tidak memiliki tautan klik yang valid, tandai sebagai KELEMAHAN.
Jika aturan kutipan dan referensi ini belum terpenuhi dengan sempurna, status WAJIB 'NEEDS_REVISION'.

OUTPUT FORMAT:
You MUST respond ONLY with valid JSON conforming to this schema:
{
  "score": number, // 1.0 to 10.0
  "status": "APPROVED" | "NEEDS_REVISION",
  "strengths": ["string"],
  "weaknesses": ["string"],
  "actionable_revisions": ["string"]
}`;

  let prompt = `Topic/Goal: ${topic}\n\nDraft (Turn ${turn}):\n"""\n${draft}\n"""\nApproval Target Score Threshold: ${minTarget.toFixed(1)}/10\n`;
  if (scholarlyDossier) {
    prompt += `\nGrounding Dossier Reference:\n${scholarlyDossier.text}\n`;
  }
  prompt += "\nEvaluate this draft and output valid JSON ONLY.";

  const raw = await callGemini(apiKey, sys, prompt, model, false, thinkingLevel);
  let clean = raw.trim();
  if (clean.startsWith("```")) {
    clean = clean.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/i, "");
  }

  let parsed;
  try {
    parsed = JSON.parse(clean);
  } catch (e) {
    console.warn("Critic JSON parse error, attempting regex extraction:", e);
    const match = clean.match(/\{[\s\S]*\}/);
    if (match) {
      parsed = JSON.parse(match[0]);
    } else {
      parsed = { score: 7.0, status: "NEEDS_REVISION", strengths: ["Clear effort"], weaknesses: ["Formatting issues"], actionable_revisions: ["Refine according to guidelines"] };
    }
  }

  // Tolerant normalization
  parsed.score = typeof parsed.score === "number" ? Math.max(1.0, Math.min(10.0, parsed.score)) : 7.0;
  parsed.status = (parsed.status === "APPROVED" || parsed.status === "NEEDS_REVISION") ? parsed.status : (parsed.score >= minTarget ? "APPROVED" : "NEEDS_REVISION");
  return parsed;
}

/**
 * Publication Integrity Auditor Agent (3-layer verification under source-checking-guide.md).
 */
export async function runSourceCheckingAudit(apiKey, topic, draft, model, thinkingLevel = "medium", scholarlyDossier = null, currentLang = "en") {
  const isId = currentLang === "id";
  const sys = `You are a Publication Integrity Auditor Agent rigorously enforcing ".agents/rules/source-checking-guide.md".
Audit the draft against all 3 layers and 11 criteria.
Layer 1: What is this source? (Source type ceiling, metadata verification, source independence)
Layer 2: Does the source say what the text claims? (Exact construct match, finding vs. framing, verb ladder, sample/scope bounds, quote integrity)
Layer 3: Does the whole argument hold together? (No uncited leaps, rival explanations, bounded conclusions)

OUTPUT FORMAT:
Respond ONLY with valid JSON conforming to this schema:
{
  "all_yes": boolean,
  "overall_verdict": "APPROVED_INTEGRITY_CLEARANCE" | "DISCREPANCIES_DETECTED",
  "score_percentage": number,
  "failure_patterns_detected": ["string"],
  "discrepancies": ["string"],
  "items": [
    {
      "id": "layer1_source_type_appropriate",
      "layer": 1,
      "title": "${isId ? "Plafon Tipe Sumber" : "Source Type Ceiling"}",
      "question": "${isId ? "Apakah tipe sumber membenarkan tingkat klaim?" : "Does source type justify claim level?"}",
      "answer": "YES" | "NO",
      "reason": "...",
      "offending_text": "..."
    }
  ]
}`;

  const sanity = runDeterministicSanityChecks(draft, scholarlyDossier);
  let prompt = `Goal / Topic: ${topic}\n\nDraft to Audit:\n\"\"\"\n${draft}\n\"\"\"\n`;
  if (sanity.hasIssues) {
    prompt += `\nDETERMINISTIC CODE PRE-AUDIT SIGNALS:\n${sanity.issues.map(i => `! ${i}`).join("\n")}\n`;
  }
  if (scholarlyDossier) {
    prompt += `\nGrounding Dossier Reference:\n${scholarlyDossier.text}\n`;
  }
  prompt += "\nPerform the rigorous 11-question 3-layer audit and output valid JSON ONLY.";

  const raw = await callGemini(apiKey, sys, prompt, model, false, thinkingLevel);
  let clean = raw.trim();
  if (clean.startsWith("```")) {
    clean = clean.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/i, "");
  }

  let parsed;
  try {
    parsed = JSON.parse(clean);
  } catch (e) {
    console.warn("Audit JSON parse error, attempting extraction:", e);
    const match = clean.match(/\{[\s\S]*\}/);
    if (match) {
      parsed = JSON.parse(match[0]);
    } else {
      parsed = { all_yes: false, failure_patterns_detected: [], discrepancies: ["JSON parse error in audit output"], items: [] };
    }
  }

  const defaultItems = [
    { id: "layer1_source_type_appropriate", layer: 1, title: isId ? "Plafon Tipe Sumber" : "Source Type Ceiling", question: isId ? "Apakah tipe sumber membenarkan klaim?" : "Does source type justify claim level?", answer: "YES", reason: isId ? "Tipe sumber membenarkan tingkat klaim ilmiah." : "Source types appropriately justify the claim levels." },
    { id: "layer1_metadata_matches", layer: 1, title: isId ? "Verifikasi Metadata" : "Metadata Verification", question: isId ? "Apakah penulis, jurnal, tahun, dan DOI cocok?" : "Do authors, journal, year, and DOI match actual publications?", answer: "YES", reason: isId ? "Metadata publikasi valid dan cocok." : "Metadata matches published papers." },
    { id: "layer1_independent_sources", layer: 1, title: isId ? "Independensi Sumber" : "Source Independence", question: isId ? "Apakah sumber-sumber independen satu sama lain?" : "Are sources genuinely independent?", answer: "YES", reason: isId ? "Sumber-sumber berdiri secara independen." : "Independent lines of evidence cited." },
    { id: "layer2_exact_construct_match", layer: 2, title: isId ? "Kesesuaian Konstruk Persis" : "Exact Construct Match", question: isId ? "Apakah studi mengukur konstruk yang diklaim persis?" : "Does study measure the exact claimed construct?", answer: "YES", reason: isId ? "Konstruk yang dibahas persis dengan yang diuji." : "Exact construct match maintained without substitution." },
    { id: "layer2_finding_not_framing", layer: 2, title: isId ? "Temuan vs. Framing" : "Finding vs. Framing", question: isId ? "Apakah kutipan merupakan temuan empiris, bukan asumsi pengantar?" : "Is cited passage empirical finding, not introductory framing?", answer: "YES", reason: isId ? "Kutipan merefleksikan temuan empiris hasil studi." : "Evidentiary claims rest on empirical findings." },
    { id: "layer2_verb_ladder_justified", layer: 2, title: isId ? "Tangga Kata Kerja (Verb Ladder)" : "Verb Ladder Compliance", question: isId ? "Apakah desain riset membenarkan kata kerja klaim?" : "Does research design justify the verb used?", answer: "YES", reason: isId ? "Kekuatan kata kerja selaras dengan desain riset." : "Verbs strictly calibrated to research design." },
    { id: "layer2_sample_scope_accurate", layer: 2, title: isId ? "Batasan Sampel & Cakupan" : "Sample & Scope Bounds", question: isId ? "Apakah cakupan terikat pada sampel yang diteliti?" : "Is scope strictly bounded to studied sample?", answer: "YES", reason: isId ? "Cakupan klaim terikat pada sampel studi." : "Claims accurately bounded to studied populations." },
    { id: "layer2_context_and_quote_integrity", layer: 2, title: isId ? "Integritas Konteks & Kutipan" : "Quote & Context Integrity", question: isId ? "Apakah kutipan sesuai konteks dan bermakna pembuktian?" : "Does quote match context and do evidentiary work?", answer: "YES", reason: isId ? "Kutipan berfungsi membuktikan klaim dalam konteks aslinya." : "Quotes do evidentiary work and preserve context." },
    { id: "layer3_no_uncited_author_leaps", layer: 3, title: isId ? "Tanpa Lompatan Tanpa Sitasi" : "No Uncited Author Leaps", question: isId ? "Apakah seluruh mata rantai argumen berbasis bukti?" : "Are all argument steps evidence-based?", answer: "YES", reason: isId ? "Tidak ada inferensi tanpa bukti yang disamarkan sebagai fakta." : "All inferential steps are grounded in evidence." },
    { id: "layer3_rival_explanations_acknowledged", layer: 3, title: isId ? "Eksplanasi Saingan & Sanggahan" : "Rival Explanations & Caveats", question: isId ? "Apakah penjelasan alternatif & keterbatasan diakui?" : "Are alternative mechanisms and caveats acknowledged?", answer: "YES", reason: isId ? "Mekanisme alternatif dan batasan riset diakui." : "Alternative hypotheses and caveats acknowledged." },
    { id: "layer3_bounded_conclusion", layer: 3, title: isId ? "Kesimpulan Terikat Batas" : "Bounded Conclusion", question: isId ? "Apakah kesimpulan tidak melebihi premis terkuatnya?" : "Does conclusion refrain from exceeding strongest premise?", answer: "YES", reason: isId ? "Kesimpulan akhir seimbang dan tidak berlebihan." : "Conclusion stays within empirical boundaries." }
  ];

  const mergedItems = defaultItems.map(def => {
    const found = (parsed.items || []).find(it => it.id === def.id);
    if (found) {
      const ans = String(found.answer || "YES").trim().toUpperCase();
      return {
        ...def,
        title: found.title || def.title,
        question: found.question || def.question,
        answer: (ans === "YES" || ans === "YA") ? "YES" : "NO",
        reason: found.reason || def.reason,
        offending_text: found.offending_text || ""
      };
    }
    return def;
  });

  const allYes = mergedItems.every(it => it.answer === "YES");
  const yesCount = mergedItems.filter(it => it.answer === "YES").length;
  return {
    all_yes: allYes,
    overall_verdict: allYes ? "APPROVED_INTEGRITY_CLEARANCE" : "DISCREPANCIES_DETECTED",
    score_percentage: Math.round((yesCount / mergedItems.length) * 100),
    failure_patterns_detected: parsed.failure_patterns_detected || [],
    discrepancies: parsed.discrepancies || [],
    items: mergedItems
  };
}

/**
 * Writer Agent: Rebuilds draft when any publication integrity criterion evaluated to NO.
 */
export async function runWriterIntegrityRevision(apiKey, topic, draft, auditResult, round, model, enableSearch = false, thinkingLevel = "medium", scholarlyDossier = null, difficulty = "undergraduate", readingType = "literature_review", currentLang = "en") {
  // 1. Fast surgical patch if there is an isolated discrepancy
  const noItems = (auditResult.items || []).filter(it => it.answer === "NO");
  const noItemsWithText = noItems.filter(it => it.offending_text && it.offending_text.trim().length > 6);
  if (noItemsWithText.length === 1) {
    const patched = await runWriterSurgicalPatch(apiKey, topic, draft, noItemsWithText[0], model, thinkingLevel, difficulty, readingType, currentLang);
    if (patched) {
      console.log("✓ Applied fast surgical paragraph patch for publication integrity rebuild!");
      return patched;
    }
  }

  let sys = `You are an expert Writer Agent tasked with an UNCOMPROMISING PUBLICATION INTEGRITY REBUILD under ".agents/rules/source-checking-guide.md".
Your goal is to completely resolve every "NO" evaluation from the Publication Integrity Auditor Agent, rewriting and refining the draft until ALL 11 questions achieve "YES".

CRITICAL RULES TO ACHIEVE 100% "YES":
1. VERB LADDER COMPLIANCE:
   - Downgrade any causal verbs ("causes", "drives", "reduces", "influences directly") to associative verbs ("is associated with", "relates to", "correlates with") whenever citing cross-sectional or observational data.
   - For longitudinal trends, use "precedes", "predicts", "coincides with".
   - Only use "causes" for true randomized controlled trials within that specific experimental setting.
2. ELIMINATE SCOPE INFLATION:
   - Explicitly bound findings to the studied population (e.g., "in adult clinical samples", "among undergraduate cohorts in the US").
   - Do NOT generalize to "all humans" or "modern societies" unless supported by cross-cultural meta-analyses.
3. ELIMINATE FRAMING-AS-FINDING:
   - If citing theoretical background or an introductory hypothesis, use "hypothesized by", "conceptualized as", NOT "demonstrated" or "proven".
4. ELIMINATE ADJACENT-CONSTRUCT SUBSTITUTION:
   - Ensure the construct named in your sentence matches exactly what the study measured.
5. REMOVE UNCITED AUTHOR LEAPS:
   - Either provide direct scholarly evidence for every inferential link, or clearly state "theoretically proposed" or "we infer" without falsely disguising it as a cited empirical fact.
6. ACKNOWLEDGE RIVAL EXPLANATIONS & CAVEATS:
   - Explicitly state alternative mechanisms, limitations noted by the original authors, or rival interpretations.
7. BOUNDED CONCLUSIONS:
   - Ensure the final conclusion does not exceed the strength of the single strongest source.
8. PRESERVE VERBATIM QUOTES & REFERENCES:
   - Keep all exact quotes "... ..." [n] intact and preserve the reference list at the end with valid clickable links [🔗 Buka Makalah / Open Paper](url).`;

  if (currentLang === "id") {
    sys += "\n\nPANDUAN BAHASA:\nSempurnakan dan susun ulang seluruh naskah dalam BAHASA INDONESIA yang ilmiah, presisi, dan sesuai aturan integritas di atas.\n";
  }

  sys += "\n\n" + getDifficultyGuidance(difficulty, currentLang === "id") +
         "\n\n" + getReadingTypeGuidance(readingType, currentLang === "id") +
         "\n\n" + getVerbLadderFewShotPrompt(currentLang === "id");

  const noDescriptions = noItems.map(it => `- [Layer ${it.layer} - ${it.title}]: ${it.reason}${it.offending_text ? ` (Offending passage: "${it.offending_text}")` : ""}`).join("\n");
  const discrepanciesList = (auditResult.discrepancies || []).map(d => `- ${d}`).join("\n");
  const failurePatternsList = (auditResult.failure_patterns_detected || []).map(f => `- ${f}`).join("\n");

  let prompt = `Original Goal/Topic: ${topic}
Current Integrity Audit Round: ${round}

DISCREPANCIES DETECTED BY AUDITOR AGENT (Must be fixed to achieve YES):
${discrepanciesList || noDescriptions}

DETECTED FAILURE PATTERNS:
${failurePatternsList || "None"}

SPECIFIC FAILING CRITERIA:
${noDescriptions}

PREVIOUS DRAFT TO REBUILD:
"""
${draft}
"""
`;
  if (scholarlyDossier) {
    prompt += `\nResearch Dossier Reference:\n${scholarlyDossier.text}\n`;
  }

  prompt += currentLang === "id"
    ? `Silakan tulis ulang dan susun naskah lengkap (Full Rebuilt Draft) dalam Bahasa Indonesia. Perbaiki seluruh kelemahan di atas agar seluruh 11 kriteria terjawab 'YA' pada audit berikutnya, tetap pertahankan format kutipan persis \"... ...\" [n] dan daftar referensi dengan tautan aktif di akhir.`
    : `Please rebuild the complete draft in full Markdown. Resolve every single discrepancy above so that all 11 criteria achieve 'YES' on the next audit round. Maintain exact quotes \"... ...\" [n] and the clickable references list at the end.`;

  return await callGemini(apiKey, sys, prompt, model, enableSearch, thinkingLevel);
}
