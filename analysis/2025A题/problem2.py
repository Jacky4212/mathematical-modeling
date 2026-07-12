"""
问题2（改进版）：单机单弹参数优化
==================================
从问题1的解出发，用更彻底的搜索策略寻找全局最优。

改进：
  1. 移除过于激进的几何预筛选
  2. 更大规模的DE搜索
  3. 基于几何分析的智能初始化
"""
import numpy as np
from scipy.optimize import minimize, differential_evolution
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core_model import *

DRONE_ID = 'FY1'
MISSILE_ID = 'M1'
T_HIT = missile_hit_time(MISSILE_ID)


def fast_coverage(theta, speed, t_drop, t_delay, dt=0.08):
    """快速遮蔽时长计算（粗粒度）"""
    p_burst = bomb_burst_position(DRONE_ID, speed, theta, t_drop, t_delay)
    t_burst = t_drop + t_delay
    if p_burst[2] <= 0 or t_burst >= T_HIT:
        return 0.0
    return compute_coverage(MISSILE_ID, p_burst, t_burst, dt=dt)


def fine_coverage(theta, speed, t_drop, t_delay):
    """精细遮蔽时长计算"""
    return fast_coverage(theta, speed, t_drop, t_delay, dt=0.02)


def solve_problem2():
    print("="*60)
    print("问题2: FY1单机单弹参数优化（改进版）")
    print("="*60)
    print(f"M1命中时间: {T_HIT:.2f}s")

    # ========================================================
    # 问题1参数作为基准
    # ========================================================
    x0 = np.array([
        heading_toward_origin(DRONE_ID),
        120.0, 1.5, 3.6
    ])
    cov0 = fine_coverage(*x0)
    print(f"问题1基准: {cov0:.4f}s")

    bounds = [
        (0.0, 2*np.pi),
        (70.0, 140.0),
        (0.1, 20.0),
        (0.5, 12.0),
    ]

    # ========================================================
    # Phase 1: 大规模随机搜索 + 几何智能采样
    # ========================================================
    print("\n>>> Phase 1: 随机搜索 (10000次)...")
    np.random.seed(42)

    best_x = x0.copy()
    best_cov = cov0

    # 分析导弹轨迹和真目标的关系，确定最优云团位置
    # 导弹从(20000,0,2000)→(0,0,0)，真目标在(0,200,0)
    # 理想云团在导弹LOS到真目标的中点附近
    for trial in range(10000):
        if trial < 3000:
            # 全空间随机
            theta = np.random.uniform(0, 2*np.pi)
            speed = np.random.uniform(70, 140)
            t_drop = np.random.uniform(0.1, 18)
            t_delay = np.random.uniform(0.5, 12)
        elif trial < 6000:
            # 朝向原点附近（±45°）
            base = heading_toward_origin(DRONE_ID)
            theta = base + np.random.normal(0, np.pi/4)
            speed = np.random.uniform(100, 140)
            t_drop = np.random.uniform(0.3, 12)
            t_delay = np.random.uniform(1, 10)
        elif trial < 8500:
            # 在best_x附近微调
            theta = best_x[0] + np.random.normal(0, np.pi/6)
            speed = best_x[1] + np.random.normal(0, 10)
            t_drop = best_x[2] + np.random.normal(0, 2)
            t_delay = best_x[3] + np.random.normal(0, 1.5)
        else:
            # 更小的微调
            theta = best_x[0] + np.random.normal(0, np.pi/12)
            speed = best_x[1] + np.random.normal(0, 5)
            t_drop = best_x[2] + np.random.normal(0, 1)
            t_delay = best_x[3] + np.random.normal(0, 0.8)

        theta = theta % (2*np.pi)
        speed = np.clip(speed, 70, 140)
        t_drop = max(0.1, t_drop)
        t_delay = max(0.5, t_delay)

        cov = fast_coverage(theta, speed, t_drop, t_delay)
        if cov > best_cov:
            best_cov = cov
            best_x = np.array([theta, speed, t_drop, t_delay])

    print(f"  随机搜索最优: {best_cov:.4f}s")

    # ========================================================
    # Phase 2: L-BFGS-B 精修
    # ========================================================
    print("\n>>> Phase 2: L-BFGS-B 精修...")

    def obj_lbfgs(x):
        return -fast_coverage(x[0], x[1], x[2], x[3])

    res = minimize(obj_lbfgs, best_x, method='L-BFGS-B', bounds=bounds,
                   options={'maxiter': 500})
    cov_lbfgs = fine_coverage(*res.x)
    if cov_lbfgs > best_cov:
        best_cov = cov_lbfgs
        best_x = res.x.copy()
        print(f"  L-BFGS-B改进: {best_cov:.4f}s")
    else:
        print(f"  L-BFGS-B未改进")

    # ========================================================
    # Phase 3: DE大规模全局搜索
    # ========================================================
    print("\n>>> Phase 3: DE全局搜索（大规模）...")

    def obj_de(x):
        return -fast_coverage(x[0], x[1], x[2], x[3])

    result = differential_evolution(
        obj_de, bounds,
        strategy='best1bin',
        maxiter=300,
        popsize=20,
        tol=1e-8,
        seed=123,
        disp=True,
        polish=True,
    )

    de_cov = fine_coverage(*result.x)
    print(f"  DE最优: {de_cov:.4f}s")

    if de_cov > best_cov:
        best_cov = de_cov
        best_x = result.x.copy()

    # ========================================================
    # 结果输出
    # ========================================================
    theta_opt, speed_opt, t_drop_opt, t_delay_opt = best_x
    t_burst_opt = t_drop_opt + t_delay_opt
    p_burst_opt = bomb_burst_position(DRONE_ID, speed_opt, theta_opt,
                                       t_drop_opt, t_delay_opt)
    coverage_final = fine_coverage(theta_opt, speed_opt, t_drop_opt, t_delay_opt)

    # 详细遮蔽区间
    intervals = find_coverage_intervals(MISSILE_ID, p_burst_opt, t_burst_opt, dt=0.02)

    print(f"\n{'='*60}")
    print(f"问题2 最终优化结果")
    print(f"{'='*60}")
    print(f"航向角:      {np.degrees(theta_opt):.2f} deg")
    print(f"飞行速度:    {speed_opt:.1f} m/s")
    print(f"投放时刻:    {t_drop_opt:.3f} s")
    print(f"起爆延迟:    {t_delay_opt:.3f} s")
    print(f"起爆时刻:    {t_burst_opt:.3f} s")
    print(f"起爆点:      ({p_burst_opt[0]:.0f}, {p_burst_opt[1]:.0f}, {p_burst_opt[2]:.0f})")
    print(f"遮蔽时长:    {coverage_final:.4f} s")
    print(f"遮蔽区间:    {len(intervals)}段")
    for i, (s, e) in enumerate(intervals, 1):
        print(f"  区间{i}: [{s:.2f}, {e:.2f}] 持续{e-s:.4f}s")

    print(f"\n对比: 问题1={cov0:.4f}s → 问题2={coverage_final:.4f}s "
          f"({(coverage_final-cov0)/cov0*100:+.1f}%)" if cov0 > 0 else "")

    return best_x, coverage_final


if __name__ == '__main__':
    solve_problem2()
