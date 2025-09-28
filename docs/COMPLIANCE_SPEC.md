
# Compliance Mapping (Spec → System)

## EWTD (European Working Time Directive)
- Max weekly average 48h (rolling): **TODO** (aggregate timeseries).
- Duty ≤24h: **Implemented** in basic validator.
- Daily rest ≥11h: **TODO**
- Weekly rest ≥24h: **TODO**
- Breaks ≥30m for >6h: **Represented** in labels; validator **TODO**.

## HSE NCHD Contract (2023)
- 39h base week: **TODO (reporting)**
- Paid breaks: **Represented**
- Teaching & supervision protected: **Partially** (protection window).
- No split shifts: **TODO (slot continuity check)**.
- Contract clauses 7–11: mapped into validators (**WIP**).

## OPD & Protected Time
- OPD guard: **WIP**
- Teaching (Wed 14:00–16:30) protected: **represented**
- Handover 30m at boundaries: **represented**
