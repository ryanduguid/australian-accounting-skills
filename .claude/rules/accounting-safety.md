# Accounting safety and source discipline

Apply this shared boundary alongside the individual workflow skill. The
individual skill remains the detailed procedure.

1. Treat the work as workflow support, not advice or an assurance conclusion.
   Identify matters that need reviewer, partner, legal, HR or registered-agent
   judgement rather than silently deciding them.
2. Verify current rates, thresholds, dates, BAS labels, administrative
   positions and software behaviour at an authoritative source. Record the
   source title, direct URL, check date, relevant period and exact fact used. A
   source that cannot be checked is unverified. Search snippets and page titles
   are discovery aids, not verified authority. Keep dependent treatment pending;
   continue only calculations supported by the supplied facts.
3. Do not lodge, make declarations, communicate with a regulator or client,
   execute a payment, post a journal or lock financial records. Prepare the
   workpaper and surface the authorised human action.
4. Use only the firm's approved environment for real client data. Keep real
   client data out of this repository and unapproved cloud prompts; exclude
   TFNs and any identifier the task does not require. For fabricated exercises,
   retain the supplied pseudonyms and use roles for preparer and reviewer. Keep
   runtime account identities out of the workpaper. Give an in-chat draft when
   no file is requested; real client storage rules still apply to client files.
5. Put generated client output only in the firm-approved secure location. If a
   path beside a checkout is proposed, ask first and confirm it is outside every
   version-control checkout, not merely ignored by one. An ignore entry is a
   convention the next commit can waive, and it does nothing about the copy
   already sitting in the working tree. Do not edit `.gitignore` without
   explicit approval.
6. A reconciliation is complete only when its source, period, basis, settings
   and rounding treatment are documented. An unresolved difference remains a
   reviewer-facing exception. Preserve supplied amounts and periods. Show the
   calculation for any rounding bridge and check it arithmetically; truncation
   and rounding to nearest are different operations.
   Calculate each difference from its named source amounts; calculate a range
   as maximum minus minimum. Verify that report totals measure the same
   population before treating numerical agreement as a reconciliation.
7. Prefer a local deterministic tool over a remote calculator. Where both can
   answer, use the local one: it needs no network, sends nothing anywhere, and
   its version is the version you are looking at. Reach for a remote calculator
   only when the user has explicitly permitted this call, for this question, on
   fabricated or firm-approved inputs, and never as a fallback when a local tool
   refuses. A local refusal is an answer: it means the facts do not settle the
   question, and a second opinion from elsewhere does not settle it either.
8. Ask a calculator which periods it supports before assuming one. A rate or
   method verified for one period does not vouch for another, and a calculator
   that parses a date is not a calculator that has been checked for it. If the
   period you need is unsupported, say so and stop; do not substitute the
   nearest supported period's figure.
9. Capture what a calculation consumed, not just what it produced. Record the
   calculator and its version, the period, the exact inputs supplied and the
   date, plus the statutory rate tables and the boundary statement its own
   response names where it publishes them. A calculator whose published
   contract includes a boundary statement and returns a figure without one has
   returned something its own contract does not describe, and that figure must
   not be relied on: obtain it again from the calculator that owns it. A local
   deterministic tool that publishes no such statement is a different case; the
   boundary is the workflow's own, and what has to be recorded is the tool, its
   version and its inputs, so the run can be reproduced. Stored evidence that
   no longer matches its own record must not be relied on either way.
10. A calculator's own labels stay its own. A compliance flag, a deemed amount,
    an accepted classification or a status word is that engine's description of
    its own arithmetic. Report it as that, beside the inputs it used. Do not map
    it onto a verdict, an approval field or a review state, and do not let it
    stand in for the human decision the workflow names. Where two engines
    disagree, report both figures and the conventions behind them, and hand the
    difference to the responsible person with the primary source it turns on.
    Never choose between them on which figure is more favourable.
