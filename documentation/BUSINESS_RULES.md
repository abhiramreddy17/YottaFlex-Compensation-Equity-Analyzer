# Business rules and decision logic

1. Only compare employees with the same role, level and location. A different group requires a documented rationale; otherwise reject the comparison.
2. Resolve the compensation band by role + level + location and review date. An expired band is not a valid benchmark.
3. Normalize currency using the dated FX rate table. Missing FX means `UNVERIFIED`, never a guessed conversion.
4. Annualized FTE-equivalent salary = annual salary amount x FX-to-INR / recorded FTE. Compare this with band values converted to INR.
5. Compa-ratio = normalized FTE salary / band midpoint in INR.
6. Within-band position = (normalized FTE salary - band minimum) / (band maximum - band minimum).
7. Flag values outside a valid band for contextual review. A flag is not a finding of discrimination.
8. An adjustment marked APPLIED must have an approver and an approval event. Payroll is never changed automatically by this prototype.
9. Review proposals preserve the employee ID, evidence, reason, status and approval trail.
10. Ground truth is generated separately and is excluded from detection inputs.

## Known limitations
- FX rates are fixed illustrative values in code, not live market rates or payroll rates. Replace with approved dated corporate rates for real use.
- The generated salary history is synthetic and uses a simple annual merit progression.
- The starter groups employees by exact role, level and location; it does not infer job equivalence.
- The application is decision support, not a legal/pay-equity determination.
