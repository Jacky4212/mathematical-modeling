"""
2025A 全部5问统一求解 — 物理引导的启发式搜索
"""
import numpy as np
import pandas as pd
from core_model import *
import sys
import warnings
warnings.filterwarnings('ignore')


def sim_one_bomb(drone_D0, ang, speed, t_rel, t_del, missile_id='M1'):
    """模拟单枚弹，返回(遮蔽时长,起始,结束,起爆点,所有遮蔽时刻)"""
    heading = np.array([np.cos(ang), np.sin(ang), 0.0])
    drone_vel = speed * heading
    release_pos = drone_D0 + drone_vel * t_rel
    t_det = t_rel + t_del
    det_pos = bomb_position(release_pos, drone_vel, t_rel, t_det)
    if det_pos[2] <= 0:
        return 0, 0, 0, det_pos, []

    dt = 0.02
    shielded = []
    t = t_det
    while t <= t_det + SMOKE_DURATION:
        M_pos = missile_position(missile_id, t)
        S_pos = smoke_center(det_pos, t_det, t)
        if is_shielded(M_pos, S_pos):
            shielded.append(t)
        t += dt

    if not shielded:
        return 0, 0, 0, det_pos, []

    dur = len(shielded) * dt
    return dur, shielded[0], shielded[-1], det_pos, shielded


def find_best_for_drone(drone_id, missile_id, n_bombs, speed_range, heading_range):
    """为给定无人机/导弹组合找最优策略"""
    D0 = DRONES[drone_id]

    best_total = 0
    best_result = None

    # 粗搜索
    for ang in np.linspace(heading_range[0], heading_range[1], 18):
        heading = np.array([np.cos(ang), np.sin(ang), 0.0])
        speeds = list(range(speed_range[0], speed_range[1]+1, 20))
        for speed in speeds:
            # 找最优投放时序
            t_rels = []
            t_dels = []
            all_shielded = set()

            for b in range(n_bombs):
                best_new = 0
                best_params = None
                best_new_times = []

                t_rel_start = 0.5 + b * BOMB_INTERVAL
                for t_rel in np.arange(t_rel_start, min(25.0, t_rel_start + 20), 0.3):
                    if t_rels and any(abs(t_rel - t0) < BOMB_INTERVAL for t0 in t_rels):
                        continue
                    for t_del in np.arange(1.0, 18.0, 0.5):
                        _, _, _, det_pos, times = sim_one_bomb(
                            D0, ang, speed, t_rel, t_del, missile_id)
                        if det_pos[2] <= 0:
                            continue
                        new_times = set(round(t, 2) for t in times) - all_shielded
                        new_dur = len(new_times) * 0.02
                        if new_dur > best_new:
                            best_new = new_dur
                            best_params = (t_rel, t_del, det_pos)
                            best_new_times = list(new_times)

                if best_params is None:
                    break

                t_rels.append(best_params[0])
                t_dels.append(best_params[1])
                all_shielded.update(round(t, 2) for t in best_new_times)

            total = len(all_shielded) * 0.02
            if total > best_total:
                best_total = total
                best_result = (ang, speed, t_rels, t_dels)

    return best_total, best_result


# ============================================================
def solve_q1():
    from core_model import calc_shielding_duration_q1
    return calc_shielding_duration_q1()

def solve_q2():
    from optimize_q2 import optimize_q2_improved
    return optimize_q2_improved()

# ============================================================
def solve_q3():
    print("=" * 60)
    print("Q3: FY1投放3枚弹对M1")
    print("=" * 60)

    D0 = DRONES['FY1']
    best_total = 0
    best_result = None

    for ang in np.linspace(-np.pi, np.pi, 24):
        for speed in [80, 100, 120, 140]:
            all_times = set()
            t_rels = []
            t_dels = []
            det_positions = []

            for b in range(3):
                best_new = 0
                best_p = None
                best_times = []

                t0 = 0.5 + b
                for t_rel in np.arange(t0, 20, 0.3):
                    if t_rels and any(abs(t_rel - tr) < 1.0 for tr in t_rels):
                        continue
                    for t_del in np.arange(1, 17, 0.5):
                        dur, t1, t2, dp, times = sim_one_bomb(D0, ang, speed, t_rel, t_del)
                        if dp[2] <= 0:
                            continue
                        new = set(round(t, 2) for t in times) - all_times
                        nd = len(new) * 0.02
                        if nd > best_new:
                            best_new = nd
                            best_p = (t_rel, t_del, dp)
                            best_times = list(new)

                if best_p is None:
                    break
                t_rels.append(best_p[0])
                t_dels.append(best_p[1])
                det_positions.append(best_p[2])
                all_times.update(round(t, 2) for t in best_times)

            total = len(all_times) * 0.02
            if total > best_total:
                best_total = total
                best_result = (ang, speed, t_rels, t_dels, det_positions)

    ang, speed, t_rels, t_dels, det_positions = best_result
    heading = np.array([np.cos(ang), np.sin(ang), 0.0])

    print(f"最优: 角度={np.degrees(ang):.1f}°, 速度={speed:.0f}m/s, 总时长={best_total:.2f}s")

    result_data = []
    for i, (tr, td, dp) in enumerate(zip(t_rels, t_dels, det_positions)):
        rp = D0 + speed * heading * tr
        dur, _, _, _, _ = sim_one_bomb(D0, ang, speed, tr, td)
        print(f"  弹{i+1}: 投t={tr:.2f}s 爆延={td:.2f}s 遮蔽={dur:.2f}s")
        result_data.append({
            '弹序号': i+1, '无人机': 'FY1',
            '飞行方向角(°)': round(np.degrees(ang),1),
            '飞行速度(m/s)': speed,
            '投放时刻(s)': round(tr,4),
            '投放点X(m)': round(rp[0],1),
            '投放点Y(m)': round(rp[1],1),
            '投放点Z(m)': round(rp[2],1),
            '起爆延迟(s)': round(td,4),
            '起爆点X(m)': round(dp[0],1),
            '起爆点Y(m)': round(dp[1],1),
            '起爆点Z(m)': round(dp[2],1),
            '有效遮蔽时长(s)': round(dur,4),
        })

    pd.DataFrame(result_data).to_excel('paper_output/results/result1.xlsx', index=False)
    return best_total


def solve_q4():
    print("\n" + "=" * 60)
    print("Q4: FY1/FY2/FY3各1枚弹对M1")
    print("=" * 60)

    all_times = set()
    results = []

    for drone_id in ['FY1', 'FY2', 'FY3']:
        D0 = DRONES[drone_id]
        best_dur = 0
        best_info = None

        for ang in np.linspace(-np.pi, np.pi, 24):
            for speed in [80, 100, 120, 140]:
                for t_rel in np.arange(0.5, 20, 0.3):
                    for t_del in np.arange(1, 17, 0.5):
                        dur, _, _, dp, times = sim_one_bomb(D0, ang, speed, t_rel, t_del)
                        if dur > best_dur and dp[2] > 0:
                            best_dur = dur
                            best_info = (ang, speed, t_rel, t_del, dp, [round(t,2) for t in times])

        ang, speed, t_rel, t_del, dp, times = best_info
        heading = np.array([np.cos(ang), np.sin(ang), 0.0])
        rp = D0 + speed * heading * t_rel
        all_times.update(times)

        print(f"  {drone_id}: 遮蔽={best_dur:.2f}s")
        results.append({
            '无人机': drone_id,
            '飞行方向角(°)': round(np.degrees(ang),1),
            '飞行速度(m/s)': speed,
            '投放时刻(s)': round(t_rel,4),
            '投放点X(m)': round(rp[0],1),
            '投放点Y(m)': round(rp[1],1),
            '投放点Z(m)': round(rp[2],1),
            '起爆延迟(s)': round(t_del,4),
            '起爆点X(m)': round(dp[0],1),
            '起爆点Y(m)': round(dp[1],1),
            '起爆点Z(m)': round(dp[2],1),
            '有效遮蔽时长(s)': round(best_dur,4),
        })

    total = len(all_times) * 0.02
    print(f"总遮蔽时长: {total:.2f}s")
    pd.DataFrame(results).to_excel('paper_output/results/result2.xlsx', index=False)
    return total


def solve_q5():
    print("\n" + "=" * 60)
    print("Q5: 5架无人机，每架≤3枚弹，对M1/M2/M3")
    print("=" * 60)

    drones = ['FY1', 'FY2', 'FY3', 'FY4', 'FY5']
    missiles = ['M1', 'M2', 'M3']
    all_times = {m: set() for m in missiles}
    results = []

    for drone_id in drones:
        D0 = DRONES[drone_id]
        # 分配最近导弹
        target = min(missiles, key=lambda m: np.linalg.norm(D0 - MISSILES[m]))
        print(f"\n{drone_id} → {target}")

        used_rels = []
        for b in range(3):
            best_new = 0
            best_info = None
            best_tls = []

            t0 = 0.5 + b
            for ang in np.linspace(-np.pi, np.pi, 16):
                for speed in [80, 100, 120, 140]:
                    for t_rel in np.arange(t0, 25, 0.3):
                        if any(abs(t_rel - ur) < 1.0 for ur in used_rels):
                            continue
                        for t_del in np.arange(1, 17, 0.5):
                            dur, _, _, dp, times = sim_one_bomb(D0, ang, speed, t_rel, t_del, target)
                            if dp[2] <= 0:
                                continue
                            nt = set(round(t,2) for t in times) - all_times[target]
                            nd = len(nt) * 0.02
                            if nd > best_new:
                                best_new = nd
                                best_info = (ang, speed, t_rel, t_del, dp)
                                best_tls = list(nt)

            if best_new < 0.05:
                break

            ang, speed, t_rel, t_del, dp = best_info
            heading = np.array([np.cos(ang), np.sin(ang), 0.0])
            rp = D0 + speed * heading * t_rel
            used_rels.append(t_rel)
            all_times[target].update(best_tls)

            print(f"  弹{b+1}: 新增={best_new:.2f}s, 角={np.degrees(ang):.0f}°, "
                  f"速={speed}m/s, 投t={t_rel:.1f}s")

            results.append({
                '无人机': drone_id, '弹序号': b+1,
                '目标导弹': target,
                '飞行方向角(°)': round(np.degrees(ang),1),
                '飞行速度(m/s)': speed,
                '投放时刻(s)': round(t_rel,4),
                '投放点X(m)': round(rp[0],1),
                '投放点Y(m)': round(rp[1],1),
                '投放点Z(m)': round(rp[2],1),
                '起爆延迟(s)': round(t_del,4),
                '起爆点X(m)': round(dp[0],1),
                '起爆点Y(m)': round(dp[1],1),
                '起爆点Z(m)': round(dp[2],1),
                '有效遮蔽时长(s)': round(best_new,4),
            })

    total = sum(len(t) * 0.02 for t in all_times.values())
    print(f"\n总遮蔽时长: {total:.2f}s")
    for m in missiles:
        print(f"  {m}: {len(all_times[m])*0.02:.2f}s")

    pd.DataFrame(results).to_excel('paper_output/results/result3.xlsx', index=False)
    return total


if __name__ == '__main__':
    print("2025 CUMCM A题 全部求解")
    print("=" * 60)

    q1 = solve_q1()
    print(f"\nQ1: {q1['duration']:.4f}s")

    q2 = solve_q2()
    print(f"\nQ2: {q2['max_duration']:.4f}s")

    q3 = solve_q3()
    print(f"\nQ3: {q3:.2f}s (total)")

    q4 = solve_q4()
    print(f"\nQ4: {q4:.2f}s (total)")

    q5 = solve_q5()
    print(f"\nQ5: {q5:.2f}s (total)")

    print("\n" + "=" * 60)
    print("全部求解完成！")
