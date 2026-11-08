# Data dictionary

All identifiers are immutable strings. Dates use ISO-8601 `YYYY-MM-DD`. Salaries are annualized amounts in the currency stated on the row. Synthetic names and records do not represent real people.

| Entity / file | Primary key | Important fields | Required validation |
|---|---|---|---|
| Employee | employee_id | employee_name, role_id, level_id, location_id, joining_date, fte, employment_status | FTE in (0,1]; master IDs exist; status ACTIVE/INACTIVE |
| Role | role_id | role_name | Unique role name |
| Level | level_id | level_name, level_order | Unique level and positive order |
| Location | location_id | city, currency, location_factor | Currency must have configured FX rate for calculations |
| CompensationBand | band_id | role_id, level_id, location_id, min_salary, mid_salary, max_salary, effective_start/end, currency | min <= midpoint <= max; valid dates |
| SalaryRecord | salary_id | employee_id, band_id, effective_date, end_date, base_salary, currency, fte_at_record, annualized | Employee and band exist; positive salary/FTE; dates ordered |
| PerformanceEvidence | evidence_id | employee_id, review_period, rating, evidence_note | Employee exists; rating 1–5 |
| Tenure | tenure_id | employee_id, start_date, years_of_service | Employee exists; non-negative years |
| Promotion | promotion_id | employee_id, from_level_id, to_level_id, effective_date, reason | Employee and levels exist; date follows hire |
| AdjustmentProposal | adjustment_id | employee_id, proposed_salary, currency, status, created_date, approved_by, reason | Status PENDING/APPROVED/REJECTED/APPLIED; applied requires approver |

## Optional / lifecycle fields
`end_date`, `approved_by`, and evidence notes may be empty where the lifecycle permits. Proposal states are PENDING -> APPROVED or REJECTED; only APPROVED -> APPLIED is valid. The deliberately injected negative scenario APPLIED with no approver is retained as an explicit issue for detection, not silently repaired.

## Relationships and cardinality
- Role 1:N Employee; Level 1:N Employee; Location 1:N Employee.
- Employee 1:N SalaryRecord, PerformanceEvidence, Tenure, Promotion and AdjustmentProposal.
- Role/Level/Location 1:N CompensationBand for each dimension; each band belongs to exactly one combination.
- Employee and Role/Level/Location are joined by foreign keys. The generated dataset uses one current role/level/location per employee; promotions are retained as events.
- Employee-to-comparable-group is logically N:M in a production system; this starter uses a deterministic composite key (role, level, location), not a bridge table.

| ComparisonRequest | comparison_id | employee_id_a, employee_id_b, rationale | Both employees must exist; different role/level/location requires rationale |
