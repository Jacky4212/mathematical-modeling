"""
问题3（修正版）：单机三弹时序优化
==================================
策略：以问题2的最优解为弹1基础，搜索弹2弹3补充覆盖。
"""
import numpy as np
from scipy.optimize import minimize
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core_model import *

DRONE_ID = 'FY1'
MISSILE_ID = 'M1'
T_HIT = missile_hit_time(MISSILE_ID)


def burst_from_params(theta, speed, t_drop, t_delay):
    """从参数计算起爆信息"""
    t_burst = t_drop + t_delay
    p_burst = bomb_burst_position(DRONE_ID, speed, theta, t_drop, t_delay)
    return p_burst, t_burst


def union_of_bursts(burst_events):
    """计算联合遮蔽"""
    if not burst_events:
        return 0.0
    return compute_multi_coverage(MISSILE_ID, burst_events, dt=0.02)


def solve_problem3():
    print("="*60)
    print("问题3: FY1 单机三弹时序优化（修正版）")
    print("="*60)
    print(f"M1 命中时间: {T_HIT:.2f} s")

    # ========================================================
    # 弹1：使用问题2最优参数
    # ========================================================
    # Problem 2 optimal: theta=7.5°, speed=70 m/s, drop=0.1s, delay=1.04s
    theta_base = np.radians(7.50)
    speed_base = 70.0
    t_drop1 = 0.100
    t_delay1 = 1.040

    p1, tb1 = burst_from_params(theta_base, speed_base, t_drop1, t_delay1)
    cov1 = compute_coverage(MISSILE_ID, p1, tb1, dt=0.02)
    intervals1 = find_coverage_intervals(MISSILE_ID, p1, tb1, dt=0.02)
    print(f"\n弹1 (问题2最优): {cov1:.4f}s")
    for s, e in intervals1:
        print(f"  遮蔽区间: [{s:.2f}, {e:.2f}] 持续{e-s:.4f}s")

    # ========================================================
    # 搜索弹2：覆盖弹1区间之后的空白
    # ========================================================
    print(f"\n搜索弹2（补充弹1覆盖空白）...")
    best_bursts = [(p1, tb1)]
    best_cov = cov1

    np.random.seed(42)
    # 尝试各种投放时机和延迟
    for trial in range(15000):
        # 弹2投放时刻在弹1之后至少1s
        t_drop2 = t_drop1 + BOMB_INTERVAL_MIN + np.random.uniform(0, 30)
        t_delay2 = np.random.uniform(0.5, 12.0)

        p2, tb2 = burst_from_params(theta_base, speed_base, t_drop2, t_delay2)
        if p2[2] <= 0 or tb2 >= T_HIT:
            continue

        union_cov = union_of_bursts([(p1, tb1), (p2, tb2)])
        if union_cov > best_cov:
            best_cov = union_cov
            best_bursts = [(p1, tb1), (p2, tb2)]
            best_t_drop2 = t_drop2
            best_t_delay2 = t_delay2
            best_p2 = p2

    if len(best_bursts) >= 2:
        _, tb2_best = best_bursts[1]
        t_drop2 = best_t_drop2
        t_delay2 = best_t_delay2
        print(f"  弹2: 投放={t_drop2:.3f}s, 延迟={t_delay2:.3f}s, "
              f"起爆={tb2_best:.3f}s, 联合={best_cov:.4f}s (增量{best_cov-cov1:+.4f}s)")
    else:
        # 没有改进
        best_bursts = [(p1, tb1)]
        t_drop2 = t_drop1 + 3.0
        t_delay2 = 3.0
        print(f"  弹2未找到改进")

    # ========================================================
    # 搜索弹3：补充前2弹的空白
    # ========================================================
    print(f"\n搜索弹3（补充前2弹覆盖空白）...")
    cov_before_3 = best_cov

    for trial in range(15000):
        t_drop3 = max(t_drop2, t_drop1) + BOMB_INTERVAL_MIN + np.random.uniform(0, 30)
        t_delay3 = np.random.uniform(0.5, 12.0)

        p3, tb3 = burst_from_params(theta_base, speed_base, t_drop3, t_delay3)
        if p3[2] <= 0 or tb3 >= T_HIT:
            continue

        test_bursts = best_bursts + [(p3, tb3)]
        union_cov = union_of_bursts(test_bursts)
        if union_cov > best_cov:
            best_cov = union_cov
            best_t_drop3 = t_drop3
            best_t_delay3 = t_delay3
            best_p3 = p3

    if best_cov > cov_before_3:
        best_bursts.append((best_p3, best_t_drop3 + best_t_delay3))
        print(f"  弹3: 投放={best_t_drop3:.3f}s, 延迟={best_t_delay3:.3f}s, "
              f"联合={best_cov:.4f}s (增量{best_cov-cov_before_3:+.4f}s)")
    else:
        t_drop3 = t_drop2 + 3.0
        t_delay3 = 3.0
        print(f"  弹3未找到改进")

    # ========================================================
    # 也尝试各种不同的theta/speed组合（不只是问题2的最优）
    # ========================================================
    print(f"\n尝试不同航向/速度组合...")
    for trial in range(5000):
        theta = np.random.uniform(0, 2*np.pi)
        speed = np.random.uniform(70, 140)
        t_drop_a = np.random.uniform(0.1, 15)
        t_delay_a = np.random.uniform(0.5, 10)
        t_drop_b = t_drop_a + BOMB_INTERVAL_MIN + np.random.uniform(0, 15)
        t_delay_b = np.random.uniform(0.5, 10)
        t_drop_c = t_drop_b + BOMB_INTERVAL_MIN + np.random.uniform(0, 15)
        t_delay_c = np.random.uniform(0.5, 10)

        events = []
        for td, tdl in [(t_drop_a, t_delay_a), (t_drop_b, t_delay_b), (t_drop_c, t_delay_c)]:
            p, tb = burst_from_params(theta, speed, td, tdl)
            if p[2] > 0 and tb < T_HIT:
                events.append((p, tb))

        if len(events) >= 1:
            cov = union_of_bursts(events)
            if cov > best_cov:
                best_cov = cov
                best_bursts = events
                theta_base = theta
                speed_base = speed
                t_drop1, t_delay1 = t_drop_a, t_delay_a
                t_drop2, t_delay2 = t_drop_b, t_delay_b
                t_drop3, t_delay3 = t_drop_c, t_delay_c

    print(f"  最优: {best_cov:.4f}s (theta={np.degrees(theta_base):.1f}deg, v={speed_base:.0f}m/s)")

    # ========================================================
    # 精细重算
    # ========================================================
    t_drops = [t_drop1, t_drop2, t_drop3]
    t_delays = [t_delay1, t_delay2, t_delay3]

    # 重建burst_events（使用最终参数）
    burst_events_final = []
    for td, tdl in zip(t_drops, t_delays):
        p, tb = burst_from_params(theta_base, speed_base, td, tdl)
        if p[2] > 0 and tb < T_HIT:
            burst_events_final.append((p, tb))

    coverage_fine = union_of_bursts(burst_events_final)

    # 单弹遮蔽
    single_covs = []
    for p, tb in burst_events_final:
        single_covs.append(compute_coverage(MISSILE_ID, p, tb, dt=0.05))

    # 联合遮蔽区间
    t_min = min(tb for _, tb in burst_events_final)
    t_max = min(T_HIT, max(tb + CLOUD_DURATION for _, tb in burst_events_final))
    intervals = []
    in_cov = False
    seg_start = 0
    t = t_min
    dt = 0.02
    while t < t_max:
        shielded = any(is_shielded_at_time(MISSILE_ID, t, p, tb)
                       for p, tb in burst_events_final)
        if shielded and not in_cov:
            seg_start = t
            in_cov = True
        elif not shielded and in_cov:
            intervals.append((seg_start, t))
            in_cov = False
        t += dt
    if in_cov:
        intervals.append((seg_start, t_max))

    # ========================================================
    # 结果输出
    # ========================================================
    print(f"\n{'='*60}")
    print(f"问题3 最终结果")
    print(f"{'='*60}")
    print(f"航向角: {np.degrees(theta_base):.2f} deg")
    print(f"飞行速度: {speed_base:.1f} m/s")
    print(f"总遮蔽时长: {coverage_fine:.4f} s")
    print()
    print(f"{'弹序':<6} {'投放时刻':>10} {'起爆延迟':>10} {'起爆时刻':>10} "
          f"{'单弹遮蔽':>10} {'起爆点'}")
    print(f"{'-'*75}")
    for i, (p, tb) in enumerate(burst_events_final):
        print(f"  {i+1:<4} {t_drops[i]:>9.3f}s {t_delays[i]:>9.3f}s "
              f"{tb:>9.3f}s {single_covs[i]:>9.4f}s "
              f"({p[0]:.0f},{p[1]:.0f},{p[2]:.0f})")

    print(f"\n联合遮蔽区间 ({len(intervals)}段):")
    for i, (s, e) in enumerate(intervals, 1):
        print(f"  区间{i}: [{s:.2f}, {e:.2f}] 持续{e-s:.4f}s")

    print(f"\n对比: 问题1={1.42:.2f}s → 问题2={4.74:.2f}s → 问题3={coverage_fine:.2f}s")

    return theta_base, speed_base, t_drops, t_delays, coverage_fine


if __name__ == '__main__':
    solve_problem3()
