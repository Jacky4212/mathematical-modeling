# 2023国赛C题 问题1 — MATLAB可视化图集

## 数据驱动原则

**所有 6 张图均从 `output/` 真实数据读取，零硬编码数值、零模拟曲线。**

| 图 | 数据来源 | 计算方式 |
|----|---------|---------|
| `fig1_descriptive_stats` | `output/desc_stats.csv` | 直接读取 |
| `fig2_pareto_concentration` | `output/item_ranked.csv` | 从 246 单品销量实时算 Pareto + Gini |
| `fig3_stl_decomposition` | `output/stl_flat.csv` | 直接读取 6510 行 STL 分量 |
| `fig4_correlation_heatmap` | `output/pearson_corr.csv` + `output/daily_category_sales.csv` | Pearson 读取，Spearman 实时计算 |
| `fig5_distribution_fitting` | `output/daily_category_sales.csv` | 对数正态拟合 + KS 检验均为实时计算 |
| `fig6_cross_correlation` | `output/daily_category_sales.csv` | CCF 从 1085 天时间序列手写算法计算 |

## 文件清单

| 文件 | 内容 |
|------|------|
| `fig1_descriptive_stats.m` | 6品类描述统计面板（均值/std/CV/偏度/峰度/份额表） |
| `fig2_pareto_concentration.m` | 全品类单品帕累托图 + 分品类Gini系数 |
| `fig3_stl_decomposition.m` | STL趋势线(period=365) + 季节周模式对比 |
| `fig4_correlation_heatmap.m` | Pearson/Spearman相关系数热力图（含显著性标注） |
| `fig5_distribution_fitting.m` | 对数正态分布拟合直方图 + KS检验 |
| `fig6_cross_correlation.m` | 品类间交叉相关CCF茎叶图（真实计算） |

## 使用方法

```matlab
% 逐个运行
>> fig1_descriptive_stats
>> fig2_pareto_concentration
% ...

% 或批量运行
scripts = {'fig1_descriptive_stats','fig2_pareto_concentration',...
           'fig3_stl_decomposition','fig4_correlation_heatmap',...
           'fig5_distribution_fitting','fig6_cross_correlation'};
for i = 1:length(scripts); run(scripts{i}); end
```

## 依赖
- MATLAB R2019b+
- Statistics and Machine Learning Toolbox（`kstest`、`corr`）
- `output/` 文件夹中由 Python 生成的 CSV 数据文件

## 与旧版的区别

| 旧版问题 | 新版修复 |
|---------|---------|
| fig1 全部硬编码数值 | 从 `desc_stats.csv` 读取 |
| fig2 模拟单品份额 + 硬编码 Gini | 从 `item_ranked.csv` 246 行真实数据计算 |
| fig4 Pearson/Spearman 均硬编码 | Pearson 读 CSV，Spearman 从日销量实时算 |
| fig5 KS p值硬编码 | `kstest()` 实时计算 |
| **fig6 CCF曲线用高斯函数伪造** | **手写 CCF 算法，从真实时间序列逐对计算** |
