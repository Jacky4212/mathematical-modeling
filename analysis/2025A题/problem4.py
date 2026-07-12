"""
问题4：三机协同单弹优化
========================
FY1, FY2, FY3 各投放1枚烟幕干扰弹，联合干扰M1。
目标：最大化三弹联合遮蔽时长。

策略：
  Phase 1 — 每架无人机独立优化（单机单弹，类似问题2）
  Phase 2 — 三机联合DE全局优化（12个变量）
  Phase 3 — 精细重算 + 输出

输出：result2.xlsx
"""
import numpy as np
from scipy.optimize import differential_evolution, minimize
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core_model import *

MISSILE_ID = 'M1'
DRONE_IDS = ['FY1', 'FY2', 'FY3']
T_HIT = missile_hit_time(MISSILE_ID)


def single_drone_coverage(drone_id, theta, speed, t_drop, t_delay, dt=0.05):
    """单架无人机单枚弹的遮蔽时长"""
    p_burst = bomb_burst_position(drone_id, speed, theta, t_drop, t_delay)
    t_burst = t_drop + t_delay
    if p_burst[2] <= 0 or t_burst >= T_HIT:
        return 0.0
    return compute_coverage(MISSILE_ID, p_burst, t_burst, dt=dt)


def multi_drone_coverage(params, drone_ids, dt=0.08):
    """
    多架无人机联合遮蔽时长（并集）。
    params: [theta1, speed1, t_drop1, t_delay1, theta2, speed2, ...]
    """
    n = len(drone_ids)
    burst_events = []
    for i in range(n):
        theta = params[4*i + 0]
        speed = params[4*i + 1]
        t_drop = params[4*i + 2]
        t_delay = params[4*i + 3]

        # 可行性检查
        if t_drop + t_delay >= T_HIT:
            continue
        if speed < 70 or speed > 140:
            continue

        p_burst = bomb_burst_position(drone_ids[i], speed, theta, t_drop, t_delay)
        if p_burst[2] <= 0:
            continue

        t_burst = t_drop + t_delay
        burst_events.append((p_burst, t_burst))

    if not burst_events:
        return 0.0

    return compute_multi_coverage(MISSILE_ID, burst_events, dt=dt)


def optimize_single_drone(drone_id, n_starts=15):
    """
    为单架无人机优化4个参数（同问题2）。
    返回: (best_params, best_coverage)
    """
    print(f"\n  >>> 独立优化 {drone_id}...")

    bounds = [
        (0.0, 2*np.pi),
        (70.0, 140.0),
        (0.1, 35.0),    # t_drop — 放宽上限，较远无人机可能需要更长时间
        (0.5, 15.0),    # t_delay
    ]

    def obj(x):
        return -single_drone_coverage(drone_id, x[0], x[1], x[2], x[3], dt=0.1)

    # 默认回退参数（朝原点飞，中等速度）
    fallback = np.array([
        heading_toward_origin(drone_id),
        120.0,
        3.0,
        4.0,
    ])
    best_x = fallback.copy()
    best_cov = single_drone_coverage(drone_id, *best_x, dt=0.05)
    print(f"    回退解: {best_cov:.3f}s")

    # 随机种子搜索（不依赖L-BFGS-B，直接对目标函数采样）
    np.random.seed(hash(drone_id) % 2**31)
    base_theta = heading_toward_origin(drone_id)

    for trial in range(2000):
        # 多样化采样
        if trial < 500:
            theta = np.random.uniform(0, 2*np.pi)
            speed = np.random.uniform(70, 140)
            t_drop = np.random.uniform(0.3, 25)
            t_delay = np.random.uniform(0.5, 12)
        elif trial < 1500:
            # 在base_theta附近搜索
            theta = base_theta + np.random.normal(0, np.pi/4)
            speed = np.random.uniform(90, 140)
            t_drop = np.random.uniform(0.3, 20)
            t_delay = np.random.uniform(1, 10)
        else:
            # 在best_x附近微调
            theta = best_x[0] + np.random.normal(0, np.pi/8)
            speed = best_x[1] + np.random.normal(0, 10)
            t_drop = best_x[2] + np.random.normal(0, 3)
            t_delay = best_x[3] + np.random.normal(0, 2)

        theta = theta % (2*np.pi)
        speed = np.clip(speed, 70, 140)
        t_drop = max(0.1, t_drop)
        t_delay = max(0.5, t_delay)

        cov = single_drone_coverage(drone_id, theta, speed, t_drop, t_delay, dt=0.08)
        if cov > best_cov:
            best_cov = cov
            best_x = np.array([theta, speed, t_drop, t_delay])

    # 用L-BFGS-B从best_x出发精修
    res = minimize(obj, best_x, method='L-BFGS-B', bounds=bounds,
                   options={'maxiter': 500})
    cov_refined = single_drone_coverage(drone_id, *res.x, dt=0.05)
    if cov_refined > best_cov:
        best_cov = cov_refined
        best_x = res.x.copy()

    # 如果还不够好，用DE
    if best_cov < 3.0:
        def obj_de(x):
            p = bomb_burst_position(drone_id, x[1], x[0], x[2], x[3])
            tb = x[2] + x[3]
            if p[2] <= 0 or tb >= T_HIT:
                return 0.0
            return -compute_coverage(MISSILE_ID, p, tb, dt=0.1)

        result = differential_evolution(
            obj_de, bounds, strategy='best1bin',
            maxiter=150, popsize=15, tol=1e-6, seed=42, disp=False, polish=True
        )
        de_cov = -result.fun
        if de_cov > best_cov:
            best_cov = de_cov
            best_x = result.x.copy()

    print(f"    {drone_id}: {best_cov:.3f}s (theta={np.degrees(best_x[0]):.1f}deg, "
          f"v={best_x[1]:.0f}m/s, drop={best_x[2]:.2f}s, delay={best_x[3]:.2f}s)")

    return best_x, best_cov


def solve_problem4():
    print("="*60)
    print("问题4: 三机协同单弹优化 (FY1+FY2+FY3 → M1)")
    print("="*60)

    # ========================================================
    # Phase 1: 独立优化每架无人机
    # ========================================================
    print("\n>>> Phase 1: 独立优化每架无人机...")
    single_results = {}
    for did in DRONE_IDS:
        params, cov = optimize_single_drone(did, n_starts=10)
        single_results[did] = {'params': params, 'coverage': cov}

    # 初始联合遮蔽
    init_combined = np.array([single_results[d]['params'] for d in DRONE_IDS]).flatten()
    init_cov = multi_drone_coverage(init_combined, DRONE_IDS, dt=0.05)
    print(f"\n  独立优化联合遮蔽: {init_cov:.3f}s")

    # ========================================================
    # Phase 2: 联合DE全局优化
    # ========================================================
    print(f"\n>>> Phase 2: 联合DE全局优化 (12变量)...")

    BOUNDS = []
    for _ in DRONE_IDS:
        BOUNDS.extend([
            (0.0, 2*np.pi),
            (70.0, 140.0),
            (0.1, 30.0),
            (0.5, 15.0),
        ])

    def obj_joint(x):
        return -multi_drone_coverage(x, DRONE_IDS, dt=0.1)

    # 先用较粗的DE搜索
    result = differential_evolution(
        obj_joint, BOUNDS,
        strategy='best1bin',
        maxiter=200,
        popsize=15,
        tol=1e-6,
        seed=123,
        disp=False,
        polish=True,
    )

    joint_params = result.x
    joint_cov = multi_drone_coverage(joint_params, DRONE_IDS, dt=0.02)

    # 如果联合优化不如独立优化之和，用独立优化的结果
    if joint_cov < init_cov:
        print(f"  联合DE未改进 ({joint_cov:.3f}s < 独立{init_cov:.3f}s)，采用独立优化结果")
        joint_params = init_combined
        joint_cov = init_cov
    else:
        print(f"  联合DE优化: {joint_cov:.3f}s")

    # ========================================================
    # Phase 3: 精细计算 + 输出
    # ========================================================
    print(f"\n>>> Phase 3: 精细计算...")

    # 用细粒度重算
    burst_events = []
    results = {}
    for i, did in enumerate(DRONE_IDS):
        theta = joint_params[4*i + 0]
        speed = joint_params[4*i + 1]
        t_drop = joint_params[4*i + 2]
        t_delay = joint_params[4*i + 3]
        t_burst = t_drop + t_delay
        p_burst = bomb_burst_position(did, speed, theta, t_drop, t_delay)

        burst_events.append((p_burst, t_burst))

        single_cov = single_drone_coverage(did, theta, speed, t_drop, t_delay, dt=0.02)
        results[did] = {
            'heading_deg': np.degrees(theta),
            'speed': speed,
            't_drop': t_drop,
            't_delay': t_delay,
            't_burst': t_burst,
            'burst_x': p_burst[0],
            'burst_y': p_burst[1],
            'burst_z': p_burst[2],
            'single_coverage': single_cov,
        }

    coverage_final = compute_multi_coverage(MISSILE_ID, burst_events, dt=0.02)

    # ========================================================
    # 打印结果
    # ========================================================
    print(f"\n{'='*60}")
    print(f"问题4 最终结果")
    print(f"{'='*60}")
    print(f"导弹M1 联合遮蔽时长: {coverage_final:.4f} s")
    print(f"\n{'无人机':<8} {'航向角':>8} {'速度':>8} {'投放时刻':>10} "
          f"{'起爆延迟':>10} {'起爆时刻':>10} {'单弹遮蔽':>10}")
    print(f"{'-'*70}")
    for did in DRONE_IDS:
        r = results[did]
        print(f"{did:<8} {r['heading_deg']:>7.1f}° {r['speed']:>7.1f}m/s "
              f"{r['t_drop']:>9.3f}s {r['t_delay']:>9.3f}s "
              f"{r['t_burst']:>9.3f}s {r['single_coverage']:>9.4f}s")

    print(f"\n起爆点详情:")
    for did in DRONE_IDS:
        r = results[did]
        print(f"  {did}: ({r['burst_x']:.0f}, {r['burst_y']:.0f}, {r['burst_z']:.0f})")

    return results, coverage_final, burst_events


if __name__ == '__main__':
    results, coverage, burst_events = solve_problem4()
