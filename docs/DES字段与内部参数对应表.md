# PackStudio 内部字段—DES—pack_script

## bare_die

### Values

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Values["die.length"]` | `Ld` | — | mm | `modify_component` | `die` | `dieLengthLd` |
| `Values["die.width"]` | `Wd` | — | mm | `modify_component` | `die` | `dieWidthWd` |
| `Values["die.thickness"]` | `td` | — | mm | `modify_component` | `die` | `dieThicknessTd` |
| `Values["die.power"]` | `P` | — | W | `modify_component` | `die` | `packagePower` |
| `Values["die.flipped"]` | `flip` | — | — | `modify_component` | `die` | `flippedDie` |
| `Values["bumps.enabled"]` | `bumped` | — | — | `modify_component` | `bumpedDie` | `bumpedDie` |
| `Values["bumps.total"]` | `nballs` | `{"visible_when":{"bumps.enabled":true}}` | — | `modify_component` | `bumpedDie` | `numberOfSolderBalls` |
| `Values["bumps.diameter"]` | `b` | `{"visible_when":{"bumps.enabled":true}}` | mm | `modify_component` | `bumpedDie` | `ballDiameterb` |
| `Values["bumps.height"]` | `tsd` | `{"visible_when":{"bumps.enabled":true}}` | mm | `modify_component` | `bumpedDie` | `ballHeight` |
| `Values["bumps.modeling"]` | — | `{"visible_when":{"bumps.enabled":true}}` | — | — | — | — |
| `Values["grid.enabled"]` | `localgrid` | — | — | `modify_component` | `modelingOptions` | `localizeGrid` |
| `Values["grid.density"]` | `radio_lgc` | `{"visible_when":{"grid.enabled":true}}` | — | `modify_component` | `modelingOptions` | `gridDensity` |

### Assignments

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Assignments["group-die"]` | `radio_die` | — | — | `modify_component` | `die` | `dieMaterial` |
| `Assignments["group-bump-solder"]` | `k_solder` | `{"bumps.enabled":true}` | — | `modify_component` | `bumpedDie` | `solderConductivity` |
| `Assignments["group-underfill"]` | `k_fill` | `{"bumps.enabled":true}` | — | `modify_component` | `bumpedDie` | `underfillConductivity` |

### ProjectDocument

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `ProjectDocument.TemplateId` | `package` | — | — | — | — | — |
| `ProjectDocument.Name` | `design` | — | — | — | — | — |
| `ProjectDocument.PresetId` | — | — | — | — | — | — |
| `ProjectDocument.CustomMaterials` | — | — | — | — | — | — |

## cbga_fc

### Values

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Values["footprint.size"]` | — | — | — | `new_package/new_value` | — | `jedecFootprint` |
| `Values["substrate.length"]` | `D` | — | mm | `modify_component` | `packageSubstrate` | `substrateLengthD` |
| `Values["substrate.width"]` | `E` | — | mm | `modify_component` | `packageSubstrate` | `substrateWidthE` |
| `Values["substrate.thickness"]` | `A2` | — | mm | `modify_component` | `packageSubstrate` | `substrateThicknessA2` |
| `Values["die.length"]` | `Ld` | — | mm | `modify_component` | `die` | `dieLengthLd` |
| `Values["die.width"]` | `Wd` | — | mm | `modify_component` | `die` | `dieWidthWd` |
| `Values["die.thickness"]` | `td` | — | mm | `modify_component` | `die` | `dieThicknessTd` |
| `Values["die.power"]` | `P` | — | W | `modify_component` | `die` | `packagePower` |
| `Values["bumps.total"]` | `MNC4` | `{"visible_when":{"bumps.array_type":"non_regular"}}` | — | `modify_component` | `flipChipBumps` | `totalNumberOfBumpsMNC4` |
| `Values["bumps.diameter"]` | `bC4` | — | mm | `modify_component` | `flipChipBumps` | `bumpDiameterBC4` |
| `Values["bumps.height"]` | `tC4` | — | mm | `modify_component` | `flipChipBumps` | `bumpHeightTC4` |
| `Values["bumps.modeling"]` | — | — | — | `modify_component` | `modelingOptions` | `modelFlipChipBumpsAs` |
| `Values["bga.columns"]` | `MD` | — | — | `modify_component` | `solderBalls` | `numberOfSolderBallsInXMD` |
| `Values["bga.rows"]` | `ME` | — | — | `modify_component` | `solderBalls` | `numberOfSolderBallsInYME` |
| `Values["bga.pitch"]` | `e` | — | mm | `modify_component` | `solderBalls` | `ballPitchE` |
| `Values["bga.diameter"]` | `b` | — | mm | `modify_component` | `solderBalls` | `ballDiameterB` |
| `Values["bga.height"]` | `A1` | — | mm | `modify_component` | `solderBalls` | `substrateStandoffA1` |
| `Values["cover.type"]` | `radio_EnCaPl` | — | — | `new_package/new_value` | — | `topCover` |
| `Values["cover.length"]` | `Le` | `{"visible_when":{"cover.type":"encapsulant"}}` | mm | `modify_component` | `topCover` | `lengthLe`; branch=`encapsulant` |
| `Values["cover.width"]` | `We` | `{"visible_when":{"cover.type":"encapsulant"}}` | mm | `modify_component` | `topCover` | `widthWe`; branch=`encapsulant` |
| `Values["cover.thickness"]` | `te` | `{"visible_when":{"cover.type":"encapsulant"}}` | mm | `modify_component` | `topCover` | `thicknessTe`; branch=`encapsulant` |
| `Values["lid.length"]` | `Lc` | `{"visible_when":{"cover.type":"lid"}}` | mm | `modify_component` | `topCover` | `lidLengthLc`; branch=`lid` |
| `Values["lid.width"]` | `Wc` | `{"visible_when":{"cover.type":"lid"}}` | mm | `modify_component` | `topCover` | `lidWidthWc`; branch=`lid` |
| `Values["lid.thickness"]` | `tc` | `{"visible_when":{"cover.type":"lid"}}` | mm | `modify_component` | `topCover` | `lidThicknessTc`; branch=`lid` |
| `Values["lid.base_thickness"]` | `tcb` | `{"visible_when":{"cover.type":"lid"}}` | mm | `modify_component` | `topCover` | `lidBaseThicknessTcb`; branch=`lid` |
| `Values["lid.die_attach"]` | `tda` | `{"visible_when":{"cover.type":"lid"}}` | mm | `modify_component` | `topCover` | `dieAttachThicknessTda`; branch=`lid` |
| `Values["lid.adhesive"]` | `tcadh` | `{"visible_when":{"cover.type":"lid"}}` | mm | `modify_component` | `topCover` | `lidAdhesiveThickness`; branch=`lid` |
| `Values["plate.length"]` | `Lc` | `{"visible_when":{"cover.type":"plate"}}` | mm | `modify_component` | `topCover` | `plateLengthLc`; branch=`plate` |
| `Values["plate.width"]` | `Wc` | `{"visible_when":{"cover.type":"plate"}}` | mm | `modify_component` | `topCover` | `plateWidthWc`; branch=`plate` |
| `Values["plate.thickness"]` | `tc` | `{"visible_when":{"cover.type":"plate"}}` | mm | `modify_component` | `topCover` | `plateThicknessTc`; branch=`plate` |
| `Values["plate.die_attach"]` | `tda` | `{"visible_when":{"cover.type":"plate"}}` | mm | `modify_component` | `topCover` | `dieAttachThicknessTda`; branch=`plate` |
| `Values["grid.enabled"]` | `localgrid` | — | — | `modify_component` | `modelingOptions` | `localizeGrid` |
| `Values["grid.density"]` | `radio_lgc` | `{"visible_when":{"grid.enabled":true}}` | — | `modify_component` | `modelingOptions` | `gridDensity` |
| `Values["bumps.array_type"]` | `radio_bump_type` | — | — | `modify_component` | `flipChipBumps` | `arrayType` |
| `Values["bumps.columns"]` | `MDC4` | `{"visible_when":{"bumps.array_type":"regular"}}` | — | `modify_component` | `flipChipBumps` | `numberOfBumpsInXMDC4` |
| `Values["bumps.rows"]` | `MEC4` | `{"visible_when":{"bumps.array_type":"regular"}}` | — | `modify_component` | `flipChipBumps` | `numberOfBumpsInYMEC4` |
| `Values["bumps.underfill"]` | `c4_underfill` | — | — | `modify_component` | `flipChipBumps` | `underfill` |
| `Values["cover.flush"]` | `check_thickness` | `{"visible_when":{"cover.type":"encapsulant"}}` | — | `modify_component` | `topCover` | `enableDieFlush`; branch=`encapsulant` |
| `Values["stiffener.enabled"]` | `radio_stiffener` | `{"visible_when":{"cover.type":"lid"}}` | — | `modify_component` | `topCover` | `stiffener`; branch=`lid` |
| `Values["stiffener.length"]` | `Ls` | `{"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | mm | `modify_component` | `topCover` | `stiffenerLengthLs`; branch=`lid` |
| `Values["stiffener.width"]` | `Ws` | `{"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | mm | `modify_component` | `topCover` | `stiffenerWidthWs`; branch=`lid` |
| `Values["stiffener.cavity_length"]` | `Lsc` | `{"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | mm | `modify_component` | `topCover` | `stiffenerCavityLengthLsc`; branch=`lid` |
| `Values["stiffener.cavity_width"]` | `Wsc` | `{"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | mm | `modify_component` | `topCover` | `stiffenerCavityWidthWsc`; branch=`lid` |
| `Values["stiffener.adhesive"]` | `tsadh` | `{"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | mm | `modify_component` | `topCover` | `stiffenerAdhesiveThickness`; branch=`lid` |
| `Values["slug.enabled"]` | `slug` | `{"enabled_when":{"cover.type":"encapsulant"}}` | — | `modify_component` | `dropInSlug` | `includeSlug` |
| `Values["slug.length"]` | `L_sl` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugLengthLsl` |
| `Values["slug.width"]` | `W_sl` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugWidthWsl` |
| `Values["slug.thickness"]` | `t_sl` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugThicknessTsl` |
| `Values["slug.diameter"]` | `dsl` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugDiameterDs` |
| `Values["slug.foot_length"]` | `L_slf` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugFootExtendLengthLsf` |
| `Values["slug.foot_width"]` | `W_slf` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugFootExtendWidthWsf` |
| `Values["slug.offset"]` | `gsl` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugOffsetGs` |
| `Values["slug.clearance"]` | `g_slf` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugFootClearanceGsf` |
| `Values["slug.adhesive_enabled"]` | `slug_adh` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | — | `modify_component` | `dropInSlug` | `adhesivePresentUnderSlugFoot` |

### Assignments

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Assignments["group-substrate"]` | `k_substr` | — | — | `modify_component` | `packageSubstrate` | `dielectricMaterial` |
| `Assignments["group-die"]` | — | — | — | — | — | — |
| `Assignments["group-encapsulant"]` | `k_encap` | `{"cover.type":"encapsulant"}` | — | `modify_component` | `topCover` | `encapsulantMaterial`; branch=`encapsulant` |
| `Assignments["group-lid"]` | `k_cap` | `{"cover.type":"lid"}` | — | `modify_component` | `topCover` | `lidMaterial`; branch=`lid` |
| `Assignments["group-lid-adhesive"]` | `k_cadh` | `{"cover.type":"lid"}` | — | `modify_component` | `topCover` | `lidAdhesiveMaterial`; branch=`lid` |
| `Assignments["group-lid-die-attach"]` | `kda` | `{"cover.type":"lid"}` | — | `modify_component` | `topCover` | `dieAttachMaterial`; branch=`lid` |
| `Assignments["group-plate"]` | `k_cap` | `{"cover.type":"plate"}` | — | `modify_component` | `topCover` | `plateMaterial`; branch=`plate` |
| `Assignments["group-plate-die-attach"]` | `kda` | `{"cover.type":"plate"}` | — | `modify_component` | `topCover` | `dieAttachMaterial`; branch=`plate` |
| `Assignments["group-bump-solder"]` | `k_C4` | — | — | `modify_component` | `flipChipBumps` | `c4SolderMaterial` |
| `Assignments["group-underfill"]` | `k_underfill` | `{"bumps.underfill":true}` | — | `modify_component` | `flipChipBumps` | `underfillMaterial` |
| `Assignments["group-bga-solder"]` | `k_solder` | — | — | `modify_component` | `solderBalls` | `solderMaterial` |
| `Assignments["group-stiffener"]` | `k_stiff` | `{"cover.type":"lid","stiffener.enabled":true}` | — | `modify_component` | `topCover` | `stiffenerMaterial`; branch=`lid` |
| `Assignments["group-stiffener-adhesive"]` | `k_sadh` | `{"cover.type":"lid","stiffener.enabled":true}` | — | `modify_component` | `topCover` | `stiffenerAdhesiveMaterial`; branch=`lid` |
| `Assignments["group-slug"]` | `k_sl` | `{"cover.type":"encapsulant","slug.enabled":true}` | — | `modify_component` | `dropInSlug` | `slugMaterial` |
| `Assignments["group-slug-adhesive"]` | `k_slad` | `{"cover.type":"encapsulant","slug.enabled":true,"slug.adhesive_enabled":true}` | — | `modify_component` | `dropInSlug` | `slugAdhesiveMaterial` |

### Bga

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Bga["representation"]` | `radio_BGA_modeling` | — | — | `modify_component` | `modelingOptions` | `modelSolderBallArrayAs` |
| `Bga["solder_removal_enabled"]` | `depop_center` | — | — | `modify_component` | `solderBallDepopulation` | `depopulatedCenter` |
| `Bga["populated_columns"]` | `MDp` | — | — | `modify_component` | `solderBallDepopulation` | `numberFullyPopulatedRowsMDp` |
| `Bga["populated_rows"]` | `MEp` | — | — | `modify_component` | `solderBallDepopulation` | `numberFullyPopulatedRowsMEp` |
| `Bga["center_solder_enabled"]` | `central_balls` | — | — | `modify_component` | `centralBalls` | `centralBalls` |
| `Bga["center_solder_columns"]` | `MDc` | — | — | `modify_component` | `centralBalls` | `numberCentralRowsMDp` |
| `Bga["center_solder_rows"]` | `MEc` | — | — | `modify_component` | `centralBalls` | `numberCentralRowsMEp` |
| `Bga["staggered"]` | `staggered_matrix` | — | — | `modify_component` | `solderBalls` | `staggeredMatrix` |
| `Bga["center_staggered"]` | `central_staggered_matrix` | — | — | `modify_component` | `centralBalls` | `staggeredMatrix` |
| `Bga["omitted_cells"]` | `balls` | — | — | `modify_component` | `solderBallDepopulation` | `depopulationDialog` |
| `Bga["removal_rows"]` | — | — | — | — | — | — |
| `Bga["removal_columns"]` | — | — | — | — | — | — |
| `Bga["ball_map_enabled"]` | `csvBGA` | — | — | `modify_component` | `solderBalls` | `solderBallMap` |
| `Bga["ball_map"]` | `csvBGA` | — | — | `modify_component` | `solderBalls` | `solderBallMapDialog` |
| `Bga["via_configuration"]` | — | — | — | — | — | — |

### ProjectDocument

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `ProjectDocument.TemplateId` | `package` | — | — | — | — | — |
| `ProjectDocument.Name` | `design` | — | — | — | — | — |
| `ProjectDocument.PresetId` | — | — | — | — | — | — |
| `ProjectDocument.CustomMaterials` | — | — | — | — | — | — |

## chip_array

### Values

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Values["footprint.size"]` | — | — | — | `new_package/new_value` | — | `jedecFootprint` |
| `Values["package.length"]` | `D` | — | mm | `modify_component` | `overallPackage` | `lengthD` |
| `Values["package.width"]` | `E` | — | mm | `modify_component` | `overallPackage` | `widthE` |
| `Values["substrate.thickness"]` | `A2` | — | mm | `modify_component` | `overallPackage` | `substrateThicknessA2` |
| `Values["trace.top_thickness"]` | `tza1（2 层）/ tz1（4 层）`, `tza1`, `tz1` | `substrate.layers=2-Layer`: `tza1`<br>`substrate.layers=4-Layer`: `tz1` | mm | `new_package/new_value` | — | `topSignalLayerThickness` |
| `Values["trace.bottom_thickness"]` | `tza2（2 层）/ tz4（4 层）`, `tza2`, `tz4` | `substrate.layers=2-Layer`: `tza2`<br>`substrate.layers=4-Layer`: `tz4` | mm | `new_package/new_value` | — | `bottomSignalLayerThickness` |
| `Values["die.length"]` | `Ld` | — | mm | `modify_component` | `die` | `dieLengthLd` |
| `Values["die.width"]` | `Wd` | — | mm | `modify_component` | `die` | `dieWidthWd` |
| `Values["die.thickness"]` | `td` | — | mm | `modify_component` | `die` | `dieThicknessTd` |
| `Values["die.attach"]` | `tda` | — | mm | `modify_component` | `die` | `dieAttachThicknessTda` |
| `Values["die.power"]` | `P` | — | W | `modify_component` | `die` | `packagePower` |
| `Values["encapsulant.thickness"]` | `te` | — | mm | `modify_component` | `encapsulant` | `thicknessTe` |
| `Values["solder_mask.thickness"]` | `tsm` | — | mm | `modify_component` | `encapsulant` | `solderMaskThicknessTsm` |
| `Values["bond_wire.extent_length"]` | `Lw` | — | mm | `modify_component` | `bondWires` | `extentOfBondWirePadsLw` |
| `Values["bond_wire.extent_width"]` | `Ww` | — | mm | `modify_component` | `bondWires` | `extentOfBondWirePadsWw` |
| `Values["bond_wire.diameter"]` | `dw` | — | mm | `modify_component` | `bondWires` | `bondWireDiameterDw` |
| `Values["vias.enabled"]` | — | — | — | — | — | — |
| `Values["vias.diameter"]` | `dv` | `{"visible_when":{"vias.enabled":true}}` | mm | `modify_component` | `vias` | `viaDiameterDv` |
| `Values["vias.plating"]` | `tpl` | `{"visible_when":{"vias.enabled":true,"vias.filled":false}}` | mm | `modify_component` | `vias` | `platingThicknessTpl` |
| `Values["vias.offset_x"]` | `vxoff` | `{"visible_when":{"vias.enabled":true}}` | mm | `modify_component` | `modelingOptions` | `viaOffsetInX` |
| `Values["vias.offset_y"]` | `vyoff` | `{"visible_when":{"vias.enabled":true}}` | mm | `modify_component` | `modelingOptions` | `viaOffsetInY` |
| `Values["bga.columns"]` | `MD` | — | — | `modify_component` | `solderBalls` | `numberOfSolderBallsInXMD` |
| `Values["bga.rows"]` | `ME` | — | — | `modify_component` | `solderBalls` | `numberOfSolderBallsInYME` |
| `Values["bga.pitch"]` | `e` | — | mm | `modify_component` | `solderBalls` | `ballPitchE` |
| `Values["bga.diameter"]` | `b` | — | mm | `modify_component` | `solderBalls` | `ballDiameterB` |
| `Values["bga.height"]` | `A1` | — | mm | `modify_component` | `solderBalls` | `substrateStandoffA1` |
| `Values["grid.enabled"]` | `localgrid` | — | — | `modify_component` | `modelingOptions` | `localizeGrid` |
| `Values["grid.density"]` | `radio_lgc` | `{"visible_when":{"grid.enabled":true}}` | — | `modify_component` | `modelingOptions` | `gridDensity` |
| `Values["substrate.layers"]` | `num_metal_layers` | — | — | `modify_component` | `metalLayers` | `substrateLayer`; branch=`substrateLayer / wizard` |
| `Values["bond_wire.auto_count"]` | `radio_default_bwNumber` | — | — | `modify_component` | `bondWires` | `numberBondWiresEqualsSolderBalls` |
| `Values["bond_wire.total"]` | `Nw` | `{"visible_when":{"bond_wire.auto_count":false}}` | — | `modify_component` | `bondWires` | `numberOfBondWiresNw` |
| `Values["bond_wire.include"]` | `radio_BW_modeling` | — | — | `modify_component` | `modelingOptions` | `bondWireModeling` |
| `Values["vias.filled"]` | `radio_filled_vias` | `{"visible_when":{"vias.enabled":true}}` | — | `modify_component` | `vias` | `filledVias` |
| `Values["vias.modeling"]` | `radio_Via_modeling` | `{"visible_when":{"vias.enabled":true}}` | — | `modify_component` | `modelingOptions` | `viaModeling` |
| `Values["metal.layers"]` | `substrate.layers=2-Layer`: `tza1`, `tza2`, `coveragea1`, `coveragea2`<br>`substrate.layers=4-Layer`: `tz1`, `tz2`, `tz3`, `tz4`, `coverage1`, `coverage2`, `coverage3`, `coverage4`, `z2`, `z3` | — | mm / % | `modify_component_table_row`<br>`modify_component_table_row` | `metalLayers`<br>`metalLayers` | `twoLayerMetalLayersTable`; `{"substrate.layers":"2-Layer"}`<br>`fourLayerMetalLayersTable`; `{"substrate.layers":"4-Layer"}` |
| `Values["metal.hole_length"]` | `Lml` | — | mm | `modify_component` | `metalLayers` | `lengthLml` |
| `Values["metal.hole_width"]` | `Wml` | — | mm | `modify_component` | `metalLayers` | `widthWml` |

### Assignments

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Assignments["group-substrate"]` | `k_substr` | — | — | `modify_component` | `overallPackage` | `dielectricMaterial` |
| `Assignments["group-die"]` | — | — | — | — | — | — |
| `Assignments["group-die-attach"]` | `k_da` | — | — | `modify_component` | `die` | `dieAttachMaterial` |
| `Assignments["group-encapsulant"]` | `k_encap` | — | — | `modify_component` | `encapsulant` | `encapsulantMaterial` |
| `Assignments["group-bond-wires"]` | `k_wire` | — | — | `modify_component` | `bondWires` | `bondWireMaterial` |
| `Assignments["group-solder-mask"]` | `k_mask` | — | — | `modify_component` | `encapsulant` | `solderMaskMaterial` |
| `Assignments["group-bga-solder"]` | `k_solder` | — | — | `modify_component` | `solderBalls` | `solderMaterial` |
| `Assignments["group-metal"]` | `k_metal` | — | — | `modify_component` | `metalLayers` | `materialOfMetal` |
| `Assignments["group-trace-hole"]` | `k_ml` | — | — | `modify_component` | `metalLayers` | `conductivity` |

### Bga

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Bga["representation"]` | — | — | — | — | — | — |
| `Bga["solder_removal_enabled"]` | `depop_center` | — | — | `modify_component` | `solderBallDepopulation` | `depopulatedCenter` |
| `Bga["populated_columns"]` | `MDp` | — | — | `modify_component` | `solderBallDepopulation` | `numberFullyPopulatedRowsMDp` |
| `Bga["populated_rows"]` | `MEp` | — | — | `modify_component` | `solderBallDepopulation` | `numberFullyPopulatedRowsMEp` |
| `Bga["center_solder_enabled"]` | `central_balls` | — | — | `modify_component` | `centralBalls` | `centralBalls` |
| `Bga["center_solder_columns"]` | `MDc` | — | — | `modify_component` | `centralBalls` | `numberCentralRowsMDp` |
| `Bga["center_solder_rows"]` | `MEc` | — | — | `modify_component` | `centralBalls` | `numberCentralRowsMEp` |
| `Bga["staggered"]` | `staggered_matrix` | — | — | `modify_component` | `solderBalls` | `staggeredMatrix` |
| `Bga["center_staggered"]` | `central_staggered_matrix` | — | — | `modify_component` | `centralBalls` | `staggeredMatrix` |
| `Bga["omitted_cells"]` | `balls` | — | — | `modify_component` | `solderBallDepopulation` | `depopulationDialog` |
| `Bga["removal_rows"]` | — | — | — | — | — | — |
| `Bga["removal_columns"]` | — | — | — | — | — | — |
| `Bga["ball_map_enabled"]` | `csvBGA` | — | — | `modify_component` | `solderBalls` | `solderBallMap` |
| `Bga["ball_map"]` | `csvBGA` | — | — | `modify_component` | `solderBalls` | `solderBallMapDialog` |
| `Bga["via_configuration"]` | — | — | — | — | — | — |

### ProjectDocument

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `ProjectDocument.TemplateId` | `package` | — | — | — | — | — |
| `ProjectDocument.Name` | `design` | — | — | — | — | — |
| `ProjectDocument.PresetId` | — | — | — | — | — | — |
| `ProjectDocument.CustomMaterials` | — | — | — | — | — | — |

## pbga_fc

### Values

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Values["footprint.size"]` | — | — | — | `new_package/new_value` | — | `jedecFootprint` |
| `Values["substrate.length"]` | `D` | — | mm | `modify_component` | `packageSubstrate` | `substrateLengthD` |
| `Values["substrate.width"]` | `E` | — | mm | `modify_component` | `packageSubstrate` | `substrateWidthE` |
| `Values["substrate.thickness"]` | `A2` | — | mm | `modify_component` | `packageSubstrate` | `substrateThicknessA2` |
| `Values["die.length"]` | `Ld` | — | mm | `modify_component` | `die` | `dieLengthLd` |
| `Values["die.width"]` | `Wd` | — | mm | `modify_component` | `die` | `dieWidthWd` |
| `Values["die.thickness"]` | `td` | — | mm | `modify_component` | `die` | `dieThicknessTd` |
| `Values["die.power"]` | `P` | — | W | `modify_component` | `die` | `packagePower` |
| `Values["bumps.total"]` | `MNC4` | `{"visible_when":{"bumps.array_type":"non_regular"}}` | — | `modify_component` | `flipChipBumps` | `totalNumberOfBumpsMNC4` |
| `Values["bumps.diameter"]` | `bC4` | — | mm | `modify_component` | `flipChipBumps` | `bumpDiameterBC4` |
| `Values["bumps.height"]` | `tC4` | — | mm | `modify_component` | `flipChipBumps` | `bumpHeightTC4` |
| `Values["bumps.modeling"]` | — | — | — | `modify_component` | `modelingOptions` | `modelFlipChipBumpsAs` |
| `Values["bga.columns"]` | `MD` | — | — | `modify_component` | `solderBalls` | `numberOfSolderBallsInXMD` |
| `Values["bga.rows"]` | `ME` | — | — | `modify_component` | `solderBalls` | `numberOfSolderBallsInYME` |
| `Values["bga.pitch"]` | `e` | — | mm | `modify_component` | `solderBalls` | `ballPitchE` |
| `Values["bga.diameter"]` | `b` | — | mm | `modify_component` | `solderBalls` | `ballDiameterB` |
| `Values["bga.height"]` | `A1` | — | mm | `modify_component` | `solderBalls` | `substrateStandoffA1` |
| `Values["cover.type"]` | `radio_EnCaPl` | — | — | `new_package/new_value` | — | `topCover` |
| `Values["cover.length"]` | `Le` | `{"visible_when":{"cover.type":"encapsulant"}}` | mm | `modify_component` | `topCover` | `lengthLe`; branch=`encapsulant` |
| `Values["cover.width"]` | `We` | `{"visible_when":{"cover.type":"encapsulant"}}` | mm | `modify_component` | `topCover` | `widthWe`; branch=`encapsulant` |
| `Values["cover.thickness"]` | `te` | `{"visible_when":{"cover.type":"encapsulant"}}` | mm | `modify_component` | `topCover` | `thicknessTe`; branch=`encapsulant` |
| `Values["lid.length"]` | `Lc` | `{"visible_when":{"cover.type":"lid"}}` | mm | `modify_component` | `topCover` | `lidLengthLc`; branch=`lid` |
| `Values["lid.width"]` | `Wc` | `{"visible_when":{"cover.type":"lid"}}` | mm | `modify_component` | `topCover` | `lidWidthWc`; branch=`lid` |
| `Values["lid.thickness"]` | `tc` | `{"visible_when":{"cover.type":"lid"}}` | mm | `modify_component` | `topCover` | `lidThicknessTc`; branch=`lid` |
| `Values["lid.base_thickness"]` | `tcb` | `{"visible_when":{"cover.type":"lid"}}` | mm | `modify_component` | `topCover` | `lidBaseThicknessTcb`; branch=`lid` |
| `Values["lid.die_attach"]` | `tda` | `{"visible_when":{"cover.type":"lid"}}` | mm | `modify_component` | `topCover` | `dieAttachThicknessTda`; branch=`lid` |
| `Values["lid.adhesive"]` | `tcadh` | `{"visible_when":{"cover.type":"lid"}}` | mm | `modify_component` | `topCover` | `lidAdhesiveThickness`; branch=`lid` |
| `Values["plate.length"]` | `Lc` | `{"visible_when":{"cover.type":"plate"}}` | mm | `modify_component` | `topCover` | `plateLengthLc`; branch=`plate` |
| `Values["plate.width"]` | `Wc` | `{"visible_when":{"cover.type":"plate"}}` | mm | `modify_component` | `topCover` | `plateWidthWc`; branch=`plate` |
| `Values["plate.thickness"]` | `tc` | `{"visible_when":{"cover.type":"plate"}}` | mm | `modify_component` | `topCover` | `plateThicknessTc`; branch=`plate` |
| `Values["plate.die_attach"]` | `tda` | `{"visible_when":{"cover.type":"plate"}}` | mm | `modify_component` | `topCover` | `dieAttachThicknessTda`; branch=`plate` |
| `Values["grid.enabled"]` | `localgrid` | — | — | `modify_component` | `modelingOptions` | `localizeGrid` |
| `Values["grid.density"]` | `radio_lgc` | `{"visible_when":{"grid.enabled":true}}` | — | `modify_component` | `modelingOptions` | `gridDensity` |
| `Values["bumps.array_type"]` | `radio_bump_type` | — | — | `modify_component` | `flipChipBumps` | `arrayType` |
| `Values["bumps.columns"]` | `MDC4` | `{"visible_when":{"bumps.array_type":"regular"}}` | — | `modify_component` | `flipChipBumps` | `numberOfBumpsInXMDC4` |
| `Values["bumps.rows"]` | `MEC4` | `{"visible_when":{"bumps.array_type":"regular"}}` | — | `modify_component` | `flipChipBumps` | `numberOfBumpsInYMEC4` |
| `Values["bumps.underfill"]` | `c4_underfill` | — | — | `modify_component` | `flipChipBumps` | `underfill` |
| `Values["cover.flush"]` | `check_thickness` | `{"visible_when":{"cover.type":"encapsulant"}}` | — | `modify_component` | `topCover` | `enableDieFlush`; branch=`encapsulant` |
| `Values["stiffener.enabled"]` | `radio_stiffener` | `{"visible_when":{"cover.type":"lid"}}` | — | `modify_component` | `topCover` | `stiffener`; branch=`lid` |
| `Values["stiffener.length"]` | `Ls` | `{"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | mm | `modify_component` | `topCover` | `stiffenerLengthLs`; branch=`lid` |
| `Values["stiffener.width"]` | `Ws` | `{"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | mm | `modify_component` | `topCover` | `stiffenerWidthWs`; branch=`lid` |
| `Values["stiffener.cavity_length"]` | `Lsc` | `{"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | mm | `modify_component` | `topCover` | `stiffenerCavityLengthLsc`; branch=`lid` |
| `Values["stiffener.cavity_width"]` | `Wsc` | `{"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | mm | `modify_component` | `topCover` | `stiffenerCavityWidthWsc`; branch=`lid` |
| `Values["stiffener.adhesive"]` | `tsadh` | `{"visible_when":{"cover.type":"lid","stiffener.enabled":true}}` | mm | `modify_component` | `topCover` | `stiffenerAdhesiveThickness`; branch=`lid` |
| `Values["slug.enabled"]` | `slug` | `{"enabled_when":{"cover.type":"encapsulant"}}` | — | `modify_component` | `dropInSlug` | `includeSlug` |
| `Values["slug.length"]` | `L_sl` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugLengthLsl` |
| `Values["slug.width"]` | `W_sl` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugWidthWsl` |
| `Values["slug.thickness"]` | `t_sl` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugThicknessTsl` |
| `Values["slug.diameter"]` | `dsl` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugDiameterDs` |
| `Values["slug.foot_length"]` | `L_slf` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugFootExtendLengthLsf` |
| `Values["slug.foot_width"]` | `W_slf` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugFootExtendWidthWsf` |
| `Values["slug.offset"]` | `gsl` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugOffsetGs` |
| `Values["slug.clearance"]` | `g_slf` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugFootClearanceGsf` |
| `Values["slug.adhesive_enabled"]` | `slug_adh` | `{"visible_when":{"cover.type":"encapsulant","slug.enabled":true}}` | — | `modify_component` | `dropInSlug` | `adhesivePresentUnderSlugFoot` |
| `Values["vias.enabled"]` | — | — | — | — | — | — |
| `Values["vias.columns"]` | `NVx` | `{"visible_when":{"vias.enabled":true}}` | — | `modify_component` | `coreVias` | `numberOfThermalViasInXNVx` |
| `Values["vias.rows"]` | `NVy` | `{"visible_when":{"vias.enabled":true}}` | — | `modify_component` | `coreVias` | `numberOfThermalViasInYNVy` |
| `Values["vias.pitch"]` | `ev` | `{"visible_when":{"vias.enabled":true}}` | mm | `modify_component` | `coreVias` | `viaPitchEv` |
| `Values["vias.diameter"]` | `dv` | `{"visible_when":{"vias.enabled":true}}` | mm | `modify_component` | `coreVias` | `viaDiameterDv` |
| `Values["vias.plating"]` | `tpl` | `{"visible_when":{"vias.enabled":true}}` | mm | `modify_component` | `coreVias` | `platingThicknessTpl` |
| `Values["vias.modeling"]` | `radio_Via_modeling` | `{"visible_when":{"vias.enabled":true}}` | — | `modify_component` | `modelingOptions` | `modelCoreViasAs` |
| `Values["metal.layers"]` | `z{i}`, `tz{i}`, `coverage{i}` | — | mm / % | `modify_component_table_row` | `metalLayers` | `metalLayersTable` |
| `Values["upper.enabled"]` | — | — | — | — | — | — |
| `Values["upper.thickness"]` | `A2b1` | `{"visible_when":{"upper.enabled":true}}` | mm | `modify_component` | `upperBuiltUpRegion` | `thicknessA2b1` |
| `Values["upper.count"]` | `Nb1` | `{"visible_when":{"upper.enabled":true}}` | — | `modify_component` | `upperBuiltUpRegion` | `totalNumberOfMicroViasNb1` |
| `Values["upper.diameter"]` | `dv_b1` | `{"visible_when":{"upper.enabled":true}}` | mm | `modify_component` | `upperBuiltUpRegion` | `viaDiameterDvb1` |
| `Values["upper.plating"]` | `tpl_b1` | `{"visible_when":{"upper.enabled":true}}` | mm | `modify_component` | `upperBuiltUpRegion` | `platingThicknessTpl` |
| `Values["upper.filled"]` | `radio_up_filled_vias` | `{"visible_when":{"upper.enabled":true}}` | — | `modify_component` | `upperBuiltUpRegion` | `filledVias` |
| `Values["upper.layers"]` | `zb1_{i}`, `tzb1_{i}`, `coverb1_{i}` | `{"visible_when":{"upper.enabled":true}}` | mm / % | `modify_component_table_row` | `upperBuiltUpRegion` | `metalLayersTable` |
| `Values["lower.enabled"]` | — | — | — | — | — | — |
| `Values["lower.thickness"]` | `A2b2` | `{"visible_when":{"lower.enabled":true}}` | mm | `modify_component` | `lowerBuiltUpRegion` | `thicknessA2b2` |
| `Values["lower.count"]` | `Nb2` | `{"visible_when":{"lower.enabled":true}}` | — | `modify_component` | `lowerBuiltUpRegion` | `totalNumberOfMicroViasNb2` |
| `Values["lower.diameter"]` | `dv_b2` | `{"visible_when":{"lower.enabled":true}}` | mm | `modify_component` | `lowerBuiltUpRegion` | `viaDiameterDvb2` |
| `Values["lower.plating"]` | `tpl_b2` | `{"visible_when":{"lower.enabled":true}}` | mm | `modify_component` | `lowerBuiltUpRegion` | `platingThicknessTpl` |
| `Values["lower.filled"]` | `radio_low_filled_vias` | `{"visible_when":{"lower.enabled":true}}` | — | `modify_component` | `lowerBuiltUpRegion` | `filledVias` |
| `Values["lower.layers"]` | `zb2_{i}`, `tzb2_{i}`, `coverb2_{i}` | `{"visible_when":{"lower.enabled":true}}` | mm / % | `modify_component_table_row` | `lowerBuiltUpRegion` | `metalLayersTable` |

### Assignments

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Assignments["group-substrate"]` | `k_substr` | — | — | `modify_component` | `packageSubstrate` | `dielectricMaterial` |
| `Assignments["group-die"]` | — | — | — | — | — | — |
| `Assignments["group-encapsulant"]` | `k_encap` | `{"cover.type":"encapsulant"}` | — | `modify_component` | `topCover` | `encapsulantMaterial`; branch=`encapsulant` |
| `Assignments["group-lid"]` | `k_cap` | `{"cover.type":"lid"}` | — | `modify_component` | `topCover` | `lidMaterial`; branch=`lid` |
| `Assignments["group-lid-adhesive"]` | `k_cadh` | `{"cover.type":"lid"}` | — | `modify_component` | `topCover` | `lidAdhesiveMaterial`; branch=`lid` |
| `Assignments["group-lid-die-attach"]` | `kda` | `{"cover.type":"lid"}` | — | `modify_component` | `topCover` | `dieAttachMaterial`; branch=`lid` |
| `Assignments["group-plate"]` | `k_cap` | `{"cover.type":"plate"}` | — | `modify_component` | `topCover` | `plateMaterial`; branch=`plate` |
| `Assignments["group-plate-die-attach"]` | `kda` | `{"cover.type":"plate"}` | — | `modify_component` | `topCover` | `dieAttachMaterial`; branch=`plate` |
| `Assignments["group-bump-solder"]` | `k_C4` | — | — | `modify_component` | `flipChipBumps` | `c4SolderMaterial` |
| `Assignments["group-underfill"]` | `k_underfill` | `{"bumps.underfill":true}` | — | `modify_component` | `flipChipBumps` | `underfillMaterial` |
| `Assignments["group-bga-solder"]` | `k_solder` | — | — | `modify_component` | `solderBalls` | `solderMaterial` |
| `Assignments["group-stiffener"]` | `k_stiff` | `{"cover.type":"lid","stiffener.enabled":true}` | — | `modify_component` | `topCover` | `stiffenerMaterial`; branch=`lid` |
| `Assignments["group-stiffener-adhesive"]` | `k_sadh` | `{"cover.type":"lid","stiffener.enabled":true}` | — | `modify_component` | `topCover` | `stiffenerAdhesiveMaterial`; branch=`lid` |
| `Assignments["group-slug"]` | `k_sl` | `{"cover.type":"encapsulant","slug.enabled":true}` | — | `modify_component` | `dropInSlug` | `slugMaterial` |
| `Assignments["group-slug-adhesive"]` | `k_slad` | `{"cover.type":"encapsulant","slug.enabled":true,"slug.adhesive_enabled":true}` | — | `modify_component` | `dropInSlug` | `slugAdhesiveMaterial` |
| `Assignments["group-metal"]` | `k_metal` | — | — | `modify_component` | `metalLayers` | `materialOfMetal` |
| `Assignments["group-upper"]` | `kb1` | `{"upper.enabled":true}` | — | `modify_component` | `upperBuiltUpRegion` | `dielectricMaterial` |
| `Assignments["group-lower"]` | `kb2` | `{"lower.enabled":true}` | — | `modify_component` | `lowerBuiltUpRegion` | `dielectricMaterial` |

### Bga

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Bga["representation"]` | `radio_BGA_modeling` | — | — | `modify_component` | `modelingOptions` | `modelSolderBallArrayAs` |
| `Bga["solder_removal_enabled"]` | `depop_center` | — | — | `modify_component` | `solderBallDepopulation` | `depopulatedCenter` |
| `Bga["populated_columns"]` | `MDp` | — | — | `modify_component` | `solderBallDepopulation` | `numberFullyPopulatedRowsMDp` |
| `Bga["populated_rows"]` | `MEp` | — | — | `modify_component` | `solderBallDepopulation` | `numberFullyPopulatedRowsMEp` |
| `Bga["center_solder_enabled"]` | `central_balls` | — | — | `modify_component` | `centralBalls` | `centralBalls` |
| `Bga["center_solder_columns"]` | `MDc` | — | — | `modify_component` | `centralBalls` | `numberCentralRowsMDp` |
| `Bga["center_solder_rows"]` | `MEc` | — | — | `modify_component` | `centralBalls` | `numberCentralRowsMEp` |
| `Bga["staggered"]` | `staggered_matrix` | — | — | `modify_component` | `solderBalls` | `staggeredMatrix` |
| `Bga["center_staggered"]` | `central_staggered_matrix` | — | — | `modify_component` | `centralBalls` | `staggeredMatrix` |
| `Bga["omitted_cells"]` | `balls` | — | — | `modify_component` | `solderBallDepopulation` | `depopulationDialog` |
| `Bga["removal_rows"]` | — | — | — | — | — | — |
| `Bga["removal_columns"]` | — | — | — | — | — | — |
| `Bga["ball_map_enabled"]` | `csvBGA` | — | — | `modify_component` | `solderBalls` | `solderBallMap` |
| `Bga["ball_map"]` | `csvBGA` | — | — | `modify_component` | `solderBalls` | `solderBallMapDialog` |
| `Bga["via_configuration"]` | — | — | — | — | — | — |

### ProjectDocument

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `ProjectDocument.TemplateId` | `package` | — | — | — | — | — |
| `ProjectDocument.Name` | `design` | — | — | — | — | — |
| `ProjectDocument.PresetId` | — | — | — | — | — | — |
| `ProjectDocument.CustomMaterials` | — | — | — | — | — | — |

## pbga_wb

### Values

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Values["footprint.size"]` | — | — | — | `new_package/new_value` | — | `jedecFootprint` |
| `Values["package.length"]` | `D` | — | mm | `modify_component` | `packageSubstrate` | `substrateLengthD` |
| `Values["package.width"]` | `E` | — | mm | `modify_component` | `packageSubstrate` | `substrateWidthE` |
| `Values["substrate.thickness"]` | `A2` | — | mm | `modify_component` | `packageSubstrate` | `substrateThicknessA2` |
| `Values["trace.top_thickness"]` | `tz1` | — | mm | `new_package/new_value` | — | `topSignalLayerThickness` |
| `Values["trace.bottom_thickness"]` | `tz6` | — | mm | `new_package/new_value` | — | `bottomSignalLayerThickness` |
| `Values["encapsulant.length"]` | `Le` | — | mm | `modify_component` | `encapsulant` | `lengthLe` |
| `Values["encapsulant.width"]` | `We` | — | mm | `modify_component` | `encapsulant` | `widthWe` |
| `Values["encapsulant.thickness"]` | `te` | — | mm | `modify_component` | `encapsulant` | `thicknessTe` |
| `Values["flag.length"]` | `Lf` | — | mm | `modify_component` | `dieFlagAndSolderMask` | `dieFlagLf` |
| `Values["flag.width"]` | `Wf` | — | mm | `modify_component` | `dieFlagAndSolderMask` | `dieFlagWf` |
| `Values["solder_mask.thickness"]` | `tsm` | — | mm | `modify_component` | `dieFlagAndSolderMask` | `solderMaskThickness` |
| `Values["die.length"]` | `Ld` | — | mm | `modify_component` | `die` | `dieLengthLd` |
| `Values["die.width"]` | `Wd` | — | mm | `modify_component` | `die` | `dieWidthWd` |
| `Values["die.thickness"]` | `td` | — | mm | `modify_component` | `die` | `dieThicknessTd` |
| `Values["die.attach"]` | `tda` | — | mm | `modify_component` | `die` | `dieAttachThicknessTda` |
| `Values["die.power"]` | `P` | — | W | `modify_component` | `die` | `packagePower` |
| `Values["bond_wire.total"]` | `Nw` | — | — | `modify_component` | `die` | `numberOfBondWiresNw` |
| `Values["bond_wire.extent_length"]` | `Lw` | — | mm | `modify_component` | `die` | `bondWireExtentLengthLw` |
| `Values["bond_wire.extent_width"]` | `Ww` | — | mm | `modify_component` | `die` | `bondWireExtentWidthWw` |
| `Values["bond_wire.diameter"]` | `dw` | — | mm | `modify_component` | `die` | `bondWireDiameterDw` |
| `Values["vias.enabled"]` | — | — | — | — | — | — |
| `Values["vias.columns"]` | `NVx` | `{"visible_when":{"vias.enabled":true}}` | — | `modify_component` | `thermalVias` | `numberOfThermalViasInXNVx` |
| `Values["vias.rows"]` | `NVy` | `{"visible_when":{"vias.enabled":true}}` | — | `modify_component` | `thermalVias` | `numberOfThermalViasInYNVy` |
| `Values["vias.pitch"]` | `ev` | `{"visible_when":{"vias.enabled":true}}` | mm | `modify_component` | `thermalVias` | `viaPitchEv` |
| `Values["vias.diameter"]` | `dv` | `{"visible_when":{"vias.enabled":true}}` | mm | `modify_component` | `thermalVias` | `viaDiameterDv` |
| `Values["vias.plating"]` | `tpl` | `{"visible_when":{"vias.enabled":true}}` | mm | `modify_component` | `thermalVias` | `platingThicknessTpl` |
| `Values["bga.columns"]` | `MD` | — | — | `modify_component` | `solderBalls` | `numberOfSolderBallsInXMD` |
| `Values["bga.rows"]` | `ME` | — | — | `modify_component` | `solderBalls` | `numberOfSolderBallsInYME` |
| `Values["bga.pitch"]` | `e` | — | mm | `modify_component` | `solderBalls` | `ballPitchE` |
| `Values["bga.diameter"]` | `b` | — | mm | `modify_component` | `solderBalls` | `ballDiameterB` |
| `Values["bga.height"]` | `A1` | — | mm | `modify_component` | `solderBalls` | `substrateStandoffA1` |
| `Values["spreader.enabled"]` | `backside_spreader` | — | — | `modify_component` | `backsideSpreader` | `includeBacksideSpreader` |
| `Values["spreader.length"]` | `L_spr` | `{"visible_when":{"spreader.enabled":true}}` | mm | `modify_component` | `backsideSpreader` | `spreaderLengthLspr` |
| `Values["spreader.width"]` | `W_spr` | `{"visible_when":{"spreader.enabled":true}}` | mm | `modify_component` | `backsideSpreader` | `spreaderWidthWspr` |
| `Values["spreader.thickness"]` | `t_spr` | `{"visible_when":{"spreader.enabled":true}}` | mm | `modify_component` | `backsideSpreader` | `spreaderThicknessTspr` |
| `Values["spreader.hole_length"]` | `Lbt` | `{"visible_when":{"spreader.enabled":true}}` | mm | `modify_component` | `backsideSpreader` | `bottomTraceHoleLengthLbt` |
| `Values["spreader.hole_width"]` | `Wbt` | `{"visible_when":{"spreader.enabled":true}}` | mm | `modify_component` | `backsideSpreader` | `bottomTraceHoleWidthWbt` |
| `Values["grid.enabled"]` | `localgrid` | — | — | `modify_component` | `modelingOptions` | `localizeGrid` |
| `Values["grid.density"]` | `radio_lgc` | `{"visible_when":{"grid.enabled":true}}` | — | `modify_component` | `modelingOptions` | `gridDensity` |
| `Values["bond_wire.modeling"]` | `radio_Bond_Wires_modeling` | — | — | `modify_component` | `modelingOptions` | `modelBondWiresAs` |
| `Values["substrate.layers"]` | — | — | — | `new_package/new_value` | — | `substrateLayer` |
| `Values["flag.coverage"]` | `cf` | — | % | `modify_component` | `dieFlagAndSolderMask` | `coveragePercentageCf` |
| `Values["metal.layers"]` | `tz1`, `tz2`, `tz3`, `tz6`, `coverage1`, `coverage2`, `coverage3`, `coverage6`, `z2`, `z3`, `via_con1`, `via_con2`, `via_con3`, `via_con6` | — | mm / % | `modify_component_table_row` | `metalLayers` | `metalLayersTable` |
| `Values["vias.modeling"]` | `radio_Via_modeling` | `{"visible_when":{"vias.enabled":true}}` | — | `modify_component` | `modelingOptions` | `modelThermalViasAs` |
| `Values["slug.enabled"]` | `slug` | — | — | `modify_component` | `dropInSlug` | `includeSlug` |
| `Values["slug.length"]` | `L_sl` | `{"visible_when":{"slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugLengthLsl` |
| `Values["slug.width"]` | `W_sl` | `{"visible_when":{"slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugWidthWsl` |
| `Values["slug.thickness"]` | `t_sl` | `{"visible_when":{"slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugThicknessTsl` |
| `Values["slug.diameter"]` | `dsl` | `{"visible_when":{"slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugDiameterDs` |
| `Values["slug.foot_length"]` | `L_slf` | `{"visible_when":{"slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugFootExtendLengthLsf` |
| `Values["slug.foot_width"]` | `W_slf` | `{"visible_when":{"slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugFootExtendWidthWsf` |
| `Values["slug.offset"]` | `gsl` | `{"visible_when":{"slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugOffsetGs` |
| `Values["slug.clearance"]` | `g_slf` | `{"visible_when":{"slug.enabled":true}}` | mm | `modify_component` | `dropInSlug` | `slugFootClearanceGsf` |
| `Values["slug.adhesive_enabled"]` | `slug_adh` | `{"visible_when":{"slug.enabled":true}}` | — | `modify_component` | `dropInSlug` | `adhesivePresentUnderSlugFoot` |

### Assignments

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Assignments["group-substrate"]` | `k_substr` | — | — | `modify_component` | `packageSubstrate` | `dielectricMaterial` |
| `Assignments["group-die"]` | — | — | — | — | — | — |
| `Assignments["group-die-attach"]` | `k_da` | — | — | `modify_component` | `die` | `dieAttachMaterial` |
| `Assignments["group-encapsulant"]` | `k_encap` | — | — | `modify_component` | `encapsulant` | `encapsulantMaterial` |
| `Assignments["group-bond-wires"]` | `k_wire` | — | — | `modify_component` | `die` | `bondWireMaterial` |
| `Assignments["group-solder-mask"]` | `ksm` | — | — | `modify_component` | `dieFlagAndSolderMask` | `solderMaskMaterial` |
| `Assignments["group-bga-solder"]` | `k_solder` | — | — | `modify_component` | `solderBalls` | `solderMaterial` |
| `Assignments["group-backside-spreader"]` | `k_spr` | `{"spreader.enabled":true}` | — | `modify_component` | `backsideSpreader` | `spreaderMaterial` |
| `Assignments["group-traces"]` | `k_metal` | — | — | `modify_component` | `metalLayers` | `materialOfMetal` |
| `Assignments["group-slug"]` | `k_sl` | `{"slug.enabled":true}` | — | `modify_component` | `dropInSlug` | `slugMaterial` |
| `Assignments["group-slug-adhesive"]` | `k_slad` | `{"slug.enabled":true,"slug.adhesive_enabled":true}` | — | `modify_component` | `dropInSlug` | `slugAdhesiveMaterial` |

### Bga

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Bga["representation"]` | `radio_BGA_modeling` | — | — | `modify_component` | `modelingOptions` | `modelSolderBallArrayAs` |
| `Bga["solder_removal_enabled"]` | `depop_center` | — | — | `modify_component` | `solderBallDepopulation` | `depopulatedCenter` |
| `Bga["populated_columns"]` | `MDp` | — | — | `modify_component` | `solderBallDepopulation` | `numberFullyPopulatedRowsMDp` |
| `Bga["populated_rows"]` | `MEp` | — | — | `modify_component` | `solderBallDepopulation` | `numberFullyPopulatedRowsMEp` |
| `Bga["center_solder_enabled"]` | `central_balls` | — | — | `modify_component` | `centralBalls` | `centralBalls` |
| `Bga["center_solder_columns"]` | `MDc` | — | — | `modify_component` | `centralBalls` | `numberCentralRowsMDp` |
| `Bga["center_solder_rows"]` | `MEc` | — | — | `modify_component` | `centralBalls` | `numberCentralRowsMEp` |
| `Bga["staggered"]` | `staggered_matrix` | — | — | `modify_component` | `solderBalls` | `staggeredMatrix` |
| `Bga["center_staggered"]` | `central_staggered_matrix` | — | — | `modify_component` | `centralBalls` | `staggeredMatrix` |
| `Bga["omitted_cells"]` | `balls` | — | — | `modify_component` | `solderBallDepopulation` | `depopulationDialog` |
| `Bga["removal_rows"]` | — | — | — | — | — | — |
| `Bga["removal_columns"]` | — | — | — | — | — | — |
| `Bga["ball_map_enabled"]` | `csvBGA` | — | — | `modify_component` | `solderBalls` | `solderBallMap` |
| `Bga["ball_map"]` | `csvBGA` | — | — | `modify_component` | `solderBalls` | `solderBallMapDialog` |
| `Bga["via_configuration"]` | — | — | — | — | — | — |

### ProjectDocument

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `ProjectDocument.TemplateId` | `package` | — | — | — | — | — |
| `ProjectDocument.Name` | `design` | — | — | — | — | — |
| `ProjectDocument.PresetId` | — | — | — | — | — | — |
| `ProjectDocument.CustomMaterials` | — | — | — | — | — | — |

## pqfp

### Values

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Values["package.type"]` | — | — | — | `new_package/new_value` | — | `pqfpPackageType` |
| `Values["footprint.size"]` | — | — | — | `new_package/new_value` | — | `tqfpJedecFootprint`; branch=`lqfpJedecFootprint / wizard` |
| `Values["package.length"]` | `D` | — | mm | `modify_component` | `overallPackage` | `lengthD` |
| `Values["package.width"]` | `E` | — | mm | `modify_component` | `overallPackage` | `widthE` |
| `Values["package.standoff"]` | `A1` | — | mm | `modify_component` | `overallPackage` | `standoffA1` |
| `Values["body.length"]` | `D1` | — | mm | `modify_component` | `encapsulant` | `lengthD1` |
| `Values["body.width"]` | `E1` | — | mm | `modify_component` | `encapsulant` | `widthE1` |
| `Values["body.thickness"]` | `A2` | — | mm | `modify_component` | `encapsulant` | `thicknessA2` |
| `Values["die.length"]` | `Ld` | — | mm | `modify_component` | `die` | `dieLengthLd` |
| `Values["die.width"]` | `Wd` | — | mm | `modify_component` | `die` | `dieWidthWd` |
| `Values["die.thickness"]` | `td` | — | mm | `modify_component` | `die` | `dieThicknessTd` |
| `Values["die.attach"]` | `tda` | — | mm | `modify_component` | `die` | `dieAttachThicknessTda` |
| `Values["die.power"]` | `P` | — | W | `modify_component` | `die` | `packagePower` |
| `Values["flag.length"]` | `Lf` | — | mm | `modify_component` | `dieFlagAndTieBars` | `dieFlagLf` |
| `Values["flag.width"]` | `Wf` | — | mm | `modify_component` | `dieFlagAndTieBars` | `dieFlagWf` |
| `Values["flag.coverage"]` | `cf` | — | % | `modify_component` | `dieFlagAndTieBars` | `metalCoverageForDieFlagCf` |
| `Values["flag.downset"]` | `ddf` | — | mm | `modify_component` | `dieFlagAndTieBars` | `dieFlagDownsetDdf` |
| `Values["tie_bar.width"]` | `wtb` | — | mm | `modify_component` | `dieFlagAndTieBars` | `tieBarWidthWtb` |
| `Values["leads.count_x"]` | `MD` | — | — | `modify_component` | `leadFrame` | `numberOfLeadsOnTopBottomMD` |
| `Values["leads.count_y"]` | `ME` | — | — | `modify_component` | `leadFrame` | `numberOfLeadsOnLeftRightME` |
| `Values["leads.pitch"]` | `e` | — | mm | `modify_component` | `leadFrame` | `pitchE` |
| `Values["leads.width"]` | `b` | — | mm | `modify_component` | `leadFrame` | `leadWidthB` |
| `Values["leads.thickness"]` | `tl` | — | mm | `modify_component` | `leadFrame` | `leadThicknessTl` |
| `Values["leads.height"]` | `hl` | — | mm | `modify_component` | `leadFrame` | `leadframeHeightHl` |
| `Values["leads.foot_length"]` | `wl` | — | mm | `modify_component` | `leadFrame` | `leadfootLengthWl` |
| `Values["leads.gap_x"]` | `g1` | — | mm | `modify_component` | `leadFrame` | `leadframeFlagGapG1` |
| `Values["leads.gap_y"]` | `g2` | — | mm | `modify_component` | `leadFrame` | `leadframeFlagGapG2` |
| `Values["bond_wire.length_x"]` | `lbwx` | — | mm | `modify_component` | `bondWires` | `bondWireLengthOnLeftRightLbwx` |
| `Values["bond_wire.length_y"]` | `lbwy` | — | mm | `modify_component` | `bondWires` | `bondWireLengthOnTopBottomLbwy` |
| `Values["bond_wire.count"]` | `N` | — | — | `modify_component` | `bondWires` | `numberOfBondWiresN` |
| `Values["bond_wire.diameter"]` | `dbw` | — | mm | `modify_component` | `bondWires` | `bondWireDiameterDbw` |
| `Values["thermal_land.enabled"]` | `landsolder` | — | — | `modify_component` | `thermalLandAndSolder` | `includeThermalLandAndSolder` |
| `Values["thermal_land.thickness"]` | `ts` | `{"visible_when":{"thermal_land.enabled":true}}` | mm | `modify_component` | `thermalLandAndSolder` | `landThickness` |
| `Values["grid.enabled"]` | `localgrid` | — | — | `modify_component` | `modelingOptions` | `localizeGrid` |
| `Values["grid.density"]` | `radio_lgc` | `{"visible_when":{"grid.enabled":true}}` | — | `modify_component` | `modelingOptions` | `gridDensity` |
| `Values["bond_wire.modeling"]` | `radio_BondWire_modeling` | — | — | `modify_component` | `modelingOptions` | `modelBondWiresAs` |
| `Values["package.exposed_pad"]` | — | — | — | `new_package/new_value` | — | `exposedPad` |
| `Values["leads.custom_coverage"]` | `radio_defined_coverage` | — | — | `modify_component` | `leadFrame` | `userDefinedLeadframeCoverage` |
| `Values["leads.coverage"]` | `cl` | `{"visible_when":{"leads.custom_coverage":true}}` | % | `modify_component` | `leadFrame` | `leadframeCoveragePercentage` |
| `Values["leads.modeling"]` | `radio_LeadFram_modeling` | — | — | `modify_component` | `modelingOptions` | `modelLeadFrameAs` |

### Assignments

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Assignments["group-encapsulant"]` | `k_encap` | — | — | `modify_component` | `encapsulant` | `encapsulantMaterial` |
| `Assignments["group-die"]` | — | — | — | — | — | — |
| `Assignments["group-die-attach"]` | `k_da` | — | — | `modify_component` | `die` | `dieAttachMaterial` |
| `Assignments["group-lead-frame"]` | `k_metal` | — | — | `modify_component` | `leadFrame` | `leadframeMaterial` |
| `Assignments["group-bond-wires"]` | `k_bw` | — | — | `modify_component` | `bondWires` | `material` |
| `Assignments["group-thermal-land"]` | `k_land` | `{"thermal_land.enabled":true}` | — | `modify_component` | `thermalLandAndSolder` | `landMaterial` |
| `Assignments["group-thermal-solder"]` | `k_sd` | `{"thermal_land.enabled":true}` | — | `modify_component` | `thermalLandAndSolder` | `solderMaterial` |

### ProjectDocument

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `ProjectDocument.TemplateId` | `package` | — | — | — | — | — |
| `ProjectDocument.Name` | `design` | — | — | — | — | — |
| `ProjectDocument.PresetId` | — | — | — | — | — | — |
| `ProjectDocument.CustomMaterials` | — | — | — | — | — | — |

## qfn

### Values

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Values["footprint.size"]` | — | — | — | `new_package/new_value` | — | `jedecFootprint` |
| `Values["package.length"]` | `D` | — | mm | `modify_component` | `overallPackage` | `lengthD` |
| `Values["package.width"]` | `E` | — | mm | `modify_component` | `overallPackage` | `widthE` |
| `Values["package.standoff"]` | `A1` | — | mm | `modify_component` | `overallPackage` | `standoffA1` |
| `Values["encapsulant.thickness"]` | `A2` | — | mm | `modify_component` | `overallPackage` | `encapsulantThicknessA2` |
| `Values["die.length"]` | `Ld` | — | mm | `modify_component` | `die` | `dieLengthLd` |
| `Values["die.width"]` | `Wd` | — | mm | `modify_component` | `die` | `dieWidthWd` |
| `Values["die.thickness"]` | `td` | — | mm | `modify_component` | `die` | `dieThicknessTd` |
| `Values["die.attach"]` | `tda` | — | mm | `modify_component` | `die` | `dieAttachThicknessTda` |
| `Values["die.power"]` | `P` | — | W | `modify_component` | `die` | `packagePower` |
| `Values["pad.length"]` | `Lp` | — | mm | `modify_component` | `dap` | `dapLengthLp` |
| `Values["pad.width"]` | `Wp` | — | mm | `modify_component` | `dap` | `dapWidthWp` |
| `Values["pad.exposed_length"]` | `Lep` | — | mm | `modify_component` | `dap` | `exposedPADLength` |
| `Values["pad.exposed_width"]` | `Wep` | — | mm | `modify_component` | `dap` | `exposedPADWidth` |
| `Values["leads.count_x"]` | `MD` | — | — | `modify_component` | `leadAndSolderInterconnect` | `numberOfLeadsOnTopBottomMD` |
| `Values["leads.count_y"]` | `ME` | — | — | `modify_component` | `leadAndSolderInterconnect` | `numberOfLeadsOnLeftRightME` |
| `Values["leads.pitch_x"]` | `ex` | — | mm | `modify_component` | `leadAndSolderInterconnect` | `pitchInXDirectionEx` |
| `Values["leads.pitch_y"]` | `ey` | — | mm | `modify_component` | `leadAndSolderInterconnect` | `pitchInYDirectionEy` |
| `Values["leads.width"]` | `wf` | — | mm | `modify_component` | `leadAndSolderInterconnect` | `leadWidthB` |
| `Values["leads.length"]` | `lf` | — | mm | `modify_component` | `leadAndSolderInterconnect` | `exposedLeadLengthL` |
| `Values["leads.exposed_thickness"]` | `hf` | — | mm | `modify_component` | `leadAndSolderInterconnect` | `exposedLeadThickness` |
| `Values["leads.thickness"]` | `tf` | — | mm | `modify_component` | `leadAndSolderInterconnect` | `leadThicknessA3` |
| `Values["leads.etch"]` | `ldent` | — | mm | `modify_component` | `leadAndSolderInterconnect` | `leadEtch` |
| `Values["bond_wire.length_x"]` | `lbwx` | — | mm | `modify_component` | `bondWires` | `bondWireLengthOnLeftRightLbwx` |
| `Values["bond_wire.length_y"]` | `lbwy` | — | mm | `modify_component` | `bondWires` | `bondWireLengthOnTopBottomLbwy` |
| `Values["bond_wire.diameter"]` | `dbw` | — | mm | `modify_component` | `bondWires` | `bondWireDiameterDbw` |
| `Values["thermal_land.enabled"]` | `isLand` | — | — | `modify_component` | `thermalLand` | `includeLand` |
| `Values["thermal_land.thickness"]` | `ts` | `{"visible_when":{"thermal_land.enabled":true}}` | mm | `modify_component` | `thermalLand` | `landThickness` |
| `Values["vias.enabled"]` | `radio_via_modeling` | — | — | `modify_component` | `vias` | `modelViasAs` |
| `Values["vias.length"]` | `lv` | `{"visible_when":{"vias.enabled":true}}` | mm | `modify_component` | `vias` | `viasLengthLv` |
| `Values["vias.diameter"]` | `dv` | `{"visible_when":{"vias.enabled":true}}` | mm | `modify_component` | `vias` | `viasDiameterDv` |
| `Values["vias.plating"]` | `tpl` | `{"visible_when":{"vias.enabled":true}}` | mm | `modify_component` | `vias` | `platingThicknessTpl` |
| `Values["vias.pitch"]` | `ev` | `{"visible_when":{"vias.enabled":true}}` | mm | `modify_component` | `vias` | `viasPitchEv` |
| `Values["vias.columns"]` | `VD` | `{"visible_when":{"vias.enabled":true}}` | — | `modify_component` | `vias` | `numberOfViasInXVD` |
| `Values["vias.rows"]` | `VE` | `{"visible_when":{"vias.enabled":true}}` | — | `modify_component` | `vias` | `numberOfViasInYVE` |
| `Values["grid.enabled"]` | `localgrid` | — | — | `modify_component` | `modelingOptions` | `localizeGrid` |
| `Values["grid.density"]` | `radio_lgc` | `{"visible_when":{"grid.enabled":true}}` | — | `modify_component` | `modelingOptions` | `gridDensity` |
| `Values["leads.modeling"]` | `radio_LeadFram_modeling` | — | — | `modify_component` | `modelingOptions` | `modelLeadAndSolderInterconnectAs` |
| `Values["bond_wire.steps"]` | `nsteps` | — | — | `modify_component` | `modelingOptions` | `numberOfDiscreteBondwireSteps` |
| `Values["vias.modeling"]` | `radio_via_modeling` | `{"visible_when":{"vias.enabled":true}}` | — | `modify_component` | `vias` | `modelViasAs` |

### Assignments

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Assignments["group-encapsulant"]` | `k_encap` | — | — | `modify_component` | `overallPackage` | `encapsulantMaterial` |
| `Assignments["group-die"]` | — | — | — | — | — | — |
| `Assignments["group-die-attach"]` | `k_da` | — | — | `modify_component` | `die` | `dieAttachMaterial` |
| `Assignments["group-exposed-pad"]` | `k_dap` | — | — | `modify_component` | `dap` | `material` |
| `Assignments["group-lead-frame"]` | `k_lead` | — | — | `modify_component` | `leadAndSolderInterconnect` | `leadframeMaterial` |
| `Assignments["group-bond-wires"]` | `k_bw` | — | — | `modify_component` | `bondWires` | `material` |
| `Assignments["group-solder"]` | `k_solder` | — | — | `modify_component` | `leadAndSolderInterconnect` | `solderMaterial` |
| `Assignments["group-thermal-land"]` | `k_land` | `{"thermal_land.enabled":true}` | — | `modify_component` | `thermalLand` | `material` |

### ProjectDocument

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `ProjectDocument.TemplateId` | `package` | — | — | — | — | — |
| `ProjectDocument.Name` | `design` | — | — | — | — | — |
| `ProjectDocument.PresetId` | — | — | — | — | — | — |
| `ProjectDocument.CustomMaterials` | — | — | — | — | — | — |

## sop

### Values

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Values["package.type"]` | — | — | — | `new_package/new_value` | — | `sopPackageType` |
| `Values["footprint.size"]` | — | — | — | `new_package/new_value` | — | `tssopJedecFootprint`; branch=`sopJedecFootprint / wizard` |
| `Values["package.length"]` | `D` | — | mm | `modify_component` | `overallPackage` | `lengthD` |
| `Values["package.width"]` | `E` | — | mm | `modify_component` | `overallPackage` | `widthE` |
| `Values["package.standoff"]` | `A1` | — | mm | `modify_component` | `overallPackage` | `standoffA1` |
| `Values["body.length"]` | `D1` | — | mm | `modify_component` | `encapsulant` | `lengthD1` |
| `Values["body.width"]` | `E1` | — | mm | `modify_component` | `encapsulant` | `widthE1` |
| `Values["body.thickness"]` | `A2` | — | mm | `modify_component` | `encapsulant` | `thicknessA2` |
| `Values["die.length"]` | `Ld` | — | mm | `modify_component` | `die` | `dieLengthLd` |
| `Values["die.width"]` | `Wd` | — | mm | `modify_component` | `die` | `dieWidthWd` |
| `Values["die.thickness"]` | `td` | — | mm | `modify_component` | `die` | `dieThicknessTd` |
| `Values["die.attach"]` | `tda` | — | mm | `modify_component` | `die` | `dieAttachThicknessTda` |
| `Values["die.power"]` | `P` | — | W | `modify_component` | `die` | `packagePower` |
| `Values["flag.length"]` | `Lf` | — | mm | `modify_component` | `dieFlagAndTieBars` | `dieFlagLf` |
| `Values["flag.width"]` | `Wf` | — | mm | `modify_component` | `dieFlagAndTieBars` | `dieFlagWf` |
| `Values["flag.thickness"]` | `tf` | — | mm | `modify_component` | `dieFlagAndTieBars` | `dieFlagThicknessTf` |
| `Values["flag.coverage"]` | `cf` | — | % | `modify_component` | `dieFlagAndTieBars` | `metalCoverageForDieFlagCf` |
| `Values["flag.downset"]` | `ddf` | — | mm | `modify_component` | `dieFlagAndTieBars` | `dieFlagDownsetDdf` |
| `Values["tie_bar.width"]` | `wtb` | — | mm | `modify_component` | `dieFlagAndTieBars` | `tieBarWidthWtb` |
| `Values["leads.total"]` | `MT` | — | — | `modify_component` | `leadFrame` | `totalNumberOfLeadsMT` |
| `Values["leads.gap"]` | `g1` | — | mm | `modify_component` | `leadFrame` | `leadframeFlagGapG1` |
| `Values["leads.pitch"]` | `e` | — | mm | `modify_component` | `leadFrame` | `pitchE` |
| `Values["leads.width"]` | `b` | — | mm | `modify_component` | `leadFrame` | `leadWidthB` |
| `Values["leads.thickness"]` | `tl` | — | mm | `modify_component` | `leadFrame` | `leadThicknessTl` |
| `Values["leads.height"]` | `hl` | — | mm | `modify_component` | `leadFrame` | `leadframeHeightHl` |
| `Values["leads.foot_length"]` | `Lft` | — | mm | `modify_component` | `leadFrame` | `leadfootLengthLft` |
| `Values["bond_wire.count"]` | `N` | — | — | `modify_component` | `bondWires` | `numberOfBondWiresN` |
| `Values["bond_wire.diameter"]` | `dbw` | — | mm | `modify_component` | `bondWires` | `bondWireDiameterDbw` |
| `Values["thermal_land.enabled"]` | `landsolder` | — | — | `modify_component` | `thermalLandAndSolder` | `includeThermalLandAndSolder` |
| `Values["thermal_land.thickness"]` | `ts` | `{"visible_when":{"thermal_land.enabled":true}}` | mm | `modify_component` | `thermalLandAndSolder` | `landThickness` |
| `Values["grid.enabled"]` | `localgrid` | — | — | `modify_component` | `modelingOptions` | `localizeGrid` |
| `Values["grid.density"]` | `radio_lgc` | `{"visible_when":{"grid.enabled":true}}` | — | `modify_component` | `modelingOptions` | `gridDensity` |
| `Values["bond_wire.modeling"]` | `radio_BondWire_modeling` | — | — | `modify_component` | `modelingOptions` | `modelBondWiresAs` |
| `Values["package.exposed_pad"]` | — | — | — | `new_package/new_value` | — | `exposedPad` |
| `Values["leads.custom_coverage"]` | `radio_defined_coverage` | — | — | `modify_component` | `leadFrame` | `userDefinedLeadframeCoverage` |
| `Values["leads.coverage"]` | `cl` | `{"visible_when":{"leads.custom_coverage":true}}` | % | `modify_component` | `leadFrame` | `leadframeCoveragePercentage` |

### Assignments

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `Assignments["group-encapsulant"]` | `k_encap` | — | — | `modify_component` | `encapsulant` | `encapsulantMaterial` |
| `Assignments["group-die"]` | — | — | — | — | — | — |
| `Assignments["group-die-attach"]` | `k_da` | — | — | `modify_component` | `die` | `dieAttachMaterial` |
| `Assignments["group-lead-frame"]` | `k_metal` | — | — | `modify_component` | `leadFrame` | `leadframeMaterial` |
| `Assignments["group-bond-wires"]` | `k_bw` | — | — | `modify_component` | `bondWires` | `material` |
| `Assignments["group-thermal-land"]` | `k_land` | `{"thermal_land.enabled":true}` | — | `modify_component` | `thermalLandAndSolder` | `landMaterial` |
| `Assignments["group-thermal-solder"]` | `k_sd` | `{"thermal_land.enabled":true}` | — | `modify_component` | `thermalLandAndSolder` | `solderMaterial` |
| `Assignments["group-die-flag"]` | `kdf` | — | — | `modify_component` | `dieFlagAndTieBars` | `dieFlagMaterial` |

### ProjectDocument

| PackStudio 内部字段 | DES 键 | DES 条件 | 单位 | pack_script command | name | property_name |
| --- | --- | --- | --- | --- | --- | --- |
| `ProjectDocument.TemplateId` | `package` | — | — | — | — | — |
| `ProjectDocument.Name` | `design` | — | — | — | — | — |
| `ProjectDocument.PresetId` | — | — | — | — | — | — |
| `ProjectDocument.CustomMaterials` | — | — | — | — | — | — |
