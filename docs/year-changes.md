# Year changes

Each rule a skill applies differently from a stated income year has one row here and a `<!-- year-change: YYYY-YY -->` marker ending the first line of its paragraph or list item in the skill, giving the first income year the change applies to. `tests/test_year_changes.py` fails when a marker has no row, a row has no marker, a row's section is not in its skill, or its source is not in the skill's `sources.json`.

A row records the change as the skill states it, the primary source and its exact words, and the day an agent or person read them. A person still reviews the source before relying on the row.

| Income year | Skill | Section | Change | Source | Quote | Checked |
| --- | --- | --- | --- | --- | --- | --- |
| 2027-28 | au-small-business-cgt | Workflow step 3 | The small business 50% active asset reduction's basic conditions are tested without the CGT small business entity limb in s 152-10(1AA)(b) of the ITAA 1997. | https://www.ato.gov.au/law/view/document?docid=PAC/19970038/152-205 | In working out for the purposes of subsection (1) whether the basic conditions in Subdivision 152-A are satisfied, disregard paragraph 152-10(1AA)(b). | 2026-11-24 |
