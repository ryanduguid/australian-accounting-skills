---
name: stp-finalisation
description: Use for Single Touch Payroll year-end finalisation — reconciling payroll registers to the GL and to STP-filed totals, checking super guarantee, including RFBA, and producing the finalisation checklist before the declaration deadline.
---

# STP Finalisation

Reconcile the payroll year three ways — register, GL, STP-filed — then finalise. The finalisation declaration is due by 14 July for most employers (verify current deadline and any concession for closely held payees at ato.gov.au).

## Inputs needed

1. Payroll activity/register report for the full financial year, per employee
2. GL detail: wages, superannuation expense and payable, PAYG withholding payable, wages clearing
3. STP reporting summary from the payroll software (what the ATO has received)
4. RFBA per employee from the FBT workpaper (see `fbt-annual-workflow`), if any
5. Termination records for the year (ETPs)

## Workflow

1. **Register vs GL.** Gross wages, PAYG withheld, and super per the payroll register agree to the GL accounts for the year. Wages clearing account nils out; explain any residue.
2. **Register vs STP.** Per-employee YTD gross, tax, and super in the software's STP summary agree to the register. Investigate every difference — common causes: unfiled pay events, post-filing adjustments, employees paid outside payroll.
3. **Super guarantee.** Check the SG rate applied against the legislated rate for each period (verify at ato.gov.au). Confirm payments reached funds by the deadline for the year being finalised — quarterly due dates up to FY2025-26; payday super (fund receipt within 7 business days of each payday) from 1 July 2026. Late payments mean SGC exposure — flag, don't bury.
4. **Categories and codes.** STP Phase 2 disaggregation: allowances in their proper categories, salary sacrifice reported correctly, ETPs coded per type. Spot-check unusual payees.
5. **RFBA.** Include reportable fringe benefits amounts for affected employees before finalising.
6. **Finalise.** Produce the checklist: every reconciliation status, exceptions and resolutions, then the finalisation declaration is made by the authorised person in the payroll software — not by this workflow. Write the checklist and workpapers under `output/`, never at repo root — confirm the repo's `.gitignore` covers `output/` and add it if absent; generated workpapers carry client data and never enter version control.

## Checks before handing over

- Three-way tie: register = GL = STP, per employee for tax and super, in total for gross
- SG rate and due-date regime cited per period (quarterly for FY2025-26 and earlier; per payday under payday super from FY2026-27); payment dates evidenced
- Exceptions list empty or explicitly accepted by the reviewer

## Boundaries

- The finalisation declaration is a legal declaration by the employer/agent — a human makes it.
- SGC calculations and remission requests are advice territory; flag exposure, hand over.
- Client data: follow the firm's CLAUDE.md privacy rules; exclude TFNs and any identifier the task does not need; keep exports and generated output out of version control.
