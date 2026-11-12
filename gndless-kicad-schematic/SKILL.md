---
name: gndless-kicad-schematic
description: Use for KiCad schematic capture, editing, and schematic review in this user's projects. Covers symbol choice, RKM values, power symbols, page and wiring conventions, ERC, and handoff to kicad/spice/datasheets. For LCSC/Akizuki/assembly fields, use gndless-kicad-fab.
---

# Gndless KiCad Schematic

Inspect the existing project and its conventions before editing. Preserve its established structure, and avoid replacing project files wholesale when a focused edit is possible.

## Symbols

- Use `Device:R_Small` and `Device:C_Small` for ordinary SMD resistors and capacitors. Use `Device:R` and `Device:C` only when the part is intentionally through-hole or needs a larger package for current, power, or another design reason.
- Use `Connector_Generic:Conn_01xNN` for pin headers, Euroblocks, and other ordinary multi-pin connectors, and assign the physical footprint separately. Reserve custom connector symbols for genuinely nonstandard pin maps such as card edges.
- For DOAs, transformers, card edges, and other nonstandard pin maps, use the matching authored symbol and footprint, and preserve the exact library identifiers. Show the pin numbers, lead colors, or terminal names needed to wire and review the part.

## Value notation

- Write resistor and capacitor values in RKM notation: replace the decimal point with the multiplier letter (`2k2`, `4R7`, `3n3`, `4u7`). Keep integral forms such as `1k`, `100n`, and `1u`; express `0.1u` as `100n`.
- Do not append unit words or symbols (`ohm`, `Ω`, `F`, `farad`).
- Omit the routine 1% tolerance. When a design specifically requires tighter resistor accuracy, state it with a slash annotation such as `1k/0.1%`.
- Add a slash annotation only for a nonstandard rating or type that matters for assembly or review, such as `1k5/1W` or `150p/C0G`. Do not add routine/default ratings or dielectric types to every value.
- Apply this convention to schematic value fields and generated value labels, not to other component types; follow the project convention or the user's instruction there.

## Power symbols

- Use `power:` symbols for rails and ground instead of ordinary text labels on power nets.
- Use `power:VCC` and `power:VEE` for generic positive and negative rails when no matching nominal-voltage symbol exists. If the rail matches `power:+5V`, `power:+12V`, `power:+15V`, and so on, use the dedicated symbol.
- Use the ground symbol whose net meaning matches: `power:GND`, `power:GNDA`, or `power:GNDPWR`. Keep signal ground, power common, and chassis distinct unless the design explicitly bonds them. Use `power:Earth` for chassis references, not as circuit ground.

## Schematic layout

- Arrange a one-page circuit so the main signal path reads left to right. Keep functional blocks distinct, put input/output connectors near the corresponding ends, and place power entry and auxiliary interfaces where they can be traced without crossing the audio path.
- Start with A4 and move to A3 only when the circuit cannot remain readable on A4. Fill the title block with a concise circuit title, revision/status, and date.
- Add a compact note block near the top for the circuit role, signal-flow summary, important options, and assumptions a reviewer needs immediately. Keep it inside the page border and put detailed calculations in Markdown.
- Do not let symbols or their text fields overlap. Keep references and values close to their own symbols, upright, and readable.
- Draw local component-to-component connections directly. Put descriptive net labels on connector pins (for example, `RIAA_OUT`), and use labels for long connections or nets that reappear in another functional area. Do not label short one-to-one connections where a visible wire is clearer.
- Draw decoupling capacitors directly to the relevant IC supply pins and return, and place them close to those pins.
- Orient positive supply symbols up, and negative supply and ground symbols down.
- Prefer the user's authored symbol and footprint libraries, especially the Akiyuki libraries, whenever a matching project asset exists.
- Finish placement to a clean, aligned, reviewable state; do not hand over a rough draft for the user to complete.

## Editing and validation

- Do not assume existing generator scripts are required or authoritative. Reuse them only when they are maintainable and fit the requested edit.
- For focused schematic property changes such as `Value`, `LCSC`, or `Footprint`, edit the native S-expression while preserving UUIDs, symbol instances, pins, and connectivity. Assigning a footprint in the schematic does not replace a footprint already placed on the PCB.
- Use `ki-stack-file-surgery` for structural or multi-object changes.
- Use `kicad-cli` for ERC, netlist export, and PDF/SVG export; it is not a general editor.
- After direct or scripted edits, run ERC and inspect an exported drawing or the GUI when practical. Report any checks that could not be run.
- For LCSC, Akizuki, and assembly exclude flags, follow `gndless-kicad-fab`.

## Third-party handoff

- `kicad` for schematic analysis and review.
- `spice` for automatic testbenches from analyzer output.
- `datasheets` for structured MPN extraction.
- Do not use `digikey`, `mouser`, `element14`, `pcbway`, or `emc`.
- Full routing table: `~/.agents/skills/gndless-kicad-review/references/third-party-routing.md`.
