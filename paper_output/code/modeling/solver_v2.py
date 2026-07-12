"""
2025A 优化求解器 v2 — 差分进化 + 最小二乘响应面 + BFGS精化

方法栈（对应知识库59法）:
- 差分进化 (Differential Evolution) → 全局搜索
- 最小二乘多项式拟合 → 响应面代理模型
- BFGS 拟牛顿法 → 局部精化
- 贪心序列优化 → 多弹协调
"""
import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize, Bounds
from scipy.interpolate import RBFInterpolator
from core_model import *
import warnings, time
warnings.filterwarnings('ignore')


# ============================================================
# 高效遮蔽评估（向量化，被所有优化器调用）
# ============================================================
def eval_shielding(det_pos, t_det, missile_id='M1', dt=0.02):
    """返回遮蔽时间集合，完全向量化"""
    t_eval = np.arange(t_det, t_det + SMOKE_DURATION + dt, dt)
    n = len(t_eval)
    if n == 0:
        return set()

    # 烟雾位置 [n]
    Sz = det_pos[2] - SMOKE_SINK_SPEED * (t_eval - t_det)
    Sx = np.full(n, det_pos[0])
    Sy = np.full(n, det_pos[1])

    # 导弹位置 [n]
    M0 = MISSILES[missile_id]
    M0_dist = np.linalg.norm(M0)
    frac = MISSILE_SPEED * t_eval / M0_dist
    Mx = M0[0] * (1 - frac)
    My = M0[1] * (1 - frac)
    Mz = M0[2] * (1 - frac)

    # 点到线距离: smoke_center → line(missile → real_target)
    Tx, Ty, Tz = REAL_TARGET
    vx, vy, vz = Tx - Mx, Ty - My, Tz - Mz
    wx, wy, wz = Sx - Mx, Sy - My, Sz - Mz
    v_n2 = vx**2 + vy**2 + vz**2 + 1e-10
    t_proj = np.clip((wx*vx + wy*vy + wz*vz) / v_n2, 0, 1)
    px = Mx + t_proj * vx
    py = My + t_proj * vy
    pz = Mz + t_proj * vz
    dist = np.sqrt((Sx - px)**2 + (Sy - py)**2 + (Sz - pz)**2)

    shielded = dist <= SMOKE_RADIUS
    return set(np.round(t_eval[shielded], 4))


def sim_bomb(params, drone_D0, missile_id='M1'):
    """给定无人机和参数，模拟单枚弹。params = [heading_angle, speed, t_release, t_delay]"""
    ang, speed, t_rel, t_del = params
    heading = np.array([np.cos(ang), np.sin(ang), 0.0])
    drone_vel = speed * heading
    t_det = t_rel + t_del
    rp = drone_D0 + drone_vel * t_rel
    dp = bomb_position(rp, drone_vel, t_rel, t_det)
    if dp[2] <= 0:
        return set(), dp, t_det
    st = eval_shielding(dp, t_det, missile_id)
    return st, dp, t_det


def objective_single(params, drone_D0, missile_id, covered_times=frozenset()):
    """单弹优化目标：最大化新增遮蔽时长"""
    st, dp, _ = sim_bomb(params, drone_D0, missile_id)
    if dp[2] <= 0:
        return 0.0
    new = st - covered_times
    return -len(new) * 0.02  # 负值用于最小化


# ============================================================
# 响应面建模 (最小二乘多项式拟合)
# ============================================================
def build_response_surface(drone_D0, missile_id, n_samples=500):
    """构建遮蔽时长对(heading, speed, t_rel, t_del)的二次响应面"""
    print(f"  [响应面] 采样 {n_samples} 点...")
    t0 = time.time()

    # Latin Hypercube 采样
    X = np.zeros((n_samples, 4))
    X[:, 0] = np.random.uniform(-np.pi, np.pi, n_samples)     # heading
    X[:, 1] = np.random.uniform(70, 140, n_samples)            # speed
    X[:, 2] = np.random.uniform(0.5, 20, n_samples)            # t_release
    X[:, 3] = np.random.uniform(1, 17, n_samples)              # t_delay

    y = np.zeros(n_samples)
    for i in range(n_samples):
        st, dp, _ = sim_bomb(X[i], drone_D0, missile_id)
        y[i] = len(st) * 0.02 if dp[2] > 0 else 0

    # 二次多项式特征: [1, x1,x2,x3,x4, x1²,x2²,x3²,x4², x1x2,x1x3,x1x4,x2x3,x2x4,x3x4]
    X_poly = np.column_stack([
        np.ones(n_samples),
        X,
        X[:, 0]**2, X[:, 1]**2, X[:, 2]**2, X[:, 3]**2,
        X[:, 0]*X[:, 1], X[:, 0]*X[:, 2], X[:, 0]*X[:, 3],
        X[:, 1]*X[:, 2], X[:, 1]*X[:, 3], X[:, 2]*X[:, 3],
    ])

    # 最小二乘拟合: β = (X^T X)^(-1) X^T y
    try:
        beta = np.linalg.lstsq(X_poly, y, rcond=None)[0]
        r2 = 1 - np.sum((y - X_poly @ beta)**2) / np.sum((y - y.mean())**2)
    except:
        beta = np.zeros(15)
        r2 = 0

    print(f"  [响应面] R² = {r2:.4f}, 耗时 {time.time()-t0:.1f}s")

    def surrogate(params):
        x = np.atleast_2d(np.asarray(params))
        xp = np.column_stack([
            np.ones(len(x)), x,
            x[:, 0]**2, x[:, 1]**2, x[:, 2]**2, x[:, 3]**2,
            x[:, 0]*x[:, 1], x[:, 0]*x[:, 2], x[:, 0]*x[:, 3],
            x[:, 1]*x[:, 2], x[:, 1]*x[:, 3], x[:, 2]*x[:, 3],
        ])
        return xp @ beta

    return surrogate, beta, r2


# ============================================================
# 问题求解
# ============================================================

def solve_q1():
    """Q1: 直接代入参数计算"""
    from core_model import calc_shielding_duration_q1
    return calc_shielding_duration_q1()


def solve_q2_de():
    """Q2: 差分进化全局优化 + BFGS局部精化"""
    print("\n" + "=" * 60)
    print("Q2: 差分进化 + BFGS 优化 FY1×1弹 → M1")
    print("=" * 60)

    D0 = DRONES['FY1']

    # 优化变量: [heading_angle, speed, t_release, t_delay]
    bounds = Bounds([-np.pi, 70, 0.5, 0.5], [np.pi, 140, 15, 15])

    def obj(x):
        return objective_single(x, D0, 'M1')

    # Phase 1: 差分进化全局搜索
    print("  [DE] 全局搜索...")
    t0 = time.time()
    result_de = differential_evolution(
        obj, bounds, seed=42, maxiter=200, popsize=20,
        mutation=(0.5, 1.5), recombination=0.9, polish=False
    )
    print(f"  [DE] 初始解: dur={-result_de.fun:.4f}s, 耗时 {time.time()-t0:.1f}s")

    # Phase 2: BFGS局部精化
    print("  [BFGS] 局部精化...")
    result_bfgs = minimize(obj, result_de.x, method='L-BFGS-B',
                           bounds=bounds, options={'maxiter': 500})
    dur = -result_bfgs.fun

    ang, speed, t_rel, t_del = result_bfgs.x
    heading = np.array([np.cos(ang), np.sin(ang), 0.0])
    drone_vel = speed * heading
    rp = D0 + drone_vel * t_rel
    t_det = t_rel + t_del
    dp = bomb_position(rp, drone_vel, t_rel, t_det)
    st, _, _ = sim_bomb(result_bfgs.x, D0)

    dur_actual = len(st) * 0.02

    print(f"\n  方向角: {np.degrees(ang):.2f}°  速度: {speed:.1f} m/s")
    print(f"  投放t: {t_rel:.3f}s  起爆延迟: {t_del:.3f}s")
    print(f"  投放点: ({rp[0]:.0f}, {rp[1]:.0f}, {rp[2]:.0f})")
    print(f"  起爆点: ({dp[0]:.0f}, {dp[1]:.0f}, {dp[2]:.0f})")
    print(f"  遮蔽时长: {dur_actual:.4f}s")

    return {'max_duration': dur_actual, 'heading_angle_deg': np.degrees(ang),
            'speed': speed, 't_release': t_rel, 't_det_delay': t_del,
            'release_pos': rp.tolist(), 'detonation_pos': dp.tolist(), 't_det': t_det}


def solve_q3_de():
    """Q3: 差分进化 + 贪心序列优化（3枚弹）"""
    print("\n" + "=" * 60)
    print("Q3: 差分进化优化 FY1×3弹 → M1")
    print("=" * 60)

    D0 = DRONES['FY1']
    bounds = Bounds([-np.pi, 70, 0.5, 0.5], [np.pi, 140, 20, 17])

    covered = set()
    bombs = []

    for b in range(3):
        print(f"\n  --- 弹{b+1} ---")

        def obj(x):
            st, dp, _ = sim_bomb(x, D0)
            if dp[2] <= 0:
                return 0.0
            # 检查投放间隔
            for prev in bombs:
                if abs(x[2] - prev['t_rel']) < BOMB_INTERVAL:
                    return 0.0
            new = st - covered
            return -len(new) * 0.02

        # 差分进化
        result = differential_evolution(
            obj, bounds, seed=42+b*10, maxiter=150, popsize=15, polish=True
        )
        dur = -result.fun
        if dur < 0.05:
            print(f"  无法找到有效弹道")
            break

        ang, speed, t_rel, t_del = result.x
        st, dp, t_det = sim_bomb(result.x, D0)
        new_times = st - covered
        covered.update(st)

        heading = np.array([np.cos(ang), np.sin(ang), 0.0])
        rp = D0 + speed * heading * t_rel

        print(f"  新增遮蔽: {len(new_times)*0.02:.2f}s  "
              f"角={np.degrees(ang):.0f}° 速={speed:.0f}m/s  "
              f"投t={t_rel:.2f}s 爆延={t_del:.2f}s")

        bombs.append({
            't_rel': t_rel, 't_del': t_del, 'ang': ang, 'speed': speed,
            'rp': rp, 'dp': dp, 't_det': t_det,
            'new_dur': len(new_times)*0.02
        })

    total = len(covered) * 0.02
    print(f"\n  总遮蔽: {total:.2f}s")

    # 保存 result1.xlsx
    result_data = []
    for i, b in enumerate(bombs):
        ang, speed = b['ang'], b['speed']
        result_data.append({
            '弹序号': i+1, '无人机': 'FY1',
            '飞行方向角(°)': round(np.degrees(ang), 1),
            '飞行速度(m/s)': speed,
            '投放时刻(s)': round(b['t_rel'], 4),
            '投放点X(m)': round(b['rp'][0], 1),
            '投放点Y(m)': round(b['rp'][1], 1),
            '投放点Z(m)': round(b['rp'][2], 1),
            '起爆延迟(s)': round(b['t_del'], 4),
            '起爆点X(m)': round(b['dp'][0], 1),
            '起爆点Y(m)': round(b['dp'][1], 1),
            '起爆点Z(m)': round(b['dp'][2], 1),
            '有效遮蔽时长(s)': round(b['new_dur'], 4),
        })
    pd.DataFrame(result_data).to_excel('paper_output/results/result1.xlsx', index=False)
    print("  → result1.xlsx 已保存")
    return total


def solve_q4_de():
    """Q4: 差分进化优化 3架无人机各1弹 → M1"""
    print("\n" + "=" * 60)
    print("Q4: 差分进化优化 FY1+FY2+FY3×1弹 → M1")
    print("=" * 60)

    bounds = Bounds([-np.pi, 70, 0.5, 0.5], [np.pi, 140, 25, 17])
    covered = set()
    results = []

    for drone_id in ['FY1', 'FY2', 'FY3']:
        D0 = DRONES[drone_id]
        print(f"\n  --- {drone_id} ---")

        def obj(x):
            st, dp, _ = sim_bomb(x, D0)
            if dp[2] <= 0:
                return 0.0
            new = st - covered
            return -len(new) * 0.02

        result = differential_evolution(
            obj, bounds, seed=42, maxiter=150, popsize=15, polish=True
        )
        dur_new = -result.fun
        if dur_new < 0.05:
            print(f"  未找到可行弹道，跳过")
            continue

        ang, speed, t_rel, t_del = result.x
        st, dp, t_det = sim_bomb(result.x, D0)
        new_times = st - covered
        covered.update(st)

        heading = np.array([np.cos(ang), np.sin(ang), 0.0])
        rp = D0 + speed * heading * t_rel

        print(f"  新增遮蔽: {len(new_times)*0.02:.2f}s  "
              f"角={np.degrees(ang):.0f}° 速={speed:.0f}m/s")

        results.append({
            '无人机': drone_id, '飞行方向角(°)': round(np.degrees(ang),1),
            '飞行速度(m/s)': speed, '投放时刻(s)': round(t_rel,4),
            '投放点X(m)': round(rp[0],1), '投放点Y(m)': round(rp[1],1),
            '投放点Z(m)': round(rp[2],1), '起爆延迟(s)': round(t_del,4),
            '起爆点X(m)': round(dp[0],1), '起爆点Y(m)': round(dp[1],1),
            '起爆点Z(m)': round(dp[2],1), '有效遮蔽时长(s)': round(len(new_times)*0.02,4),
        })

    total = len(covered) * 0.02
    print(f"\n  总遮蔽: {total:.2f}s")
    pd.DataFrame(results).to_excel('paper_output/results/result2.xlsx', index=False)
    print("  → result2.xlsx 已保存")
    return total


def solve_q5_de():
    """Q5: 差分进化 + 目标均衡分配 → M1/M2/M3"""
    print("\n" + "=" * 60)
    print("Q5: 差分进化优化 5机×≤3弹 → M1/M2/M3")
    print("=" * 60)

    bounds = Bounds([-np.pi, 70, 0.5, 0.5], [np.pi, 140, 30, 17])
    drones = ['FY1', 'FY2', 'FY3', 'FY4', 'FY5']
    missiles = ['M1', 'M2', 'M3']
    covered = {m: set() for m in missiles}
    results = []

    for drone_id in drones:
        D0 = DRONES[drone_id]
        # 选择当前最需要覆盖的导弹（遮蔽最少）
        target = min(missiles, key=lambda m: len(covered[m]))
        print(f"\n  {drone_id} → {target} (当前覆盖: {len(covered[target])*0.02:.1f}s)")

        used_rels = []
        for b in range(3):
            def obj(x):
                if any(abs(x[2] - ur) < BOMB_INTERVAL for ur in used_rels):
                    return 0.0
                st, dp, _ = sim_bomb(x, D0, target)
                if dp[2] <= 0:
                    return 0.0
                new = st - covered[target]
                return -len(new) * 0.02

            result = differential_evolution(
                obj, bounds, seed=42+b, maxiter=100, popsize=12, polish=False
            )
            dur_new = -result.fun
            if dur_new < 0.05:
                break

            ang, speed, t_rel, t_del = result.x
            st, dp, t_det = sim_bomb(result.x, D0, target)
            new_times = st - covered[target]
            covered[target].update(st)
            used_rels.append(t_rel)

            heading = np.array([np.cos(ang), np.sin(ang), 0.0])
            rp = D0 + speed * heading * t_rel

            print(f"    弹{b+1}: 新增={len(new_times)*0.02:.2f}s  "
                  f"角={np.degrees(ang):.0f}° 速={speed:.0f}m/s 投t={t_rel:.1f}s")

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

    print("\n  汇总:")
    total = 0
    for m in missiles:
        d = len(covered[m]) * 0.02
        print(f"    {m}: {d:.2f}s")
        total += d
    print(f"  总遮蔽: {total:.2f}s")

    pd.DataFrame(results).to_excel('paper_output/results/result3.xlsx', index=False)
    print("  → result3.xlsx 已保存")
    return total


# ============================================================
if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

    print("2025 CUMCM A题 优化求解器 v2")
    print("方法: 差分进化(DE) + BFGS + 贪心序列")
    print("=" * 60)

    q1 = solve_q1()
    q2 = solve_q2_de()
    q3 = solve_q3_de()
    q4 = solve_q4_de()
    q5 = solve_q5_de()

    print("\n" + "=" * 60)
    print("求解完成!")
    print(f"Q1={q1['duration']:.2f}s  Q2={q2['max_duration']:.2f}s  "
          f"Q3={q3:.2f}s  Q4={q4:.2f}s  Q5={q5:.2f}s")
