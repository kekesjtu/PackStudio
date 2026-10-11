# Model Solder Ball Array As

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `modelingOptions.modelSolderBallArrayAs` |
| 值 | `discreteCuboids` / `orthotropicCuboid` / `isotropicCuboid` |
| 模板 | 各 BGA；当前 option sweep 覆盖 Flip-chip CBGA/PBGA、Wirebond PBGA |

## Discrete Cuboids

每个球用与圆形最大截面积相等的正方形柱表示：

```text
s = d*sqrt(pi)/2
size = (s, s, h_standoff)
center_x(i) = (i-(Nx-1)/2)*px
center_y(j) = (j-(Ny-1)/2)*py
```

材料为纯 solder。球体真实的弧形轮廓未保留，但柱体体积
`s^2*h = pi*d^2*h/4` 与“直径 d、高 h 的圆柱”相同。

## 整阵列等效公式

满阵列包络：

```text
Lx = (Nx-1)*px + d
Ly = (Ny-1)*py + d
N  = Nx*Ny
phi_solder = N*pi*d^2/(4*Lx*Ly)
```

以 solder 和空气为组分：

```text
k_normal = phi_solder*k_solder + (1-phi_solder)*k_air
rho_eff  = phi_solder*rho_solder + (1-phi_solder)*rho_air
cp_eff   = (phi_solder*rho_solder*cp_solder
           +(1-phi_solder)*rho_air*cp_air) / rho_eff
```

Sn63/Pb37 的参考值为 `rho=8400`、`cp=150`、`k=50.9`。

### Orthotropic Cuboid

```text
kx = ky = k_air = 0.0261
kz = k_normal
```

只输出一个 `Lx×Ly×h_standoff` 块。z 是 ball 轴向。

### Isotropic Cuboid

```text
kx = ky = kz = k_normal
```

几何、rho 和 cp 与 Orthotropic 相同，只是把 z 向高导热率复制到 x、y。

## 精确基准

| 模板 | Nx×Ny | d/p/h (mm) | Lx=Ly (mm) | phi | k_normal | rho | cp |
|---|---:|---|---:|---:|---:|---:|---:|
| Flip-chip CBGA/PBGA | 7×7 | 0.5/0.8/0.4 | 5.3 | 0.3425107690 | 17.4509586118 | 2877.85406772 | 150.227395842 |
| Wirebond PBGA | 11×11 | 0.75/1.27/0.6 | 13.45 | 0.2954970910 | 15.0591894555 | 2482.99377369 | 150.282403324 |

Wirebond PBGA 的 discrete 球边长为
`0.75*sqrt(pi)/2=0.664670194090 mm`，共 121 个。

## 其他排布的处理

- 中央去球：等效层拆成四个边框块，见 [Depopulated Center](34-depopulated-center.md)。
- 中央球：建立独立中心阵列，见 [Central Balls](35-central-balls.md)。
- stagger：离散阵列按棋盘格删球；等效层把 `phi` 乘 0.5。
- map：必须先取得编辑器中的占位矩阵，不能只切换布尔值。

## PackStudio 取舍

按照当前产品决策，只有 BGA array 层暴露 `discreteCuboids` 与各向异性等效层两种模式；
不提供 PACK 的 isotropic 选项。各向异性模式使用上述 Orthotropic 公式。

## 证据

- `../templates/cbga_fc/xml_variations/option_switches/opt_v2_c006_modelsolderballarrayas_discretecuboids/`
- `../templates/pbga_fc/xml_variations/option_switches/opt_v2_c006_modelsolderballarrayas_discretecuboids/`
- `../templates/pbga_wb/xml_variations/option_switches/opt_v2_c004_modelsolderballarrayas_isotropiccuboid/`
- `../templates/pbga_wb/xml_variations/option_switches/opt_v2_c005_modelsolderballarrayas_discretecuboids/`
