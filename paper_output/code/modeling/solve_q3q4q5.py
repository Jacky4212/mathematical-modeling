"""
Q3-Q5 高效求解器 — 2025 CUMCM A题
关键优化：只搜索heading/speed，投放时序用贪心
"""
import numpy as np
import pandas as pd
from core_model import *
from optimize_q2 import simulate_detailed
import warnings
warnings.filterwarnings('ignore')

D0 = DRONES['FY1']

def bomb_shielding_time(ang, speed, t_rel, t_del, missile_id='M1'):
    """单枚弹对指定导弹的遮蔽信息"""
    heading = np.array([np.cos(ang), np.sin(ang), 0.0])
    drone_vel = speed * heading
    release_pos = D0 + drone_vel * t_rel
    t_det = t_rel + t_del
    det_pos = bomb_position(release_pos, drone_vel, t_rel, t_det)
    if det_pos[2] <= 0:
        return 0, 0, 0, None

    dt = 0.02
    times = []
    t = t_det
    while t <= t_det + SMOKE_DURATION:
        M_pos = missile_position(missile_id, t)
        S_pos = smoke_center(det_pos, t_det, t)
        if is_shielded(M_pos, S_pos):
            times.append(t)
        t += dt

    if not times:
        return 0, 0, 0, None

    # 合并为连续段
    segs = []
    seg_start = times[0]
    seg_end = times[0]
    for ti in times[1:]:
        if ti - seg_end <= 0.03:
            seg_end = ti
        else:
            segs.append((seg_start, seg_end))
            seg_start = seg_end = ti
    segs.append((seg_start, seg_end))

    total_dur = sum(e - s + 0.02 for s, e in segs)

    return total_dur, segs[0][0], segs[-1][1], {
        'release_pos': release_pos, 'det_pos': det_pos, 't_det': t_det,
        'segments': segs, 'times': times
    }


def solve_q3_fast():
    """Q3: FY1投放3枚弹，全角度+速度扫描"""
    print("=" * 60)
    print("Q3: FY1投放3枚弹对M1干扰")
    print("=" * 60)

    best_total = 0
    best_config = None

    # 只扫描heading和speed，内部用动态规划安排3枚弹
    count = 0
    for ang in np.linspace(-np.pi, np.pi, 36):
        for speed in [70, 80, 90, 100, 110, 120, 130, 140]:
            count += 1
            if count % 20 == 0:
                print(f"  进度: {count}/288...")

            # 对每个t_rel预计算最佳遮蔽
            candidates = []
            for t_rel in np.arange(0.5, 15.0, 0.2):
                for t_del in np.arange(1.0, 18.0, 0.5):
                    dur, t1, t2, info = bomb_shielding_time(ang, speed, t_rel, t_del)
                    if dur > 0.1:
                        candidates.append((t_rel, t_del, dur, t1, t2, info))

            if len(candidates) < 3:
                continue

            # 贪心选择3枚弹：每次选能增加最多新遮蔽时间的弹
            candidates.sort(key=lambda x: -x[2])  # 按时长排序

            selected = []
            covered_times = set()

            for t_rel, t_del, dur, t1, t2, info in candidates:
                # 检查投放间隔约束
                if selected:
                    if min(abs(t_rel - s[0]) for s in selected) < BOMB_INTERVAL:
                        continue

                new_times = set(round(t, 2) for t in info['times'])
                new_coverage = len(new_times - covered_times)

                if new_coverage > 5:  # 至少带来0.1s新遮蔽
                    selected.append((t_rel, t_del, dur, t1, t2, info))
                    covered_times.update(new_times)

                if len(selected) >= 3:
                    break

            if len(selected) >= 3:
                total = len(covered_times) * 0.02
                if total > best_total:
                    best_total = total
                    best_config = (ang, speed, selected)

    if best_config is None:
        print("ERROR: 未找到可行解")
        return None

    ang, speed, selected = best_config

    print(f"\n最优策略:")
    print(f"  飞行方向角: {np.degrees(ang):.2f}°")
    print(f"  飞行速度: {speed:.2f} m/s")
    print(f"  总遮蔽时长: {best_total:.4f} s")

    heading = np.array([np.cos(ang), np.sin(ang), 0.0])
    result_data = []
    for i, (t_rel, t_del, dur, t1, t2, info) in enumerate(selected):
        print(f"  弹{i+1}: 投放t={t_rel:.2f}s, 起爆延迟={t_del:.2f}s, "
              f"遮蔽={dur:.2f}s, 时段={t1:.1f}-{t2:.1f}s")
        rp = info['release_pos']
        dp = info['det_pos']
        result_data.append({
            '弹序号': i+1, '无人机': 'FY1',
            '飞行方向角(°)': round(np.degrees(ang), 1),
            '飞行速度(m/s)': speed,
            '投放时刻(s)': round(t_rel, 4),
            '投放点X(m)': round(rp[0], 1), '投放点Y(m)': round(rp[1], 1),
            '投放点Z(m)': round(rp[2], 1),
            '起爆延迟(s)': round(t_del, 4),
            '起爆点X(m)': round(dp[0], 1), '起爆点Y(m)': round(dp[1], 1),
            '起爆点Z(m)': round(dp[2], 1),
            '有效遮蔽时长(s)': round(dur, 4),
        })

    pd.DataFrame(result_data).to_excel('paper_output/results/result1.xlsx', index=False)
    return best_config, best_total


def solve_q4_fast():
    """Q4: 3架无人机各投1枚弹"""
    print("\n" + "=" * 60)
    print("Q4: FY1/FY2/FY3各投1枚弹对M1干扰")
    print("=" * 60)

    all_times = []
    results = []

    for drone_id in ['FY1', 'FY2', 'FY3']:
        drone_D0 = DRONES[drone_id]
        best_dur = 0
        best_info = None

        for ang in np.linspace(-np.pi, np.pi, 36):
            heading = np.array([np.cos(ang), np.sin(ang), 0.0])
            for speed in [80, 100, 120, 140]:
                for t_rel in np.arange(0.5, 15, 0.5):
                    for t_del in np.arange(1, 18, 0.5):
                        t_det = t_rel + t_del
                        rel_pos = drone_D0 + speed * heading * t_rel
                        det_pos = bomb_position(rel_pos, speed*heading, t_rel, t_det)
                        if det_pos[2] <= 0:
                            continue

                        dt = 0.05
                        times_local = []
                        t = t_det
                        while t <= t_det + 20:
                            if is_shielded(missile_position('M1', t),
                                          smoke_center(det_pos, t_det, t)):
                                times_local.append(t)
                            t += dt

                        dur = len(times_local) * dt
                        if dur > best_dur:
                            best_dur = dur
                            best_info = (ang, speed, t_rel, t_del, rel_pos,
                                        det_pos, t_det, times_local)

        ang, speed, t_rel, t_del, rp, dp, t_det, tls = best_info
        print(f"  {drone_id}: 遮蔽={best_dur:.2f}s, "
              f"角度={np.degrees(ang):.0f}°, 速度={speed:.0f}m/s")

        results.append({
            '无人机': drone_id, '飞行方向角(°)': round(np.degrees(ang), 1),
            '飞行速度(m/s)': speed, '投放时刻(s)': round(t_rel, 4),
            '投放点X(m)': round(rp[0], 1), '投放点Y(m)': round(rp[1], 1),
            '投放点Z(m)': round(rp[2], 1), '起爆延迟(s)': round(t_del, 4),
            '起爆点X(m)': round(dp[0], 1), '起爆点Y(m)': round(dp[1], 1),
            '起爆点Z(m)': round(dp[2], 1), '有效遮蔽时长(s)': round(best_dur, 4),
        })
        all_times.extend(tls)

    # 合并遮蔽时间
    ut = sorted(set(round(t, 2) for t in all_times))
    total = len(ut) * 0.05
    print(f"\n总遮蔽时长: {total:.4f} s")

    pd.DataFrame(results).to_excel('paper_output/results/result2.xlsx', index=False)
    return results, total


def solve_q5_fast():
    """Q5: 5架无人机，每架≤3，对3枚导弹"""
    print("\n" + "=" * 60)
    print("Q5: 5架无人机协同对M1/M2/M3干扰")
    print("=" * 60)

    drones = ['FY1', 'FY2', 'FY3', 'FY4', 'FY5']
    missiles = ['M1', 'M2', 'M3']
    all_times = {m: [] for m in missiles}
    results = []

    for drone_id in drones:
        drone_D0 = DRONES[drone_id]
        # 分配目标：初始距离最近的导弹
        target_m = min(missiles, key=lambda m: np.linalg.norm(drone_D0 - MISSILES[m]))
        print(f"\n{drone_id} → {target_m}")

        used_release_times = []
        for bomb_idx in range(3):
            best_dur = 0
            best_info = None

            for ang in np.linspace(-np.pi, np.pi, 24):
                heading = np.array([np.cos(ang), np.sin(ang), 0.0])
                for speed in [80, 100, 120]:
                    for t_rel in np.arange(0.5, 20, 0.5):
                        # 投放间隔约束
                        if any(abs(t_rel - t0) < 1.0 for t0 in used_release_times):
                            continue
                        for t_del in np.arange(1, 18, 0.5):
                            t_det = t_rel + t_del
                            rp = drone_D0 + speed*heading*t_rel
                            dp = bomb_position(rp, speed*heading, t_rel, t_det)
                            if dp[2] <= 0:
                                continue
                            dt = 0.05
                            dur = 0
                            t = t_det
                            tls_local = []
                            while t <= t_det + 20:
                                M_pos = missile_position(target_m, t)
                                if is_shielded(M_pos, smoke_center(dp, t_det, t)):
                                    dur += dt
                                    tls_local.append(t)
                                t += dt
                            if dur > best_dur:
                                best_dur = dur
                                best_info = (ang, speed, t_rel, t_del, rp, dp, t_det, tls_local)

            if best_dur < 0.1:
                break

            ang, speed, t_rel, t_del, rp, dp, t_det, tls = best_info
            used_release_times.append(t_rel)
            print(f"  弹{bomb_idx+1}: 遮蔽={best_dur:.2f}s")

            results.append({
                '无人机': drone_id, '弹序号': bomb_idx+1,
                '目标导弹': target_m, '飞行方向角(°)': round(np.degrees(ang), 1),
                '飞行速度(m/s)': speed, '投放时刻(s)': round(t_rel, 4),
                '投放点X(m)': round(rp[0], 1), '投放点Y(m)': round(rp[1], 1),
                '投放点Z(m)': round(rp[2], 1), '起爆延迟(s)': round(t_del, 4),
                '起爆点X(m)': round(dp[0], 1), '起爆点Y(m)': round(dp[1], 1),
                '起爆点Z(m)': round(dp[2], 1), '有效遮蔽时长(s)': round(best_dur, 4),
            })
            all_times[target_m].extend(tls)

    # 汇总
    total_all = 0
    for m in missiles:
        ut = sorted(set(round(t, 2) for t in all_times[m]))
        m_dur = len(ut) * 0.05
        print(f"  {m}: {m_dur:.4f} s")
        total_all += m_dur
    print(f"\n总遮蔽时长: {total_all:.4f} s")

    pd.DataFrame(results).to_excel('paper_output/results/result3.xlsx', index=False)
    return results, total_all


if __name__ == '__main__':
    q3 = solve_q3_fast()
    q4 = solve_q4_fast()
    q5 = solve_q5_fast()
