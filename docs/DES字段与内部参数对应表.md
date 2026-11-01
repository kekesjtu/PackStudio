# PackStudio 内部字段—DES—pack_script

## bare_die

### Values

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `die.length` | `Ld`<br>`unit=mm` | `name="die"`; `property_name="dieLengthLd"` |
| `die.width` | `Wd`<br>`unit=mm` | `name="die"`; `property_name="dieWidthWd"` |
| `die.thickness` | `td`<br>`unit=mm` | `name="die"`; `property_name="dieThicknessTd"` |
| `die.power` | `P`<br>`unit=W` | `name="die"`; `property_name="packagePower"` |
| `die.flipped` | `flip` | `name="die"`; `property_name="flippedDie"` |
| `bumps.enabled` | `bumped` | `name="bumpedDie"`; `property_name="bumpedDie"` |
| `bumps.total` | `nballs`<br>`conditions={"visible_when":{"bumps.enabled":true}}` | `name="bumpedDie"`; `property_name="numberOfSolderBalls"` |
| `bumps.diameter` | `b`<br>`unit=mm`<br>`conditions={"visible_when":{"bumps.enabled":true}}` | `name="bumpedDie"`; `property_name="ballDiameterb"` |
| `bumps.height` | `tsd`<br>`unit=mm`<br>`conditions={"visible_when":{"bumps.enabled":true}}` | `name="bumpedDie"`; `property_name="ballHeight"` |
| `bumps.modeling` | `conditions={"visible_when":{"bumps.enabled":true}}` | — |
| `grid.enabled` | `localgrid` | `name="modelingOptions"`; `property_name="localizeGrid"` |
| `grid.density` | `radio_lgc`<br>`conditions={"visible_when":{"grid.enabled":true}}` | `name="modelingOptions"`; `property_name="gridDensity"` |

### Assignments

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `group-die` | `radio_die` | `name="die"`; `property_name="dieMaterial"` |
| `group-bump-solder` | `k_solder`<br>`conditions={"bumps.enabled":true}` | `name="bumpedDie"`; `property_name="solderConductivity"` |
| `group-underfill` | `k_fill`<br>`conditions={"bumps.enabled":true}` | `name="bumpedDie"`; `property_name="underfillConductivity"` |

### ProjectDocument

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `TemplateId` | `package` | — |
| `Name` | `design` | — |
| `PresetId` | — | — |
| `CustomMaterials` | — | — |

## cbga_fc

### Values

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `footprint.size` | — | `name=null`; `property_name="jedecFootprint"` |
| `substrate.length` | `D`<br>`unit=mm` | `name="packageSubstrate"`; `property_name="substrateLengthD"` |
| `substrate.width` | `E`<br>`unit=mm` | `name="packageSubstrate"`; `property_name="substrateWidthE"` |
| `substrate.thickness` | `A2`<br>`unit=mm` | `name="packageSubstrate"`; `property_name="substrateThicknessA2"` |
| `die.length` | `Ld`<br>`unit=mm` | `name="die"`; `property_name="dieLengthLd"` |
| `die.width` | `Wd`<br>`unit=mm` | `name="die"`; `property_name="dieWidthWd"` |
| `die.thickness` | `td`<br>`unit=mm` | `name="die"`; `property_name="dieThicknessTd"` |
| `die.power` | `P`<br>`unit=W` | `name="die"`; `property_name="packagePower"` |
| `bumps.total` | `MNC4`<br>`conditions={"visible_when":{"bumps.array_type":"non_regular"}}` | `name="flipChipBumps"`; `property_name="totalNumberOfBumpsMNC4"` |
| `bumps.diameter` | `bC4`<br>`unit=mm` | `name="flipChipBumps"`; `property_name="bumpDiameterBC4"` |
| `bumps.height` | `tC4`<br>`unit=mm` | `name="flipChipBumps"`; `property_name="bumpHeightTC4"` |
| `bumps.modeling` | — | `name="modelingOptions"`; `property_name="modelFlipChipBumpsAs"` |
| `bga.columns` | `MD` | `name="solderBalls"`; `property_name="numberOfSolderBallsInXMD"` |
| `bga.rows` | `ME` | `name="solderBalls"`; `property_name="numberOfSolderBallsInYME"` |
| `bga.pitch` | `e`<br>`unit=mm` | `name="solderBalls"`; `property_name="ballPitchE"` |
| `bga.diameter` | `b`<br>`unit=mm` | `name="solderBalls"`; `property_name="ballDiameterB"` |
| `bga.height` | `A1`<br>`unit=mm` | `name="solderBalls"`; `property_name="substrateStandoffA1"` |
| `cover.type` | `radio_EnCaPl` | `name=null`; `property_name="topCover"` |
| `cover.length` | `Le`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant"}}` | `name="topCover"`; `property_name="lengthLe"`; `branch="encapsulant"` |
| `cover.width` | `We`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant"}}` | `name="topCover"`; `property_name="widthWe"`; `branch="encapsulant"` |
| `cover.thickness` | `te`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant"}}` | `name="topCover"`; `property_name="thicknessTe"`; `branch="encapsulant"` |
| `lid.length` | `Lc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid"}}` | `name="topCover"`; `property_name="lidLengthLc"`; `branch="lid"` |
| `lid.width` | `Wc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid"}}` | `name="topCover"`; `property_name="lidWidthWc"`; `branch="lid"` |
| `lid.thickness` | `tc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid"}}` | `name="topCover"`; `property_name="lidThicknessTc"`; `branch="lid"` |
| `lid.base_thickness` | `tcb`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid"}}` | `name="topCover"`; `property_name="lidBaseThicknessTcb"`; `branch="lid"` |
| `lid.die_attach` | `tda`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid"}}` | `name="topCover"`; `property_name="dieAttachThicknessTda"`; `branch="lid"` |
| `lid.adhesive` | `tcadh`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid"}}` | `name="topCover"`; `property_name="lidAdhesiveThickness"`; `branch="lid"` |
| `plate.length` | `Lc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"plate"}}` | `name="topCover"`; `property_name="plateLengthLc"`; `branch="plate"` |
| `plate.width` | `Wc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"plate"}}` | `name="topCover"`; `property_name="plateWidthWc"`; `branch="plate"` |
| `plate.thickness` | `tc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"plate"}}` | `name="topCover"`; `property_name="plateThicknessTc"`; `branch="plate"` |
| `plate.die_attach` | `tda`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"plate"}}` | `name="topCover"`; `property_name="dieAttachThicknessTda"`; `branch="plate"` |
| `grid.enabled` | `localgrid` | `name="modelingOptions"`; `property_name="localizeGrid"` |
| `grid.density` | `radio_lgc`<br>`conditions={"visible_when":{"grid.enabled":true}}` | `name="modelingOptions"`; `property_name="gridDensity"` |
| `bumps.array_type` | `radio_bump_type` | `name="flipChipBumps"`; `property_name="arrayType"` |
| `bumps.columns` | `MDC4`<br>`conditions={"visible_when":{"bumps.array_type":"regular"}}` | `name="flipChipBumps"`; `property_name="numberOfBumpsInXMDC4"` |
| `bumps.rows` | `MEC4`<br>`conditions={"visible_when":{"bumps.array_type":"regular"}}` | `name="flipChipBumps"`; `property_name="numberOfBumpsInYMEC4"` |
| `bumps.underfill` | `c4_underfill` | `name="flipChipBumps"`; `property_name="underfill"` |
| `cover.flush` | `check_thickness`<br>`conditions={"visible_when":{"cover.type":"encapsulant"}}` | `name="topCover"`; `property_name="enableDieFlush"`; `branch="encapsulant"` |
| `stiffener.enabled` | `radio_stiffener`<br>`conditions={"visible_when":{"cover.type":"lid"}}` | `name="topCover"`; `property_name="stiffener"`; `branch="lid"` |
| `stiffener.length` | `Ls`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | `name="topCover"`; `property_name="stiffenerLengthLs"`; `branch="lid"` |
| `stiffener.width` | `Ws`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | `name="topCover"`; `property_name="stiffenerWidthWs"`; `branch="lid"` |
| `stiffener.cavity_length` | `Lsc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | `name="topCover"`; `property_name="stiffenerCavityLengthLsc"`; `branch="lid"` |
| `stiffener.cavity_width` | `Wsc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | `name="topCover"`; `property_name="stiffenerCavityWidthWsc"`; `branch="lid"` |
| `stiffener.adhesive` | `tsadh`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | `name="topCover"`; `property_name="stiffenerAdhesiveThickness"`; `branch="lid"` |
| `slug.enabled` | `slug`<br>`conditions={"enabled_when":{"cover.type":"encapsulant"}}` | `name="dropInSlug"`; `property_name="includeSlug"` |
| `slug.length` | `L_sl`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugLengthLsl"` |
| `slug.width` | `W_sl`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugWidthWsl"` |
| `slug.thickness` | `t_sl`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugThicknessTsl"` |
| `slug.diameter` | `dsl`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugDiameterDs"` |
| `slug.foot_length` | `L_slf`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugFootExtendLengthLsf"` |
| `slug.foot_width` | `W_slf`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugFootExtendWidthWsf"` |
| `slug.offset` | `gsl`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugOffsetGs"` |
| `slug.clearance` | `g_slf`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugFootClearanceGsf"` |
| `slug.adhesive_enabled` | `slug_adh`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="adhesivePresentUnderSlugFoot"` |

### Assignments

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `group-substrate` | `k_substr` | `name="packageSubstrate"`; `property_name="dielectricMaterial"` |
| `group-die` | — | — |
| `group-encapsulant` | `k_encap`<br>`conditions={"cover.type":"encapsulant"}` | `name="topCover"`; `property_name="encapsulantMaterial"`; `branch="encapsulant"` |
| `group-lid` | `k_cap`<br>`conditions={"cover.type":"lid"}` | `name="topCover"`; `property_name="lidMaterial"`; `branch="lid"` |
| `group-lid-adhesive` | `k_cadh`<br>`conditions={"cover.type":"lid"}` | `name="topCover"`; `property_name="lidAdhesiveMaterial"`; `branch="lid"` |
| `group-lid-die-attach` | `kda`<br>`conditions={"cover.type":"lid"}` | `name="topCover"`; `property_name="dieAttachMaterial"`; `branch="lid"` |
| `group-plate` | `k_cap`<br>`conditions={"cover.type":"plate"}` | `name="topCover"`; `property_name="plateMaterial"`; `branch="plate"` |
| `group-plate-die-attach` | `kda`<br>`conditions={"cover.type":"plate"}` | `name="topCover"`; `property_name="dieAttachMaterial"`; `branch="plate"` |
| `group-bump-solder` | `k_C4` | `name="flipChipBumps"`; `property_name="c4SolderMaterial"` |
| `group-underfill` | `k_underfill`<br>`conditions={"bumps.underfill":true}` | `name="flipChipBumps"`; `property_name="underfillMaterial"` |
| `group-bga-solder` | `k_solder` | `name="solderBalls"`; `property_name="solderMaterial"` |
| `group-stiffener` | `k_stiff`<br>`conditions={"cover.type":"lid","stiffener.enabled":true}` | `name="topCover"`; `property_name="stiffenerMaterial"`; `branch="lid"` |
| `group-stiffener-adhesive` | `k_sadh`<br>`conditions={"cover.type":"lid","stiffener.enabled":true}` | `name="topCover"`; `property_name="stiffenerAdhesiveMaterial"`; `branch="lid"` |
| `group-slug` | `k_sl`<br>`conditions={"cover.type":"encapsulant","slug.enabled":true}` | `name="dropInSlug"`; `property_name="slugMaterial"` |
| `group-slug-adhesive` | `k_slad`<br>`conditions={"cover.type":"encapsulant","slug.enabled":true,"slug.adhesive_enabled":true}` | `name="dropInSlug"`; `property_name="slugAdhesiveMaterial"` |

### Bga

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `representation` | `radio_BGA_modeling` | `name="modelingOptions"`; `property_name="modelSolderBallArrayAs"` |
| `solder_removal_enabled` | `depop_center` | `name="solderBallDepopulation"`; `property_name="depopulatedCenter"` |
| `populated_columns` | `MDp` | `name="solderBallDepopulation"`; `property_name="numberFullyPopulatedRowsMDp"` |
| `populated_rows` | `MEp` | `name="solderBallDepopulation"`; `property_name="numberFullyPopulatedRowsMEp"` |
| `center_solder_enabled` | `central_balls` | `name="centralBalls"`; `property_name="centralBalls"` |
| `center_solder_columns` | `MDc` | `name="centralBalls"`; `property_name="numberCentralRowsMDp"` |
| `center_solder_rows` | `MEc` | `name="centralBalls"`; `property_name="numberCentralRowsMEp"` |
| `staggered` | `staggered_matrix` | `name="solderBalls"`; `property_name="staggeredMatrix"` |
| `center_staggered` | `central_staggered_matrix` | `name="centralBalls"`; `property_name="staggeredMatrix"` |
| `omitted_cells` | `balls` | `name="solderBallDepopulation"`; `property_name="depopulationDialog"` |
| `removal_rows` | — | — |
| `removal_columns` | — | — |
| `ball_map_enabled` | `csvBGA` | `name="solderBalls"`; `property_name="solderBallMap"` |
| `ball_map` | `csvBGA` | `name="solderBalls"`; `property_name="solderBallMapDialog"` |
| `via_configuration` | — | — |

### ProjectDocument

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `TemplateId` | `package` | — |
| `Name` | `design` | — |
| `PresetId` | — | — |
| `CustomMaterials` | — | — |

## chip_array

### Values

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `footprint.size` | — | `name=null`; `property_name="jedecFootprint"` |
| `package.length` | `D`<br>`unit=mm` | `name="overallPackage"`; `property_name="lengthD"` |
| `package.width` | `E`<br>`unit=mm` | `name="overallPackage"`; `property_name="widthE"` |
| `substrate.thickness` | `A2`<br>`unit=mm` | `name="overallPackage"`; `property_name="substrateThicknessA2"` |
| `trace.top_thickness` | `substrate.layers=2-Layer`: `tza1`<br>`substrate.layers=4-Layer`: `tz1`<br>`unit=mm` | `name=null`; `property_name="topSignalLayerThickness"` |
| `trace.bottom_thickness` | `substrate.layers=2-Layer`: `tza2`<br>`substrate.layers=4-Layer`: `tz4`<br>`unit=mm` | `name=null`; `property_name="bottomSignalLayerThickness"` |
| `die.length` | `Ld`<br>`unit=mm` | `name="die"`; `property_name="dieLengthLd"` |
| `die.width` | `Wd`<br>`unit=mm` | `name="die"`; `property_name="dieWidthWd"` |
| `die.thickness` | `td`<br>`unit=mm` | `name="die"`; `property_name="dieThicknessTd"` |
| `die.attach` | `tda`<br>`unit=mm` | `name="die"`; `property_name="dieAttachThicknessTda"` |
| `die.power` | `P`<br>`unit=W` | `name="die"`; `property_name="packagePower"` |
| `encapsulant.thickness` | `te`<br>`unit=mm` | `name="encapsulant"`; `property_name="thicknessTe"` |
| `solder_mask.thickness` | `tsm`<br>`unit=mm` | `name="encapsulant"`; `property_name="solderMaskThicknessTsm"` |
| `bond_wire.extent_length` | `Lw`<br>`unit=mm` | `name="bondWires"`; `property_name="extentOfBondWirePadsLw"` |
| `bond_wire.extent_width` | `Ww`<br>`unit=mm` | `name="bondWires"`; `property_name="extentOfBondWirePadsWw"` |
| `bond_wire.diameter` | `dw`<br>`unit=mm` | `name="bondWires"`; `property_name="bondWireDiameterDw"` |
| `vias.enabled` | — | — |
| `vias.diameter` | `dv`<br>`unit=mm`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="vias"`; `property_name="viaDiameterDv"` |
| `vias.plating` | `tpl`<br>`unit=mm`<br>`conditions={"visible_when":{"vias.enabled":true,"vias.filled":false}}` | `name="vias"`; `property_name="platingThicknessTpl"` |
| `vias.offset_x` | `vxoff`<br>`unit=mm`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="modelingOptions"`; `property_name="viaOffsetInX"` |
| `vias.offset_y` | `vyoff`<br>`unit=mm`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="modelingOptions"`; `property_name="viaOffsetInY"` |
| `bga.columns` | `MD` | `name="solderBalls"`; `property_name="numberOfSolderBallsInXMD"` |
| `bga.rows` | `ME` | `name="solderBalls"`; `property_name="numberOfSolderBallsInYME"` |
| `bga.pitch` | `e`<br>`unit=mm` | `name="solderBalls"`; `property_name="ballPitchE"` |
| `bga.diameter` | `b`<br>`unit=mm` | `name="solderBalls"`; `property_name="ballDiameterB"` |
| `bga.height` | `A1`<br>`unit=mm` | `name="solderBalls"`; `property_name="substrateStandoffA1"` |
| `grid.enabled` | `localgrid` | `name="modelingOptions"`; `property_name="localizeGrid"` |
| `grid.density` | `radio_lgc`<br>`conditions={"visible_when":{"grid.enabled":true}}` | `name="modelingOptions"`; `property_name="gridDensity"` |
| `substrate.layers` | `num_metal_layers` | `name="metalLayers"`; `property_name="substrateLayer"`; `branch="substrateLayer / wizard"` |
| `bond_wire.auto_count` | `radio_default_bwNumber` | `name="bondWires"`; `property_name="numberBondWiresEqualsSolderBalls"` |
| `bond_wire.total` | `Nw`<br>`conditions={"visible_when":{"bond_wire.auto_count":false}}` | `name="bondWires"`; `property_name="numberOfBondWiresNw"` |
| `bond_wire.include` | `radio_BW_modeling` | `name="modelingOptions"`; `property_name="bondWireModeling"` |
| `vias.filled` | `radio_filled_vias`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="vias"`; `property_name="filledVias"` |
| `vias.modeling` | `radio_Via_modeling`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="modelingOptions"`; `property_name="viaModeling"` |
| `metal.layers` | `substrate.layers=2-Layer`: `tza1`, `tza2`, `coveragea1`, `coveragea2`<br>`substrate.layers=4-Layer`: `tz1`, `tz2`, `tz3`, `tz4`, `coverage1`, `coverage2`, `coverage3`, `coverage4`, `z2`, `z3`<br>`unit=mm / %` | `name="metalLayers"`; `property_name="twoLayerMetalLayersTable"`; `conditions={"substrate.layers":"2-Layer"}`<br>`name="metalLayers"`; `property_name="fourLayerMetalLayersTable"`; `conditions={"substrate.layers":"4-Layer"}` |
| `metal.hole_length` | `Lml`<br>`unit=mm` | `name="metalLayers"`; `property_name="lengthLml"` |
| `metal.hole_width` | `Wml`<br>`unit=mm` | `name="metalLayers"`; `property_name="widthWml"` |

### Assignments

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `group-substrate` | `k_substr` | `name="overallPackage"`; `property_name="dielectricMaterial"` |
| `group-die` | — | — |
| `group-die-attach` | `k_da` | `name="die"`; `property_name="dieAttachMaterial"` |
| `group-encapsulant` | `k_encap` | `name="encapsulant"`; `property_name="encapsulantMaterial"` |
| `group-bond-wires` | `k_wire` | `name="bondWires"`; `property_name="bondWireMaterial"` |
| `group-solder-mask` | `k_mask` | `name="encapsulant"`; `property_name="solderMaskMaterial"` |
| `group-bga-solder` | `k_solder` | `name="solderBalls"`; `property_name="solderMaterial"` |
| `group-metal` | `k_metal` | `name="metalLayers"`; `property_name="materialOfMetal"` |
| `group-trace-hole` | `k_ml` | `name="metalLayers"`; `property_name="conductivity"` |

### Bga

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `representation` | — | — |
| `solder_removal_enabled` | `depop_center` | `name="solderBallDepopulation"`; `property_name="depopulatedCenter"` |
| `populated_columns` | `MDp` | `name="solderBallDepopulation"`; `property_name="numberFullyPopulatedRowsMDp"` |
| `populated_rows` | `MEp` | `name="solderBallDepopulation"`; `property_name="numberFullyPopulatedRowsMEp"` |
| `center_solder_enabled` | `central_balls` | `name="centralBalls"`; `property_name="centralBalls"` |
| `center_solder_columns` | `MDc` | `name="centralBalls"`; `property_name="numberCentralRowsMDp"` |
| `center_solder_rows` | `MEc` | `name="centralBalls"`; `property_name="numberCentralRowsMEp"` |
| `staggered` | `staggered_matrix` | `name="solderBalls"`; `property_name="staggeredMatrix"` |
| `center_staggered` | `central_staggered_matrix` | `name="centralBalls"`; `property_name="staggeredMatrix"` |
| `omitted_cells` | `balls` | `name="solderBallDepopulation"`; `property_name="depopulationDialog"` |
| `removal_rows` | — | — |
| `removal_columns` | — | — |
| `ball_map_enabled` | `csvBGA` | `name="solderBalls"`; `property_name="solderBallMap"` |
| `ball_map` | `csvBGA` | `name="solderBalls"`; `property_name="solderBallMapDialog"` |
| `via_configuration` | — | — |

### ProjectDocument

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `TemplateId` | `package` | — |
| `Name` | `design` | — |
| `PresetId` | — | — |
| `CustomMaterials` | — | — |

## pbga_fc

### Values

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `footprint.size` | — | `name=null`; `property_name="jedecFootprint"` |
| `substrate.length` | `D`<br>`unit=mm` | `name="packageSubstrate"`; `property_name="substrateLengthD"` |
| `substrate.width` | `E`<br>`unit=mm` | `name="packageSubstrate"`; `property_name="substrateWidthE"` |
| `substrate.thickness` | `A2`<br>`unit=mm` | `name="packageSubstrate"`; `property_name="substrateThicknessA2"` |
| `die.length` | `Ld`<br>`unit=mm` | `name="die"`; `property_name="dieLengthLd"` |
| `die.width` | `Wd`<br>`unit=mm` | `name="die"`; `property_name="dieWidthWd"` |
| `die.thickness` | `td`<br>`unit=mm` | `name="die"`; `property_name="dieThicknessTd"` |
| `die.power` | `P`<br>`unit=W` | `name="die"`; `property_name="packagePower"` |
| `bumps.total` | `MNC4`<br>`conditions={"visible_when":{"bumps.array_type":"non_regular"}}` | `name="flipChipBumps"`; `property_name="totalNumberOfBumpsMNC4"` |
| `bumps.diameter` | `bC4`<br>`unit=mm` | `name="flipChipBumps"`; `property_name="bumpDiameterBC4"` |
| `bumps.height` | `tC4`<br>`unit=mm` | `name="flipChipBumps"`; `property_name="bumpHeightTC4"` |
| `bumps.modeling` | — | `name="modelingOptions"`; `property_name="modelFlipChipBumpsAs"` |
| `bga.columns` | `MD` | `name="solderBalls"`; `property_name="numberOfSolderBallsInXMD"` |
| `bga.rows` | `ME` | `name="solderBalls"`; `property_name="numberOfSolderBallsInYME"` |
| `bga.pitch` | `e`<br>`unit=mm` | `name="solderBalls"`; `property_name="ballPitchE"` |
| `bga.diameter` | `b`<br>`unit=mm` | `name="solderBalls"`; `property_name="ballDiameterB"` |
| `bga.height` | `A1`<br>`unit=mm` | `name="solderBalls"`; `property_name="substrateStandoffA1"` |
| `cover.type` | `radio_EnCaPl` | `name=null`; `property_name="topCover"` |
| `cover.length` | `Le`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant"}}` | `name="topCover"`; `property_name="lengthLe"`; `branch="encapsulant"` |
| `cover.width` | `We`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant"}}` | `name="topCover"`; `property_name="widthWe"`; `branch="encapsulant"` |
| `cover.thickness` | `te`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant"}}` | `name="topCover"`; `property_name="thicknessTe"`; `branch="encapsulant"` |
| `lid.length` | `Lc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid"}}` | `name="topCover"`; `property_name="lidLengthLc"`; `branch="lid"` |
| `lid.width` | `Wc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid"}}` | `name="topCover"`; `property_name="lidWidthWc"`; `branch="lid"` |
| `lid.thickness` | `tc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid"}}` | `name="topCover"`; `property_name="lidThicknessTc"`; `branch="lid"` |
| `lid.base_thickness` | `tcb`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid"}}` | `name="topCover"`; `property_name="lidBaseThicknessTcb"`; `branch="lid"` |
| `lid.die_attach` | `tda`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid"}}` | `name="topCover"`; `property_name="dieAttachThicknessTda"`; `branch="lid"` |
| `lid.adhesive` | `tcadh`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid"}}` | `name="topCover"`; `property_name="lidAdhesiveThickness"`; `branch="lid"` |
| `plate.length` | `Lc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"plate"}}` | `name="topCover"`; `property_name="plateLengthLc"`; `branch="plate"` |
| `plate.width` | `Wc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"plate"}}` | `name="topCover"`; `property_name="plateWidthWc"`; `branch="plate"` |
| `plate.thickness` | `tc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"plate"}}` | `name="topCover"`; `property_name="plateThicknessTc"`; `branch="plate"` |
| `plate.die_attach` | `tda`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"plate"}}` | `name="topCover"`; `property_name="dieAttachThicknessTda"`; `branch="plate"` |
| `grid.enabled` | `localgrid` | `name="modelingOptions"`; `property_name="localizeGrid"` |
| `grid.density` | `radio_lgc`<br>`conditions={"visible_when":{"grid.enabled":true}}` | `name="modelingOptions"`; `property_name="gridDensity"` |
| `bumps.array_type` | `radio_bump_type` | `name="flipChipBumps"`; `property_name="arrayType"` |
| `bumps.columns` | `MDC4`<br>`conditions={"visible_when":{"bumps.array_type":"regular"}}` | `name="flipChipBumps"`; `property_name="numberOfBumpsInXMDC4"` |
| `bumps.rows` | `MEC4`<br>`conditions={"visible_when":{"bumps.array_type":"regular"}}` | `name="flipChipBumps"`; `property_name="numberOfBumpsInYMEC4"` |
| `bumps.underfill` | `c4_underfill` | `name="flipChipBumps"`; `property_name="underfill"` |
| `cover.flush` | `check_thickness`<br>`conditions={"visible_when":{"cover.type":"encapsulant"}}` | `name="topCover"`; `property_name="enableDieFlush"`; `branch="encapsulant"` |
| `stiffener.enabled` | `radio_stiffener`<br>`conditions={"visible_when":{"cover.type":"lid"}}` | `name="topCover"`; `property_name="stiffener"`; `branch="lid"` |
| `stiffener.length` | `Ls`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | `name="topCover"`; `property_name="stiffenerLengthLs"`; `branch="lid"` |
| `stiffener.width` | `Ws`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | `name="topCover"`; `property_name="stiffenerWidthWs"`; `branch="lid"` |
| `stiffener.cavity_length` | `Lsc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | `name="topCover"`; `property_name="stiffenerCavityLengthLsc"`; `branch="lid"` |
| `stiffener.cavity_width` | `Wsc`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | `name="topCover"`; `property_name="stiffenerCavityWidthWsc"`; `branch="lid"` |
| `stiffener.adhesive` | `tsadh`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | `name="topCover"`; `property_name="stiffenerAdhesiveThickness"`; `branch="lid"` |
| `slug.enabled` | `slug`<br>`conditions={"enabled_when":{"cover.type":"encapsulant"}}` | `name="dropInSlug"`; `property_name="includeSlug"` |
| `slug.length` | `L_sl`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugLengthLsl"` |
| `slug.width` | `W_sl`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugWidthWsl"` |
| `slug.thickness` | `t_sl`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugThicknessTsl"` |
| `slug.diameter` | `dsl`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugDiameterDs"` |
| `slug.foot_length` | `L_slf`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugFootExtendLengthLsf"` |
| `slug.foot_width` | `W_slf`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugFootExtendWidthWsf"` |
| `slug.offset` | `gsl`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugOffsetGs"` |
| `slug.clearance` | `g_slf`<br>`unit=mm`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugFootClearanceGsf"` |
| `slug.adhesive_enabled` | `slug_adh`<br>`conditions={"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | `name="dropInSlug"`; `property_name="adhesivePresentUnderSlugFoot"` |
| `vias.enabled` | — | — |
| `vias.columns` | `NVx`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="coreVias"`; `property_name="numberOfThermalViasInXNVx"` |
| `vias.rows` | `NVy`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="coreVias"`; `property_name="numberOfThermalViasInYNVy"` |
| `vias.pitch` | `ev`<br>`unit=mm`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="coreVias"`; `property_name="viaPitchEv"` |
| `vias.diameter` | `dv`<br>`unit=mm`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="coreVias"`; `property_name="viaDiameterDv"` |
| `vias.plating` | `tpl`<br>`unit=mm`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="coreVias"`; `property_name="platingThicknessTpl"` |
| `vias.modeling` | `radio_Via_modeling`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="modelingOptions"`; `property_name="modelCoreViasAs"` |
| `metal.layers` | `z{i}`, `tz{i}`, `coverage{i}`<br>`unit=mm / %` | `name="metalLayers"`; `property_name="metalLayersTable"` |
| `upper.enabled` | — | — |
| `upper.thickness` | `A2b1`<br>`unit=mm`<br>`conditions={"visible_when":{"upper.enabled":true}}` | `name="upperBuiltUpRegion"`; `property_name="thicknessA2b1"` |
| `upper.count` | `Nb1`<br>`conditions={"visible_when":{"upper.enabled":true}}` | `name="upperBuiltUpRegion"`; `property_name="totalNumberOfMicroViasNb1"` |
| `upper.diameter` | `dv_b1`<br>`unit=mm`<br>`conditions={"visible_when":{"upper.enabled":true}}` | `name="upperBuiltUpRegion"`; `property_name="viaDiameterDvb1"` |
| `upper.plating` | `tpl_b1`<br>`unit=mm`<br>`conditions={"visible_when":{"upper.enabled":true}}` | `name="upperBuiltUpRegion"`; `property_name="platingThicknessTpl"` |
| `upper.filled` | `radio_up_filled_vias`<br>`conditions={"visible_when":{"upper.enabled":true}}` | `name="upperBuiltUpRegion"`; `property_name="filledVias"` |
| `upper.layers` | `zb1_{i}`, `tzb1_{i}`, `coverb1_{i}`<br>`unit=mm / %`<br>`conditions={"visible_when":{"upper.enabled":true}}` | `name="upperBuiltUpRegion"`; `property_name="metalLayersTable"` |
| `lower.enabled` | — | — |
| `lower.thickness` | `A2b2`<br>`unit=mm`<br>`conditions={"visible_when":{"lower.enabled":true}}` | `name="lowerBuiltUpRegion"`; `property_name="thicknessA2b2"` |
| `lower.count` | `Nb2`<br>`conditions={"visible_when":{"lower.enabled":true}}` | `name="lowerBuiltUpRegion"`; `property_name="totalNumberOfMicroViasNb2"` |
| `lower.diameter` | `dv_b2`<br>`unit=mm`<br>`conditions={"visible_when":{"lower.enabled":true}}` | `name="lowerBuiltUpRegion"`; `property_name="viaDiameterDvb2"` |
| `lower.plating` | `tpl_b2`<br>`unit=mm`<br>`conditions={"visible_when":{"lower.enabled":true}}` | `name="lowerBuiltUpRegion"`; `property_name="platingThicknessTpl"` |
| `lower.filled` | `radio_low_filled_vias`<br>`conditions={"visible_when":{"lower.enabled":true}}` | `name="lowerBuiltUpRegion"`; `property_name="filledVias"` |
| `lower.layers` | `zb2_{i}`, `tzb2_{i}`, `coverb2_{i}`<br>`unit=mm / %`<br>`conditions={"visible_when":{"lower.enabled":true}}` | `name="lowerBuiltUpRegion"`; `property_name="metalLayersTable"` |

### Assignments

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `group-substrate` | `k_substr` | `name="packageSubstrate"`; `property_name="dielectricMaterial"` |
| `group-die` | — | — |
| `group-encapsulant` | `k_encap`<br>`conditions={"cover.type":"encapsulant"}` | `name="topCover"`; `property_name="encapsulantMaterial"`; `branch="encapsulant"` |
| `group-lid` | `k_cap`<br>`conditions={"cover.type":"lid"}` | `name="topCover"`; `property_name="lidMaterial"`; `branch="lid"` |
| `group-lid-adhesive` | `k_cadh`<br>`conditions={"cover.type":"lid"}` | `name="topCover"`; `property_name="lidAdhesiveMaterial"`; `branch="lid"` |
| `group-lid-die-attach` | `kda`<br>`conditions={"cover.type":"lid"}` | `name="topCover"`; `property_name="dieAttachMaterial"`; `branch="lid"` |
| `group-plate` | `k_cap`<br>`conditions={"cover.type":"plate"}` | `name="topCover"`; `property_name="plateMaterial"`; `branch="plate"` |
| `group-plate-die-attach` | `kda`<br>`conditions={"cover.type":"plate"}` | `name="topCover"`; `property_name="dieAttachMaterial"`; `branch="plate"` |
| `group-bump-solder` | `k_C4` | `name="flipChipBumps"`; `property_name="c4SolderMaterial"` |
| `group-underfill` | `k_underfill`<br>`conditions={"bumps.underfill":true}` | `name="flipChipBumps"`; `property_name="underfillMaterial"` |
| `group-bga-solder` | `k_solder` | `name="solderBalls"`; `property_name="solderMaterial"` |
| `group-stiffener` | `k_stiff`<br>`conditions={"cover.type":"lid","stiffener.enabled":true}` | `name="topCover"`; `property_name="stiffenerMaterial"`; `branch="lid"` |
| `group-stiffener-adhesive` | `k_sadh`<br>`conditions={"cover.type":"lid","stiffener.enabled":true}` | `name="topCover"`; `property_name="stiffenerAdhesiveMaterial"`; `branch="lid"` |
| `group-slug` | `k_sl`<br>`conditions={"cover.type":"encapsulant","slug.enabled":true}` | `name="dropInSlug"`; `property_name="slugMaterial"` |
| `group-slug-adhesive` | `k_slad`<br>`conditions={"cover.type":"encapsulant","slug.enabled":true,"slug.adhesive_enabled":true}` | `name="dropInSlug"`; `property_name="slugAdhesiveMaterial"` |
| `group-metal` | `k_metal` | `name="metalLayers"`; `property_name="materialOfMetal"` |
| `group-upper` | `kb1`<br>`conditions={"upper.enabled":true}` | `name="upperBuiltUpRegion"`; `property_name="dielectricMaterial"` |
| `group-lower` | `kb2`<br>`conditions={"lower.enabled":true}` | `name="lowerBuiltUpRegion"`; `property_name="dielectricMaterial"` |

### Bga

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `representation` | `radio_BGA_modeling` | `name="modelingOptions"`; `property_name="modelSolderBallArrayAs"` |
| `solder_removal_enabled` | `depop_center` | `name="solderBallDepopulation"`; `property_name="depopulatedCenter"` |
| `populated_columns` | `MDp` | `name="solderBallDepopulation"`; `property_name="numberFullyPopulatedRowsMDp"` |
| `populated_rows` | `MEp` | `name="solderBallDepopulation"`; `property_name="numberFullyPopulatedRowsMEp"` |
| `center_solder_enabled` | `central_balls` | `name="centralBalls"`; `property_name="centralBalls"` |
| `center_solder_columns` | `MDc` | `name="centralBalls"`; `property_name="numberCentralRowsMDp"` |
| `center_solder_rows` | `MEc` | `name="centralBalls"`; `property_name="numberCentralRowsMEp"` |
| `staggered` | `staggered_matrix` | `name="solderBalls"`; `property_name="staggeredMatrix"` |
| `center_staggered` | `central_staggered_matrix` | `name="centralBalls"`; `property_name="staggeredMatrix"` |
| `omitted_cells` | `balls` | `name="solderBallDepopulation"`; `property_name="depopulationDialog"` |
| `removal_rows` | — | — |
| `removal_columns` | — | — |
| `ball_map_enabled` | `csvBGA` | `name="solderBalls"`; `property_name="solderBallMap"` |
| `ball_map` | `csvBGA` | `name="solderBalls"`; `property_name="solderBallMapDialog"` |
| `via_configuration` | — | — |

### ProjectDocument

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `TemplateId` | `package` | — |
| `Name` | `design` | — |
| `PresetId` | — | — |
| `CustomMaterials` | — | — |

## pbga_wb

### Values

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `footprint.size` | — | `name=null`; `property_name="jedecFootprint"` |
| `package.length` | `D`<br>`unit=mm` | `name="packageSubstrate"`; `property_name="substrateLengthD"` |
| `package.width` | `E`<br>`unit=mm` | `name="packageSubstrate"`; `property_name="substrateWidthE"` |
| `substrate.thickness` | `A2`<br>`unit=mm` | `name="packageSubstrate"`; `property_name="substrateThicknessA2"` |
| `trace.top_thickness` | `tz1`<br>`unit=mm` | `name=null`; `property_name="topSignalLayerThickness"` |
| `trace.bottom_thickness` | `tz6`<br>`unit=mm` | `name=null`; `property_name="bottomSignalLayerThickness"` |
| `encapsulant.length` | `Le`<br>`unit=mm` | `name="encapsulant"`; `property_name="lengthLe"` |
| `encapsulant.width` | `We`<br>`unit=mm` | `name="encapsulant"`; `property_name="widthWe"` |
| `encapsulant.thickness` | `te`<br>`unit=mm` | `name="encapsulant"`; `property_name="thicknessTe"` |
| `flag.length` | `Lf`<br>`unit=mm` | `name="dieFlagAndSolderMask"`; `property_name="dieFlagLf"` |
| `flag.width` | `Wf`<br>`unit=mm` | `name="dieFlagAndSolderMask"`; `property_name="dieFlagWf"` |
| `solder_mask.thickness` | `tsm`<br>`unit=mm` | `name="dieFlagAndSolderMask"`; `property_name="solderMaskThickness"` |
| `die.length` | `Ld`<br>`unit=mm` | `name="die"`; `property_name="dieLengthLd"` |
| `die.width` | `Wd`<br>`unit=mm` | `name="die"`; `property_name="dieWidthWd"` |
| `die.thickness` | `td`<br>`unit=mm` | `name="die"`; `property_name="dieThicknessTd"` |
| `die.attach` | `tda`<br>`unit=mm` | `name="die"`; `property_name="dieAttachThicknessTda"` |
| `die.power` | `P`<br>`unit=W` | `name="die"`; `property_name="packagePower"` |
| `bond_wire.total` | `Nw` | `name="die"`; `property_name="numberOfBondWiresNw"` |
| `bond_wire.extent_length` | `Lw`<br>`unit=mm` | `name="die"`; `property_name="bondWireExtentLengthLw"` |
| `bond_wire.extent_width` | `Ww`<br>`unit=mm` | `name="die"`; `property_name="bondWireExtentWidthWw"` |
| `bond_wire.diameter` | `dw`<br>`unit=mm` | `name="die"`; `property_name="bondWireDiameterDw"` |
| `vias.enabled` | — | — |
| `vias.columns` | `NVx`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="thermalVias"`; `property_name="numberOfThermalViasInXNVx"` |
| `vias.rows` | `NVy`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="thermalVias"`; `property_name="numberOfThermalViasInYNVy"` |
| `vias.pitch` | `ev`<br>`unit=mm`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="thermalVias"`; `property_name="viaPitchEv"` |
| `vias.diameter` | `dv`<br>`unit=mm`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="thermalVias"`; `property_name="viaDiameterDv"` |
| `vias.plating` | `tpl`<br>`unit=mm`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="thermalVias"`; `property_name="platingThicknessTpl"` |
| `bga.columns` | `MD` | `name="solderBalls"`; `property_name="numberOfSolderBallsInXMD"` |
| `bga.rows` | `ME` | `name="solderBalls"`; `property_name="numberOfSolderBallsInYME"` |
| `bga.pitch` | `e`<br>`unit=mm` | `name="solderBalls"`; `property_name="ballPitchE"` |
| `bga.diameter` | `b`<br>`unit=mm` | `name="solderBalls"`; `property_name="ballDiameterB"` |
| `bga.height` | `A1`<br>`unit=mm` | `name="solderBalls"`; `property_name="substrateStandoffA1"` |
| `spreader.enabled` | `backside_spreader` | `name="backsideSpreader"`; `property_name="includeBacksideSpreader"` |
| `spreader.length` | `L_spr`<br>`unit=mm`<br>`conditions={"visible_when":{"spreader.enabled":true}}` | `name="backsideSpreader"`; `property_name="spreaderLengthLspr"` |
| `spreader.width` | `W_spr`<br>`unit=mm`<br>`conditions={"visible_when":{"spreader.enabled":true}}` | `name="backsideSpreader"`; `property_name="spreaderWidthWspr"` |
| `spreader.thickness` | `t_spr`<br>`unit=mm`<br>`conditions={"visible_when":{"spreader.enabled":true}}` | `name="backsideSpreader"`; `property_name="spreaderThicknessTspr"` |
| `spreader.hole_length` | `Lbt`<br>`unit=mm`<br>`conditions={"visible_when":{"spreader.enabled":true}}` | `name="backsideSpreader"`; `property_name="bottomTraceHoleLengthLbt"` |
| `spreader.hole_width` | `Wbt`<br>`unit=mm`<br>`conditions={"visible_when":{"spreader.enabled":true}}` | `name="backsideSpreader"`; `property_name="bottomTraceHoleWidthWbt"` |
| `grid.enabled` | `localgrid` | `name="modelingOptions"`; `property_name="localizeGrid"` |
| `grid.density` | `radio_lgc`<br>`conditions={"visible_when":{"grid.enabled":true}}` | `name="modelingOptions"`; `property_name="gridDensity"` |
| `bond_wire.modeling` | `radio_Bond_Wires_modeling` | `name="modelingOptions"`; `property_name="modelBondWiresAs"` |
| `substrate.layers` | — | `name=null`; `property_name="substrateLayer"` |
| `flag.coverage` | `cf`<br>`unit=%` | `name="dieFlagAndSolderMask"`; `property_name="coveragePercentageCf"` |
| `metal.layers` | `tz1`, `tz2`, `tz3`, `tz6`, `coverage1`, `coverage2`, `coverage3`, `coverage6`, `z2`, `z3`, `via_con1`, `via_con2`, `via_con3`, `via_con6`<br>`unit=mm / %` | `name="metalLayers"`; `property_name="metalLayersTable"` |
| `vias.modeling` | `radio_Via_modeling`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="modelingOptions"`; `property_name="modelThermalViasAs"` |
| `slug.enabled` | `slug` | `name="dropInSlug"`; `property_name="includeSlug"` |
| `slug.length` | `L_sl`<br>`unit=mm`<br>`conditions={"visible_when":{"slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugLengthLsl"` |
| `slug.width` | `W_sl`<br>`unit=mm`<br>`conditions={"visible_when":{"slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugWidthWsl"` |
| `slug.thickness` | `t_sl`<br>`unit=mm`<br>`conditions={"visible_when":{"slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugThicknessTsl"` |
| `slug.diameter` | `dsl`<br>`unit=mm`<br>`conditions={"visible_when":{"slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugDiameterDs"` |
| `slug.foot_length` | `L_slf`<br>`unit=mm`<br>`conditions={"visible_when":{"slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugFootExtendLengthLsf"` |
| `slug.foot_width` | `W_slf`<br>`unit=mm`<br>`conditions={"visible_when":{"slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugFootExtendWidthWsf"` |
| `slug.offset` | `gsl`<br>`unit=mm`<br>`conditions={"visible_when":{"slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugOffsetGs"` |
| `slug.clearance` | `g_slf`<br>`unit=mm`<br>`conditions={"visible_when":{"slug.enabled":true}}` | `name="dropInSlug"`; `property_name="slugFootClearanceGsf"` |
| `slug.adhesive_enabled` | `slug_adh`<br>`conditions={"visible_when":{"slug.enabled":true}}` | `name="dropInSlug"`; `property_name="adhesivePresentUnderSlugFoot"` |

### Assignments

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `group-substrate` | `k_substr` | `name="packageSubstrate"`; `property_name="dielectricMaterial"` |
| `group-die` | — | — |
| `group-die-attach` | `k_da` | `name="die"`; `property_name="dieAttachMaterial"` |
| `group-encapsulant` | `k_encap` | `name="encapsulant"`; `property_name="encapsulantMaterial"` |
| `group-bond-wires` | `k_wire` | `name="die"`; `property_name="bondWireMaterial"` |
| `group-solder-mask` | `ksm` | `name="dieFlagAndSolderMask"`; `property_name="solderMaskMaterial"` |
| `group-bga-solder` | `k_solder` | `name="solderBalls"`; `property_name="solderMaterial"` |
| `group-backside-spreader` | `k_spr`<br>`conditions={"spreader.enabled":true}` | `name="backsideSpreader"`; `property_name="spreaderMaterial"` |
| `group-traces` | `k_metal` | `name="metalLayers"`; `property_name="materialOfMetal"` |
| `group-slug` | `k_sl`<br>`conditions={"slug.enabled":true}` | `name="dropInSlug"`; `property_name="slugMaterial"` |
| `group-slug-adhesive` | `k_slad`<br>`conditions={"slug.enabled":true,"slug.adhesive_enabled":true}` | `name="dropInSlug"`; `property_name="slugAdhesiveMaterial"` |

### Bga

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `representation` | `radio_BGA_modeling` | `name="modelingOptions"`; `property_name="modelSolderBallArrayAs"` |
| `solder_removal_enabled` | `depop_center` | `name="solderBallDepopulation"`; `property_name="depopulatedCenter"` |
| `populated_columns` | `MDp` | `name="solderBallDepopulation"`; `property_name="numberFullyPopulatedRowsMDp"` |
| `populated_rows` | `MEp` | `name="solderBallDepopulation"`; `property_name="numberFullyPopulatedRowsMEp"` |
| `center_solder_enabled` | `central_balls` | `name="centralBalls"`; `property_name="centralBalls"` |
| `center_solder_columns` | `MDc` | `name="centralBalls"`; `property_name="numberCentralRowsMDp"` |
| `center_solder_rows` | `MEc` | `name="centralBalls"`; `property_name="numberCentralRowsMEp"` |
| `staggered` | `staggered_matrix` | `name="solderBalls"`; `property_name="staggeredMatrix"` |
| `center_staggered` | `central_staggered_matrix` | `name="centralBalls"`; `property_name="staggeredMatrix"` |
| `omitted_cells` | `balls` | `name="solderBallDepopulation"`; `property_name="depopulationDialog"` |
| `removal_rows` | — | — |
| `removal_columns` | — | — |
| `ball_map_enabled` | `csvBGA` | `name="solderBalls"`; `property_name="solderBallMap"` |
| `ball_map` | `csvBGA` | `name="solderBalls"`; `property_name="solderBallMapDialog"` |
| `via_configuration` | — | — |

### ProjectDocument

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `TemplateId` | `package` | — |
| `Name` | `design` | — |
| `PresetId` | — | — |
| `CustomMaterials` | — | — |

## pqfp

### Values

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `package.type` | — | `name=null`; `property_name="pqfpPackageType"` |
| `footprint.size` | — | `name=null`; `property_name="tqfpJedecFootprint"`; `branch="lqfpJedecFootprint / wizard"` |
| `package.length` | `D`<br>`unit=mm` | `name="overallPackage"`; `property_name="lengthD"` |
| `package.width` | `E`<br>`unit=mm` | `name="overallPackage"`; `property_name="widthE"` |
| `package.standoff` | `A1`<br>`unit=mm` | `name="overallPackage"`; `property_name="standoffA1"` |
| `body.length` | `D1`<br>`unit=mm` | `name="encapsulant"`; `property_name="lengthD1"` |
| `body.width` | `E1`<br>`unit=mm` | `name="encapsulant"`; `property_name="widthE1"` |
| `body.thickness` | `A2`<br>`unit=mm` | `name="encapsulant"`; `property_name="thicknessA2"` |
| `die.length` | `Ld`<br>`unit=mm` | `name="die"`; `property_name="dieLengthLd"` |
| `die.width` | `Wd`<br>`unit=mm` | `name="die"`; `property_name="dieWidthWd"` |
| `die.thickness` | `td`<br>`unit=mm` | `name="die"`; `property_name="dieThicknessTd"` |
| `die.attach` | `tda`<br>`unit=mm` | `name="die"`; `property_name="dieAttachThicknessTda"` |
| `die.power` | `P`<br>`unit=W` | `name="die"`; `property_name="packagePower"` |
| `flag.length` | `Lf`<br>`unit=mm` | `name="dieFlagAndTieBars"`; `property_name="dieFlagLf"` |
| `flag.width` | `Wf`<br>`unit=mm` | `name="dieFlagAndTieBars"`; `property_name="dieFlagWf"` |
| `flag.coverage` | `cf`<br>`unit=%` | `name="dieFlagAndTieBars"`; `property_name="metalCoverageForDieFlagCf"` |
| `flag.downset` | `ddf`<br>`unit=mm` | `name="dieFlagAndTieBars"`; `property_name="dieFlagDownsetDdf"` |
| `tie_bar.width` | `wtb`<br>`unit=mm` | `name="dieFlagAndTieBars"`; `property_name="tieBarWidthWtb"` |
| `leads.count_x` | `MD` | `name="leadFrame"`; `property_name="numberOfLeadsOnTopBottomMD"` |
| `leads.count_y` | `ME` | `name="leadFrame"`; `property_name="numberOfLeadsOnLeftRightME"` |
| `leads.pitch` | `e`<br>`unit=mm` | `name="leadFrame"`; `property_name="pitchE"` |
| `leads.width` | `b`<br>`unit=mm` | `name="leadFrame"`; `property_name="leadWidthB"` |
| `leads.thickness` | `tl`<br>`unit=mm` | `name="leadFrame"`; `property_name="leadThicknessTl"` |
| `leads.height` | `hl`<br>`unit=mm` | `name="leadFrame"`; `property_name="leadframeHeightHl"` |
| `leads.foot_length` | `wl`<br>`unit=mm` | `name="leadFrame"`; `property_name="leadfootLengthWl"` |
| `leads.gap_x` | `g1`<br>`unit=mm` | `name="leadFrame"`; `property_name="leadframeFlagGapG1"` |
| `leads.gap_y` | `g2`<br>`unit=mm` | `name="leadFrame"`; `property_name="leadframeFlagGapG2"` |
| `bond_wire.length_x` | `lbwx`<br>`unit=mm` | `name="bondWires"`; `property_name="bondWireLengthOnLeftRightLbwx"` |
| `bond_wire.length_y` | `lbwy`<br>`unit=mm` | `name="bondWires"`; `property_name="bondWireLengthOnTopBottomLbwy"` |
| `bond_wire.count` | `N` | `name="bondWires"`; `property_name="numberOfBondWiresN"` |
| `bond_wire.diameter` | `dbw`<br>`unit=mm` | `name="bondWires"`; `property_name="bondWireDiameterDbw"` |
| `thermal_land.enabled` | `landsolder` | `name="thermalLandAndSolder"`; `property_name="includeThermalLandAndSolder"` |
| `thermal_land.thickness` | `ts`<br>`unit=mm`<br>`conditions={"visible_when":{"thermal_land.enabled":true}}` | `name="thermalLandAndSolder"`; `property_name="landThickness"` |
| `grid.enabled` | `localgrid` | `name="modelingOptions"`; `property_name="localizeGrid"` |
| `grid.density` | `radio_lgc`<br>`conditions={"visible_when":{"grid.enabled":true}}` | `name="modelingOptions"`; `property_name="gridDensity"` |
| `bond_wire.modeling` | `radio_BondWire_modeling` | `name="modelingOptions"`; `property_name="modelBondWiresAs"` |
| `package.exposed_pad` | — | `name=null`; `property_name="exposedPad"` |
| `leads.custom_coverage` | `radio_defined_coverage` | `name="leadFrame"`; `property_name="userDefinedLeadframeCoverage"` |
| `leads.coverage` | `cl`<br>`unit=%`<br>`conditions={"visible_when":{"leads.custom_coverage":true}}` | `name="leadFrame"`; `property_name="leadframeCoveragePercentage"` |
| `leads.modeling` | `radio_LeadFram_modeling` | `name="modelingOptions"`; `property_name="modelLeadFrameAs"` |

### Assignments

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `group-encapsulant` | `k_encap` | `name="encapsulant"`; `property_name="encapsulantMaterial"` |
| `group-die` | — | — |
| `group-die-attach` | `k_da` | `name="die"`; `property_name="dieAttachMaterial"` |
| `group-lead-frame` | `k_metal` | `name="leadFrame"`; `property_name="leadframeMaterial"` |
| `group-bond-wires` | `k_bw` | `name="bondWires"`; `property_name="material"` |
| `group-thermal-land` | `k_land`<br>`conditions={"thermal_land.enabled":true}` | `name="thermalLandAndSolder"`; `property_name="landMaterial"` |
| `group-thermal-solder` | `k_sd`<br>`conditions={"thermal_land.enabled":true}` | `name="thermalLandAndSolder"`; `property_name="solderMaterial"` |

### ProjectDocument

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `TemplateId` | `package` | — |
| `Name` | `design` | — |
| `PresetId` | — | — |
| `CustomMaterials` | — | — |

## qfn

### Values

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `footprint.size` | — | `name=null`; `property_name="jedecFootprint"` |
| `package.length` | `D`<br>`unit=mm` | `name="overallPackage"`; `property_name="lengthD"` |
| `package.width` | `E`<br>`unit=mm` | `name="overallPackage"`; `property_name="widthE"` |
| `package.standoff` | `A1`<br>`unit=mm` | `name="overallPackage"`; `property_name="standoffA1"` |
| `encapsulant.thickness` | `A2`<br>`unit=mm` | `name="overallPackage"`; `property_name="encapsulantThicknessA2"` |
| `die.length` | `Ld`<br>`unit=mm` | `name="die"`; `property_name="dieLengthLd"` |
| `die.width` | `Wd`<br>`unit=mm` | `name="die"`; `property_name="dieWidthWd"` |
| `die.thickness` | `td`<br>`unit=mm` | `name="die"`; `property_name="dieThicknessTd"` |
| `die.attach` | `tda`<br>`unit=mm` | `name="die"`; `property_name="dieAttachThicknessTda"` |
| `die.power` | `P`<br>`unit=W` | `name="die"`; `property_name="packagePower"` |
| `pad.length` | `Lp`<br>`unit=mm` | `name="dap"`; `property_name="dapLengthLp"` |
| `pad.width` | `Wp`<br>`unit=mm` | `name="dap"`; `property_name="dapWidthWp"` |
| `pad.exposed_length` | `Lep`<br>`unit=mm` | `name="dap"`; `property_name="exposedPADLength"` |
| `pad.exposed_width` | `Wep`<br>`unit=mm` | `name="dap"`; `property_name="exposedPADWidth"` |
| `leads.count_x` | `MD` | `name="leadAndSolderInterconnect"`; `property_name="numberOfLeadsOnTopBottomMD"` |
| `leads.count_y` | `ME` | `name="leadAndSolderInterconnect"`; `property_name="numberOfLeadsOnLeftRightME"` |
| `leads.pitch_x` | `ex`<br>`unit=mm` | `name="leadAndSolderInterconnect"`; `property_name="pitchInXDirectionEx"` |
| `leads.pitch_y` | `ey`<br>`unit=mm` | `name="leadAndSolderInterconnect"`; `property_name="pitchInYDirectionEy"` |
| `leads.width` | `wf`<br>`unit=mm` | `name="leadAndSolderInterconnect"`; `property_name="leadWidthB"` |
| `leads.length` | `lf`<br>`unit=mm` | `name="leadAndSolderInterconnect"`; `property_name="exposedLeadLengthL"` |
| `leads.exposed_thickness` | `hf`<br>`unit=mm` | `name="leadAndSolderInterconnect"`; `property_name="exposedLeadThickness"` |
| `leads.thickness` | `tf`<br>`unit=mm` | `name="leadAndSolderInterconnect"`; `property_name="leadThicknessA3"` |
| `leads.etch` | `ldent`<br>`unit=mm` | `name="leadAndSolderInterconnect"`; `property_name="leadEtch"` |
| `bond_wire.length_x` | `lbwx`<br>`unit=mm` | `name="bondWires"`; `property_name="bondWireLengthOnLeftRightLbwx"` |
| `bond_wire.length_y` | `lbwy`<br>`unit=mm` | `name="bondWires"`; `property_name="bondWireLengthOnTopBottomLbwy"` |
| `bond_wire.diameter` | `dbw`<br>`unit=mm` | `name="bondWires"`; `property_name="bondWireDiameterDbw"` |
| `thermal_land.enabled` | `isLand` | `name="thermalLand"`; `property_name="includeLand"` |
| `thermal_land.thickness` | `ts`<br>`unit=mm`<br>`conditions={"visible_when":{"thermal_land.enabled":true}}` | `name="thermalLand"`; `property_name="landThickness"` |
| `vias.enabled` | `radio_via_modeling` | `name="vias"`; `property_name="modelViasAs"` |
| `vias.length` | `lv`<br>`unit=mm`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="vias"`; `property_name="viasLengthLv"` |
| `vias.diameter` | `dv`<br>`unit=mm`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="vias"`; `property_name="viasDiameterDv"` |
| `vias.plating` | `tpl`<br>`unit=mm`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="vias"`; `property_name="platingThicknessTpl"` |
| `vias.pitch` | `ev`<br>`unit=mm`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="vias"`; `property_name="viasPitchEv"` |
| `vias.columns` | `VD`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="vias"`; `property_name="numberOfViasInXVD"` |
| `vias.rows` | `VE`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="vias"`; `property_name="numberOfViasInYVE"` |
| `grid.enabled` | `localgrid` | `name="modelingOptions"`; `property_name="localizeGrid"` |
| `grid.density` | `radio_lgc`<br>`conditions={"visible_when":{"grid.enabled":true}}` | `name="modelingOptions"`; `property_name="gridDensity"` |
| `leads.modeling` | `radio_LeadFram_modeling` | `name="modelingOptions"`; `property_name="modelLeadAndSolderInterconnectAs"` |
| `bond_wire.steps` | `nsteps` | `name="modelingOptions"`; `property_name="numberOfDiscreteBondwireSteps"` |
| `vias.modeling` | `radio_via_modeling`<br>`conditions={"visible_when":{"vias.enabled":true}}` | `name="vias"`; `property_name="modelViasAs"` |

### Assignments

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `group-encapsulant` | `k_encap` | `name="overallPackage"`; `property_name="encapsulantMaterial"` |
| `group-die` | — | — |
| `group-die-attach` | `k_da` | `name="die"`; `property_name="dieAttachMaterial"` |
| `group-exposed-pad` | `k_dap` | `name="dap"`; `property_name="material"` |
| `group-lead-frame` | `k_lead` | `name="leadAndSolderInterconnect"`; `property_name="leadframeMaterial"` |
| `group-bond-wires` | `k_bw` | `name="bondWires"`; `property_name="material"` |
| `group-solder` | `k_solder` | `name="leadAndSolderInterconnect"`; `property_name="solderMaterial"` |
| `group-thermal-land` | `k_land`<br>`conditions={"thermal_land.enabled":true}` | `name="thermalLand"`; `property_name="material"` |

### ProjectDocument

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `TemplateId` | `package` | — |
| `Name` | `design` | — |
| `PresetId` | — | — |
| `CustomMaterials` | — | — |

## sop

### Values

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `package.type` | — | `name=null`; `property_name="sopPackageType"` |
| `footprint.size` | — | `name=null`; `property_name="tssopJedecFootprint"`; `branch="sopJedecFootprint / wizard"` |
| `package.length` | `D`<br>`unit=mm` | `name="overallPackage"`; `property_name="lengthD"` |
| `package.width` | `E`<br>`unit=mm` | `name="overallPackage"`; `property_name="widthE"` |
| `package.standoff` | `A1`<br>`unit=mm` | `name="overallPackage"`; `property_name="standoffA1"` |
| `body.length` | `D1`<br>`unit=mm` | `name="encapsulant"`; `property_name="lengthD1"` |
| `body.width` | `E1`<br>`unit=mm` | `name="encapsulant"`; `property_name="widthE1"` |
| `body.thickness` | `A2`<br>`unit=mm` | `name="encapsulant"`; `property_name="thicknessA2"` |
| `die.length` | `Ld`<br>`unit=mm` | `name="die"`; `property_name="dieLengthLd"` |
| `die.width` | `Wd`<br>`unit=mm` | `name="die"`; `property_name="dieWidthWd"` |
| `die.thickness` | `td`<br>`unit=mm` | `name="die"`; `property_name="dieThicknessTd"` |
| `die.attach` | `tda`<br>`unit=mm` | `name="die"`; `property_name="dieAttachThicknessTda"` |
| `die.power` | `P`<br>`unit=W` | `name="die"`; `property_name="packagePower"` |
| `flag.length` | `Lf`<br>`unit=mm` | `name="dieFlagAndTieBars"`; `property_name="dieFlagLf"` |
| `flag.width` | `Wf`<br>`unit=mm` | `name="dieFlagAndTieBars"`; `property_name="dieFlagWf"` |
| `flag.thickness` | `tf`<br>`unit=mm` | `name="dieFlagAndTieBars"`; `property_name="dieFlagThicknessTf"` |
| `flag.coverage` | `cf`<br>`unit=%` | `name="dieFlagAndTieBars"`; `property_name="metalCoverageForDieFlagCf"` |
| `flag.downset` | `ddf`<br>`unit=mm` | `name="dieFlagAndTieBars"`; `property_name="dieFlagDownsetDdf"` |
| `tie_bar.width` | `wtb`<br>`unit=mm` | `name="dieFlagAndTieBars"`; `property_name="tieBarWidthWtb"` |
| `leads.total` | `MT` | `name="leadFrame"`; `property_name="totalNumberOfLeadsMT"` |
| `leads.gap` | `g1`<br>`unit=mm` | `name="leadFrame"`; `property_name="leadframeFlagGapG1"` |
| `leads.pitch` | `e`<br>`unit=mm` | `name="leadFrame"`; `property_name="pitchE"` |
| `leads.width` | `b`<br>`unit=mm` | `name="leadFrame"`; `property_name="leadWidthB"` |
| `leads.thickness` | `tl`<br>`unit=mm` | `name="leadFrame"`; `property_name="leadThicknessTl"` |
| `leads.height` | `hl`<br>`unit=mm` | `name="leadFrame"`; `property_name="leadframeHeightHl"` |
| `leads.foot_length` | `Lft`<br>`unit=mm` | `name="leadFrame"`; `property_name="leadfootLengthLft"` |
| `bond_wire.count` | `N` | `name="bondWires"`; `property_name="numberOfBondWiresN"` |
| `bond_wire.diameter` | `dbw`<br>`unit=mm` | `name="bondWires"`; `property_name="bondWireDiameterDbw"` |
| `thermal_land.enabled` | `landsolder` | `name="thermalLandAndSolder"`; `property_name="includeThermalLandAndSolder"` |
| `thermal_land.thickness` | `ts`<br>`unit=mm`<br>`conditions={"visible_when":{"thermal_land.enabled":true}}` | `name="thermalLandAndSolder"`; `property_name="landThickness"` |
| `grid.enabled` | `localgrid` | `name="modelingOptions"`; `property_name="localizeGrid"` |
| `grid.density` | `radio_lgc`<br>`conditions={"visible_when":{"grid.enabled":true}}` | `name="modelingOptions"`; `property_name="gridDensity"` |
| `bond_wire.modeling` | `radio_BondWire_modeling` | `name="modelingOptions"`; `property_name="modelBondWiresAs"` |
| `package.exposed_pad` | — | `name=null`; `property_name="exposedPad"` |
| `leads.custom_coverage` | `radio_defined_coverage` | `name="leadFrame"`; `property_name="userDefinedLeadframeCoverage"` |
| `leads.coverage` | `cl`<br>`unit=%`<br>`conditions={"visible_when":{"leads.custom_coverage":true}}` | `name="leadFrame"`; `property_name="leadframeCoveragePercentage"` |

### Assignments

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `group-encapsulant` | `k_encap` | `name="encapsulant"`; `property_name="encapsulantMaterial"` |
| `group-die` | — | — |
| `group-die-attach` | `k_da` | `name="die"`; `property_name="dieAttachMaterial"` |
| `group-lead-frame` | `k_metal` | `name="leadFrame"`; `property_name="leadframeMaterial"` |
| `group-bond-wires` | `k_bw` | `name="bondWires"`; `property_name="material"` |
| `group-thermal-land` | `k_land`<br>`conditions={"thermal_land.enabled":true}` | `name="thermalLandAndSolder"`; `property_name="landMaterial"` |
| `group-thermal-solder` | `k_sd`<br>`conditions={"thermal_land.enabled":true}` | `name="thermalLandAndSolder"`; `property_name="solderMaterial"` |
| `group-die-flag` | `kdf` | `name="dieFlagAndTieBars"`; `property_name="dieFlagMaterial"` |

### ProjectDocument

| PackStudio 内部字段 | des | pack script 的字段 |
| --- | --- | --- |
| `TemplateId` | `package` | — |
| `Name` | `design` | — |
| `PresetId` | — | — |
| `CustomMaterials` | — | — |
