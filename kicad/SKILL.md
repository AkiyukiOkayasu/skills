---
name: kicad
description: Create or edit KiCad schematics and PCB layouts, following the project's conventions and keeping schematic and board data consistent.
---

# KiCad

Use this skill for KiCad project work, including schematic and PCB edits, library or footprint selection, and project checks. Inspect the existing project and its conventions before making changes; preserve its established structure and avoid replacing project files wholesale when a focused edit is possible.

## Schematic value notation

- For resistor and capacitor values, omit the unit symbol. Use forms such as `1k`, `10k`, `100n`, and `1u`; do not append `ohm`, `Ω`, `F`, or `farad`.
- Keep the value readable and unambiguous. Apply this convention to schematic value fields and any generated value labels.
- Do not generalize this rule to other component types; follow the project convention or the user's instruction for those.

## Schematic design and readability

- Place each decoupling capacitor close to the component or power pin it is intended to support.
- During drafting, one-to-one net labels on pins are acceptable if they help build or revise the design. For a schematic presented to the user for review, minimize labels so component-to-component connections are easy to recognize at a glance.
- Use labels when a net connects multiple components or when connected components must be separated in the drawing. For simple local connections, draw the wire directly instead of replacing it with labels.
- Keep schematic placement functional and clear, but do not spend excessive effort or tokens polishing component positions. The user expects to adjust placement themselves; prioritize correct connectivity and a readable rough arrangement.
- Start schematic page layout on A4. Move to A3 only when the design cannot reasonably fit on A4 while keeping it readable.

When changing a schematic or board, preserve existing references and connectivity unless the requested change requires otherwise. Check the edited design in KiCad or with available project tools when practical, and report any checks that could not be completed.

## PCB copper zones

- Prefer copper zones (pours) when laying out the board. Use a GND zone by default where the layer stack and routing allow it; also consider zones for power nets when they make sense for the design.
- Choose zone layers and coverage based on the actual copper-layer count and routing constraints. Do not assume a plane is available on a particular layer; if a zone cannot be used effectively, explain the constraint and use an appropriate routed alternative.
- After adding or changing zones, refill them and check that the intended nets connect correctly and that clearances/isolation are preserved.

## Automation and validation

- Do not assume KiCad is limited to computer-use UI automation. Prefer command-line and scriptable workflows for repeatable edits, exports, and checks; use the GUI for operations that require interactive editing and for visual review when available.
- On macOS, `kicad-cli` may be installed inside the KiCad app bundle without being on `PATH`; check the app bundle (for example, `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`) before concluding that the CLI is unavailable. Use it for schematic ERC, PCB DRC, netlist export, and PDF/SVG export.
- For edits, use KiCad-supported scripting such as `pcbnew` where available, or carefully edit/generate the KiCad S-expression files when that is the most reliable project workflow. The CLI validates and exports designs; it is not itself a general schematic/PCB editor. Preserve UUIDs, embedded library definitions, project instances, pin mappings, and connectivity during direct S-expression edits.
- A missing `pcbnew` import in the system Python does not mean the KiCad scripting API is unavailable. Check the KiCad-bundled Python/runtime or use the project’s established generation workflow, then validate the saved board with `kicad-cli`.
- After scripted or direct file edits, run the appropriate CLI checks and inspect an exported drawing or the GUI when practical. Clearly report checks that could not be run.
