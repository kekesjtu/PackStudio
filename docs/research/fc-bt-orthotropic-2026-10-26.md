# FC Core Vias：将 BT 表示为三向均为 0.2 的各向异性材料

## 1. 结论

恢复正常。PACK 2504 原生 FC PBGA Core Vias 的 Orthotropic Cuboid 分支中，将基板改选为新建的 orthotropic 材料，设置 $k_x=k_y=k_z=0.2$ W/(m·K)、$\rho=1900$ kg/m³、$c=921$ J/(kg·K)，可以恢复基体导热率的正常贡献。

内置 BT 与新建 constant 类型的 BT 对照均重现异常，因此结果不取决于 BT 的内置身份或材料名称。三个方案的物理导热张量均应为 $\operatorname{diag}(0.2,0.2,0.2)$，差别是原生材料类型及其所用的存储字段。

这个实验强烈支持“FC Core Via 等效分支对各向同性标量导热率的兼容存在问题，结果依赖方向字段”的解释。它不能单独证明内部具体使用了哪个 getter，也不能证明完全不存在各向同性分支。

**无需让三个方向的数值不同：使用 orthotropic 类型，即使三个方向全部为 0.2，本对照也能正常等效。**

## 2. 原生方案与参数控制

使用与前次异常相同的 FC 基线：PBGAFC_49_6X6mm、已初始化 Core Vias、Orthotropic Cuboid。

- 原始阵列 $5\times5$，无去孔。
- $d_v=0.20$ mm，镀层厚度 $t_{pl}=0.025$ mm，间距 $e_v=0.80$ mm。
- 包络 $3.40\times3.40\times1.15$ mm。
- 孔金属为 Copper (Pure)，$k=385$、$\rho=8930$、$c=385$。
- 基板仅改变材料选择；保存 DES 的其他所有参数与原始基线逐项相等。
- 自定义材料由原生 create_material／modify_material 创建，所在材料组为 Substrate Dielectrics；没有修改安装库。

| 方案 | 原生类型 | 标量 k | 方向字段 kx／ky／kz | 密度 | 比热 |
| --- | --- | ---: | --- | ---: | ---: |
| 内置 BT | constant | 0.2 | 内置非当前类型字段均为 0 | 1900 | 921 |
| 新建 BT 对照 | constant | 0.2 | 0／0／0 | 1900 | 921 |
| 新建三向 BT | orthotropic | 0.2，非当前类型字段 | 0.2／0.2／0.2 | 1900 | 921 |

三者发射率均为 0.8。原生 FlopackMaterialDataSet 中 conductivityType 的枚举为 constant／temperatureDependent／orthotropic，本次未改变温度依赖参数。

## 3. 结果

| 基板材料 | Via 等效 kx | Via 等效 ky | Via 等效 kz | 反算基体 kx／ky／kz |
| --- | ---: | ---: | ---: | --- |
| 内置 BT | 0 | 0 | 11.4438151511 | 0／0／约 0 |
| 新建 constant BT | 0 | 0 | 11.4438151511 | 0／0／约 0 |
| 新建 orthotropic BT，三向均为 0.2 | 0.2 | 0.2 | 11.6302269476 | 0.2／0.2／0.2 |

单位为 W/(m·K)。三者的 Via 等效密度、比热均为：

$$
\rho_{\rm eff}=2036.3491296858,\qquad c_{\rm eff}=851.1326753079
$$

本例孔体积分数 $\phi=0.067941017594935$，单孔等效 $k_v=168.4375$。正确轴向等效为：

$$
k_z=\phi k_v+(1-\phi)\times0.2
=11.6302269476
$$

各向同性 BT 的异常输出只有 $\phi k_v=11.4438151511$，恰好缺少基体项 $(1-\phi)\times0.2=0.1864117965$。

原生 FloXML 也确认基板材料本身的有效物性：内置／新建 constant BT 输出 isotropic_material_att，导热率为 0.2；orthotropic BT 输出 biaxial_material_att，其 in_plane_conductivity 与 normal_conductivity 均为 0.2。后者的类型折叠与 x、y 相等相符，未将结果归零。

## 4. 验证与复现

3 个首次导出、3 个独立 PACK 进程中的保存重载导出全部通过，正式运行退出码为 0，无原生 ERROR。保存重载后的材料定义、包络、Via 材料及反算基体一致。每个进程的隔离材料库都由相同原生命令创建自定义材料，重载的是保存的封装 DES；没有把“材料可用”混同于“材料被封装文件内嵌保存”。

- 工具：[verify_fc_bt_orthotropic.py](../../tools/verify_fc_bt_orthotropic.py)。
- 小型结果记录：[results.json](../validation/fc-bt-orthotropic/results.json)。
- 大型原始导出：本地 flotherm_pack_data/validation/fc_bt_orthotropic_2026-10-26/。
- 运行记录包含可执行文件、相关 DLL、原生脚本、启动脚本、XML、DES 指纹。
- PACK 文件版本 2025.13.1.1142。

本结论限于本机版本和本轮 FC Core Via 等效对照，不外推任意材料、温度依赖类型或其他封装分支。未修改外部笔记、生产代码或用户安装材料库。
