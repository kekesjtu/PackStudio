# micro/C4 bumps 与 underfill 层的各向异性等效热导率推导

## 1. 文献依据与等效目标

工作区三份论文给出的共同思想是：当封装中存在大量周期性 micro bumps 或 C4 bumps 且其尺度远小于系统级模型尺度时，可以把 bump+underfill 的真实细节层替换为一个几何尺寸不变的均匀各向异性等效层。热导率张量：

$$
\mathbf{k}_{\mathrm{eff}}=
\begin{bmatrix}
k_x & 0 & 0\\
0 & k_y & 0\\
0 & 0 & k_z
\end{bmatrix}
$$

其中 $z$ 为层厚方向，$x,y$ 为面内方向。对于正方阵列、圆形或轴对称 bump，通常有

$$
k_x=k_y=k_{xy}
$$

等效前后需要保持：

1. 几何外包尺寸一致：等效层厚度、覆盖面积与原 bump+underfill 层一致。
2. 宏观热流一致：在相同边界温差或热流下，层的总体热阻一致。
3. 材料体积分数一致：bump 金属相和 underfill 相的体积占比不变。

本文使用三类公式：

- 傅里叶定律和热阻定义：$R=L/(kA)$。
- $z$ 向热流下，bump 与 underfill 在同一水平截面内通常是并联热阻。
- $x/y$ 向热流下，热流需要绕过低导热 underfill 和高导热 bump 的横向几何，通常需要串并联热阻网络或微分积分。

参考文献：

- [Li2022] `Equivalent_Modeling_of_Microbump_Layer_in_Microsystem_for_Thermal_Analysis_Based_on_Differential_Idea.pdf`
- [Fang2025] `FC-BGA封装微凸点等效热模型及其验证研究_方玉财.pdf`
- [Rao2023] `thermal_modelling_and_analysis_of_3D_integtated_circuits_with_irregular_structure.pdf`

## 2. 符号

| 符号   | 含义                                          |
| ------ | --------------------------------------------- |
| $p$    | bump 阵列 pitch。正方阵列时单胞面积 $A_c=p^2$ |
| $H$    | bump+underfill 等效层厚度                     |
| $r$    | 圆柱 bump 半径                                |
| $R$    | 球冠或截球 bump 的母球半径                    |
| $r(z)$ | 高度 $z$ 处 bump 横截面半径                   |
| $k_b$  | bump 材料热导率                               |
| $k_u$  | underfill 热导率                              |
| $f$    | bump 面积分数或体积分数                       |
| $s$    | 把圆柱 bump 等体积替换为方柱后的方柱边长      |
| $A_b$  | bump 截面积                                   |
| $A_u$  | underfill 截面积                              |
| $A_c$  | 单胞总截面积                                  |

## 3. 基本热阻关系

对任意均匀材料块：

$$
Q=\frac{kA\Delta T}{L}, \qquad R=\frac{\Delta T}{Q}=\frac{L}{kA}
$$

若两个热阻承受相同温差，其热流相加，是并联：

$$
\frac{1}{R_{\parallel}}=\sum_i \frac{1}{R_i}
$$

若热流依次经过多个热阻，是串联：

$$
R_{\mathrm{series}}=\sum_i R_i
$$

等效热导率由目标方向的总热阻反推：

$$
k_{\mathrm{eff}}=\frac{L}{R_{\mathrm{eff}}A}
$$

## 4. 圆柱 C4 bump 的工程闭式公式

这一组公式适用于 C4 bump 或近似圆柱状 micro bump。单胞为 $p\times p\times H$，圆柱 bump 半径为 $r$，underfill 填充剩余空间。

### 4.1 $z$ 向等效热导率

$z$ 向热流下，bump 与 underfill 贯穿上下表面，承受同一温差，所以是并联热阻：

$$
R_b=\frac{H}{k_b A_b}, \qquad
R_u=\frac{H}{k_u A_u}
$$

其中

$$
A_b=\pi r^2, \qquad A_u=p^2-\pi r^2, \qquad A_c=p^2
$$

并联后：

$$
\frac{1}{R_z}=\frac{1}{R_b}+\frac{1}{R_u}
$$

代入 $k_z=H/(R_z A_c)$：

$$
k_z
=\frac{k_b A_b+k_u A_u}{A_c}
=\frac{\pi r^2}{p^2}k_b+\left(1-\frac{\pi r^2}{p^2}\right)k_u
$$

令

$$
f=\frac{\pi r^2}{p^2}
$$

则

$$
\boxed{k_z=fk_b+(1-f)k_u}
$$

这就是面积分数加权的并联上限。由于 bump 金属热导率通常远高于 underfill，$k_z$ 对 bump 面积分数非常敏感。

### 4.2 $x/y$ 向等效热导率

面内热流不是简单面积并联。Fang2025 的工程做法是把圆柱 bump 替换为等体积方柱，使方柱与圆柱的 bump 体积相同：

$$
s^2 H=\pi r^2 H
$$

因此

$$
s=\sqrt{\pi}\,r
$$

以 $x$ 向为例，热流跨过单胞长度 $p$。热阻网络分为三段：

1. 左侧 underfill 串联段，长度 $(p-s)/2$。
2. 中央段，长度 $s$，其中 bump 方柱与两侧 underfill 并联。
3. 右侧 underfill 串联段，长度 $(p-s)/2$。

各热阻为：

$$
R_{1u}=\frac{(p-s)/2}{k_u\,pH}
$$

中央段中，每个 underfill 半区热阻为

$$
R_{2u}=\frac{s}{k_u\,[(p-s)/2]H}
$$

bump 方柱热阻为

$$
R_{2b}=\frac{s}{k_b\,sH}
$$

中央段总热阻是两个 underfill 半区与 bump 的并联：

$$
R_2=
\left(
\frac{2}{R_{2u}}+\frac{1}{R_{2b}}
\right)^{-1}
$$

所以单胞面内总热阻为

$$
R_{xy}=2R_{1u}+R_2
$$

由 $k_{xy}=p/(R_{xy}pH)$ 得

$$
\boxed{
k_{xy}
=
\frac{p}{R_{xy}\,pH}
=
\frac{1}{R_{xy}H}
}
$$

即：

$$
\boxed{
k_{xy}=
\left[
\frac{p-s}{k_u p}
+
\frac{s}{k_u(p-s)+k_b s}
\right]^{-1}
}
$$

该式通常显著低于 $k_z$，因为面内热流必须穿过低热导 underfill 串联区。正方阵列下 $k_x=k_y=k_{xy}$；若 pitch 在 $x,y$ 两方向不同，应分别按对应方向重建单胞热阻网络。

## 5. 球冠或截球 micro bump 的微分积分公式

Li2022 指出，实际 micro bump 往往不是严格圆柱，而是焊接塌陷后的球冠或截球形状。如果直接用方柱或圆柱等效，会引入几何误差。因此可沿高度方向切成无穷多个薄层，在每个薄层内先做串并联热阻，再对厚度积分。

以下给出对称 bump 的推导。取等效层厚度为 $H$，单胞面积为 $p^2$。由于几何上下对称，只需对 $z\in[0,H/2]$ 积分，最后乘以 2。若坐标原点取在 bump 中心平面，截面半径为

$$
r_z=\sqrt{R^2-z^2}
$$

对于一般截球或实测轮廓，也可以直接用实际的 $r(z)$ 替代 $r_z$。

### 5.1 $z$ 向微分公式

高度 $z$ 处的薄层厚度为 $\mathrm{d}z$。该薄层内 bump 截面积和 underfill 截面积为：

$$
A_b(z)=\pi r_z^2=\pi(R^2-z^2)
$$

$$
A_u(z)=p^2-\pi(R^2-z^2)
$$

该薄层的局部 $z$ 向等效热导率为并联平均：

$$
k_z^{\mathrm{loc}}(z)
=
\frac{k_b A_b(z)+k_u A_u(z)}{p^2}
$$

即

$$
k_z^{\mathrm{loc}}(z)
=
k_u+
\frac{\pi(R^2-z^2)}{p^2}(k_b-k_u)
$$

这些薄层沿 $z$ 向串联，因此总 $z$ 向等效热导率是调和平均：

$$
k_z
=
\frac{H}{2\displaystyle\int_0^{H/2}
\frac{\mathrm{d}z}{k_z^{\mathrm{loc}}(z)}}
$$

代入局部热导率：

$$
\boxed{
k_z
=
\frac{H}{
2\displaystyle\int_0^{H/2}
\frac{p^2\,\mathrm{d}z}
{\pi(R^2-z^2)(k_b-k_u)+p^2k_u}
}
}
$$

若 $r_z$ 不随 $z$ 变化，即圆柱 bump，该式退化为第 4.1 节的 $k_z=fk_b+(1-f)k_u$。

### 5.2 $x/y$ 向微分公式

仍以 $y$ 向为例。对某一高度 $z$，bump 截面半径为 $r_z$。再在该截面内按 $y$ 坐标切成微小条带。条带处 bump 沿横向的弦长为

$$
a_y=2\sqrt{r_z^2-y^2}
$$

该条带内 bump 与 underfill 对面内热流呈并联关系，局部条带热导率为

$$
k_y^{\mathrm{strip}}(y,z)
=
k_u+\frac{a_y}{p}(k_b-k_u)
$$

即：

$$
k_y^{\mathrm{strip}}(y,z)
=
k_u+
\frac{2\sqrt{r_z^2-y^2}}{p}(k_b-k_u)
$$

在中央 bump 区域 $0\le y\le r_z$ 内，条带沿热流方向串联，得到中央区域的等效热导率：

$$
k_{By}(z)
=
\frac{r_z}
{\displaystyle\int_0^{r_z}
\frac{\mathrm{d}y}{k_y^{\mathrm{strip}}(y,z)}}
$$

写成紧凑形式：

$$
\boxed{
k_{By}(z)
=
\frac{r_z}
{\displaystyle\int_0^{r_z}
\frac{p\,\mathrm{d}y}
{2\sqrt{r_z^2-y^2}(k_b-k_u)+pk_u}}
}
$$

对该高度的整个半单胞，外侧纯 underfill 区长度为 $p/2-r_z$，中央 bump 区长度为 $r_z$，两者串联。因此该薄层的面内等效热导率为：

$$
k_y^{\mathrm{loc}}(z)
=
\frac{p/2}
{\displaystyle\frac{p/2-r_z}{k_u}+\frac{r_z}{k_{By}(z)}}
$$

不同高度的薄层对 $y$ 向热流是并联截面，因此沿厚度作算术平均：

$$
k_y
=
\frac{2}{H}\int_0^{H/2} k_y^{\mathrm{loc}}(z)\,\mathrm{d}z
$$

所以

$$
\boxed{
k_y
=
\frac{2}{H}\int_0^{H/2}
\frac{(p/2)k_{By}(z)k_u}
{r_z[k_u-k_{By}(z)]+(p/2)k_{By}(z)}
\,\mathrm{d}z
}
$$

正方阵列和轴对称 bump 下：

$$
\boxed{k_x=k_y}
$$

若 bump 轮廓、pitch 或阵列在 $x,y$ 方向不对称，需要分别建立 $x$ 向和 $y$ 向的微分热阻网络。

## 6. bump 自身为多材料层时的处理

Rao2023 中的 micro-bump 可包含 Cu、Ni、Ni$_3$Sn$_4$、SnAg 等多层连续相。可以将它先等效为各项异性材料。

若 bump 柱内部沿 $z$ 方向由 $n$ 层材料组成，第 $i$ 层厚度为 $t_i$，热导率为 $k_i$，总厚度为

$$
H_b=\sum_{i=1}^n t_i
$$

层厚体积分数为

$$
v_i=\frac{t_i}{H_b}, \qquad \sum_i v_i=1
$$

bump 柱自身的 through-plane 热导率为串联调和平均：

$$
\boxed{
k_{b,z}=
\left(\sum_{i=1}^n\frac{v_i}{k_i}\right)^{-1}
}
$$

bump 柱自身的 in-plane 热导率为并联算术平均：

$$
\boxed{
k_{b,xy}=
\sum_{i=1}^n v_i k_i
}
$$

将多材料 bump 与 underfill 继续等效时，可在第 4 或第 5 节公式中作如下替换：

$$
k_b \rightarrow k_{b,z} \quad \text{用于 } k_z
$$

$$
k_b \rightarrow k_{b,xy} \quad \text{用于 } k_x,k_y
$$

如果不同金属层的横截面积也随高度变化，更稳妥的做法是直接使用 $k_b(z)$ 和 $r(z)$ 做分层积分，而不是先把 bump 自身压缩成一个常数。

## 7. 密度与比热的等效

热仿真若包含瞬态过程，还需要等效体积热容。对 bump+underfill 单胞，按体积或质量守恒：

$$
\rho_{\mathrm{eff}}
=
f\rho_b+(1-f)\rho_u
$$

$$
(\rho c_p)_{\mathrm{eff}}
=
f\rho_b c_{p,b}+(1-f)\rho_u c_{p,u}
$$

因此

$$
\boxed{
c_{p,\mathrm{eff}}
=
\frac{
f\rho_b c_{p,b}+(1-f)\rho_u c_{p,u}
}{
f\rho_b+(1-f)\rho_u
}
}
$$

对多材料 bump，先把 bump 相内部按同样的体积热容规则求出 $\rho_b$ 和 $c_{p,b}$，再与 underfill 混合。

## 8. 用单胞仿真反向校验

三篇文献都强调公式等效后需要用详细模型或测试校验。推荐流程：

1. 建立一个含真实 bump 和 underfill 的周期单胞。
2. 提取 $k_z$：顶部施加均匀热流 $q_z$，底部定温，侧面绝热，求两截面平均温差 $\Delta T_z$。
3. 反推：$$k_z=q_z\frac{H}{\Delta T_z}$$
4. 提取 $k_x$ 或 $k_y$：在对应方向施加均匀热流，另一侧定温，其余面绝热。
5. 反推：$$
k_x=q_x\frac{L_x}{\Delta T_x}, \qquad k_y=q_y\frac{L_y}{\Delta T_y}$$
6. 将详细模型与等效层模型放入封装级模型中比较结温、最大温度、热阻和温度梯度。

Fang2025 对 FC-BGA 模型用仿真和 T3Ster 热阻测试验证，等效模型热阻误差控制在约 5% 以内。Rao2023 对 3D IC 的详细模型和等效模型比较，最大温度偏差小于 1%，且计算时间明显降低。Li2022 对球冠/截球 micro bump 层采用微分积分公式，也通过详细模型和热测试验证了等效方法的可用性。

## 9. 选用建议

| bump 形状或建模阶段                 | 推荐公式                                              |
| ----------------------------------- | ----------------------------------------------------- |
| C4 或近似圆柱 bump，快速封装级建模  | 第 4 节闭式公式                                       |
| 圆柱 bump 只关心 through-plane 导热 | $k_z=fk_b+(1-f)k_u$                                   |
| 焊接塌陷后球冠/截球 micro bump      | 第 5 节微分积分公式                                   |
| bump 内部是 Cu/Ni/SnAg/IMC 多材料层 | 先用第 6 节求 bump 自身各向异性，再进入第 4 或第 5 节 |
| 非对称                              | 分别计算 $k_x,k_y,k_z$，不要假设 $k_x=k_y$            |
