"""
问题5（简化版）：全系统协同优化
===============================
5架无人机，每架1枚弹（可扩展至3枚），干扰3枚来袭导弹。
策略：几何分配 → 独立优化 → 联合取并集
"""
import numpy as np
from scipy.optimize import minimize
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core_model import *

DRONE_IDS = ['FY1', 'FY2', 'FY3', 'FY4', 'FY5']
MISSILE_IDS = ['M1', 'M2', 'M3']


def geometric_assignment():
    """基于几何关系分配无人机到导弹"""
    assignments = {m: [] for m in MISSILE_IDS}
    for did in DRONE_IDS:
        dpos = DRONES[did]
        d_horiz = np.array([dpos[0], dpos[1]])
        scores = {}
        for mid in MISSILE_IDS:
            mpos = MISSILES[mid]
            m_horiz = np.array([mpos[0], mpos[1]])
            traj_dir = -m_horiz / np.linalg.norm(m_horiz)
            vec = d_horiz - m_horiz
            proj = np.dot(vec, traj_dir)
            perp = np.linalg.norm(vec - proj * traj_dir)
            height_match = 1.0 / (1.0 + abs(dpos[2] - mpos[2]) / 1000)
            scores[mid] = (1.0 / (1.0 + perp / 500)) * height_match
        best = max(scores, key=scores.get)
        assignments[best].append(did)
    return assignments


def optimize_single_for_missile(drone_id, missile_id, n_trials=8000):
    """
    为单架无人机优化单弹参数以遮蔽特定导弹。
    返回: (theta, speed, t_drop, t_delay, coverage, burst_pos, t_burst)
    """
    t_hit = missile_hit_time(missile_id)
    base_theta = heading_toward_origin(drone_id)

    best_cov = 0.0
    best_x = np.array([base_theta, 120.0, 3.0, 4.0])

    np.random.seed(hash(drone_id + missile_id) % 2**31)

    for trial in range(n_trials):
        if trial < n_trials * 0.3:
            theta = np.random.uniform(0, 2*np.pi)
            speed = np.random.uniform(70, 140)
            t_drop = np.random.uniform(0.1, 30)
            t_delay = np.random.uniform(0.5, 12)
        elif trial < n_trials * 0.6:
            theta = base_theta + np.random.normal(0, np.pi/3)
            speed = np.random.uniform(90, 140)
            t_drop = np.random.uniform(0.1, 20)
            t_delay = np.random.uniform(1, 10)
        else:
            theta = best_x[0] + np.random.normal(0, np.pi/8)
            speed = best_x[1] + np.random.normal(0, 8)
            t_drop = best_x[2] + np.random.normal(0, 2)
            t_delay = best_x[3] + np.random.normal(0, 1.5)

        theta = theta % (2*np.pi)
        speed = np.clip(speed, 70, 140)
        t_drop = max(0.1, t_drop)
        t_delay = max(0.5, t_delay)

        p_burst = bomb_burst_position(drone_id, speed, theta, t_drop, t_delay)
        t_burst = t_drop + t_delay
        if p_burst[2] <= 0 or t_burst >= t_hit:
            continue

        cov = compute_coverage(missile_id, p_burst, t_burst, dt=0.06)
        if cov > best_cov:
            best_cov = cov
            best_x = np.array([theta, speed, t_drop, t_delay])

    # L-BFGS-B 精修
    bounds = [(0, 2*np.pi), (70, 140), (0.1, 30), (0.5, 12)]

    def obj(x):
        p = bomb_burst_position(drone_id, x[1], x[0], x[2], x[3])
        tb = x[2] + x[3]
        if p[2] <= 0 or tb >= t_hit:
            return 0.0
        return -compute_coverage(missile_id, p, tb, dt=0.08)

    res = minimize(obj, best_x, method='L-BFGS-B', bounds=bounds,
                   options={'maxiter': 300})
    cov_refined = -obj(res.x)
    if cov_refined > best_cov:
        best_cov = cov_refined
        best_x = res.x.copy()

    theta, speed, t_drop, t_delay = best_x
    p_burst = bomb_burst_position(drone_id, speed, theta, t_drop, t_delay)
    t_burst = t_drop + t_delay

    return theta, speed, t_drop, t_delay, best_cov, p_burst, t_burst


def solve_problem5():
    print("="*60, flush=True)
    print("问题5: 全系统协同优化 (5机各1弹 → M1+M2+M3)", flush=True)
    print("="*60, flush=True)

    t_start = time.time()

    # ========================================================
    # 几何分配
    # ========================================================
    print("\n>>> 无人机-导弹几何分配...", flush=True)
    assignments = geometric_assignment()
    for mid in MISSILE_IDS:
        print(f"  {mid}: {assignments[mid]}", flush=True)

    # ========================================================
    # 逐导弹优化
    # ========================================================
    all_results = {}
    total_cov = 0.0

    for mid in MISSILE_IDS:
        drone_list = assignments[mid]
        if not drone_list:
            print(f"\n  {mid}: 无分配, 跳过", flush=True)
            continue

        print(f"\n{'='*50}", flush=True)
        print(f"  {mid}: {len(drone_list)}架无人机", flush=True)
        print(f"{'='*50}", flush=True)

        t_hit = missile_hit_time(mid)
        burst_events = []
        decoded = {}

        for did in drone_list:
            theta, speed, t_drop, t_delay, cov, p_burst, t_burst = \
                optimize_single_for_missile(did, mid)
            print(f"  {did}: {cov:.3f}s "
                  f"(θ={np.degrees(theta):.1f}°, v={speed:.0f}m/s, "
                  f"drop={t_drop:.2f}s, delay={t_delay:.2f}s)", flush=True)

            burst_events.append((p_burst, t_burst))
            decoded[did] = {
                'theta': theta,
                'speed': speed,
                'drops': [(t_drop, t_delay)],
            }

        # 联合遮蔽
        coverage = compute_multi_coverage(mid, burst_events, dt=0.02)
        print(f"  {mid} 联合遮蔽: {coverage:.4f}s", flush=True)

        all_results[mid] = {
            'decoded': decoded,
            'coverage': coverage,
            'burst_events': burst_events,
            'drone_list': drone_list,
        }
        total_cov += coverage

    # ========================================================
    # 结果输出
    # ========================================================
    elapsed = time.time() - t_start
    print(f"\n{'='*60}", flush=True)
    print(f"问题5 最终结果 (耗时 {elapsed:.1f}s)", flush=True)
    print(f"{'='*60}", flush=True)

    for mid in MISSILE_IDS:
        if mid not in all_results:
            continue
        r = all_results[mid]
        print(f"\n{mid}: {r['coverage']:.4f}s", flush=True)
        for did in r['drone_list']:
            d = r['decoded'][did]
            for bi, (t_drop, t_delay) in enumerate(d['drops'], 1):
                t_burst = t_drop + t_delay
                p = bomb_burst_position(did, d['speed'], d['theta'], t_drop, t_delay)
                print(f"  {did} 弹{bi}: drop={t_drop:.3f}s delay={t_delay:.3f}s "
                      f"burst={t_burst:.3f}s ({p[0]:.0f},{p[1]:.0f},{p[2]:.0f})",
                      flush=True)

    print(f"\n总遮蔽: {total_cov:.4f}s "
          f"(M1={all_results.get('M1',{}).get('coverage',0):.3f}s, "
          f"M2={all_results.get('M2',{}).get('coverage',0):.3f}s, "
          f"M3={all_results.get('M3',{}).get('coverage',0):.3f}s)",
          flush=True)

    print(f"\n问题1-5 汇总:")
    print(f"  问题1 (FY1单弹给定): 1.42s")
    print(f"  问题2 (FY1单弹优化): 4.74s")
    print(f"  问题3 (FY1三弹优化): ~4.74s+")
    print(f"  问题4 (三机协同):   6.54s")
    print(f"  问题5 (全系统):     {total_cov:.4f}s")

    return all_results, total_cov


if __name__ == '__main__':
    solve_problem5()
