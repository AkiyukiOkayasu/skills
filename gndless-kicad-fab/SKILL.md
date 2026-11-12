---
name: gndless-kicad-fab
description: Use for KiCad BOM, JLCPCB/Akizuki sourcing, assembly fields, and fabrication preparation in this user's projects. Covers LCSC fields, JLC Basic vs Extended, Akizuki fields, exclude flags, and bom/jlcpcb/lcsc handoff.
---

# Gndless KiCad Fab

## Part and assembly fields

- For JLCPCB assembly, prefer electrically and mechanically suitable JLC Basic parts over Extended parts. Do not compromise required voltage, power, tolerance, package, or other design constraints to use a Basic part.
- When a JLC Basic part is selected, fill the symbol's `LCSC` field with the exact LCSC part number (for example, `C50254`) and carry it into the BOM. Leave it blank when no JLC part is selected.
- For parts sourced from Akizuki Denshi, add an `Akizuki` field with the Akizuki sales code (for example, `108290`).
- Check both `Exclude from bill of materials` and `Exclude from position files` for Akizuki-sourced hand-assembled parts. Keep their reference, value, and footprint assigned; these flags only omit them from JLC assembly exports.
- For symbol, value, and footprint edits, follow `gndless-kicad-schematic`.

## BOM and sourcing

- Use `bom` as the BOM workflow. Use `jlcpcb` for JLCPCB rules and assembly constraints, and `lcsc` for LCSC part search.
- Do not use `digikey`, `mouser`, `element14`, or `pcbway`.
- BOM and CPL output goes through `bom`. Do not use `kicad-export`; it is not installed.
- Preserve `LCSC`, `Akizuki`, and both exclude flags in every BOM/CPL export.

## Fabrication preparation

- No export or render skill is installed. Use KiCad's GUI or `kicad-cli` directly for Gerber, drill, and position files.
- Run DRC/ERC through `kicad` or `kicad-cli` before ordering.
- Check JLCPCB capabilities and assembly constraints before release.
- For 4-layer stackup and planes, follow `gndless-kicad-pcb`.

## Third-party handoff

- `bom`, `jlcpcb`, `lcsc`.
- Full routing table: `~/.agents/skills/gndless-kicad-review/references/third-party-routing.md`.
