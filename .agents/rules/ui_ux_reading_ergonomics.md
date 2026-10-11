# Universal UI/UX Design & Digital Reading Ergonomics Guardrails

When designing, implementing, or styling web interfaces, reading layouts, and mobile-responsive applications, adhere strictly to the following ergonomic standards and anti-pattern guardrails.

---

## 1. Typographic Measure & Long-Form Reading Ergonomics
- **The Golden Measure**: Constrain reading containers to `max-width: 65ch` to `75ch` on desktop (`max-width: 72ch; margin: 0 auto;`), and `35ch` to `50ch` on mobile screens to eliminate saccadic eye wandering and line re-reading.
- **Generous Leading**: Set `line-height` between `1.6` and `1.75` for body text. Dense leading strains the eyes during deep reading sessions.
- **Fluid & Scalable Typography**: Never lock the font size. Provide user-controllable font steppers (`A- / A / A+`) and typeface toggles (Editorial Serif for deep reading vs. Clean Modern Sans for technical scanning).
- **Default Font Size**: Use a comfortable base font size (`16px–18px` / `1rem–1.1rem`) with fluid responsive scaling via `clamp()`.

---

## 2. Quotation & Academic Evidence Callout Invariants
- **NEVER use `box-decoration-break: clone` with borders on multi-line text**:
  - *Anti-Pattern*: Applying `display: inline`, `border-left: 3px`, and `border-radius` with `box-decoration-break: clone` breaks every wrapped line into an isolated rounded pill with its own vertical stripe, creating an unsightly column of fragmented boxes.
- **Two-Tier Quotation Pattern**:
  1. **Block / Standalone Quotes (`.verbatim-quote-block`)**:
     - Use `<blockquote class="verbatim-quote-block">` for quotes that occupy their own line or paragraph.
     - Render with a **single continuous vertical left border** (`border-left: 3.5px solid var(--quote-border)`).
     - Render with **one uniform background tint** (`background: var(--quote-bg)`).
     - Use soft rounded corners on the right (`border-radius: 0 0.75rem 0.75rem 0`).
     - Text must flow naturally as italic editorial prose with line-height ~1.72.
     - Citation anchors (`[1]`) must sit cleanly inline at the end of the quotation.
  2. **Inline Quotes (`.verbatim-quote`)**:
     - In-text quotes embedded inside sentences must flow naturally without vertical borders or box fragmentation (`border: none !important; display: inline;`).

---

## 3. Optical Palettes & Theme Synchronization
- **Provide 4 Core Reading Environments**:
  1. *Warm Sepia (Paper / Kindle style)*: Soft amber/parchment background (`#F8F5EE`), warm charcoal text (`#2D2820`), chestnut borders.
  2. *Midnight Slate (Soft Dark Mode)*: Deep blue-slate (`#0B0F19`), crisp slate text (`#E2E8F0`), electric cyan accents.
  3. *Nordic Daylight (Editorial Light)*: Crisp editorial paper (`#F8FAFC`), deep navy typography (`#0F172A`).
  4. *OLED Pure Black (Battery Saver)*: Pure `#000000`, zinc typography (`#D4D4D8`).
- **Dynamic Mobile Status Bar Sync**: Always dynamically update `<meta name="theme-color">` whenever the user toggles a theme so the mobile browser top chrome (address bar and OS status bar) seamlessly matches the content background without harsh color borders.

---

## 4. Mobile-First Progressive Disclosure & Touch Ergonomics
- **Combat Screen Congestion**: On smartphone viewports (< 640px), preserve vertical screen real estate above the fold:
  - *Single-Row App Bar*: Replace tall, multi-row headers with a slim 48–52px native app bar.
  - *Auto-Collapsing State Badges*: Once persistent data (e.g. API keys or user profiles) is saved in `localStorage`, collapse bulky form cards into a clean 1-line badge (`✓ Configured (••••••••) [Edit]`) with an immediate `[Edit]` re-expansion toggle.
  - *Collapsible Parameter Accordions*: Fold deep settings (iterations, reasoning levels, threshold scores) into `<details>` with live summary pills (`🧠 Medium • 3 Turns • Target 9.5`). Default to collapsed on mobile (< 768px) and expanded on desktop.
  - *Responsive 2-Column Chip Grids*: Replace tall stacked card lists with compact 2-column chips and batch action buttons (`[Select All]` / `[Clear]`).
- **Touch-Friendly Citation & Interaction Model**:
  - Desktop (`>= 640px`): Show floating cursor tooltips on hover.
  - Mobile (`< 640px`): Tap events must trigger a native-style **Bottom Sheet Drawer** sliding up with `transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1)`.
  - Provide large 48px touch-target action buttons (`🔗 Open Source ↗`) and intuitive backdrop tap-to-dismiss.
- **Zero Horizontal Overflow**: Guarantee `scrollWidth <= clientWidth` on all viewport widths down to 375px. Fluid card padding should step down to `p-4` on mobile and `p-6` on desktop.
