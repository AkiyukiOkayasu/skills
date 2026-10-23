---
name: kicad
description: Create or edit KiCad schematics and PCB layouts, following the project's conventions and keeping schematic and board data consistent.
---

# KiCad

Use this skill for KiCad project work, including schematic and PCB edits, library or footprint selection, and project checks. Inspect the existing project and its conventions before making changes; preserve its established structure and avoid replacing project files wholesale when a focused edit is possible.

## Passive symbol selection

- Use `Device:R_Small` and `Device:C_Small` for ordinary SMD resistors and capacitors. Use `Device:R` and `Device:C` when the part is intentionally through-hole or uses a larger SMD package for a design reason such as current or power handling. Keep the schematic symbol choice consistent with the intended component size and electrical role.

## Component sourcing and LCSC fields

- When selecting parts for JLCPCB assembly, prefer electrically and mechanically suitable JLC Basic parts over Extended parts. Do not compromise required voltage, power, tolerance, package, or other design constraints just to use a Basic part.
- When a JLC Basic part is selected, fill the symbol’s `LCSC` field with its exact LCSC/JLC part number (for example, `C50254`) and carry that field into the BOM when one is maintained. Leave the field blank when no JLC part has been selected.

## Akizuki sourcing fields and assembly exclusions

- When a selected component is sourced from Akizuki Denshi, add an `Akizuki` field to the schematic symbol and enter the Akizuki sales code (for example, `108290`). Keep the field name consistent so the code is easy to use when hand-assembling the board.
- Check both `Exclude from bill of materials` and `Exclude from position files` for Akizuki-sourced hand-assembled parts. These exports are intended for JLCPCB assembly, so hand-installed Akizuki parts must not appear in the JLC BOM or placement file.
- Keep the normal component reference, value, and footprint assigned. These flags keep the parts in the KiCad schematic and PCB while omitting them from JLC assembly exports.

## Schematic value notation

- Write resistor and capacitor values in RKM notation: replace a decimal point with the relevant multiplier letter, for example `2k2`, `4R7`, `3n3`, and `4u7`. Keep integral forms such as `1k`, `100n`, and `1u`; express sub-unit values at a readable adjacent decade when appropriate, such as `0.1u` as `100n`.
- Omit unit words and symbols from resistor and capacitor values; do not append `ohm`, `Ω`, `F`, or `farad`. Preserve meaningful tolerance, dielectric, material, voltage, and power annotations. For a nonstandard or unusually high rating/type that matters for assembly or review, append a concise slash annotation in the value, such as `1k5/1W` for a 1.5 kΩ 1 W resistor or `150p/C0G` for a 150 pF C0G capacitor. Do not add routine/default ratings or dielectric types to every value. Apply this convention to schematic value fields and generated value labels.
- Do not generalize this rule to other component types; follow the project convention or the user's instruction for those.

## Power symbols

- Use KiCad `power:` symbols for schematic power rails and ground references instead of placing ordinary text labels on those nets. Use `power:VCC` and `power:VEE` for generic positive and negative rails when no matching nominal-voltage symbol exists. If the actual rail matches a defined symbol such as `power:+5V`, `power:+12V`, or `power:+15V`, use that dedicated symbol.
- Use the appropriate ground symbol (`power:GND`, `power:GNDA`, or `power:GNDPWR`) where its net meaning matches the circuit. Keep signal ground, power common, and chassis ground distinct unless the design explicitly bonds them; a symbol change must not silently join those nets.

## Schematic design and readability

- Arrange a one-page circuit so its main signal path reads left to right. Keep functional blocks visually distinct and put input/output connectors near the corresponding ends; place power entry and auxiliary interfaces where they can be traced without crossing the audio path.
- Use A4 as the starting sheet size. Move to A3 only when the circuit cannot remain readable on A4. Fill the title block with a concise circuit title, revision/status, and date.
- Add a compact note block near the top of the sheet for the circuit role, signal-flow summary, important options, and assumptions that a reviewer needs immediately. Break long notes into readable lines, keep them inside the page border, and put detailed calculations and background in Markdown documentation.
- Do not let schematic symbols or their text fields overlap. Keep references and values close to their own symbols, upright, and readable. Align related parts where practical without sacrificing clear signal flow.
- Draw local component-to-component connections directly. Use descriptive net labels at connector pins to state each interface signal (for example, `RIAA_OUT`), even when that named net appears only once. Also use labels for long connections or nets that reappear in separate functional areas. Do not add labels to short one-to-one connections between components when a visible wire is clearer. Draw decoupling capacitors directly to the relevant IC supply pins and return, and place them close to those pins.
- Orient positive supply symbols so their arrows point up. Orient negative supply and ground symbols so their arrows point down. Use the appropriate ground symbol for the actual net; keep audio/signal common, power common, and chassis separate unless the circuit deliberately connects them. Use `power:Earth` for chassis references, not as a substitute for circuit ground.
- Prefer the user's authored symbol and footprint libraries, especially Akiyuki libraries, whenever a matching project asset exists. Preserve the exact library identifiers. For DOAs, transformers, card edges, and other nonstandard pin maps, use the matching authored symbol and show pin numbers, lead colors, or terminal names needed to wire and review the part correctly.
- For pin headers, Euroblocks, and other ordinary multi-pin connectors, use the matching `Connector_Generic:Conn_01xNN` symbol and assign the physical footprint separately. Reserve custom connector symbols for genuinely nonstandard pin maps such as a card-edge connector.
- Produce a clean, aligned, reviewable schematic layout before handing it over; do not treat placement as a rough draft for the user to finish. Avoid spending repeated effort on tiny cosmetic shifts once signal flow, grouping, spacing, and field placement are clear and consistent.

When changing a schematic or board, preserve existing references and connectivity unless the requested change requires otherwise. Check the edited design in KiCad or with available project tools when practical, and report any checks that could not be completed.

## PCB copper zones

- Prefer copper zones (pours) when laying out the board. Use a GND zone by default where the layer stack and routing allow it; also consider zones for power nets when they make sense for the design.
- Choose zone layers and coverage based on the actual copper-layer count and routing constraints. Do not assume a plane is available on a particular layer; if a zone cannot be used effectively, explain the constraint and use an appropriate routed alternative.
- After adding or changing zones, refill them and check that the intended nets connect correctly and that clearances/isolation are preserved.

## Choose an editing method for each change

- Do not assume a project’s existing generator scripts are required or authoritative. Reuse them only when they are maintainable and fit the requested edit; otherwise use KiCad’s native files or editor workflow directly.
- For focused schematic property changes such as `Value`, `LCSC`, or the symbol’s `Footprint` assignment, edit the native S-expression while preserving UUIDs, symbol instances, pins, and connectivity. A schematic footprint assignment does not by itself replace a footprint already placed on the PCB.
- For PCB footprint replacement, update the complete placed footprint and preserve its board identity, schematic path, and pad-to-net mapping. Prefer KiCad’s Update PCB from Schematic workflow when it can apply the change cleanly. Never replace only the footprint library identifier when the pad geometry changes.
- Use `pcbnew` scripting when a repeatable geometric operation benefits from it and the supported KiCad runtime is available. Do not assume the system Python can safely load KiCad’s native modules.
- Use `kicad-cli` for validation and exports, not as a general editor. After direct file or API edits, validate with the relevant ERC/DRC checks and open the result in KiCad for visual review when practical.

## Automation and validation

- Do not assume KiCad is limited to computer-use UI automation. Prefer command-line and scriptable workflows for repeatable edits, exports, and checks; use the GUI for operations that require interactive editing and for visual review when available.
- On macOS, `kicad-cli` may be installed inside the KiCad app bundle without being on `PATH`; check the app bundle (for example, `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`) before concluding that the CLI is unavailable. Use it for schematic ERC, PCB DRC, netlist export, and PDF/SVG export.
- For edits, use KiCad-supported scripting such as `pcbnew` where available, or carefully edit/generate the KiCad S-expression files when that is the most reliable project workflow. The CLI validates and exports designs; it is not itself a general schematic/PCB editor. Preserve UUIDs, embedded library definitions, project instances, pin mappings, and connectivity during direct S-expression edits.
- A missing `pcbnew` import in the system Python does not mean the KiCad scripting API is unavailable. Check the KiCad-bundled Python/runtime or use the project’s established generation workflow, then validate the saved board with `kicad-cli`.
- After scripted or direct file edits, run the appropriate CLI checks and inspect an exported drawing or the GUI when practical. Clearly report checks that could not be run.
