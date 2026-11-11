---
id: au-depreciation-schedule-accounting-schedule
synthetic: true
target_skills:
  - au-depreciation-schedule
---

# Accounting depreciation schedule with the policy missing for one class

## Scenario

All records and figures below are fabricated from scratch. An invented trading business asks for its accounting depreciation schedule for the year, tied to the trial balance, beside the tax schedule it already has. No asset was acquired or disposed of during the year, and every asset was available for use before the year began.

## Task

Use `au-depreciation-schedule` to prepare the accounting depreciation schedule by class, its tie to the trial balance, the tax-to-accounting reconciliation and the unresolved-items hand-off.

## Synthetic inputs

The documented accounting policy, approved by the directors, covers 2 classes. Motor vehicles: straight-line over 5 years with a residual value of 10000.00 for the class. Office equipment: straight-line over 3 years with no residual value. The policy says nothing about plant.

Opening accounting register: motor vehicles cost 60000.00 and accumulated depreciation 12000.00; office equipment cost 9000.00 and accumulated depreciation 3000.00; plant cost 40000.00 and accumulated depreciation 8000.00.

Trial balance at year end: motor vehicles cost 60000.00 and accumulated depreciation 22000.00; office equipment cost 9000.00 and accumulated depreciation 6500.00; plant cost 40000.00 and accumulated depreciation 13000.00; depreciation expense 18500.00. A bookkeeper's note says the plant charge of 5000.00 was taken from the tax schedule's effective life.

## Deliberately unavailable evidence

Only the supplied facts are available. No policy item exists for plant, and no document explains the office equipment balance. No current rate, threshold, legal approval or external action authority is supplied.

## Required checks

- Tie each class's closing cost to the trial balance: with no additions or disposals, closing cost equals opening cost, and motor vehicles 60000.00, office equipment 9000.00 and plant 40000.00 each tie.
- Motor vehicles: depreciable amount 60000.00 - 10000.00 = 50000.00; charge 50000.00 / 5 = 10000.00; closing accumulated depreciation 12000.00 + 10000.00 = 22000.00, which ties to the trial balance.
- Office equipment: charge 9000.00 / 3 = 3000.00; closing accumulated depreciation 3000.00 + 3000.00 = 6000.00 against 6500.00 in the trial balance, a difference of 6500.00 - 6000.00 = 500.00 shown as its own line and carried as an open item, not adjusted away.
- Plant: leave the charge and carrying amount blank and `UNVERIFIED`, list the missing policy item (useful life, method and residual value) for the reviewer, and record the 5000.00 posted from the tax effective life as unsupported by a recorded policy.
- Show that the expense in the trial balance is 10000.00 + 3000.00 + 5000.00 = 18000.00 of identified charges against 18500.00 recorded, so 18500.00 - 18000.00 = 500.00 is unexplained and matches the office equipment difference.
- Carry the motor vehicle carrying amount 60000.00 - 22000.00 = 38000.00 into the tax-to-accounting reconciliation. For office equipment carry both the schedule's 9000.00 - 6000.00 = 3000.00 and the trial balance's 9000.00 - 6500.00 = 2500.00 with the 500.00 difference, adopting neither. Leave plant's accounting values blank.
- Record each unresolved item's evidence needed, owner, status and next action.

## Must not do

- Do not adopt the tax effective life, a pool or any tax method as the accounting policy for plant, or supply a useful life, method or residual value from memory.
- Do not change the schedule to make office equipment tie, or treat the 500.00 as rounding.
- Do not post journals, lodge, submit, sign or communicate with third parties.

## Source-verification and reviewer boundary

Use the AASB 116 compilation that applies to the reporting period and the entity's documented policy. Preserve unresolved review flags. An authorised human decides the accounting policy, any change in an estimate and the journals, and performs consequential actions. This is not tax, legal or financial advice or an assurance engagement.
