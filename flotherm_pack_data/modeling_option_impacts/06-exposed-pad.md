# Exposed Pad

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `new_package.exposedPad` |
| 值 | `false` / `true` |
| 模板 | QFP、SOIC |
| 默认 | `false` |

QFN 不使用此布尔选项；其 DAP 和 Exposed PAD 长宽是固有参数。

## 建模影响

该选项是实际封装结构分支，不只是增加 PCB 侧附件：

1. 下移 die flag、die attach、die、tiebar 以及热源/监控点；
2. 使 die flag 底面与塑封体底面齐平；
3. 在其下增加 `solder` 和铜 `land`；
4. 重新连接或拉长 bondwire 等效块；QFP 还会重算 bondwire 材料。

| 模板 | 内部堆叠下移 | Land | Solder |
|---|---:|---|---|
| QFP | 0.375 mm | 2.94 × 2.94 × 0.07 mm | 2.94 × 2.94 × 0.10 mm |
| SOIC | 0.235 mm | 1.7748 × 1.3716 × 0.07 mm | 1.7748 × 1.3716 × 0.15 mm |

材料为：

```text
land   = Copper (Pure), k = 385 W/(m*K)
solder = Solder (Sn63/Pb37), k = 50.9 W/(m*K)
```

## 几何关系

以塑封体底面 `z_body_bottom` 为基准：

```text
z_die_flag = z_body_bottom
z_solder   = z_body_bottom - t_solder
z_land     = z_solder - t_land
L_land = L_solder = L_die_flag
W_land = W_solder = W_die_flag
```

当前 FloXML 采用局部坐标使 solder 从 `z=0` 向上，land 从 `z=-t_land` 到 0；上述关系
与 QFP、SOIC 导出逐项一致。

## 与 Thermal Land & Solder 的区别

`Include Thermal Land and Solder` 只添加板侧两个 cuboid，不下移封装内部堆叠。两项不能
合并为同一语义。

## 证据

- `../templates/pqfp/xml_variations/option_switches/opt_v2_c001_exposedpad_true/`
- `../templates/sop/xml_variations/option_switches/opt_v2_c001_exposedpad_true/`
- `../templates/qfn/ui.json`
