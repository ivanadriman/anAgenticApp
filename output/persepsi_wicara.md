# Final Draft: Persepsi wicara

**Language:** `ID`
**Model:** `gemini-3.5-flash-lite`
**Thinking Mode:** `medium`
**Web Search:** `Disabled`
**Academic Grounding Sources:** `8 source(s) active`
**Final Score:** 9.2/10.0
**Total Iterations:** 1

## Content

# Persepsi Wicara: Tinjauan Komputasi, Neurosains, dan Integrasi Sensorimotor

## Pendahuluan

Persepsi wicara adalah proses kompleks di mana sistem pendengaran dan kognitif manusia menguraikan sinyal akustik atau isyarat audiovisual menjadi representasi linguistik yang bermakna. Memahami mekanisme ini tidak hanya krusial bagi ilmu saraf kognitif, tetapi juga mendasari pengembangan teknologi kecerdasan buatan, seperti evaluasi kualitas wicara sintetik dan antarmuka otak-komputer (*brain-computer interface* / BCI) [1, 2]. 

Penelitian modern menggabungkan pemodelan komputasi terinspirasi biologi, perekaman aktivitas intrakranial, serta analisis neuroimaging untuk memetakan bagaimana otak manusia memproses dan merepresentasikan wicara.

---

## 1. Pemodelan Komputasi dan Persepsi Auditori

Penilaian kualitas wicara otomatis berupaya meniru penilaian subjektif manusia menggunakan model komputasi. Sebagaimana dinyatakan dalam literatur mengenai model APG-MOS: 
> `"Automatic speech quality assessment aims to quantify subjective human perception of speech through computational models to reduce the need for labor-consuming manual evaluations."` [1]

Meskipun model pembelajaran mendalam telah berkembang pesat, pengabaian terhadap mekanisme persepsi auditori fundamental seringkali membatasi konsistensi model dengan penilaian manusia [1]. Untuk mengatasi hal ini, pendekatan terkini merancang modul perseptual yang berakar pada mekanisme auditori biologis guna mensimulasikan fungsi koklea, yang kemudian dikombinasikan dengan analisis semantik [1].

Selain itu, dalam pemodelan persepsi fonetik, kerangka kerja baru telah dikembangkan untuk meniru cara manusia memproses bukti akustik. Seperti yang diusulkan oleh Guo dan rekan-rekan melalui kerangka kerja HuPER:
> `"We propose HuPER, a human-inspired framework that models phonetic perception as adaptive inference over acoustic-phonetics evidence and linguistic knowledge."` [3]

Kerangka kerja semacam ini mampu mencapai tingkat kesalahan fonetik yang rendah di berbagai bahasa serta mendukung persepsi fonetik adaptif multi-jalur di bawah kondisi akustik yang beragam [3].

---

## 2. Dekode Aktivitas Otak Selama Mendengarkan dan Memproduksi Wicara

Studi neurosaintifik kontemporer juga berfokus pada upaya mendekode aktivitas listrik di otak saat seseorang mendengarkan wicara. Penelitian oleh Fodor et al. menggunakan data *intracranial electroencephalographic* (iEEG) dengan metode pembelajaran mendalam:
> `"The aim of the study is to investigate the complex mechanisms of speech perception and ultimately decode the electrical changes in the brain accruing while listening to speech."` [2]

Pendekatan ini mengalihkan fokus konvensional dari produksi wicara menuju investigasi representasi saraf dari wicara yang dipersepsikan, guna memperkuat teknologi BCI [2]. 

Pada ranah non-invasif, tantangan decoding sinyal *electroencephalography* (EEG) untuk kalimat yang kompleks (seperti bahasa Mandarin) dijembatani oleh kerangka kerja efisien parameter seperti **EEGAlign**. Metode ini menyelaraskan EEG dengan penyematan teks dan fitur wicara melalui pembelajaran kontrastif (*contrastive learning*) [4].

---

## 3. Peran Isyarat Visual dalam Persepsi Wicara Audiovisual

Persepsi wicara jarang terjadi secara eksklusif melalui saluran auditori; isyarat visual seperti gerakan bibir (*lipreading*) memainkan peran penting. Berdasarkan temuan dari rekaman iEEG pada girus temporal superior (*superior temporal gyrus* / STG):
> `"Visual speech, such as lipreading, facilitates spoken word recognition, but the neural mechanisms underlying audiovisual speech perception remain poorly understood."` [5]

Lebih lanjut, analisis menunjukkan bahwa penglihatan tidak sekadar memperkuat semua informasi terkait wicara secara merata. Sebaliknya, masukan visual secara selektif mempertajam representasi fonetik yang bersifat kategoris di dalam korteks auditori:
> `"Seeing a speaker’s face improves speech perception, especially in noise, but the neural representations altered by visual speech remain unclear."` [5]

Hal ini mengklarifikasi bahwa fasilitasi audiovisual bekerja secara primer pada representasi wicara kategoris yang mendukung pengenalan kata secara langsung [5].

---

## 4. Representasi Sensorimotor dalam Produksi Terselubung (*Covert Speech*)

Persepsi dan produksi wicara juga terhubung erat melalui mekanisme internal, seperti saat seseorang berbicara dalam hati (*inner speaking*). Orpella dan rekan-rekannya menyelidiki dinamika saraf selama produksi suku kata terselubung:
> `"Inner speaking-the deliberate generation of speech through covert production mechanisms-is a common human experience."` [7]

Hasil studi ini menunjukkan bahwa korteks motorik wicara dan korteks auditori mempertahankan struktur temporal dan granularitas yang mirip dengan wicara terbuka (*overt speech*), di mana kontras artikulasi dan akustik diproses secara terstruktur pada tahapan yang spesifik [7].

---

## Kesimpulan

Persepsi wicara melibatkan interaksi canggih antara mekanisme koklea biologis, pemrosesan semantik, integrasi audiovisual di girus temporal superior, serta dinamika sensorimotor internal. Integrasi antara temuan neurosaintifik (iEEG/EEG) dan model komputasi prediktif (seperti APG-MOS, HuPER, dan EEGAlign) membuka jalan baru menuju pemahaman kognitif yang lebih mendalam serta pengembangan teknologi antarmuka otak-komputer yang canggih di masa depan.

---

## 📚 Referensi & Sumber Terkutip

[1] Zhicheng Lian, Lizhi Wang, Hua Huang (2025). *APG-MOS: Auditory Perception Guided-MOS Predictor for Synthetic Speech*. arXiv:2504.20447. [http://arxiv.org/abs/2504.20447](http://arxiv.org/abs/2504.20447)

[2] Milán András Fodor, Tamás Gábor Csapó, Frigyes Viktor Arthur (2024). *Towards Decoding Brain Activity During Passive Listening of Speech*. arXiv:2402.16996. [http://arxiv.org/abs/2402.16996](http://arxiv.org/abs/2402.16996)

[3] Chenxu Guo, Jiachen Lian, Yisi Liu (2026). *HuPER: A Human-Inspired Framework for Phonetic Perception*. arXiv:2602.01634. [https://arxiv.org/abs/2602.01634](https://arxiv.org/abs/2602.01634)

[4] Tian Zheng, Xurong Xie, Xinxin Zhu (2026). *Joint Text-Audio Alignment for EEG-to-Text Decoding in Chinese Speech Production and Perception*. arXiv:2607.25626. [https://arxiv.org/abs/2607.25626](https://arxiv.org/abs/2607.25626)

[5] Li Y, DeWitt I, Brennan JR (2026). *Visual speech enhances phoneme separability in human superior temporal gyrus*. PubMed / DOI. [https://doi.org/10.64898/2026.09.10.750762](https://doi.org/10.64898/2026.09.10.750762)

[6] Researchers (2026). *Visual speech enhances phoneme separability in human superior temporal gyrus*. PubMed Central. [https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13622663/](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13622663/)

[7] Orpella J, Mantegna F, Oderbolz C (2026). *Temporally structured motor and auditory representations in covert syllable production*. PubMed Central. [https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13578806/](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13578806/)

[8] Olivares C, Schettini N. (Recent). *A high-precision synchronization and centroid-based framework for single-trial decoding of perceived natural speech*. PubMed Central. [https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13642302/](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13642302/)

---
## Revision History & Critic Log

### Draft 1 (Score: 9.2/10)
**Critic Status:** `APPROVED`
**Actionable Feedback:**
- Kombinasikan beberapa kutipan langsung dengan parafrase analitis untuk membuat alur bacaan lebih mengalir alami.

