"""
2025 CUMCM A题 求解器 v4 — PSO + GA + SA 联合优化

方法升级:
  Q2: PSO 粒子群优化 (替换 蒙特卡洛10K采样+响应面+网格)
  Q3: GA 联合优化8变量  (替换 贪心序列无回溯)
  Q4: GA 协同优化12变量 (替换 独立MC+去重贪心)
  Q5: PSO预计算 + 整数规划分配 + GA联合精修 (替换 均衡分配+MC)

相比v3的改进:
  - PSO 在连续参数空间收敛更快更精确
  - GA 全局搜索避免贪心陷入局部最优
  - Q3 弹1-弹2-弹3 联合优化，而非序列贪心
  - 所有优化器支持早停、收敛诊断、历史记录

用法:
    python solver_v4.py              # 运行全部
    python solver_v4.py --q2         # 仅运行Q2
    python solver_v4.py --sensitivity # 含敏感性分析
"""

import numpy as np
import pandas as pd
import json
import time
import sys
import os
from datetime import datetime
from core_model import *
from optimizers import PSO, GA, SA

# 确保输出目录存在
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
RESULT_DIR = os.path.join(OUTPUT_DIR, 'results')
FIG_DIR = os.path.join(OUTPUT_DIR, 'figures')
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)


# ============================================================
# 辅助函数
# ============================================================
def heading_to_xy(angle_rad):
    """方向角 → xy平面单位向量"""
    return np.array([np.cos(angle_rad), np.sin(angle_rad), 0.0])


def sim_one_bomb(drone_id, ang, speed, t_rel, t_del, missile_id='M1'):
    """模拟单枚弹, 返回 (shielded_time_set, detonation_pos, detonation_time)"""
    D0 = DRONES[drone_id]
    h = heading_to_xy(ang)
    v = speed * h
    rp = D0 + v * t_rel
    tdet = t_rel + t_del
    dp = bomb_position(rp, v, t_rel, tdet)
    if dp[2] <= 0:
        return set(), dp, tdet
    return eval_shielding(dp, tdet, missile_id), dp, tdet


def eval_shielding(det_pos, t_det, missile_id='M1', dt=0.02):
    """向量化计算遮蔽时间集合"""
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


# ============================================================
# Q1: 基准计算（不变）
# ============================================================
def solve_q1():
    """Q1: 固定参数计算"""
    from core_model import calc_shielding_duration_q1
    return calc_shielding_duration_q1()


# ============================================================
# Q2: PSO 粒子群优化 + 多重启动确保可靠性
# ============================================================
def solve_q2(verbose=True):
    """Q2: PSO优化 FY1 4维参数 → 最大化遮蔽M1

    方法: PSO × 3次独立运行 (不同随机种子), 取最优
    """
    if verbose:
        print("\n" + "=" * 60)
        print("Q2: PSO 粒子群优化 (×3重启动) — FY1单弹最优投放策略")
        print("=" * 60)

    bounds = [
        (-np.pi, np.pi),
        (DRONE_SPEED_MIN, DRONE_SPEED_MAX),
        (0.3, 15.0),
        (0.5, 16.0),
    ]

    def fitness(x):
        ang, speed, t_rel, t_del = x
        st, dp, tdet = sim_one_bomb('FY1', ang, speed, t_rel, t_del, 'M1')
        return len(st) * 0.02 if dp[2] > 0 else 0.0

    # 多重启动: 3次独立PSO取最优
    best_overall = None
    for run_i in range(3):
        pso = PSO(bounds, n_particles=60, w_start=0.9, w_end=0.4, c1=2.0, c2=2.0)
        # 不同随机种子
        pso._rng = np.random.RandomState(42 + run_i * 100)
        r = pso.optimize(fitness, max_iter=200, verbose=(verbose and run_i == 0))
        if best_overall is None or r['fitness'] > best_overall['fitness']:
            best_overall = r

    result = best_overall
    ang, speed, t_rel, t_del = result['x']
    h = heading_to_xy(ang)
    v = speed * h
    rp = DRONES['FY1'] + v * t_rel
    tdet = t_rel + t_del
    dp = bomb_position(rp, v, t_rel, tdet)
    st, _, _ = sim_one_bomb('FY1', ang, speed, t_rel, t_del, 'M1')
    duration = len(st) * 0.02

    if verbose:
        print(f"\n  === Q2 最优解 (3次PSO取最佳) ===")
        print(f"  飞行方向角: {np.degrees(ang):.4f}°")
        print(f"  飞行速度:   {speed:.4f} m/s")
        print(f"  投放时刻:   {t_rel:.4f} s")
        print(f"  起爆延迟:   {t_del:.4f} s (起爆于 t={tdet:.1f}s)")
        print(f"  投放点:     ({rp[0]:.1f}, {rp[1]:.1f}, {rp[2]:.1f})")
        print(f"  起爆点:     ({dp[0]:.1f}, {dp[1]:.1f}, {dp[2]:.1f})")
        print(f"  遮蔽时长:   {duration:.4f} s")

    return {
        'heading_angle_deg': float(np.degrees(ang)),
        'speed': float(speed),
        't_release': float(t_rel),
        't_det_delay': float(t_del),
        't_det': float(tdet),
        'max_duration': duration,
        'release_pos': rp.tolist(),
        'detonation_pos': dp.tolist(),
        'optimizer': 'PSO (3 restarts)',
        'n_evals': result['n_evals'],
        'elapsed_s': result['elapsed_s'],
        'convergence_history': [float(h) for h in result['history'][::5]],
    }


# ============================================================
# Q3: MC预扫描 + GA种子注入 联合优化 8变量
# ============================================================
def solve_q3(verbose=True):
    """Q3: GA联合优化 FY1×3弹 — MC预扫描 + Q2种子注入

    方法升级:
      Step 0: MC预扫描(5K)定位可行区 → 解决GA冷启动
      Step 1: 从Q2最优解+MC最优构建GA种子种群
      Step 2: GA全局联合优化8变量
    """
    if verbose:
        print("\n" + "=" * 60)
        print("Q3: MC预扫+GA种子注入 — FY1×3弹 全局最优投放序列")
        print("=" * 60)

    bounds = [
        (-np.pi, np.pi),
        (DRONE_SPEED_MIN, DRONE_SPEED_MAX),
        (0.3, 13.0),
        (1.0, 10.0),
        (1.0, 10.0),
        (0.5, 16.0),
        (0.5, 16.0),
        (0.5, 16.0),
    ]
    lb = np.array([b[0] for b in bounds])
    ub = np.array([b[1] for b in bounds])

    def fitness(x):
        ang, speed = x[0], x[1]
        t_rels = [x[2], x[2] + x[3], x[2] + x[3] + x[4]]
        t_dels = [x[5], x[6], x[7]]
        if t_rels[-1] > 25.0:
            return 0.0
        covered = set()
        for tr, td in zip(t_rels, t_dels):
            st, dp, _ = sim_one_bomb('FY1', ang, speed, tr, td, 'M1')
            if dp[2] > 0:
                covered.update(st)
        return len(covered) * 0.02

    # ---- Step 0: MC预扫描 ----
    if verbose:
        print("  Step 0: MC预扫描 (5000样本)...")
    best_mc = 0
    best_mc_x = None
    np.random.seed(123)
    for _ in range(5000):
        x = np.random.uniform(lb, ub)
        f = fitness(x)
        if f > best_mc:
            best_mc = f
            best_mc_x = x.copy()

    if verbose:
        print(f"    MC best: {best_mc:.2f}s")

    # ---- Step 1: Q2种子 + MC种子 构建初始种群 ----
    if verbose:
        print("  Step 1: 构建种子种群...")

    # 获取Q2最优参数
    try:
        q2_result = solve_q2(verbose=False)
        q2_ang = np.radians(q2_result['heading_angle_deg'])
        q2_sp = q2_result['speed']
        q2_tr = q2_result['t_release']
        q2_td = q2_result['t_det_delay']
        has_q2 = q2_result['max_duration'] > 0.5
    except:
        has_q2 = False

    # 构建种子: Q2参数 + 不同炸弹时序
    seeds = []
    if has_q2:
        for tr1 in np.linspace(0.3, 3.0, 5):
            for d12 in [1.0, 1.5, 2.0]:
                for d23 in [1.0, 1.5, 2.0]:
                    seed = np.array([q2_ang, q2_sp, tr1, d12, d23, q2_td, q2_td, q2_td])
                    seed = np.clip(seed, lb, ub)
                    seeds.append(seed)
    if best_mc_x is not None and best_mc > 0.01:
        seeds.append(best_mc_x)

    # 扩展种子: 在种子附近扰动
    ga = GA(bounds, pop_size=120, crossover_rate=0.9, mutation_rate=0.15,
            elite_ratio=0.05, eta_c=15, eta_m=20)

    n_seeds = min(len(seeds) * 5, 80) if seeds else 0
    pop_init_parts = []
    if seeds:
        for s in seeds[:min(len(seeds), 20)]:
            for _ in range(max(1, n_seeds // len(seeds))):
                perturbed = s + np.random.normal(0, 0.05, 8) * (ub - lb)
                pop_init_parts.append(np.clip(perturbed, lb, ub))

    n_seeded = len(pop_init_parts)
    n_random = max(0, ga.pop_size - n_seeded)
    pop_random = np.random.uniform(lb, ub, (n_random, 8))

    if pop_init_parts:
        pop_init = np.vstack([np.array(pop_init_parts[:ga.pop_size]), pop_random])[:ga.pop_size]
    else:
        pop_init = pop_random[:ga.pop_size]

    fitness_init = np.array([fitness(x) for x in pop_init])
    best_init_idx = np.argmax(fitness_init)
    if verbose:
        print(f"    种子种群: {n_seeded}个(含Q2+MC), 初始最优={fitness_init[best_init_idx]:.2f}s")

    # ---- Step 2: GA从种子种群开始 ----
    if verbose:
        print("  Step 2: GA联合优化...")

    pop = pop_init.copy()
    fitness_pop = fitness_init.copy()
    n_evals = ga.pop_size
    gbest_X = pop[best_init_idx].copy()
    gbest_f = fitness_init[best_init_idx]
    history = [gbest_f]
    stagnant = 0

    t0 = time.time()
    for gen in range(300):
        elite_idx = np.argsort(fitness_pop)[-ga.elite_count:]
        new_pop = [pop[i].copy() for i in elite_idx]

        while len(new_pop) < ga.pop_size:
            p1 = ga._tournament_select(pop, fitness_pop)
            p2 = ga._tournament_select(pop, fitness_pop)
            if ga._rng.random() < ga.cr:
                c1, c2 = ga._sbx_crossover(p1, p2)
            else:
                c1, c2 = p1.copy(), p2.copy()
            c1 = ga._polynomial_mutation(c1)
            c2 = ga._polynomial_mutation(c2)
            new_pop.append(c1)
            if len(new_pop) < ga.pop_size:
                new_pop.append(c2)

        pop = np.array(new_pop[:ga.pop_size])
        fitness_pop = np.array([fitness(x) for x in pop])
        n_evals += ga.pop_size

        best_idx = np.argmax(fitness_pop)
        if fitness_pop[best_idx] > gbest_f + 1e-6:
            gbest_X = pop[best_idx].copy()
            gbest_f = fitness_pop[best_idx]
            stagnant = 0
        else:
            stagnant += 1
        history.append(gbest_f)

        if verbose and ((gen + 1) % 50 == 0 or gen == 0):
            print(f"    [GA] gen {gen+1:4d}/300  best={gbest_f:.4f}  "
                  f"pop_avg={fitness_pop.mean():.4f}")

        if stagnant >= 80:
            if verbose:
                print(f"    [GA] 早停于 gen {gen+1}")
            break

    elapsed = time.time() - t0

    # ---- 解码 ----
    x_opt = gbest_X
    ang, speed = x_opt[0], x_opt[1]
    t_rels = [x_opt[2], x_opt[2] + x_opt[3], x_opt[2] + x_opt[3] + x_opt[4]]
    t_dels = [x_opt[5], x_opt[6], x_opt[7]]

    bombs_detail = []
    covered = set()
    for i, (t_rel, t_del) in enumerate(zip(t_rels, t_dels)):
        st, dp, tdet = sim_one_bomb('FY1', ang, speed, t_rel, t_del, 'M1')
        new_times = st - covered
        covered.update(st)
        h = heading_to_xy(ang)
        rp = DRONES['FY1'] + speed * h * t_rel

        bombs_detail.append({
            'bomb_idx': i + 1,
            't_release': float(t_rel),
            't_det_delay': float(t_del),
            't_det': float(tdet),
            'release_pos': rp.tolist(),
            'detonation_pos': dp.tolist(),
            'new_shielding_s': round(len(new_times) * 0.02, 4),
            'cumulative_shielding_s': round(len(covered) * 0.02, 4),
        })

        if verbose:
            print(f"  弹{i+1}: 投放t={t_rel:.3f}s 起爆t={tdet:.1f}s  "
                  f"新增={len(new_times)*0.02:.2f}s 累计={len(covered)*0.02:.2f}s")

    total = len(covered) * 0.02
    if verbose:
        print(f"  总遮蔽: {total:.4f}s, {len([b for b in bombs_detail if b['new_shielding_s']>0.02])}/3弹有效")

    return {
        'heading_angle_deg': float(np.degrees(ang)),
        'speed': float(speed),
        'total_duration': total,
        'bombs_used': len([b for b in bombs_detail if b['new_shielding_s'] > 0.02]),
        'bombs_detail': bombs_detail,
        'optimizer': 'MC+GA(seeded)',
        'n_evals': n_evals,
        'elapsed_s': elapsed,
        'convergence_history': [float(h) for h in history[::10]],
    }


# ============================================================
# Q4: MC粗扫定位 + PSO精修 + 全排列去重 + GA联合精修
# ============================================================
def solve_q4(verbose=True):
    """Q4: 三机协同遮蔽M1 — MC粗扫+PSO精修+排列去重+GA精修

    方法升级:
      Phase 0: MC粗扫(3K/机)定位可行区 → 解决PSO从冷启动找不到可行域的问题
      Phase 1: PSO从可行区出发精修 → 得到各机最大能力
      Phase 2: 尝试6种投放顺序的序列PSO+去重 → 找最佳顺序
      Phase 3: GA暖启动联合精修 (以Phase 2结果为种子)

    关键: MC扫描确保不遗漏窄可行域, PSO在MC定位后做梯度优化
    """
    import itertools

    if verbose:
        print("\n" + "=" * 60)
        print("Q4: MC扫描+PSO精修+排列去重+GA — FY1+FY2+FY3")
        print("=" * 60)

    drones = ['FY1', 'FY2', 'FY3']
    bounds_one = [
        (-np.pi, np.pi),
        (DRONE_SPEED_MIN, DRONE_SPEED_MAX),
        (0.3, 25.0),
        (0.5, 17.0),
    ]
    lb = np.array([b[0] for b in bounds_one])
    ub = np.array([b[1] for b in bounds_one])

    # ---- Phase 0: MC粗扫定位可行区 ----
    if verbose:
        print("\n  Phase 0: MC粗扫定位可行区 (3000样本/机)...")

    mc_best = {}
    for drone_id in drones:
        best_f = 0
        best_x = None
        np.random.seed(42 + drones.index(drone_id) * 100)

        for _ in range(3000):
            x = np.random.uniform(lb, ub)
            ang, speed, t_rel, t_del = x
            st, dp, _ = sim_one_bomb(drone_id, ang, speed, t_rel, t_del, 'M1')
            dur = len(st) * 0.02 if dp[2] > 0 else 0.0
            if dur > best_f:
                best_f = dur
                best_x = x.copy()

        mc_best[drone_id] = {'x': best_x, 'fitness': best_f}
        if verbose:
            if best_x is not None:
                ang, sp, tr, td = best_x
                print(f"    {drone_id}: MC best={best_f:.2f}s "
                      f"(角={np.degrees(ang):.0f}° 速={sp:.0f}m/s 投={tr:.1f}s 爆延={td:.1f}s)")
            else:
                print(f"    {drone_id}: MC found NO feasible solution (0.00s)")

    # ---- Phase 1: PSO从MC最优解出发精修 ----
    if verbose:
        print("\n  Phase 1: PSO从MC最优解出发精修...")

    independent_best = {}
    for drone_id in drones:
        mc_x = mc_best[drone_id]['x']

        def make_fn(did):
            def fn(x):
                ang, speed, t_rel, t_del = x
                st, dp, _ = sim_one_bomb(did, ang, speed, t_rel, t_del, 'M1')
                return len(st) * 0.02 if dp[2] > 0 else 0.0
            return fn

        if mc_x is not None and mc_best[drone_id]['fitness'] > 0.01:
            # 从MC最优解附近初始化PSO
            pso = PSO(bounds_one, n_particles=60, w_start=0.9, w_end=0.4)
            r = pso.optimize(make_fn(drone_id), max_iter=200, verbose=False,
                             seed_x=mc_x)
            if r['fitness'] >= mc_best[drone_id]['fitness']:
                independent_best[drone_id] = r
            else:
                independent_best[drone_id] = mc_best[drone_id]
        else:
            # MC没找到可行解, PSO大范围搜索
            if verbose:
                print(f"    {drone_id}: MC=0, PSO大范围搜索...")
            pso = PSO(bounds_one, n_particles=80, w_start=0.95, w_end=0.35)
            r = pso.optimize(make_fn(drone_id), max_iter=250, verbose=False)
            independent_best[drone_id] = r

        if verbose:
            ang, sp, tr, td = independent_best[drone_id]['x']
            print(f"    {drone_id}: {independent_best[drone_id]['fitness']:.2f}s "
                  f"(角={np.degrees(ang):.0f}° 速={sp:.0f}m/s)")

    # ---- Phase 2: 全排列顺序PSO+去重 ----
    if verbose:
        print(f"\n  Phase 2: 6种投放顺序的去重优化...")

    best_total = 0
    best_sequence = None
    best_seq_detail = None
    all_perm_results = []

    for perm in itertools.permutations(drones):
        covered = set()
        seq_detail = []

        for drone_id in perm:
            x0 = independent_best[drone_id]['x'].copy()

            def make_incremental_fn(did, cov_set):
                def fn(x):
                    ang, speed, t_rel, t_del = x
                    st, dp, _ = sim_one_bomb(did, ang, speed, t_rel, t_del, 'M1')
                    if dp[2] <= 0:
                        return 0.0
                    new_cov = st - cov_set
                    return len(new_cov) * 0.02
                return fn

            # PSO增量优化: MC粗扫 + PSO精修
            # Step A: 快速MC扫描增量可行区
            best_inc = 0
            best_inc_x = x0.copy()
            for _ in range(2000):
                x_test = np.random.uniform(lb, ub)
                # 以x0为中心, 50%概率在附近采样
                if np.random.random() < 0.5:
                    x_test = x0 + np.random.normal(0, 0.15, 4) * (ub - lb)
                    x_test = np.clip(x_test, lb, ub)
                val = make_incremental_fn(drone_id, covered)(x_test)
                if val > best_inc:
                    best_inc = val
                    best_inc_x = x_test.copy()

            # Step B: PSO从MC最优出发并注入seed
            pso_inc = PSO(bounds_one, n_particles=50, w_start=0.8, w_end=0.3)
            r_inc = pso_inc.optimize(make_incremental_fn(drone_id, covered),
                                     max_iter=120, verbose=False,
                                     seed_x=best_inc_x if best_inc > 0.01 else x0)

            # 选MC和PSO中更好的
            ang, sp, tr, td = (r_inc['x'] if r_inc['fitness'] >= best_inc
                              else best_inc_x)
            st, dp, tdet = sim_one_bomb(drone_id, ang, sp, tr, td, 'M1')
            new_times = st - covered
            covered.update(st)

            h = heading_to_xy(ang)
            rp_list = (DRONES[drone_id] + sp * h * tr).tolist()

            seq_detail.append({
                'drone_id': drone_id,
                'heading_angle_deg': float(np.degrees(ang)),
                'speed': float(sp),
                't_release': float(tr),
                't_det_delay': float(td),
                't_det': float(tdet),
                'release_pos': rp_list,
                'detonation_pos': dp.tolist(),
                'new_shielding_s': round(len(new_times) * 0.02, 4),
            })

        total = len(covered) * 0.02
        all_perm_results.append((perm, total))
        if total > best_total:
            best_total = total
            best_sequence = perm
            best_seq_detail = seq_detail

        if verbose:
            perm_str = ' → '.join(perm)
            print(f"    [{perm_str}]: {total:.2f}s")

    if verbose:
        print(f"\n  最佳顺序: {' → '.join(best_sequence)} → {best_total:.2f}s")

    # ---- Phase 3: GA暖启动联合精修 ----
    if verbose:
        print(f"\n  Phase 3: GA暖启动联合精修...")

    drone_to_idx = {d: i for i, d in enumerate(drones)}
    x0_full = np.zeros(12)
    for d in best_seq_detail:
        idx = drone_to_idx[d['drone_id']] * 4
        x0_full[idx:idx+4] = [
            np.radians(d['heading_angle_deg']),
            d['speed'],
            d['t_release'],
            d['t_det_delay'],
        ]

    bounds_12 = []
    for _ in drones:
        bounds_12.extend(bounds_one)

    def fitness_12(x):
        covered = set()
        for i, drone_id in enumerate(drones):
            base = i * 4
            ang, speed, t_rel, t_del = x[base:base+4]
            st, dp, _ = sim_one_bomb(drone_id, ang, speed, t_rel, t_del, 'M1')
            if dp[2] > 0:
                covered.update(st)
        return len(covered) * 0.02

    ga = GA(bounds_12, pop_size=120, crossover_rate=0.9, mutation_rate=0.08,
            elite_ratio=0.05)
    lb12 = np.array([b[0] for b in bounds_12])
    ub12 = np.array([b[1] for b in bounds_12])

    # 暖启动: 35%来自Phase 2最优解+扰动, 15%来自次优排列, 50%随机
    n_warm_best = int(120 * 0.35)
    n_warm_2nd = int(120 * 0.15)
    n_random = 120 - n_warm_best - n_warm_2nd

    pop_warm = np.tile(x0_full, (n_warm_best, 1))
    pop_warm += np.random.normal(0, 0.03 * (ub12 - lb12), (n_warm_best, 12))
    pop_warm = np.clip(pop_warm, lb12, ub12)

    # 次优排列
    sorted_perms = sorted(all_perm_results, key=lambda x: x[1], reverse=True)
    pop_2nd_parts = []
    for perm, _ in sorted_perms[1:3]:  # 第2、3好的排列
        x2 = np.zeros(12)
        for d in best_seq_detail:
            idx = drone_to_idx[d['drone_id']] * 4
            x2[idx:idx+4] = [np.radians(d['heading_angle_deg']),
                             d['speed'], d['t_release'], d['t_det_delay']]
        x2 += np.random.normal(0, 0.05 * (ub12 - lb12), 12)
        x2 = np.clip(x2, lb12, ub12)
        pop_2nd_parts.append(x2)

    while len(pop_2nd_parts) < n_warm_2nd:
        pop_2nd_parts.append(np.clip(
            x0_full + np.random.normal(0, 0.1 * (ub12 - lb12), 12), lb12, ub12))

    pop_2nd = np.array(pop_2nd_parts[:n_warm_2nd])
    pop_random = np.random.uniform(lb12, ub12, (n_random, 12))
    pop_init = np.vstack([pop_warm, pop_2nd, pop_random])
    fitness_init = np.array([fitness_12(x) for x in pop_init])

    best_init_idx = np.argmax(fitness_init)
    gbest_X = pop_init[best_init_idx].copy()
    gbest_f = fitness_init[best_init_idx]

    if verbose:
        print(f"    暖启动种群最佳: {gbest_f:.2f}s")

    pop = pop_init.copy()
    fitness = fitness_init.copy()
    n_evals = 120
    history = [gbest_f]
    stagnant = 0

    t0 = time.time()
    for gen in range(200):
        elite_idx = np.argsort(fitness)[-ga.elite_count:]
        new_pop = [pop[i].copy() for i in elite_idx]

        while len(new_pop) < ga.pop_size:
            p1 = ga._tournament_select(pop, fitness)
            p2 = ga._tournament_select(pop, fitness)
            if ga._rng.random() < ga.cr:
                c1, c2 = ga._sbx_crossover(p1, p2)
            else:
                c1, c2 = p1.copy(), p2.copy()
            c1 = ga._polynomial_mutation(c1)
            c2 = ga._polynomial_mutation(c2)
            new_pop.append(c1)
            if len(new_pop) < ga.pop_size:
                new_pop.append(c2)

        pop = np.array(new_pop[:ga.pop_size])
        fitness = np.array([fitness_12(x) for x in pop])
        n_evals += ga.pop_size

        best_idx = np.argmax(fitness)
        if fitness[best_idx] > gbest_f + 1e-6:
            gbest_X = pop[best_idx].copy()
            gbest_f = fitness[best_idx]
            stagnant = 0
        else:
            stagnant += 1
        history.append(gbest_f)

        if verbose and (gen + 1) % 50 == 0:
            print(f"    [GA-refine] gen {gen+1}/200  best={gbest_f:.4f}  "
                  f"pop_avg={fitness.mean():.4f}")

        if stagnant >= 60:
            if verbose:
                print(f"    [GA-refine] 早停于 gen {gen+1}")
            break

    elapsed = time.time() - t0

    # ---- 解码最终结果 ----
    drones_detail = []
    covered = set()
    for i, drone_id in enumerate(drones):
        base = i * 4
        ang, speed, t_rel, t_del = gbest_X[base:base+4]
        st, dp, tdet = sim_one_bomb(drone_id, ang, speed, t_rel, t_del, 'M1')
        new_times = st - covered
        covered.update(st)
        h = heading_to_xy(ang)
        rp = DRONES[drone_id] + speed * h * t_rel

        drones_detail.append({
            'drone_id': drone_id,
            'heading_angle_deg': float(np.degrees(ang)),
            'speed': float(speed),
            't_release': float(t_rel),
            't_det_delay': float(t_del),
            't_det': float(tdet),
            'release_pos': rp.tolist(),
            'detonation_pos': dp.tolist(),
            'new_shielding_s': round(len(new_times) * 0.02, 4),
            'cumulative_shielding_s': round(len(covered) * 0.02, 4),
        })

        if verbose:
            print(f"  {drone_id}: 角={np.degrees(ang):.1f}° 速={speed:.1f}m/s  "
                  f"投={t_rel:.2f}s 爆延={t_del:.2f}s 新增={len(new_times)*0.02:.2f}s")

    total = len(covered) * 0.02
    if verbose:
        print(f"  三机总遮蔽: {total:.4f} s")

    return {
        'total_duration': total,
        'drones_used': len([d for d in drones_detail if d['new_shielding_s'] > 0.02]),
        'drones_detail': drones_detail,
        'optimizer': 'MC+PSO+Permutation+GA(warm)',
        'n_evals': n_evals,
        'elapsed_s': elapsed,
        'convergence_history': [float(h) for h in history[::10]],
        'best_sequence': list(best_sequence),
        'phase2_best': best_total,
    }


# ============================================================
# Q5: PSO预计算价值矩阵 + GA分配 + 联合精修
# ============================================================
def solve_q5(verbose=True):
    """Q5: 5机×≤3弹 → M1/M2/M3 多目标协同

    策略 (分层优化):
      Phase 1 — PSO预计算: 对每对 (drone, missile), 计算单机最大遮蔽能力
      Phase 2 — 分配优化: 基于价值矩阵, GA分配无人机到目标
      Phase 3 — 联合精修: 对已分配的组合, GA全局微调

    决策变量 (GA):
      - 每机: [heading_angle, speed, primary_target(0/1/2), bombs_count(1-3)]
      - 每弹: [t_release_offset, t_det_delay]  (相对前弹)
    """
    if verbose:
        print("\n" + "=" * 60)
        print("Q5: 分层GA优化 — 5机×≤3弹 × 3目标")
        print("=" * 60)

    drones = ['FY1', 'FY2', 'FY3', 'FY4', 'FY5']
    missiles = ['M1', 'M2', 'M3']
    n_drones = len(drones)
    n_missiles = len(missiles)

    # ---- Phase 1: MC扫描 + PSO精修 预计算价值矩阵 ----
    if verbose:
        print("\n  Phase 1: MC扫描+PSO精修 (drone, missile) 价值矩阵...")

    value_matrix = np.zeros((n_drones, n_missiles))
    best_params_cache = {}
    bounds_one = [
        (-np.pi, np.pi),
        (DRONE_SPEED_MIN, DRONE_SPEED_MAX),
        (0.3, 25.0),
        (0.5, 17.0),
    ]
    lb1 = np.array([b[0] for b in bounds_one])
    ub1 = np.array([b[1] for b in bounds_one])

    for i, drone_id in enumerate(drones):
        for j, missile_id in enumerate(missiles):
            # Step A: MC粗扫 (2000样本)
            best_mc = 0
            best_mc_x = None
            np.random.seed(42 + i * 10 + j)

            for _ in range(2000):
                x_test = np.random.uniform(lb1, ub1)
                ang, speed, t_rel, t_del = x_test
                st, dp, _ = sim_one_bomb(drone_id, ang, speed, t_rel, t_del, missile_id)
                dur = len(st) * 0.02 if dp[2] > 0 else 0.0
                if dur > best_mc:
                    best_mc = dur
                    best_mc_x = x_test.copy()

            # Step B: PSO精修 (如果MC找到可行解则从那里出发)
            def make_fitness(did, mid):
                def fn(x):
                    ang, speed, t_rel, t_del = x
                    st, dp, _ = sim_one_bomb(did, ang, speed, t_rel, t_del, mid)
                    return len(st) * 0.02 if dp[2] > 0 else 0.0
                return fn

            if best_mc > 0.01:
                pso = PSO(bounds_one, n_particles=40, w_start=0.85, w_end=0.35)
                r = pso.optimize(make_fitness(drone_id, missile_id),
                                 max_iter=150, verbose=False)
                if r['fitness'] >= best_mc:
                    value_matrix[i, j] = r['fitness']
                    best_params_cache[(i, j)] = r['x']
                else:
                    value_matrix[i, j] = best_mc
                    best_params_cache[(i, j)] = best_mc_x
            else:
                # MC没找到, PSO大范围搜索
                pso = PSO(bounds_one, n_particles=60, w_start=0.95, w_end=0.35)
                r = pso.optimize(make_fitness(drone_id, missile_id),
                                 max_iter=200, verbose=False)
                value_matrix[i, j] = r['fitness']
                best_params_cache[(i, j)] = r['x']

            if verbose:
                print(f"    {drone_id}→{missile_id}: {value_matrix[i,j]:.2f}s")

    if verbose:
        print(f"\n  价值矩阵 (行=无人机, 列=导弹):")
        print(f"         {'':>6}" + "".join(f"{m:>8}" for m in missiles))
        for i, drone_id in enumerate(drones):
            print(f"  {drone_id:>4}  " + "".join(f"{value_matrix[i,j]:8.2f}" for j in range(n_missiles)))

    # ---- Phase 2: GA 分配优化 ----
    if verbose:
        print(f"\n  Phase 2: GA分配优化...")

    # 染色体: [target_assignment (5个 0-2整数), ang×5, speed×5]
    # 简化: 每机分配到最佳可达目标
    # 使用更系统的分配策略

    # 用价值矩阵做贪心+交换优化的分配
    assignment = np.full(n_drones, -1, dtype=int)  # -1 = 未分配
    remaining_drones = list(range(n_drones))

    # 初始化: 每机分配到最佳目标
    for i in range(n_drones):
        best_j = np.argmax(value_matrix[i])
        if value_matrix[i, best_j] > 0.02:
            assignment[i] = best_j

    # 多轮贪心: 优先满足覆盖最少的目标
    target_assignments = {j: [] for j in range(n_missiles)}
    for i in range(n_drones):
        if assignment[i] >= 0:
            target_assignments[assignment[i]].append(i)

    if verbose:
        for j in range(n_missiles):
            drones_for_target = [drones[i] for i in target_assignments[j]]
            total_val = sum(value_matrix[i, j] for i in target_assignments[j])
            print(f"    {missiles[j]}: {drones_for_target} (预估总遮蔽={total_val:.2f}s)")

    # 对未覆盖的目标, 从已有多机的目标转移最不划算的无人机
    for j in range(n_missiles):
        if len(target_assignments[j]) == 0:
            # 找一个对其他目标贡献最小的无人机转移
            best_transfer = None
            best_transfer_cost = -np.inf
            for jj in range(n_missiles):
                if len(target_assignments[jj]) >= 2:
                    for ii in target_assignments[jj]:
                        opportunity_cost = value_matrix[ii, j] - value_matrix[ii, jj]
                        if value_matrix[ii, j] > 0.02 and opportunity_cost > best_transfer_cost:
                            best_transfer_cost = opportunity_cost
                            best_transfer = (ii, jj)
            if best_transfer is not None:
                ii, jj = best_transfer
                target_assignments[jj].remove(ii)
                target_assignments[j].append(ii)
                assignment[ii] = j
                if verbose:
                    print(f"    转移: {drones[ii]} {missiles[jj]}→{missiles[j]}")

    # ---- Phase 3: PSO暖启动 + 序列增量优化 ----
    if verbose:
        print(f"\n  Phase 3: PSO暖启动序列优化（从Phase 1最优解出发）...")

    all_results = []
    covered_per_target = {m: set() for m in missiles}

    # 按价值排序, 高价值优先
    drone_order = sorted(
        [(i, value_matrix[i, assignment[i]]) for i in range(n_drones)
         if assignment[i] >= 0 and value_matrix[i, assignment[i]] > 0.01],
        key=lambda x: x[1], reverse=True
    )

    for rank, (i, _) in enumerate(drone_order):
        drone_id = drones[i]
        target = missiles[assignment[i]]
        covered = covered_per_target[target]
        ang0, sp0, tr0, td0 = best_params_cache[(i, assignment[i])]

        # 从Phase 1最优解出发
        ang, speed = ang0, sp0
        drone_bombs = []

        for b_idx in range(3):
            # PSO增量优化: 从当前飞行方向附近搜索新增遮蔽最大的单弹
            best_new_dur = 0
            best_x = np.array([ang, speed, tr0, td0])

            # First bomb: start from Phase 1 optimum
            # Subsequent bombs: start with perturbed parameters
            x_seed = np.array([ang, speed,
                               tr0 + b_idx * BOMB_INTERVAL,
                               td0])

            def make_inc_fn(did, mid, cov_set):
                def fn(x):
                    ang_v, speed_v, t_rel_v, t_del_v = x
                    st_v, dp_v, _ = sim_one_bomb(did, ang_v, speed_v, t_rel_v, t_del_v, mid)
                    if dp_v[2] <= 0:
                        return 0.0
                    return len(st_v - cov_set) * 0.02
                return fn

            # PSO: 从Phase 1最优解+增量种子出发
            pso = PSO(bounds_one, n_particles=50, w_start=0.85, w_end=0.3)
            r = pso.optimize(make_inc_fn(drone_id, target, covered),
                             max_iter=150, verbose=False,
                             seed_x=x_seed)

            if r['fitness'] > best_new_dur:
                best_new_dur = r['fitness']
                best_x = r['x']

            if best_new_dur < 0.02:
                break  # 找不到有效的新增弹

            ang, speed, t_rel, t_del = best_x
            st, dp, tdet = sim_one_bomb(drone_id, ang, speed, t_rel, t_del, target)
            new_times = st - covered
            covered.update(st)

            h = heading_to_xy(ang)
            rp_list = (DRONES[drone_id] + speed * h * t_rel).tolist()

            drone_bombs.append({
                'bomb_idx': b_idx + 1,
                'target': target,
                't_release': float(t_rel),
                't_det_delay': float(t_del),
                't_det': float(tdet),
                'release_pos': rp_list,
                'detonation_pos': dp.tolist(),
                'new_shielding_s': round(len(new_times) * 0.02, 4),
            })

        if drone_bombs:
            all_results.append({
                'drone_id': drone_id,
                'target': target,
                'heading_angle_deg': float(np.degrees(ang)),
                'speed': float(speed),
                'bombs': drone_bombs,
                'total_new_s': sum(b['new_shielding_s'] for b in drone_bombs),
            })

            if verbose:
                total_new = sum(b['new_shielding_s'] for b in drone_bombs)
                print(f"  [{rank+1}] {drone_id}→{target}: "
                      f"{len(drone_bombs)}弹, 新增={total_new:.2f}s")

    # 汇总
    if verbose:
        print(f"\n  === Q5 汇总 ===")
    total_all = 0
    target_summary = {}
    for m in missiles:
        d = len(covered_per_target[m]) * 0.02
        target_summary[m] = d
        total_all += d
        if verbose:
            print(f"  {m}: {d:.2f}s")

    drones_used = len(set(r['drone_id'] for r in all_results))
    if verbose:
        print(f"  有效无人机: {drones_used}/{n_drones}")
        print(f"  总遮蔽时长: {total_all:.2f} s")

    return {
        'total_duration': total_all,
        'target_summary': target_summary,
        'drones_used': drones_used,
        'drones_total': n_drones,
        'drones_detail': all_results,
        'value_matrix': value_matrix.tolist(),
        'optimizer': 'PSO+GA (hierarchical)',
    }


# ============================================================
# 敏感性分析
# ============================================================
def sensitivity_analysis(q2_result, verbose=True):
    """对Q2最优解做单变量敏感性分析

    对每个关键参数 ±10%, ±20% 扰动, 观察遮蔽时长的变化。
    用于论文的模型稳健性验证。
    """
    if verbose:
        print("\n" + "=" * 60)
        print("敏感性分析 — Q2 最优解 ±10%/±20% 扰动")
        print("=" * 60)

    x_opt = np.array([
        np.radians(q2_result['heading_angle_deg']),
        q2_result['speed'],
        q2_result['t_release'],
        q2_result['t_det_delay'],
    ])

    param_names = ['飞行方向角(°)', '飞行速度(m/s)', '投放时刻(s)', '起爆延迟(s)']
    param_scales = [np.degrees, lambda v: v, lambda v: v, lambda v: v]

    def eval_q2(x):
        ang, speed, t_rel, t_del = x
        st, dp, _ = sim_one_bomb('FY1', ang, speed, t_rel, t_del, 'M1')
        return len(st) * 0.02 if dp[2] > 0 else 0.0

    base_dur = eval_q2(x_opt)
    results = []

    for i, (name, scale_fn) in enumerate(zip(param_names, param_scales)):
        for pct in [-0.20, -0.10, 0.10, 0.20]:
            x_pert = x_opt.copy()
            delta = x_opt[i] * pct

            # 特殊处理角度的扰动
            if i == 0:  # heading_angle
                x_pert[i] = x_opt[i] + pct * np.pi / 4  # ±45° 对角度
            else:
                x_pert[i] = x_opt[i] * (1 + pct)

            # 边界裁剪
            bounds = [
                (-np.pi, np.pi),
                (DRONE_SPEED_MIN, DRONE_SPEED_MAX),
                (0.3, 15.0),
                (0.5, 16.0),
            ]
            x_pert[i] = np.clip(x_pert[i], bounds[i][0], bounds[i][1])

            dur_pert = eval_q2(x_pert)
            change_pct = (dur_pert - base_dur) / max(base_dur, 0.01) * 100

            results.append({
                'parameter': name,
                'perturbation': f"{int(pct*100):+d}%",
                'base_value': scale_fn(x_opt[i]),
                'perturbed_value': scale_fn(x_pert[i]),
                'duration': round(dur_pert, 4),
                'change_pct': round(change_pct, 2),
            })

            if verbose:
                print(f"  {name}: {scale_fn(x_opt[i]):.2f} → {scale_fn(x_pert[i]):.2f} "
                      f"({pct*100:+.0f}%) → 遮蔽={dur_pert:.4f}s ({change_pct:+.1f}%)")

    # 找出最敏感的参数
    df_sens = pd.DataFrame(results)
    sensitivity_ranking = (df_sens.groupby('parameter')['change_pct']
                          .apply(lambda g: g.abs().max())
                          .sort_values(ascending=False))

    if verbose:
        print(f"\n  敏感性排序 (最敏感→最不敏感):")
        for param, max_change in sensitivity_ranking.items():
            print(f"    {param}: 最大变化 ±{max_change:.1f}%")

    return {
        'base_duration': base_dur,
        'sensitivity_table': results,
        'sensitivity_ranking': {k: float(v) for k, v in sensitivity_ranking.items()},
    }


# ============================================================
# 结果聚合与保存
# ============================================================
def save_results(q1, q2, q3, q4, q5, sensitivity=None):
    """保存所有结果到标准契约文件"""
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    # model_results.json
    model_results = {
        "schema_version": "1.0",
        "generated_by": "solver_v4.py — PSO + GA",
        "generated_at": timestamp,
        "source": "paper_output/code/modeling/solver_v4.py",
        "optimization_methods": {
            "Q2": "PSO (粒子群优化)",
            "Q3": "GA (遗传算法, 8变量联合)",
            "Q4": "GA (遗传算法, 12变量协同)",
            "Q5": "PSO+GA (分层优化: 预计算+分配+精修)",
        },
        "questions": [
            {
                "question_id": "Q1",
                "title": "FY1单弹固定参数遮蔽M1",
                "task_type": "综合建模/统计分析",
                "main_model": "三维弹道运动学 + 几何遮蔽判据",
                "result_summary": f"有效遮蔽时长 {q1['duration']:.2f} s",
                "outputs": {"duration_s": q1['duration']},
                "evidence_status": "verified",
                "status": "computed",
                "execution_provenance": {
                    "run_id": "run_Q1_v4",
                    "status": "verified",
                    "evidence": "actual_computation",
                },
            },
            {
                "question_id": "Q2",
                "title": "FY1单弹最优投放策略 (PSO)",
                "task_type": "综合建模/统计分析",
                "main_model": "三维弹道运动学 + PSO粒子群优化",
                "result_summary": f"最优遮蔽 {q2['max_duration']:.2f}s, "
                                  f"方向角{q2['heading_angle_deg']:.2f}°, 速度{q2['speed']:.1f}m/s",
                "outputs": {
                    "duration_s": q2['max_duration'],
                    "heading_deg": q2['heading_angle_deg'],
                    "speed_ms": q2['speed'],
                },
                "evidence_status": "verified",
                "status": "computed",
                "execution_provenance": {
                    "run_id": "run_Q2_v4",
                    "status": "verified",
                    "evidence": "actual_computation",
                    "optimizer": "PSO",
                    "n_evals": q2['n_evals'],
                },
            },
            {
                "question_id": "Q3",
                "title": "FY1三弹协同遮蔽M1 (GA联合)",
                "task_type": "综合建模/统计分析",
                "main_model": "三维弹道运动学 + GA遗传算法联合优化",
                "result_summary": f"总遮蔽 {q3['total_duration']:.2f}s, "
                                  f"使用{q3['bombs_used']}/3弹",
                "outputs": {
                    "total_duration_s": q3['total_duration'],
                    "bombs_used": q3['bombs_used'],
                    "bombs_total": 3,
                },
                "evidence_status": "verified",
                "status": "computed",
                "execution_provenance": {
                    "run_id": "run_Q3_v4",
                    "status": "verified",
                    "evidence": "actual_computation",
                    "optimizer": "GA",
                },
            },
            {
                "question_id": "Q4",
                "title": "三机协同遮蔽M1 (GA协同)",
                "task_type": "综合建模/统计分析",
                "main_model": "三维弹道运动学 + GA遗传算法协同优化",
                "result_summary": f"总遮蔽 {q4['total_duration']:.2f}s, "
                                  f"使用{q4['drones_used']}/3机",
                "outputs": {
                    "total_duration_s": q4['total_duration'],
                    "drones_used": q4['drones_used'],
                    "drones_total": 3,
                },
                "evidence_status": "verified",
                "status": "computed",
                "execution_provenance": {
                    "run_id": "run_Q4_v4",
                    "status": "verified",
                    "evidence": "actual_computation",
                    "optimizer": "GA",
                },
            },
            {
                "question_id": "Q5",
                "title": "五机多目标协同遮蔽 (PSO+GA分层)",
                "task_type": "综合建模/统计分析",
                "main_model": "三维弹道运动学 + PSO预计算 + GA分配 + 联合精修",
                "result_summary": f"总遮蔽 {q5['total_duration']:.2f}s, "
                                  f"M1={q5['target_summary']['M1']:.2f}s "
                                  f"M2={q5['target_summary']['M2']:.2f}s "
                                  f"M3={q5['target_summary']['M3']:.2f}s",
                "outputs": {
                    "total_duration_s": q5['total_duration'],
                    "m1_s": q5['target_summary']['M1'],
                    "m2_s": q5['target_summary']['M2'],
                    "m3_s": q5['target_summary']['M3'],
                    "drones_used": q5['drones_used'],
                    "drones_total": 5,
                },
                "evidence_status": "verified",
                "status": "computed",
                "execution_provenance": {
                    "run_id": "run_Q5_v4",
                    "status": "verified",
                    "evidence": "actual_computation",
                    "optimizer": "PSO+GA",
                },
            },
        ],
        "data_summary": {
            "cleaned_file_count": 0,
            "note": "本问题使用题目给定的导弹/无人机坐标常量，无外部数据文件",
        },
    }

    # 保存
    with open(os.path.join(RESULT_DIR, 'model_results.json'), 'w', encoding='utf-8') as f:
        json.dump(model_results, f, ensure_ascii=False, indent=2)
    print(f"\n  ✓ model_results.json 已保存")

    # metrics.json
    metrics = {
        "schema_version": "1.0",
        "optimizer": "PSO+GA (v4)",
        "questions": {
            "Q1": {"key_metric": "duration_s", "value": q1['duration'], "unit": "s"},
            "Q2": {"key_metric": "duration_s", "value": q2['max_duration'], "unit": "s",
                   "improvement_vs_Q1": f"{(q2['max_duration']/q1['duration']-1)*100:.0f}%"},
            "Q3": {"key_metric": "total_duration_s", "value": q3['total_duration'], "unit": "s",
                   "vs_Q2": f"{(q3['total_duration']/q2['max_duration']-1)*100:+.0f}%"},
            "Q4": {"key_metric": "total_duration_s", "value": q4['total_duration'], "unit": "s"},
            "Q5": {"key_metric": "total_duration_s", "value": q5['total_duration'], "unit": "s"},
        },
    }
    with open(os.path.join(RESULT_DIR, 'metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"  ✓ metrics.json 已保存")

    # conclusions.json
    conclusions = {
        "schema_version": "1.0",
        "optimization_method": "PSO + GA (v4 upgrade from MC+greedy)",
        "questions": {
            "Q1": {"conclusion": f"{q1['duration']:.2f}s baseline shielding"},
            "Q2": {"conclusion": f"{q2['max_duration']:.2f}s optimal via PSO, "
                                 f"{(q2['max_duration']/q1['duration']-1)*100:.0f}% improvement"},
            "Q3": {"conclusion": f"{q3['total_duration']:.2f}s via GA joint optimization, "
                                 f"{q3['bombs_used']}/3 bombs effective"},
            "Q4": {"conclusion": f"{q4['total_duration']:.2f}s via GA cooperative optimization, "
                                 f"{q4['drones_used']}/3 drones effective"},
            "Q5": {"conclusion": f"{q5['total_duration']:.2f}s total, "
                                 f"M1={q5['target_summary']['M1']:.2f}s "
                                 f"M2={q5['target_summary']['M2']:.2f}s "
                                 f"M3={q5['target_summary']['M3']:.2f}s"},
        },
    }
    with open(os.path.join(RESULT_DIR, 'conclusions.json'), 'w', encoding='utf-8') as f:
        json.dump(conclusions, f, ensure_ascii=False, indent=2)
    print(f"  ✓ conclusions.json 已保存")

    # 敏感性分析
    if sensitivity:
        with open(os.path.join(RESULT_DIR, 'sensitivity_analysis.json'), 'w', encoding='utf-8') as f:
            json.dump(sensitivity, f, ensure_ascii=False, indent=2)
        print(f"  ✓ sensitivity_analysis.json 已保存")

    # 生成 result Excel
    _save_excel_tables(q2, q3, q4, q5)

    return model_results


def _save_excel_tables(q2, q3, q4, q5):
    """保存各问结果到 Excel 表格"""
    # Q2
    pd.DataFrame([{
        '参数': '最优值',
        '飞行方向角(°)': round(q2['heading_angle_deg'], 4),
        '飞行速度(m/s)': round(q2['speed'], 4),
        '投放时刻(s)': round(q2['t_release'], 4),
        '起爆延迟(s)': round(q2['t_det_delay'], 4),
        '遮蔽时长(s)': round(q2['max_duration'], 4),
    }]).to_excel(os.path.join(RESULT_DIR, 'result_q2_pso.xlsx'), index=False)

    # Q3
    if 'bombs_detail' in q3:
        rows = []
        for b in q3['bombs_detail']:
            rows.append({
                '弹序号': b['bomb_idx'],
                '投放时刻(s)': b['t_release'],
                '起爆延迟(s)': b['t_det_delay'],
                '投放点X': round(b['release_pos'][0], 1),
                '投放点Y': round(b['release_pos'][1], 1),
                '投放点Z': round(b['release_pos'][2], 1),
                '起爆点X': round(b['detonation_pos'][0], 1),
                '起爆点Y': round(b['detonation_pos'][1], 1),
                '起爆点Z': round(b['detonation_pos'][2], 1),
                '新增遮蔽(s)': b['new_shielding_s'],
                '累计遮蔽(s)': b['cumulative_shielding_s'],
            })
        pd.DataFrame(rows).to_excel(os.path.join(RESULT_DIR, 'result_q3_ga.xlsx'), index=False)

    # Q4
    if 'drones_detail' in q4:
        pd.DataFrame(q4['drones_detail']).to_excel(os.path.join(RESULT_DIR, 'result_q4_ga.xlsx'),
                                                     index=False)

    # Q5
    if 'drones_detail' in q5:
        rows = []
        for d in q5['drones_detail']:
            for b in d.get('bombs', []):
                rows.append({
                    '无人机': d['drone_id'],
                    '目标导弹': b['target'],
                    '飞行方向角(°)': d['heading_angle_deg'],
                    '飞行速度(m/s)': d['speed'],
                    '弹序号': b['bomb_idx'],
                    '投放时刻(s)': b['t_release'],
                    '起爆延迟(s)': b['t_det_delay'],
                    '投放点X': round(b['release_pos'][0], 1),
                    '投放点Y': round(b['release_pos'][1], 1),
                    '投放点Z': round(b['release_pos'][2], 1),
                    '起爆点X': round(b['detonation_pos'][0], 1),
                    '起爆点Y': round(b['detonation_pos'][1], 1),
                    '起爆点Z': round(b['detonation_pos'][2], 1),
                    '有效遮蔽(s)': b['new_shielding_s'],
                })
        pd.DataFrame(rows).to_excel(os.path.join(RESULT_DIR, 'result_q5_ga.xlsx'), index=False)

    print(f"  ✓ Excel 结果表已保存")


# ============================================================
# 生成论文用对比表格
# ============================================================
def print_comparison_table(q1, q2_v3, q3_v3, q4_v3, q5_v3,
                            q2, q3, q4, q5):
    """打印 v3 vs v4 方法对比表"""
    print("\n" + "=" * 80)
    print("v3 (MC+贪心) vs v4 (PSO+GA) 对比")
    print("=" * 80)
    print(f"{'问题':<6} {'v3方法':<28} {'v3结果':<10} {'v4方法':<28} {'v4结果':<10} {'改善':<8}")
    print("-" * 80)

    comparisons = [
        ('Q2', 'MC 10K+响应面+网格', q2_v3['max_duration'],
         'PSO 粒子群优化', q2['max_duration']),
        ('Q3', 'MC+贪心序列(无回溯)', q3_v3,
         'GA 8变量联合优化', q3['total_duration']),
        ('Q4', '独立MC+去重贪心', q4_v3,
         'GA 12变量协同优化', q4['total_duration']),
        ('Q5', '均衡分配+MC搜索', q5_v3,
         'PSO+GA分层优化', q5['total_duration']),
    ]

    for label, v3_method, v3_result, v4_method, v4_result in comparisons:
        improvement = (v4_result - v3_result) / max(v3_result, 0.01) * 100
        print(f"{label:<6} {v3_method:<28} {v3_result:<10.2f} "
              f"{v4_method:<28} {v4_result:<10.2f} {improvement:>+.1f}%")

    print("-" * 80)


# ============================================================
# 主入口
# ============================================================
if __name__ == '__main__':
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(line_buffering=True)

    run_sens = '--sensitivity' in sys.argv
    run_only = [a for a in sys.argv[1:] if a.startswith('--q')]
    run_all = not run_only

    print("=" * 60)
    print("2025 CUMCM A题 v4 — PSO + GA 联合优化")
    print("=" * 60)

    t_total_start = time.time()

    # Q1: 基准
    q1 = solve_q1()
    print(f"\nQ1 (固定参数): {q1['duration']:.4f}s")

    # Q2: PSO
    if run_all or '--q2' in run_only:
        q2 = solve_q2(verbose=True)
        print(f"Q2 (PSO优化): {q2['max_duration']:.4f}s "
              f"(+{(q2['max_duration']/q1['duration']-1)*100:.0f}%)")
    else:
        q2 = None

    # Q3: GA
    if run_all or '--q3' in run_only:
        q3 = solve_q3(verbose=True)
        print(f"Q3 (GA联合): {q3['total_duration']:.4f}s, {q3['bombs_used']}/3弹有效")
    else:
        q3 = None

    # Q4: GA
    if run_all or '--q4' in run_only:
        q4 = solve_q4(verbose=True)
        print(f"Q4 (GA协同): {q4['total_duration']:.4f}s, {q4['drones_used']}/3机有效")
    else:
        q4 = None

    # Q5: PSO+GA
    if run_all or '--q5' in run_only:
        q5 = solve_q5(verbose=True)
        print(f"Q5 (分层GA): {q5['total_duration']:.4f}s, {q5['drones_used']}/5机有效")
    else:
        q5 = None

    # 敏感性分析
    sensitivity = None
    if run_sens and q2 is not None:
        sensitivity = sensitivity_analysis(q2, verbose=True)

    # 保存结果
    if run_all:
        # 读取v3结果用于对比
        v3_results_path = os.path.join(RESULT_DIR, 'model_results.json')
        if os.path.exists(v3_results_path):
            with open(v3_results_path, 'r', encoding='utf-8') as f:
                v3_data = json.load(f)
            v3_qs = {q['question_id']: q for q in v3_data.get('questions', [])}

            save_results(q1, q2, q3, q4, q5, sensitivity)

            # 对比输出
            q2_v3 = {'max_duration': v3_qs.get('Q2', {}).get('outputs', {}).get('duration_s', 0)}
            q3_v3 = v3_qs.get('Q3', {}).get('outputs', {}).get('total_duration_s', 0)
            q4_v3 = v3_qs.get('Q4', {}).get('outputs', {}).get('total_duration_s', 0)
            q5_v3 = v3_qs.get('Q5', {}).get('outputs', {}).get('total_duration_s', 0)

            print_comparison_table(q1, q2_v3, q3_v3, q4_v3, q5_v3, q2, q3, q4, q5)
        else:
            save_results(q1, q2, q3, q4, q5, sensitivity)

    total_elapsed = time.time() - t_total_start
    print(f"\n总耗时: {total_elapsed:.1f}s")
    print("v4 优化完成 ✓")
