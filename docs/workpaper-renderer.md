# Workpaper renderer and formula verifier

`workpaper-renderer` is a native Rust utility built from `tools/accounting-skills/` with zero extra runtime dependencies. It converts structured JSON or Markdown workpaper drafts into review-ready `.xlsx` (with live formulas and deterministic formula verification), `.docx` and `.pdf` deliverables.

## Boundaries

- **Prep only:** every generated `.xlsx`, `.docx` and `.pdf` carries the non-removable `DRAFT FOR HUMAN REVIEW - PREP ONLY - NOT FOR LODGEMENT - NOT ADVICE` banner.
- **No silent suppression:** open reviewer exceptions and `UNVERIFIED` markers are counted on the cover summary and reported in the JSON verification output.
- **Formula safety:** text cells are stored as OOXML inline strings (neutralising spreadsheet formula injection). Formula cells reject external workbook references (`[...]`) and disallowed external or volatile functions (`WEBSERVICE`, `HYPERLINK`, `CALL`, `REGISTER.ID`, `IMPORTXML`, `IMPORTDATA`, `IMPORTHTML`, `EXEC`, `CMD`) as non-catchable policy violations (so `IFERROR` cannot conceal them), detect circular references and `#DIV/0!`, reject non-finite cached values (`NaN`/`inf`) and write verified finite cached values (`<v>`) alongside `<f>`.
- **Character encoding:** `.xlsx` and `.docx` preserve full UTF-8 Unicode; `.pdf` uses `WinAnsiEncoding` (ASCII, Latin-1 and common currency/punctuation) and explicitly fails rather than silently substituting `?` when text contains a character outside `WinAnsiEncoding`.
- **Client data:** write rendered client deliverables only to a firm-approved secure folder outside this repository.

## Usage

Build the binary from `tools/accounting-skills/`:

```bash
cargo build --locked --release --bin workpaper-renderer
```

Render a structured JSON or Markdown workpaper into `.xlsx`, `.docx` and `.pdf` with a verification report:

```bash
workpaper-renderer render \
  --input /secure/path/bas-draft.json \
  --xlsx /secure/path/bas-draft.xlsx \
  --docx /secure/path/bas-draft.docx \
  --pdf /secure/path/bas-draft.pdf \
  --report /secure/path/bas-report.json
```

Verify an existing `.xlsx` workpaper (ZIP CRC-32 integrity, mandatory draft banner, formula safety, error cells and finite cached-value agreement):

```bash
workpaper-renderer verify-xlsx --input /secure/path/bas-draft.xlsx
```

Print the JSON input schema:

```bash
workpaper-renderer schema
```
