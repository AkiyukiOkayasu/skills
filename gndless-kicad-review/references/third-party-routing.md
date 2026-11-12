# KiCad skill routing

KiCad work starts with one of the personal phase skills. Third-party skills are
tools that the phase skill calls when needed.

| Phase skill | Use for |
|---|---|
| `gndless-kicad-schematic` | Schematic capture, editing, schematic review, ERC |
| `gndless-kicad-pcb` | Placement, 4-layer stackup, planes, routing, DRC |
| `gndless-kicad-fab` | BOM, JLCPCB/Akizuki sourcing, assembly fields |
| `gndless-kicad-review` | Cross-cutting design review and verification report |

## Third-party packs

| Pack | Installed IDs | Main role |
|---|---|---|
| kicad-happy | `kicad`, `bom`, `datasheets`, `jlcpcb`, `lcsc`, `spice` | Analysis, review, BOM, sourcing |
| Milind220 Ki-Stack | `ki-stack-file-surgery`, `ki-stack-symbols`, `ki-stack-footprints` | Structural file surgery and library inspection |
| KiCadRoutingTools | `analyze-power-nets`, `diagnose-routing-failures`, `find-high-speed-nets`, `identify-diff-pairs`, `plan-pcb-placement`, `plan-pcb-routing`, `recommend-plane-mappings`, `recommend-stackup`, `review-routed-board` | Stackup, plane, differential-pair, power, placement, and routing work |

Export, render, distributor-search, EMC, and live-IPC skills are intentionally
not installed. `kicad-export`, `kicad-gerbers`, `ki-stack-render`,
`make-3d-movie`, `digikey`, `mouser`, `element14`, `pcbway`, and `emc` were
removed, along with the Ki-Stack orientation/live/schematic/PCB/verify skills.

Four layers are the default; two layers are exceptional. The KRT stackup,
plane, power, and differential-pair helpers are installed because the boards
include 4-layer stackups, USB 2.0, and differential 50 MHz PDM.

## Precedence

1. Project-local conventions.
2. The phase skills above for symbols, values, power symbols, page and layout
   style, library choice, stackup, routing policy, and BOM/assembly fields.
3. Third-party skills for analysis, tooling, and workflows they own.

A third-party skill may describe a valid workflow while still conflicting with
the phase skills. Take the workflow, not the convention.

## Route by task

| Task | Phase skill | Third-party tool |
|---|---|---|
| Schematic authoring | `gndless-kicad-schematic` | `kicad`, `spice`, `datasheets` |
| Schematic review | `gndless-kicad-schematic` / `gndless-kicad-review` | `kicad` |
| PCB placement | `gndless-kicad-pcb` | `plan-pcb-placement` |
| 4-layer stackup | `gndless-kicad-pcb` | `recommend-stackup` |
| Plane assignment | `gndless-kicad-pcb` | `recommend-plane-mappings` |
| Power-net widths | `gndless-kicad-pcb` | `analyze-power-nets` |
| Differential pairs | `gndless-kicad-pcb` | `identify-diff-pairs` |
| High-speed nets / impedance | `gndless-kicad-pcb` | `find-high-speed-nets` |
| Routing | `gndless-kicad-pcb` | `plan-pcb-routing` |
| Post-route review | `gndless-kicad-review` | `review-routed-board` |
| BOM and sourcing | `gndless-kicad-fab` | `bom`, `jlcpcb`, `lcsc` |
| Fabrication preparation | `gndless-kicad-fab` | KiCad GUI or `kicad-cli` directly |
| Full design review | `gndless-kicad-review` | `kicad`, `spice`, `datasheets` |
| Manual SPICE deck | `gndless-ngspice` | none |
| Local PDF extraction | `gndless-pdf` | `datasheets` for structured specs |
| Structural file surgery | schematic or PCB phase skill | `ki-stack-file-surgery` |
| Symbol/footprint inspection | schematic or PCB phase skill | `ki-stack-symbols`, `ki-stack-footprints` |

## Removed skills

| Removed skill | Reason |
|---|---|
| `kicad-schematic` | Assumed Backplane and conflicted on symbols, values, power symbols, page size, wiring, and libraries |
| `kicad-layout` | Assumed Backplane and advised against autorouting |
| `kicad-bom` | Required the `pcbparts.dev` or `zenode.ai` MCP; `bom` covers the workflow |
| `kicad-pcb` | Overlapped `kicad` and `kicad-export` |
| `kicad-footprint`, `kicad-symbol` | Required KLC / kicad-library-tools setup |
| `kicad-export` | Export is not needed; `bom` / `kicad-cli` cover the remaining cases |
| `kicad-gerbers` | Gerber rendering and review are not needed |
| `kicad-panelize` | KiKit is not used |
| `layout-placement` | Overlapped `plan-pcb-placement` |
| `pcb-product-render` | Blender-specific product rendering |
| `ki-stack-render` | Rendering is not needed |
| `ki-stack-orient` | Overlapped the phase skills and `kicad` |
| `ki-stack-schematic` | Overlapped `gndless-kicad-schematic` |
| `ki-stack-pcb`, `ki-stack-live` | Live IPC is not used |
| `ki-stack-verify` | Overlapped `kicad` DRC/ERC |
| `make-3d-movie` | 3D movie rendering is not needed |
| `digikey`, `mouser`, `element14` | Rarely used; `lcsc` or direct web search is enough |
| `pcbway` | JLCPCB is the fab used |
| `emc` | Full EMC pre-compliance is not part of the workflow |
| `stress-test-router` | Router regression testing is not needed |

## Remaining overlaps

| Overlap | Skills | Resolution |
|---|---|---|
| Review | `gndless-kicad-review`, `kicad`, `review-routed-board` | `kicad` for analysis; `review-routed-board` only after KRT routing |
| Analysis | `kicad`, `analyze-power-nets`, `find-high-speed-nets`, `identify-diff-pairs`, `recommend-stackup`, `recommend-plane-mappings` | Use the KRT helpers as routing-plan inputs; use `kicad` for the design review |
| BOM | `bom`, `jlcpcb`, `lcsc` | `bom` is the workflow; the others are sourcing helpers |
| PDF | `gndless-pdf`, `datasheets`, `kicad` PDF analysis | Extract with `gndless-pdf`; structured specs with `datasheets`; PDF schematic analysis with `kicad` |
| SPICE | `spice`, `gndless-ngspice` | Automatic testbenches vs manual decks; complementary |
| Name confusion | `plan-workflow` vs `plan-pcb-*` | `plan-workflow` manages `plan/*.md`; the others manage PCB placement/routing |

## Recommended disposition

Keep as primary: `gndless-kicad-schematic`, `gndless-kicad-pcb`,
`gndless-kicad-fab`, `gndless-kicad-review`, `kicad`, `bom`, `jlcpcb`, `lcsc`,
`spice`, `datasheets`, `gndless-ngspice`, `gndless-pdf`,
`recommend-stackup`, `recommend-plane-mappings`, `analyze-power-nets`,
`identify-diff-pairs`, `find-high-speed-nets`, `plan-pcb-placement`,
`plan-pcb-routing`, `review-routed-board`, `diagnose-routing-failures`, and
`ki-stack-file-surgery`.

Use only when the task needs them: `ki-stack-symbols`, `ki-stack-footprints`.
