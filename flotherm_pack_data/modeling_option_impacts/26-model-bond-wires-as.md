# Model Bond Wires As

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `modelingOptions.modelBondWiresAs` |
| 值 | `orthotropicCuboid` / `isotropicCuboid` |
| 模板 | QFP、SOIC、Wirebond PBGA |
| 默认 | `orthotropicCuboid` |

## 共同几何

切换模式不改变 8 个 bondwire 等效 cuboid 的尺寸、位置或数量，只改变 material type 和
引用。每个块仍代表一组平行金线与周围 mold 的均质区域。

## Orthotropic

设 wire 体积分数为 `phi_w`：

```text
k_high = phi_w*k_wire + (1-phi_w)*k_mold
k_low  = k_mold
rho_eff = phi_w*rho_wire + (1-phi_w)*rho_mold
cp_eff  = (phi_w*rho_wire*cp_wire
          +(1-phi_w)*rho_mold*cp_mold) / rho_eff
```

对于沿 x 的块，PACK 赋值 `(kx,ky,kz)=(k_high,k_low,k_high)`；沿 y 的块为
`(k_low,k_high,k_high)`。z 同样取高值是 PACK 的等效约定，不是圆柱金线在三轴上天然相同。

## Isotropic

```text
kx = ky = kz = k_high
```

`rho_eff`、`cp_eff` 不变。QFP/SOIC 保留两种材料名但改为 isotropic；Wirebond PBGA 则把
`bondwire_1`、`bondwire_2` 合并为一个 `bondwire`，8 个块全部改引该材料。

| 模板 | k_high (W/(m·K)) | rho (kg/m³) | cp (J/(kg·K)) |
|---|---:|---:|---:|
| QFP | 54.8883051392 | 5028.59126992 | 353.621418579 |
| SOIC | 11.2952762295 | 2448.31853072 | 669.485242994 |
| Wirebond PBGA | 47.4553300989 | 4588.63324573 | 382.357668406 |

## 物理含义

Isotropic 将一组 wire 的轴向高导热率复制到横向，会显著放大横向扩散，尤其在 `phi_w`
较高时。Orthotropic 更符合“离散平行线束嵌在树脂中”的等效方向性。

## 证据

- `../templates/pqfp/xml_variations/option_switches/opt_v2_c007_modelbondwiresas_isotropiccuboid/`
- `../templates/sop/xml_variations/option_switches/opt_v2_c007_modelbondwiresas_isotropiccuboid/`
- `../templates/pbga_wb/xml_variations/option_switches/opt_v2_c008_modelbondwiresas_isotropiccuboid/`
