---
name: gndless-kicad-pcb
description: Use for KiCad PCB placement, stackup, planes, routing, and PCB review in this user's projects. Defaults to 4-layer boards; covers USB2/PDM differential pairs, zones, KRT placement/routing tools, and DRC.
---

# Gndless KiCad PCB

Inspect the existing board and its conventions before editing. Keep one writer per board and preserve the project structure.

## Stackup and planes

- Assume a 4-layer board by default. Use 2 layers only when the user explicitly asks or the circuit is simple enough that 4 layers add no value.
- For 4-layer boards, decide the stackup and plane assignment before routing; do not treat inner layers as an afterthought.
- Use `recommend-stackup` and `recommend-plane-mappings` before routing.
- Prefer copper zones. Use a GND zone by default where the layer stack and routing allow, and consider power zones where they make sense.
- Choose zone layers and coverage from the actual copper-layer count and routing constraints; do not assume a plane exists on a particular layer. If a zone cannot be used effectively, explain the constraint and route the net instead.
- After adding or changing zones, refill them and check that the intended nets connect and clearances are preserved.

## Placement

- Use `plan-pcb-placement` for automated placement. For manual placement, edit in KiCad itself.
- Place decoupling capacitors close to the IC supply pins and minimize the supply-return loop area.
- Put horizontal connectors near board edges; confirm double-sided assembly and outline changes with the user.

## Routing

- Route manually by default. Use `plan-pcb-routing` when the user asks for autorouting or the board is too complex to route by hand.
- For USB 2.0 and differential PDM, use `identify-diff-pairs` and `find-high-speed-nets` for pair detection and impedance/return-via guidance.
- Use `analyze-power-nets` when power-plane widths need datasheet-based sizing.
- Use `review-routed-board` after KRT routing.

## Editing and validation

- Do not assume existing generator scripts are required or authoritative. Reuse them only when they are maintainable and fit the requested edit.
- Use `pcbnew` scripting for repeatable headless geometry. For open-editor state, use KiCad itself.
- Do not assume the system Python can load KiCad's native modules; use the supported KiCad runtime for `pcbnew`.
- For PCB footprint replacement, update the complete placed footprint and preserve board identity, schematic path, and pad-to-net mapping. Prefer KiCad's Update PCB from Schematic when it applies cleanly. Never replace only the library identifier when pad geometry changes.
- Use `ki-stack-file-surgery` for structural board-file changes.
- Use `kicad-cli` for DRC; use `kicad` for analysis and review.
- After direct or scripted edits, run DRC and inspect an exported drawing or the GUI when practical. Report any checks that could not be run.

## Third-party handoff

- `kicad` for PCB analysis and review.
- KRT placement/routing/stackup/power/differential tools listed above.
- `ki-stack-symbols` / `ki-stack-footprints` for library inspection.
- Do not use export, render, distributor, or EMC skills.
- Full routing table: `~/.agents/skills/gndless-kicad-review/references/third-party-routing.md`.
