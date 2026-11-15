# MUTUAL CONFIDENTIALITY / NDA & SAMPLE REDACTION CHECKLIST

**Purpose:** Zero-friction mutual confidentiality agreement + redaction checklist for `$10M–$50M` commercial specialty contractors sharing 3 sample historical bids, plan sheets, or work orders for a **Senior Estimator Co-Pilot** proof-of-concept.

---

## 1. Mutual Confidentiality Terms (Summary Form — Pre-Assessment)
1. **Parties & Effective Date:** Between **Recipient (`[COMPANY_NAME]`)** and **LUNORA Engineering / Certified AI Partners**, effective as of the date of file handoff (`[DATE]`).
2. **Confidential Information:** Includes any uploaded plans, takeoffs, vendor unit-price sheets, markup formulas, historical quote spreadsheets, or frontline crew interview notes.
3. **Strict Non-Training & Zero-Retention Guarantee:** Client sample files are processed exclusively through isolated API endpoints under zero-training commercial terms (`earnest-reactor-511010-r9`) and local APFS SQLite WAL storage on an air-scoped workstation. **No client drawings, margins, or customer names are ever used to train public foundation models or shared with third parties.**
4. **Return / Destruction:** Within 7 days of written request (or immediately if Engagement does not proceed past the diagnostic), all uploaded sample PDFs/PNGs and cached JSON extracts are permanently deleted (`sqlite3 VACUUM` + secure unlink).
5. **Survival:** Confidentiality obligations remain in effect for **two (2) years** following final file handoff.

**Authorized Sign-Off (Email Reply Acceptance Valid):**
- Client Authorized Representative: `_________________________` (`[TITLE]`, `[COMPANY_NAME]`)
- Provider Authorized Representative: `_________________________` (LUNORA Engineering)

---

## 2. 3-Bullet Pre-Handoff Redaction Checklist (Under 5 Minutes)
Before sending **3 redacted sample job files** (ideal mix: 1 clean standard job, 1 blurry/marked-up field change order, 1 complex multi-trade bid):
- [ ] **Strip Client PII & Site Addresses:** Black out customer names, billing contacts, phone numbers, emails, and exact street addresses on plan title blocks.
- [ ] **Mask Sensitive Overhead / Net Margin Formulas:** Keep unit labor hours, equipment classes, and raw quantities visible; redact proprietary corporate net-profit multipliers or banking details.
- [ ] **Leave Ambiguous Notes & Handwritten Markups Intact:** Do *not* pre-clean blurry scans, mixed-scale annotations, or weld/utility exclusion footnotes—our Senior Estimator Co-Pilot explicitly surfaces `human_verify_flags` and `confidence` (`HIGH | MEDIUM | LOW`) with sheet/section citations so your lead estimator can validate edge cases in seconds.
