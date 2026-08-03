# Substrate Layer

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `new_package.substrateLayer` |
| 值 | `2-Layer` / `4-Layer` |
| 模板 | FBGA/FSBGA、Wirebond PBGA |
| 默认 | `2-Layer` |

## 建模影响

该选项改变真实堆叠，不只是改变层数标签。在当前两个基准中，选择 4-Layer 后：

1. dielectric 总厚度从 0.36 mm 增至 0.56 mm；
2. 增加两个内部 trace cuboid，并增加相应均质材料；
3. die、die attach、encapsulant、bondwire、solder mask 和顶部监控点整体上移 0.20 mm；
4. 穿过 core 的 via 高度随 core 增厚 0.20 mm；
5. z 网格包络及最大网格尺寸按新总高度重算。

Wirebond PBGA 的 4 层输出还增加 `discon3`，并按新增层的 via-disconnect 拓扑省略一部分
离散 via。因而不能通过“给 2-Layer 模型再叠两张铜片”来实现该选项。

## 金属覆盖率均质公式

trace cuboid 不是纯铜，而是铜与 BT dielectric 的等效材料。若铜覆盖率为 `C%`，
`c=C/100`：

```text
k_trace   = c*k_Cu + (1-c)*k_BT
rho_trace = c*rho_Cu + (1-c)*rho_BT
cp_trace  = (c*rho_Cu*cp_Cu + (1-c)*rho_BT*cp_BT) / rho_trace
```

参考数据使用：

```text
Cu: rho=8930 kg/m^3, cp=385 J/(kg*K), k=385 W/(m*K)
BT: rho=1900 kg/m^3, cp=921 J/(kg*K), k=0.2 W/(m*K)
```

精确反算结果：

| 铜覆盖率 | rho (kg/m³) | cp (J/(kg·K)) | k (W/(m·K)) |
|---:|---:|---:|---:|
| 10% | 2603 | 737.116788321 | 38.68 |
| 20% | 3306 | 631.436781609 | 77.16 |
| 30% | 4009 | 562.819905213 | 115.64 |
| 90% | 8227 | 397.378752887 | 346.52 |

FBGA 4-Layer 的 `Trace0..3` 分别对应 20%、90%、90%、10%；Wirebond PBGA 的相关
材料依次为 30%、90%、90%、10%。具体覆盖率仍应从每层参数读取，不应由层号硬编码。

## 实现约束

- 层厚、深度、覆盖率和 disconnect-to-via 是每层数据；`4-Layer` 只是启用该组数据。
- 所有 z 坐标应从堆叠关系重新生成，不能在已有 FloXML 上做常数平移补丁。
- trace 的热容必须质量加权，不能直接对 `cp` 做体积分数平均。

## 证据

- `../templates/fbga_fsbga/xml_variations/option_switches/opt_v2_c003_substratelayer_4_layer/`
- `../templates/wirebond_pbga/xml_variations/option_switches/opt_v2_c003_substratelayer_4_layer/`
