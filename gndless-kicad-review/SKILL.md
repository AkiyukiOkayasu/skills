---
name: gndless-kicad-review
description: Use for a full KiCad design review in this user's projects. Orchestrates kicad analysis, spice, datasheets, and review-routed-board; reports blockers, warnings, and verification gaps.
---

# Gndless KiCad Review

Use this for cross-cutting review. For schematic-only work use `gndless-kicad-schematic`; for PCB-only work use `gndless-kicad-pcb`; for BOM and fab use `gndless-kicad-fab`.

## Workflow

1. Run the `kicad` analyzer: `analyze_schematic.py`, then `analyze_pcb.py --full --schematic`, then `cross_analysis.py`.
2. Run `spice` when a simulator is installed. Report `pass` / `warn` / `fail` / `info` / `skip`.
3. Run `datasheets` when MPN coverage is available. If datasheets are missing, state the verification gap and do not claim datasheet-verified findings.
4. Use `review-routed-board` only after KRT routing. Otherwise use `kicad` for DRC/DFM and connectivity review.
5. Report blockers, warnings, and skipped analyses separately. Do not claim EMC coverage; the `emc` skill is not installed.

## Output

- Separate confirmed findings from consistency-only findings.
- Include the exact commands and artifact paths used.
- State which analyzers were run and which were skipped.
- Do not present analyzer output as a final review without cross-checking.

## Third-party handoff

- `kicad`, `spice`, `datasheets`, `review-routed-board`.
- Do not use `digikey`, `mouser`, `element14`, `pcbway`, or `emc`.
- Full routing table: `references/third-party-routing.md`.
