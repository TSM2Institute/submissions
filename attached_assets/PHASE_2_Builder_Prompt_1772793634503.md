# PHASE 2 — Form Expansion: Criteria Declaration Checkboxes

## Context for Builder

This is Phase 2 of the TSM2 Submission Portal update. Phase 1 (language fixes, back button, criteria accordion) is complete and verified.

Phase 2 adds criteria declaration checkboxes to the submission form. The submitter confirms their PDF addresses each of the 9 structural criteria. The PDF remains the authoritative record — these checkboxes are self-certification, not content entry.

**Important:** The existing form fields (title, core_claim, primary_scale, falsifiability) already cover Criteria 1, 7, and 8. We are adding checkboxes for the remaining criteria (2, 3, 4, 5, 6, 9) that are NOT currently captured.

---

## 1. New Form Step: "Criteria Confirmation"

### Insert a new Step 3 between the current Step 2 (Submission Details) and current Step 3 (Falsifiability Condition).

The form flow becomes:

| Step | Name | Content |
|------|------|---------|
| 1 | Your Information | Name, Email, Organization, etc. *(unchanged)* |
| 2 | Submission Details | Title, Core Claim, Primary Scale *(unchanged)* |
| **3** | **Criteria Confirmation** | **NEW — checkboxes for criteria 2, 3, 4, 5, 6, 9** |
| 4 | Falsifiability Condition | Falsifiability text field *(was Step 3, renumbered)* |
| 5 | Document Upload | PDF upload *(was Step 4, renumbered)* |
| 6 | Declaration | Final declaration checkboxes *(was Step 5, renumbered)* |

### Step 3 Content:

**Step Title:** "Criteria Confirmation"

**Step Subtitle/Helper Text:**
> Your PDF document is the authoritative record. Please confirm it addresses each of the following structural criteria. All boxes must be checked to proceed.

**Checkboxes (all required — form cannot advance to Step 4 unless all are checked):**

Each checkbox has a label and a brief helper line beneath it.

---

**☐ Key Terms Defined** *(Criterion 2)*
Helper: "My PDF defines all non-standard or framework-specific terminology used in the claim."

**☐ Assumptions Declared** *(Criterion 3)*
Helper: "My PDF explicitly states all foundational assumptions upon which the claim depends."

**☐ Mechanism Described** *(Criterion 4)*
Helper: "My PDF describes the physical mechanism connecting cause to effect, with a step-by-step causal sequence."

**☐ Energy Conservation Addressed** *(Criterion 5)*
Helper: "My PDF demonstrates how the claim preserves conservation laws, or states which law is modified and why."

**☐ Empirical Anchor Identified** *(Criterion 6)*
Helper: "My PDF identifies the dataset, measurable phenomenon, or observational reference that grounds the claim."

**☐ Category Integrity Maintained** *(Criterion 9)*
Helper: "My PDF does not replace physical causation with metaphor, geometry, or undefined abstraction."

---

### Design Notes:

- Match existing form styling (Tailwind + Alpine.js, cosmic theme, Inter font)
- Each checkbox should be clearly labelled with the criterion name in bold
- Helper text in smaller, lighter text beneath each label
- The criterion numbers (2, 3, 4, 5, 6, 9) should NOT be prominently displayed to avoid confusing submitters about numbering gaps — these are internal reference numbers. The labels are what matter.
- Optional: add a subtle link/reference to the Criteria Accordion (from Phase 1) so submitters can review full descriptions. Something like: "See full criteria descriptions above" with a scroll link.

### Validation:

- All 6 checkboxes must be checked before the "Next" button enables
- If a submitter tries to advance without all boxes checked, show a validation message: "Please confirm your PDF addresses all structural criteria before proceeding."

---

## 2. Data Model Update

### Add to the `form` object in Alpine.js:

```javascript
form: {
    submission_title: '',
    core_claim: '',
    primary_scale: '',
    falsifiability: '',
    // NEW — criteria declarations
    criteria_definitions: false,    // Criterion 2
    criteria_assumptions: false,    // Criterion 3
    criteria_mechanism: false,      // Criterion 4
    criteria_energy: false,         // Criterion 5
    criteria_empirical: false,      // Criterion 6
    criteria_category: false,       // Criterion 9
    declaration: false
}
```

---

## 3. Submission Data — What Changes

### 3A. formData sent to server

The `formData` JSON string sent to `/api/submit` should now include the new boolean fields:

```javascript
formData.append('formData', JSON.stringify(this.form));
// this.form now includes criteria_definitions, criteria_assumptions, etc.
```

The server doesn't need to do anything special with these booleans yet — they're just included in the payload. Phase 3 will update the Grok prompt to reference them.

### 3B. GitHub Issue Markdown

Update the `generateMarkdown()` function to include a new section in the issue body. Add this **after** the Falsifiability Condition section and **before** the Document section:

```markdown
---

### Criteria Self-Certification

The submitter has confirmed their PDF addresses:

- [x] Key terms defined (Criterion 2)
- [x] Assumptions declared (Criterion 3)
- [x] Mechanism described (Criterion 4)
- [x] Energy conservation addressed (Criterion 5)
- [x] Empirical anchor identified (Criterion 6)
- [x] Category integrity maintained (Criterion 9)

*Note: Criteria 1 (Explicit Claim), 7 (Falsifiability), and 8 (Scale) are captured in form fields above.*
```

Since all checkboxes are required, these will always show as `[x]` checked. This creates a clear audit trail in the GitHub issue showing the submitter confirmed coverage.

---

## 4. Step Navigation Update

Update all step numbering throughout `index.html`:

- Step indicators/progress bar: 1 → 2 → 3 → 4 → 5 → 6 (was 1-5)
- "Next" and "Back" button logic: ensure the new step is wired into the navigation correctly
- Step counter display (if shown, e.g., "Step 3 of 6")

Test that:
- Navigation flows correctly through all 6 steps
- Back button works from every step
- Form state persists when navigating back and forward

---

## 5. What NOT To Change in Phase 2

- Do NOT modify server.py or the API endpoint
- Do NOT modify the Grok AI prompt (Phase 3)
- Do NOT add/remove GitHub labels (Phase 4)
- Do NOT change the criteria accordion from Phase 1
- Do NOT change the `userInfo` fields
- Do NOT change the PDF upload validation

---

## Verification Checklist (for Graham)

After applying these changes, confirm:

- [ ] New Step 3 "Criteria Confirmation" appears in the form flow
- [ ] All 6 checkboxes render with correct labels and helper text
- [ ] Form cannot advance past Step 3 without all boxes checked
- [ ] Validation message appears if trying to advance without all checked
- [ ] Steps 4, 5, 6 work correctly (renumbered from old 3, 4, 5)
- [ ] Back navigation works through all 6 steps
- [ ] Step counter/progress bar shows 6 steps
- [ ] Complete a test submission end-to-end
- [ ] GitHub issue includes new "Criteria Self-Certification" section
- [ ] All criteria checkboxes show as `[x]` in the issue
- [ ] Existing form fields (title, claim, scale, falsifiability) still work correctly
- [ ] PDF upload still works
- [ ] AI pre-check still runs (even though prompt isn't updated yet)
- [ ] Email notification still sends

---

*Phase 2 of 5 — TSM2 Submission Portal Update*
*Planner: Claude (Anthropic) — Builder: Replit Claude*
