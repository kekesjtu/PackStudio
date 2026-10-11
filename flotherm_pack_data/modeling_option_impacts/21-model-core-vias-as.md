# Model Core Vias As

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `modelingOptions.modelCoreViasAs` |
| 值 | `discreteCuboids` / `orthotropicCuboid` |
| 模板 | Flip-chip PBGA |
| 默认 | `discreteCuboids` |

## Discrete Cuboids

输出 5×5 个 `core_vias_i_j`。每个圆 via 外径 `d=0.20 mm` 被转换为等面积正方形，
高度为 core 厚度 1.15 mm。

铜镀层厚度 `t=0.025 mm`，镀层截面比例：

```text
phi_Cu_shell = 1 - ((d-2t)/d)^2 = 0.4375
```

PACK 将孔芯视为无质量、无导热占位，因此离散 `Thermal Via` 为：

```text
k_via   = phi_Cu_shell*385 = 168.4375 W/(m*K)
rho_via = phi_Cu_shell*8930 = 3906.875 kg/m^3
cp_via  = 385 J/(kg*K)
```

## Orthotropic Cuboid

25 个 via 被一个 `core_vias` 双轴材料块替换。阵列包络：

```text
Lx = (Nx-1)*px + d = 3.4 mm
Ly = (Ny-1)*py + d = 3.4 mm
h  = 1.15 mm
phi_via = Nx*Ny*pi*d^2/(4*Lx*Ly)
        = 0.067941017594935
```

基体是原有 biaxial substrate：

```text
k_sub,in_plane = 20 W/(m*K)
k_sub,normal   = 4 W/(m*K)
rho_sub = 1900 kg/m^3
cp_sub  = 921 J/(kg*K)
```

精确等效公式：

```text
k_in_plane = k_sub,in_plane = 20
k_normal   = phi_via*k_via + (1-phi_via)*k_sub,normal
           = 15.1720510807671 W/(m*K)
rho_eff    = phi_via*rho_via + (1-phi_via)*rho_sub
           = 2036.349129685835 kg/m^3
cp_eff     = (phi_via*rho_via*cp_via
             +(1-phi_via)*rho_sub*cp_sub) / rho_eff
           = 851.132675307873 J/(kg*K)
```

这里的 normal 是 via 轴向，即封装 z 方向。in-plane 保持 substrate 的 20，而不是用串联
或 Maxwell 模型重算；这是 FloTHERM PACK 的已反算规则。

## 证据

- `../templates/pbga_fc/xml_variations/option_switches/opt_v2_c007_modelcoreviasas_orthotropiccuboid/`
- 基准：`../templates/pbga_fc/baseline/model.xml`
