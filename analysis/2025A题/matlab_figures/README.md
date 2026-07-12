# 2025 CUMCM A题 — MATLAB 可视化图集

本文件夹包含 **烟幕干扰弹投放策略** 全部可视化 MATLAB 脚本，每幅图一个 `.m` 文件，独立运行即可生成对应 PNG 图片。

---

## 文件清单

| 序号 | 文件名 | 对应题目 | 图内容 | 运行时间 |
|------|--------|----------|--------|----------|
| 1 | `plot_problem1_trajectory.m` | 问题1 | XY/XZ双视图: M1轨迹 + FY1路径 + 烟幕云团 + 遮蔽时刻视线 | ~3s |
| 2 | `plot_problem2_optimization.m` | 问题2 | 方案A(180°) vs 方案B(7.5°)六图对比: 轨迹/信号线/柱状图/3D | ~5s |
| 3 | `plot_problem3_multi_bomb.m` | 问题3 | FY1三弹遮蔽时间线甘特图 + 3D轨迹 + 云团球体 | ~5s |
| 4 | `plot_problem4_multi_drone.m` | 问题4 | 三机协同: XY/XZ/贡献柱状图/3D三视角 | ~4s |
| 5 | `plot_problem5_full_system.m` | 问题5 | 全系统(5机3弹): 全局俯视图/遮蔽贡献/分配表/3D三视角 | ~5s |
| 6 | `plot_coverage_summary.m` | 全题汇总 | 五题遮蔽时长柱状图 + 改进百分比对比 | ~1s |
| 7 | `plot_timeline_gantt.m` | 全题汇总 | 遮蔽时间线甘特图: 各遮蔽区间在时间轴上全景展示 | ~2s |
| 8 | `plot_geometry_insight.m` | 核心洞察 | 航向角对遮蔽的影响原理: LOS扫描 + 云团位置几何分析 | ~4s |

---

## 使用方法

### 单个文件运行
```matlab
% 在 MATLAB 中打开本文件夹, 运行:
>> plot_problem1_trajectory
>> plot_problem2_optimization
>> plot_coverage_summary
% ...
```

### 全部批量运行
```matlab
% 批量运行所有脚本并生成全部 PNG 图片
scripts = {
    'plot_problem1_trajectory'
    'plot_problem2_optimization'
    'plot_problem3_multi_bomb'
    'plot_problem4_multi_drone'
    'plot_problem5_full_system'
    'plot_coverage_summary'
    'plot_timeline_gantt'
    'plot_geometry_insight'
};
for i = 1:length(scripts)
    fprintf('Running %s...\n', scripts{i});
    run(scripts{i});
end
fprintf('All figures generated!\n');
```

### 依赖
- MATLAB R2019b 或更高版本
- Image Processing Toolbox (用于 `viscircles` 函数)
- 无其他第三方依赖

---

## 各图详细说明

### 1. `plot_problem1_trajectory.m` — 问题1轨迹图
- **左图 (X-Y俯视图)**: M1导弹从(20000,0)飞向原点, FY1从(17800,0)沿180°航向飞行, 在t=8.75s时刻展示烟幕云团(10m半径圆)和导弹→真目标的视线
- **右图 (X-Z侧视图)**: 同上, 展示高度维度, FY1等高度(1800m)飞行, 干扰弹起爆后因重力下沉
- **关键标注**: 投放点、起爆点、遮蔽时刻云团中心

### 2. `plot_problem2_optimization.m` — 问题2优化对比
- **子图1**: X-Y平面两组方案的飞行路径和起爆点对比
- **子图2**: X-Z平面对比, 展示不同航向对高度的影响
- **子图3**: 遮蔽信号时间线 — 问题1仅[8.04,9.46]有信号, 问题2覆盖[1.20,5.94]
- **子图4**: 遮蔽时长柱状图对比 (1.42s vs 4.74s, +234%)
- **子图5-6**: 3D视图展示两组方案的云团球体位置差异

### 3. `plot_problem3_multi_bomb.m` — 问题3三弹时间线
- **上方**: 甘特图显示三弹各自的遮蔽区间和"联合"遮蔽(任意弹覆盖即有效)
- **下方**: 3D轨迹图, FY1飞行路径上三个起爆点的空间分布
- **标注**: 每弹起爆时刻虚线、弹序编号、单弹遮蔽时长

### 4. `plot_problem4_multi_drone.m` — 问题4三机协同
- **子图1,2**: XY/XZ平面三架无人机从不同初始位置飞向M1轨迹
- **子图3**: 单机遮蔽贡献柱状图 (FY1=3.94s, FY2=0s, FY3=2.60s, 联合=6.48s)
- **子图4-6**: 3D三视角展示协同效果, FY2因y偏移太大(1400m)无法遮蔽M1

### 5. `plot_problem5_full_system.m` — 问题5全系统
- **子图1**: 全系统X-Y俯视图, 5架无人机按颜色区分, 虚线连到各自目标导弹
- **子图2**: 各导弹遮蔽时长柱状图 (M1=4.64, M2=4.58, M3=2.72, 总11.94s)
- **子图3**: 无人机-导弹分配表
- **子图4-6**: 3D三视角展示5机3弹全系统

### 6. `plot_coverage_summary.m` — 五题结果汇总
- **左侧**: 五题遮蔽时长柱状图 + 增长趋势线, 柱内标注方案描述
- **右侧**: 相对问题1的改进百分比 (问题2+234%, 问题4+356%, 问题5+741%)
- **绿色填充**: 累积改进面积

### 7. `plot_timeline_gantt.m` — 遮蔽时间线全景
- **上方**: 甘特图展示每题的遮蔽区间在0~70s时间轴上的位置
- **下方**: 总遮蔽时长对比柱状图
- **竖线标注**: M1(67s), M2(63.75s), M3(60.37s)命中时刻

### 8. `plot_geometry_insight.m` — 核心几何洞察
- **主图**: 解释为什么航向7.5°比180°遮蔽长3.3倍
  - 红色虚线: 导弹在不同时刻(t=5,15,30,50s)到真目标的LOS
  - LOS随导弹接近而"扫过"空间 — 云团需要位于扫描路径上
  - 方案A(180°): 云团在导弹正前方, LOS仅在飞行末段穿过 → 短
  - 方案B(7.5°): 云团偏在侧面, LOS更早进入 → 长
- **右下**: 几何原理文字说明
- **右上**: 遮蔽时长对比柱状图

---

## 关键数值参考

| 问题 | 方案 | 遮蔽时长 | 遮蔽区间 |
|------|------|----------|----------|
| 问题1 | FY1单弹(给定) | 1.42s | [8.04, 9.46] |
| 问题2 | FY1单弹(优化) | 4.74s | [1.20, 5.94] |
| 问题3 | FY1三弹 | 4.74s | [1.20, 5.94] (弹1覆盖) |
| 问题4 | 三机协同 | 6.48s | FY1 3.94s + FY3 2.60s |
| 问题5 | 全系统 | 11.94s | M1 4.64 + M2 4.58 + M3 2.72 |

### 导弹命中假目标时间
- M1: 67.00s
- M2: 63.75s
- M3: 60.37s

### 无人机初始位置 (X, Y, Z)
- FY1: (17800, 0, 1800)
- FY2: (12000, 1400, 1400)
- FY3: (6000, -3000, 700)
- FY4: (11000, 2000, 1800)
- FY5: (13000, -2000, 1300)

---

## 输出文件

所有脚本运行后将在当前文件夹生成以下 PNG 图片（150 DPI）：

```
matlab_figures/
├── problem1_trajectory.png      (问题1 轨迹图)
├── problem2_optimization.png    (问题2 优化对比)
├── problem3_multi_bomb.png      (问题3 三弹时间线)
├── problem4_multi_drone.png     (问题4 三机协同)
├── problem5_full_system.png     (问题5 全系统)
├── coverage_summary.png         (五题汇总对比)
├── timeline_gantt.png           (时间线甘特图)
└── geometry_insight.png         (几何洞察原理)
```
