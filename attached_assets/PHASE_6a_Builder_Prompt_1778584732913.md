# PHASE 6a — Criteria Realignment (Accordion + Checkboxes)

## Context for Builder

This is Phase 6a of the TSM2 Submission Portal update. Phases 1-5 are complete (v1.0 stamped).

The criteria set has been updated based on the Institute's actual review practice. The old 9-criteria set (from Phases 1-3) is being replaced with a new 9-criteria set that better reflects how submissions are actually evaluated. This phase updates the **frontend only** — the criteria accordion and the self-certification checkboxes in `index.html`. No server changes.

**Important context:** The self-certification checkboxes are becoming **informational only**. They still appear on the form and the submitter still checks them, but the AI pre-check (Phase 6b) will assess the PDF content directly, not these checkboxes. The checkboxes serve as a self-check for the submitter: "Have I addressed this in my PDF?"

---

## 1. The New 9 Criteria

These replace the previous set entirely.

| # | Name | What It Requires |
|---|------|-----------------|
| 1 | **Clear Singular Claim** | A single, identifiable, operationally testable claim. Not compound, not vague, not metaphorical. |
| 2 | **Defined Terms and Ontology** | All key technical terms operationally defined. Mathematical layer separated from empirical layer where applicable. |
| 3 | **Causal Mechanism** | A physical or structural mechanism proposed that explains why the claim holds. Must be more than analogy or mathematics alone. |
| 4 | **Empirical Test Path** | An explicit, operationalised test the claim could be subjected to. Pre-registered criteria, quantitative thresholds, or specified methodology. |
| 5 | **Falsifiability** | A clear, measurable condition that would defeat the claim if observed. An explicit binary falsifier with a threshold, not a vague gesture. |
| 6 | **Dependency Transparency** | Author explicitly acknowledges assumptions, limitations, interpretive judgements, and future formalisation requirements. |
| 7 | **Non-Arbitrary Selection** | Analysis protected against confirmation bias, cherry-picking, and post-hoc selection. Target defined before the search, not selected from it. |
| 8 | **Predictive Capability** | The claim generates at least one novel, testable prediction of undiscovered phenomena. Not just re-description of existing data. |
| 9 | **Reproducibility** | An independent reviewer could follow the methodology to replicate the analysis from the description provided. |

### What changed from the old set:

| Removed | Replaced by / rationale |
|---------|------------------------|
| Declared Assumptions | Folded into Criterion 6 (Dependency Transparency) — broader and more useful |
| Energy / Conservation Consistency | Removed — too narrow for a general-purpose gate |
| Scale Consistency | Removed — subsumed by Criterion 1 (claim clarity) and Criterion 3 (mechanism) |
| Category Integrity | Removed — subsumed by Criterion 3 (causal mechanism must be physical, not metaphorical) |

| Added | Rationale |
|-------|-----------|
| Non-Arbitrary Selection (7) | Protects against confirmation bias — critical for scientific submissions |
| Predictive Capability (8) | Distinguishes genuine theory from pattern-matching and re-description |
| Reproducibility (9) | Standard scientific requirement — can someone else replicate this? |

---

## 2. Update the Criteria Accordion (Landing Page)

Replace the current 10-item accordion (criteria 1-9 plus examiner-only criterion 10) with a new 10-item accordion reflecting the updated criteria.

### New Accordion Items:

**1. Clear Singular Claim**
The submission must state a single, identifiable, operationally testable claim. The claim must not be compound, vague, or metaphorical. If the claim contains multiple independent assertions, or cannot in principle be tested, it does not meet this criterion.

**2. Defined Terms and Ontology**
All key technical terms must be operationally defined and used consistently. Where applicable, the mathematical layer must be separated from the empirical layer. Undefined terminology, circular definitions, or inconsistent usage results in non-compliance.

**3. Causal Mechanism**
The submission must propose a physical or structural mechanism that explains why the claim holds. The mechanism must go beyond analogy, metaphor, or mathematical description alone. If the paper explicitly disclaims causality, this criterion fails.

**4. Empirical Test Path**
The submission must specify an explicit, operationalised test the claim could be subjected to. This means pre-registered criteria, quantitative thresholds, or a specified methodology — not a vague suggestion that testing could theoretically occur.

**5. Falsifiability**
There must be a clear, measurable condition that would defeat the claim if observed. An explicit binary falsifier with a defined threshold — not a qualitative gesture or a condition that the framework could absorb through reinterpretation. If it cannot fail, it cannot pass.

**6. Dependency Transparency**
The author must explicitly acknowledge their assumptions, observational limitations, interpretive judgements, and any future formalisation requirements. Hidden premises or undeclared dependencies invalidate compliance.

**7. Non-Arbitrary Selection**
The analysis must be protected against confirmation bias, cherry-picking, and post-hoc selection. The analysis target must be defined before the search, not selected from it. Pre-registered selection criteria and blind sampling strengthen compliance.

**8. Predictive Capability**
The claim must generate at least one novel, testable prediction of undiscovered phenomena. Re-description, classification, or reinterpretation of existing data alone is insufficient. The prediction must be derivable from the claim and independently verifiable.

**9. Reproducibility**
An independent reviewer must be able to follow the methodology to replicate the analysis from the description provided. Methodology, data sources, and inclusion criteria must be explicit. Significant reliance on subjective judgement weakens compliance.

**10. Why Is This Claim True? — *Examiner Assessment Only***
*(Keep the same visual treatment as before — greyed out or distinct badge saying "Examiner Only")*

The Examiner evaluates whether the submission answers in structured causal form: **"Because X interacts with Y, therefore Z"** — where X is the causal driver, Y is the interacting condition, and Z is the necessary outcome. This criterion is assessed by the qualified examiner, not by the submitter or the AI pre-check.

### Accordion subtitle text:

Update the subtitle above the accordion from:
> "All submissions are evaluated against these 9 structural criteria. Your PDF document must address each one. Criterion 10 is assessed by the Examiner only."

To:
> "All submissions are evaluated against these 9 structural criteria. The AI pre-check assesses your PDF content directly against each criterion. Criterion 10 is assessed by the Examiner only."

---

## 3. Update the Self-Certification Checkboxes (Step 3)

### Step subtitle text:

Change the Step 3 subtitle from:
> "Your PDF document is the authoritative record. Please confirm it addresses each of the following structural criteria. All boxes must be checked to proceed."

To:
> "Your PDF document is the authoritative record and will be assessed directly by the AI pre-check. As a self-check, please confirm your PDF addresses each of the following. All boxes must be checked to proceed."

### Replace the 6 checkboxes with the following 8 checkboxes:

The old checkboxes mapped to old criteria 2, 3, 4, 5, 6, 9. The new checkboxes map to all criteria except Criterion 1 (already captured by the Core Claim field) and Criterion 5 (already captured by the Falsifiability field). That leaves 7 criteria needing checkboxes. However, Criterion 5 (Falsifiability) in the new set is stricter than the old version — it specifically requires a measurable threshold. So we add a checkbox for it too, making 8 checkboxes total.

**New checkboxes (all required):**

**☐ Terms Defined** *(Criterion 2)*
Helper: "My PDF operationally defines all key technical terms and separates mathematical from empirical claims where applicable."

**☐ Causal Mechanism Described** *(Criterion 3)*
Helper: "My PDF proposes a physical or structural mechanism explaining why the claim holds — not just analogy or mathematics."

**☐ Empirical Test Path Specified** *(Criterion 4)*
Helper: "My PDF specifies an operationalised test with pre-registered criteria, quantitative thresholds, or defined methodology."

**☐ Falsifiability Condition with Threshold** *(Criterion 5)*
Helper: "My PDF states a clear, measurable condition that would defeat the claim, with a defined threshold."

**☐ Dependencies and Limitations Declared** *(Criterion 6)*
Helper: "My PDF explicitly acknowledges assumptions, observational limitations, and interpretive judgements."

**☐ Selection Criteria Pre-Defined** *(Criterion 7)*
Helper: "My PDF defines the analysis target before the search, with protection against confirmation bias and cherry-picking."

**☐ Novel Predictions Derived** *(Criterion 8)*
Helper: "My PDF derives at least one novel, testable prediction — not just re-description of existing data."

**☐ Methodology Reproducible** *(Criterion 9)*
Helper: "My PDF provides enough methodological detail for an independent reviewer to replicate the analysis."

### Data model update:

Replace the old boolean fields in the Alpine.js `form` object:

```javascript
// OLD — remove these
criteria_definitions: false,    // was Criterion 2
criteria_assumptions: false,    // was Criterion 3
criteria_mechanism: false,      // was Criterion 4
criteria_energy: false,         // was Criterion 5
criteria_empirical: false,      // was Criterion 6
criteria_category: false,       // was Criterion 9

// NEW — add these
criteria_terms: false,          // Criterion 2 - Defined Terms
criteria_mechanism: false,      // Criterion 3 - Causal Mechanism (name kept, meaning updated)
criteria_test_path: false,      // Criterion 4 - Empirical Test Path
criteria_falsifiability: false, // Criterion 5 - Falsifiability with Threshold
criteria_transparency: false,   // Criterion 6 - Dependency Transparency
criteria_selection: false,      // Criterion 7 - Non-Arbitrary Selection
criteria_predictions: false,    // Criterion 8 - Predictive Capability
criteria_reproducibility: false // Criterion 9 - Reproducibility
```

### Validation:

Same as before — all 8 checkboxes must be checked before the form advances past Step 3.

---

## 4. Update GitHub Issue Markdown — Criteria Self-Certification Section

Update the `generateMarkdown()` function to reflect the new checkboxes:

```markdown
---

### Criteria Self-Certification

The submitter has confirmed their PDF addresses:

- [x] Terms operationally defined (Criterion 2)
- [x] Causal mechanism described (Criterion 3)
- [x] Empirical test path specified (Criterion 4)
- [x] Falsifiability condition with threshold (Criterion 5)
- [x] Dependencies and limitations declared (Criterion 6)
- [x] Selection criteria pre-defined (Criterion 7)
- [x] Novel predictions derived (Criterion 8)
- [x] Methodology reproducible (Criterion 9)

*Note: Criterion 1 (Clear Singular Claim) is captured in the Core Claim field above. These self-certifications are informational — the AI pre-check assesses the PDF content directly.*
```

---

## 5. Update governance.md — Criteria Table

Replace the 9-criteria table that was added in Phase 5 with the new criteria set:

```markdown
## The 9 Structural Compliance Criteria

All submissions are evaluated against these 9 mandatory structural criteria. Every criterion must be satisfied for a submission to be deemed structurally compliant. This is an AND-gate model — failure on any single criterion results in non-compliance.

| # | Criterion | What It Requires |
|---|-----------|-----------------|
| 1 | **Clear Singular Claim** | A single, identifiable, operationally testable claim. Not compound, vague, or metaphorical. |
| 2 | **Defined Terms and Ontology** | Key technical terms operationally defined; mathematical and empirical layers separated where applicable. |
| 3 | **Causal Mechanism** | A physical or structural mechanism explaining why the claim holds. More than analogy or mathematics alone. |
| 4 | **Empirical Test Path** | An explicit, operationalised test with pre-registered criteria, quantitative thresholds, or specified methodology. |
| 5 | **Falsifiability** | A clear, measurable condition with a defined threshold that would defeat the claim if observed. |
| 6 | **Dependency Transparency** | Explicit acknowledgement of assumptions, limitations, interpretive judgements, and formalisation requirements. |
| 7 | **Non-Arbitrary Selection** | Protection against confirmation bias and post-hoc selection. Analysis target defined before the search. |
| 8 | **Predictive Capability** | At least one novel, testable prediction derived from the claim. Not re-description of existing data. |
| 9 | **Reproducibility** | Methodology explicit enough for independent replication. |
```

Keep the Criterion 10 (Examiner Assessment Only) section as-is — it hasn't changed.

---

## 6. What NOT To Change in Phase 6a

- Do NOT modify server.py (Phase 6b handles the AI prompt)
- Do NOT modify the Grok prompt
- Do NOT change PDF upload, validation, or storage
- Do NOT change email notifications
- Do NOT change the API endpoint
- Do NOT change the form step count (still 6 steps)
- Do NOT change the declaration step (Step 6)

---

## Verification Checklist (for Graham)

After applying these changes, confirm:

- [ ] Criteria accordion shows 10 items with updated names and descriptions
- [ ] Criterion 10 still visually distinct (examiner-only)
- [ ] Accordion subtitle updated to reference AI assessing PDF directly
- [ ] Step 3 has 8 checkboxes (not 6) with new labels and helper text
- [ ] Step 3 subtitle updated
- [ ] All 8 checkboxes required — form blocks if any unchecked
- [ ] Form navigation still works through all 6 steps
- [ ] Make a test submission end-to-end
- [ ] GitHub issue shows updated self-certification section with 8 items
- [ ] Self-certification note says "informational — AI assesses PDF directly"
- [ ] governance.md criteria table updated
- [ ] Old criteria names no longer appear anywhere in the portal
- [ ] AI pre-check still runs (it will still use the old Phase 3 prompt — that's fine, Phase 6b replaces it)

---

*Phase 6a of 6c — TSM2 Submission Portal Update*
*Planner: Claude (Anthropic) — Builder: Replit Claude*
