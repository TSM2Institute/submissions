# PHASE 6e — Multimodal Vision Upgrade

## Context for Builder

This is Phase 6e. Phase 6d landed clean and is validated against ground truth — Grok's verdicts now match Geoffrey's manual ChatGPT verdicts criterion-for-criterion on the *Polarity and Oscillation* paper (v1 NON_COMPLIANT verdict matched 9/9, v2 COMPLIANT verdict matched 9/9). The system is structurally calibrated.

**The remaining bias gap:** Grok currently sees PDF text only. Diagrams, figures, equations rendered as images, and structured visual content are invisible to it. The text extraction layer (`pdfplumber`) captures captions and surrounding prose but not the visual content itself.

This is a real bias against diagram-heavy and equation-heavy submissions. Examples already in our test set:

- *Polarity and Oscillation*: Chladni cymatics figure (Figure 1), *Testable Consequences* table with prediction/observable/method diagrams (Section 10.6)
- *Cross-Domain 72-12-4-7*: Generative cascade flowchart (Figure 1)

Without vision, criteria like Mechanism (Crit 3), Test Path (Crit 4), Predictive Capability (Crit 8), and Reproducibility (Crit 9) systematically under-score on papers where the figures carry the argument.

**This phase adds vision.** Grok 4.3 is already the configured model and natively supports multimodal input. The change is pipeline-only: render each PDF page to a PNG image server-side, and send those images alongside the existing extracted text in the API call. No prompt changes. No verdict format changes. No GitHub issue format changes.

**Out of scope:** Email notifications, examiner workflow, prompt calibration, form fields, scorecard format. All of these stay exactly as they are in Phase 6d.

---

## 1. Add the PyMuPDF Dependency

Install `pymupdf` (the official package name; imported as `pymupdf` or as `fitz` for legacy compatibility — use `import pymupdf` for new code).

**Why PyMuPDF and not `pdf2image`:**

- No system-level dependencies. `pip install pymupdf` is the entire install. `pdf2image` requires `poppler-utils` installed via Nix/system packages, which is brittle on Replit.
- 3–10× faster than `pdf2image` for page-to-image rendering.
- Single library can handle both text extraction and image rendering, which simplifies future maintenance (though we keep `pdfplumber` for text in this phase — see §3).
- Licensing: AGPL or commercial. The Institute's submissions repo is public-source and the use case is non-commercial structural screening, so AGPL is appropriate. Add a one-line acknowledgement in `replit.md` (see §7).

Add `pymupdf` to whatever dependency manifest the project uses (`pyproject.toml`, `requirements.txt`, or Replit's package config). Verify it installs cleanly and the server still starts.

---

## 2. Add Page-to-Image Rendering

Create a new function (suggested name: `render_pdf_pages_to_images`) in `server.py` that takes a PDF file path and returns a list of base64-encoded PNG image data URIs, one per page.

**Specification:**

```python
import pymupdf
import base64

def render_pdf_pages_to_images(pdf_path: str, max_pages: int = 50, dpi: int = 200) -> list[dict]:
    """
    Render each page of a PDF to a PNG image and return as base64 data URIs.
    
    Returns a list of dicts in Grok multimodal format:
        [{"type": "input_image", "image_url": "data:image/png;base64,..."}, ...]
    
    If the PDF exceeds max_pages, only the first max_pages are rendered and a 
    truncation flag is included in the return value.
    """
    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    pages_to_render = min(total_pages, max_pages)
    
    images = []
    for page_num in range(pages_to_render):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        png_bytes = pix.tobytes("png")
        b64 = base64.b64encode(png_bytes).decode("ascii")
        images.append({
            "type": "input_image",
            "image_url": f"data:image/png;base64,{b64}"
        })
    
    doc.close()
    
    return {
        "images": images,
        "total_pages": total_pages,
        "rendered_pages": pages_to_render,
        "truncated": total_pages > max_pages
    }
```

**Configuration constants:**

- `max_pages = 50` — defensive cap. PDFs over 50 pages get the first 50 pages rendered; remaining pages are not sent to Grok. The existing text extraction step is unaffected by this cap (it extracts whatever the existing pdfplumber logic extracts).
- `dpi = 200` — sweet spot for legibility of equations and small text without bloating payload size. Do NOT change to 150 (too low for equations) or 300 (~2× the payload for marginal quality gain).
- Format = PNG. Do NOT use JPEG — compression artifacts degrade equation and thin-line legibility, which matters for criteria 3 (Mechanism), 8 (Predictive Capability), and 9 (Reproducibility).

---

## 3. Modify the Grok API Call to Include Images

Locate the existing Grok API call in `server.py`. Currently it sends a single text message containing the system prompt, form field metadata, and extracted PDF text.

**Modify the user message content to be a list of content blocks instead of a single text block:**

Current structure (text-only):
```python
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt_text}
]
```

New structure (multimodal):
```python
# Render pages to images
render_result = render_pdf_pages_to_images(pdf_path)

# Build multimodal content array
user_content = []

# Add all page images first
user_content.extend(render_result["images"])

# Then add the text prompt last (text comes after images per Grok 4.3 convention)
user_content.append({
    "type": "input_text",
    "text": user_prompt_text
})

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_content}
]
```

**Important:**

- Keep `pdfplumber` text extraction exactly as it is. The text is still sent to Grok — vision is *additive*, not a replacement. Grok 4.3 reads both inputs together.
- The system prompt stays unchanged.
- The user prompt text stays unchanged.
- The JSON response schema stays unchanged.
- The response parsing stays unchanged.

**Truncation handling:** If `render_result["truncated"]` is `True`, prepend a note to the user_prompt_text:

```python
if render_result["truncated"]:
    truncation_note = (
        f"NOTE: This PDF has {render_result['total_pages']} pages. "
        f"Only the first {render_result['rendered_pages']} pages have been "
        f"rendered as images for visual analysis. The text extraction "
        f"covers the full document."
    )
    user_prompt_text = truncation_note + "\n\n" + user_prompt_text
```

---

## 4. Add Image Render Status to the GitHub Issue

In the GitHub issue scorecard footer (already contains the truncation note for text extraction), add a short note about the image render status. This goes in the existing footer area where the text truncation note currently appears:

```markdown
> 🔬 **Visual analysis:** {rendered_pages} of {total_pages} pages rendered to images at 200 DPI and analyzed alongside extracted text. {truncation_message_if_any}
```

Where `truncation_message_if_any` is:
- Empty string if `rendered_pages == total_pages`
- `"Pages beyond page {max_pages} were not rendered visually but their text was still extracted."` if truncated

This makes it transparent to the submitter and examiner that vision was used and what was covered.

---

## 5. Error Handling

If PyMuPDF fails to render the PDF (corrupt PDF, unsupported format, etc.):

- Log the error
- Fall back to text-only mode for that submission
- Add a flag to the GitHub issue: `⚠️ **Visual analysis unavailable for this submission.** The PDF could not be rendered to images. The pre-check assessment is based on extracted text only.`
- Still produce a verdict from the text-only assessment — do not block the submission

The fallback behaviour mirrors the existing pattern for `pdfplumber` failures: vision is enhancement, not gating.

---

## 6. Token Budget Awareness

Grok 4.3 has a 1M token context window. Image inputs at 200 DPI consume roughly 1500–3000 tokens per page depending on visual complexity. A typical 30-page submission therefore consumes:

- Image tokens: ~45,000–90,000
- Extracted text tokens: ~20,000–30,000
- System prompt + user prompt: ~3,000

Total per submission: ~70,000–125,000 tokens. Well within the 1M context window with significant headroom.

No special batching, chunking, or async logic required. The synchronous request path stays as it is.

---

## 7. Update Documentation

After §1–§6 are complete and verified, update:

- **`README.md`** — Add a brief note under the AI Pre-Check description that the system now uses multimodal vision: "The AI pre-check uses Grok 4.3 in multimodal mode, analyzing both extracted text and rendered page images. This allows assessment of figures, diagrams, and equations that text extraction alone cannot capture."

- **`replit.md`** — Update the implementation notes section to reflect:
  - PyMuPDF added as a dependency for page-to-image rendering at 200 DPI PNG
  - Multimodal Grok call with images + text sent together
  - 50-page rendering cap; text extraction unaffected
  - AGPL licensing note for PyMuPDF (acceptable for the Institute's non-commercial public-source use; reassess if the platform ever moves to commercial SaaS)
  - Text extraction via `pdfplumber` retained — vision is additive, not a replacement

---

## 8. What NOT To Change

- Do NOT change the Grok system message
- Do NOT change the Grok user prompt template (only the *content* wrapping changes from single text block to list of blocks)
- Do NOT change the JSON response schema
- Do NOT change the response parsing logic
- Do NOT change the GitHub issue scorecard structure or rendering (only the small footer note in §4 is added)
- Do NOT change the submit screen or any frontend code
- Do NOT change PDF upload pipeline, form fields, declarations, or self-certification fields
- Do NOT change auto-labelling logic (`AI Pre-Check: Compliant` / `Non-Compliant` / `Screening: Unavailable`)
- Do NOT remove or modify `pdfplumber` — text extraction stays exactly as it is
- Do NOT change the criterion definitions, the binary grading scale, or the prescriptive `required_correction` voice
- Do NOT add image preprocessing (cropping, deskewing, OCR fallback, etc.) — Grok 4.3 handles raw page images natively
- Do NOT add a "hybrid" mode that decides per-page whether to render images. Always render all pages (up to the 50-page cap). Simpler, more robust, consistent across submissions.

---

*Phase 6e — TSM2 Submission Portal Update*
*Planner: Claude (Anthropic) — Builder: Replit Claude*
