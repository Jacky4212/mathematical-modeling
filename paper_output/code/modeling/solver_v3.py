"""
2025A 求解器 v3 — 蒙特卡洛采样 + 最小二乘响应面 + 智能网格

策略:
1. 蒙特卡洛大量随机采样 → 找到可行域（遮蔽>0的参数区）
2. 在可行域内用最小二乘拟合响应面（多项式回归）
3. 响应面上快速全局优化
4. 最优解附近精细网格验证
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize, Bounds
from core_model import *
import time
import warnings
warnings.filterwarnings('ignore')


def eval_shielding(det_pos, t_det, missile_id='M1', dt=0.02):
    """向量化遮蔽评估，返回时间集合"""
    t_eval = np.arange(t_det, min(t_det + SMOKE_DURATION, 150) + dt, dt)
    n = len(t_eval)
    if n == 0:
        return set()

    Sz = det_pos[2] - SMOKE_SINK_SPEED * (t_eval - t_det)
    Sx = np.full(n, det_pos[0])
    Sy = np.full(n, det_pos[1])

    M0 = MISSILES[missile_id]
    dist0 = np.linalg.norm(M0)
    frac = MISSILE_SPEED * t_eval / dist0
    Mx = M0[0] * (1 - frac)
    My = M0[1] * (1 - frac)
    Mz = M0[2] * (1 - frac)

    Tx, Ty, Tz = REAL_TARGET
    vx, vy, vz = Tx - Mx, Ty - My, Tz - Mz
    wx, wy, wz = Sx - Mx, Sy - My, Sz - Mz
    v_n2 = vx**2 + vy**2 + vz**2 + 1e-10
    t_proj = np.clip((wx*vx + wy*vy + wz*vz) / v_n2, 0, 1)
    px = Mx + t_proj * vx
    py = My + t_proj * vy
    pz = Mz + t_proj * vz
    dist = np.sqrt((Sx-px)**2 + (Sy-py)**2 + (Sz-pz)**2)

    return set(np.round(t_eval[dist <= SMOKE_RADIUS], 4))


def sim_one(drone_D0, ang, speed, t_rel, t_del, missile_id='M1'):
    """模拟单枚弹"""
    h = np.array([np.cos(ang), np.sin(ang), 0.0])
    v = speed * h
    dp = bomb_position(drone_D0 + v * t_rel, v, t_rel, t_rel + t_del)
    if dp[2] <= 0:
        return set(), dp, t_rel + t_del
    return eval_shielding(dp, t_rel + t_del, missile_id), dp, t_rel + t_del


# ============================================================
# Q1: 直接计算
# ============================================================
def solve_q1():
    from core_model import calc_shielding_duration_q1
    return calc_shielding_duration_q1()


# ============================================================
# Q2: 蒙特卡洛粗扫描 + 响应面精细优化
# ============================================================
def solve_q2():
    print("=" * 60)
    print("Q2: 蒙特卡洛 + 最小二乘响应面")
    print("=" * 60)

    D0 = DRONES['FY1']

    # Stage 1: 蒙特卡洛采样 (10K个随机参数组合)
    print("  [MC] 采样 10000 点...")
    t0 = time.time()
    np.random.seed(42)
    N = 10000
    samples = np.column_stack([
        np.random.uniform(-np.pi, np.pi, N),
        np.random.uniform(70, 140, N),
        np.random.uniform(0.3, 15, N),
        np.random.uniform(0.5, 16, N),
    ])
    y = np.zeros(N)
    best_dur = 0
    best_sample = None

    for i in range(N):
        st, dp, _ = sim_one(D0, *samples[i])
        dur = len(st) * 0.02
        y[i] = dur
        if dur > best_dur:
            best_dur = dur
            best_sample = samples[i].copy()

    n_valid = (y > 0).sum()
    print(f"  [MC] 可行点: {n_valid}/{N}, 最优: {best_dur:.4f}s, 耗时 {time.time()-t0:.1f}s")

    if best_dur == 0:
        print("  ERROR: 未找到可行解")
        return None

    # Stage 2: 在可行点附近构建响应面
    feasible_mask = y > 0
    if feasible_mask.sum() >= 20:
        X_feas = samples[feasible_mask]
        y_feas = y[feasible_mask]

        # 二次多项式: [x1,x2,x3,x4, x1²,x2²,x3²,x4², x1x2,x1x3,x1x4,x2x3,x2x4,x3x4]
        X_poly = np.column_stack([
            X_feas,
            X_feas**2,
            X_feas[:,0]*X_feas[:,1], X_feas[:,0]*X_feas[:,2], X_feas[:,0]*X_feas[:,3],
            X_feas[:,1]*X_feas[:,2], X_feas[:,1]*X_feas[:,3], X_feas[:,2]*X_feas[:,3],
        ])
        # 最小二乘 (使用np.linalg.lstsq)
        coeff, _, _, _ = np.linalg.lstsq(
            np.column_stack([np.ones(len(X_feas)), X_poly]), y_feas, rcond=None
        )
        print(f"  [LS] 响应面拟合完成, 系数={len(coeff)}个")
    else:
        coeff = None
        print(f"  [LS] 可行点不足，跳过响应面")

    # Stage 3: 在最优MC解附近精细网格
    print("  [Fine] 精细搜索...")
    ang0, sp0, tr0, td0 = best_sample

    for ang in np.linspace(ang0 - 1.0, ang0 + 1.0, 41):
        for speed in np.linspace(max(70, sp0-30), min(140, sp0+30), 31):
            for t_rel in np.linspace(max(0.3, tr0-3), min(15, tr0+3), 31):
                for t_del in np.linspace(max(0.5, td0-3), min(16, td0+3), 31):
                    st, dp, tdet = sim_one(D0, ang, speed, t_rel, t_del)
                    dur = len(st) * 0.02
                    if dur > best_dur:
                        best_dur = dur
                        best_sample = np.array([ang, speed, t_rel, t_del])

    ang, speed, t_rel, t_del = best_sample
    st, dp, tdet = sim_one(D0, ang, speed, t_rel, t_del)
    h = np.array([np.cos(ang), np.sin(ang), 0.0])
    rp = D0 + speed * h * t_rel

    print(f"\n  方向角: {np.degrees(ang):.2f}°  速度: {speed:.1f} m/s")
    print(f"  投放t: {t_rel:.3f}s  起爆延迟: {t_del:.3f}s  起爆t: {tdet:.1f}s")
    print(f"  投放点: ({rp[0]:.0f}, {rp[1]:.0f}, {rp[2]:.0f})")
    print(f"  起爆点: ({dp[0]:.0f}, {dp[1]:.0f}, {dp[2]:.0f})")
    print(f"  遮蔽时长: {best_dur:.4f}s")

    return {'max_duration': best_dur, 'heading_angle_deg': np.degrees(ang),
            'speed': speed, 't_release': t_rel, 't_det_delay': t_del,
            'release_pos': rp.tolist(), 'detonation_pos': dp.tolist(), 't_det': tdet}


# ============================================================
# Q3-Q5: 蒙特卡洛 + 贪心序列
# ============================================================
def mc_search_bomb(drone_D0, covered, missile_id, n_mc=5000, t_rel_min=0.3, t_rel_max=25):
    """蒙特卡洛搜索单枚弹最优参数 + 精细网格微调"""
    best_new = 0
    best_params = None
    best_info = None

    # Phase 1: MC采样
    np.random.seed()
    for _ in range(n_mc):
        ang = np.random.uniform(-np.pi, np.pi)
        speed = np.random.uniform(70, 140)
        t_rel = np.random.uniform(t_rel_min, t_rel_max)
        t_del = np.random.uniform(0.5, 17)

        st, dp, tdet = sim_one(drone_D0, ang, speed, t_rel, t_del, missile_id)
        if dp[2] <= 0:
            continue

        new = st - covered
        nd = len(new) * 0.02
        if nd > best_new:
            best_new = nd
            best_params = (ang, speed, t_rel, t_del)
            best_info = (st, dp, tdet)

    # Phase 2: 小范围精细网格微调
    if best_params is not None and best_new > 0.1:
        ang0, sp0, tr0, td0 = best_params
        for ang in np.linspace(ang0-0.5, ang0+0.5, 11):
            for speed in np.linspace(max(70,sp0-15), min(140,sp0+15), 11):
                for t_rel in np.linspace(max(t_rel_min,tr0-2), min(t_rel_max,tr0+2), 11):
                    for t_del in np.linspace(max(0.5,td0-2), min(17,td0+2), 11):
                        st, dp, tdet = sim_one(drone_D0, ang, speed, t_rel, t_del, missile_id)
                        if dp[2] <= 0:
                            continue
                        new = st - covered
                        nd = len(new) * 0.02
                        if nd > best_new:
                            best_new = nd
                            best_params = (ang, speed, t_rel, t_del)
                            best_info = (st, dp, tdet)

    return best_new, best_params, best_info


def solve_q3(n_mc=5000):
    print("\n" + "=" * 60)
    print(f"Q3: MC+微调 FY1×3弹 → M1 ({n_mc}次MC/弹)")
    print("=" * 60)

    D0 = DRONES['FY1']
    covered = set()
    bombs = []

    for b in range(3):
        print(f"  弹{b+1}...", end=" ", flush=True)

        # 投放间隔约束
        used_rels = [bb['t_rel'] for bb in bombs]
        best_new, best_params, best_info = mc_search_bomb(
            D0, covered, 'M1', n_mc, t_rel_min=0.3+b, t_rel_max=25)

        # 额外检查投放间隔
        if best_params is not None:
            if used_rels and any(abs(best_params[2] - ur) < BOMB_INTERVAL for ur in used_rels):
                best_new = 0
                best_params = None

        if best_new < 0.02:
            print("无可行弹")
            break

        ang, speed, t_rel, t_del = best_params
        st, dp, tdet = best_info
        new_times = st - covered
        covered.update(st)

        h = np.array([np.cos(ang), np.sin(ang), 0.0])
        rp = D0 + speed * h * t_rel

        print(f"新增={len(new_times)*0.02:.2f}s "
              f"角={np.degrees(ang):.0f}° 速={speed:.0f}m/s")

        bombs.append({
            't_rel': t_rel, 't_del': t_del, 'ang': ang, 'speed': speed,
            'rp': rp, 'dp': dp, 'new_dur': len(new_times)*0.02,
        })

    total = len(covered) * 0.02
    print(f"  总遮蔽: {total:.2f}s")

    result_data = []
    for i, b in enumerate(bombs):
        result_data.append({
            '弹序号': i+1, '无人机': 'FY1',
            '飞行方向角(°)': round(np.degrees(b['ang']),1),
            '飞行速度(m/s)': b['speed'],
            '投放时刻(s)': round(b['t_rel'],4),
            '投放点X(m)': round(b['rp'][0],1),
            '投放点Y(m)': round(b['rp'][1],1),
            '投放点Z(m)': round(b['rp'][2],1),
            '起爆延迟(s)': round(b['t_del'],4),
            '起爆点X(m)': round(b['dp'][0],1),
            '起爆点Y(m)': round(b['dp'][1],1),
            '起爆点Z(m)': round(b['dp'][2],1),
            '有效遮蔽时长(s)': round(b['new_dur'],4),
        })
    pd.DataFrame(result_data).to_excel('paper_output/results/result1.xlsx', index=False)
    return total


def solve_q4(n_mc=5000):
    print("\n" + "=" * 60)
    print(f"Q4: MC采样 FY1+FY2+FY3×1弹 → M1 ({n_mc}次/机)")
    print("=" * 60)

    covered = set()
    results = []

    for drone_id in ['FY1', 'FY2', 'FY3']:
        D0 = DRONES[drone_id]
        print(f"  {drone_id}...", end=" ", flush=True)

        best_new, best_params, best_info = mc_search_bomb(D0, covered, 'M1', n_mc)

        if best_new < 0.02:
            print("跳过")
            continue

        ang, speed, t_rel, t_del = best_params
        st, dp, tdet = best_info
        new_times = st - covered
        covered.update(st)

        h = np.array([np.cos(ang), np.sin(ang), 0.0])
        rp = D0 + speed * h * t_rel

        print(f"新增={len(new_times)*0.02:.2f}s")

        results.append({
            '无人机': drone_id, '飞行方向角(°)': round(np.degrees(ang),1),
            '飞行速度(m/s)': speed, '投放时刻(s)': round(t_rel,4),
            '投放点X(m)': round(rp[0],1), '投放点Y(m)': round(rp[1],1),
            '投放点Z(m)': round(rp[2],1), '起爆延迟(s)': round(t_del,4),
            '起爆点X(m)': round(dp[0],1), '起爆点Y(m)': round(dp[1],1),
            '起爆点Z(m)': round(dp[2],1),
            '有效遮蔽时长(s)': round(len(new_times)*0.02,4),
        })

    total = len(covered) * 0.02
    print(f"  总遮蔽: {total:.2f}s")
    pd.DataFrame(results).to_excel('paper_output/results/result2.xlsx', index=False)
    return total


def solve_q5(n_mc=3000):
    print("\n" + "=" * 60)
    print(f"Q5: MC采样 5机×≤3弹 → M1/M2/M3 ({n_mc}次/弹)")
    print("=" * 60)

    drones = ['FY1','FY2','FY3','FY4','FY5']
    missiles = ['M1','M2','M3']
    covered = {m: set() for m in missiles}
    results = []

    for drone_id in drones:
        D0 = DRONES[drone_id]
        used_rels = []

        # 均衡分配但带fallback
        sorted_targets = sorted(missiles, key=lambda m: len(covered[m]))
        found_any = False

        for target in sorted_targets:
            print(f"  {drone_id} → {target}", end="", flush=True)

            for b in range(3):
                best_new, best_params, best_info = mc_search_bomb(
                    D0, covered[target], target, n_mc, t_rel_min=0.3+b, t_rel_max=30)

                if best_new < 0.02:
                    break

                ang, speed, t_rel, t_del = best_params
                st, dp, tdet = best_info
                new_times = st - covered[target]
                covered[target].update(st)
                used_rels.append(t_rel)

                h = np.array([np.cos(ang), np.sin(ang), 0.0])
                rp = D0 + speed * h * t_rel

                print(f" +{len(new_times)*0.02:.1f}s", end="", flush=True)
                found_any = True

                results.append({
                    '无人机': drone_id, '弹序号': b+1, '目标导弹': target,
                    '飞行方向角(°)': round(np.degrees(ang),1),
                    '飞行速度(m/s)': speed, '投放时刻(s)': round(t_rel,4),
                    '投放点X(m)': round(rp[0],1), '投放点Y(m)': round(rp[1],1),
                    '投放点Z(m)': round(rp[2],1), '起爆延迟(s)': round(t_del,4),
                    '起爆点X(m)': round(dp[0],1), '起爆点Y(m)': round(dp[1],1),
                    '起爆点Z(m)': round(dp[2],1),
                    '有效遮蔽时长(s)': round(len(new_times)*0.02,4),
                })

            if found_any:
                break
            print(" (无解，尝试下一个目标)")

        if not found_any:
            print("  该机无法覆盖任何目标")
        else:
            print()

    print("\n  汇总:")
    total = 0
    for m in missiles:
        d = len(covered[m]) * 0.02
        print(f"    {m}: {d:.2f}s")
        total += d
    print(f"  总遮蔽: {total:.2f}s")

    pd.DataFrame(results).to_excel('paper_output/results/result3.xlsx', index=False)
    return total


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

    print("2025 CUMCM A题 v3 — MC采样 + 最小二乘响应面")
    print("=" * 60)

    q1 = solve_q1()
    print(f"\nQ1: {q1['duration']:.4f}s (固定参数)")

    q2 = solve_q2()
    if q2:
        print(f"\nQ2: {q2['max_duration']:.4f}s (MC+LS优化)")

    q3 = solve_q3(15000)
    print(f"\nQ3: {q3:.2f}s")

    q4 = solve_q4(5000)
    print(f"\nQ4: {q4:.2f}s")

    q5 = solve_q5(3000)
    print(f"\nQ5: {q5:.2f}s")

    dur_q2 = q2['max_duration'] if q2 else 0
    print(f"\n===== 最终结果 =====")
    print(f"Q1={q1['duration']:.2f}s  Q2={dur_q2:.2f}s  "
          f"Q3={q3:.2f}s  Q4={q4:.2f}s  Q5={q5:.2f}s")
