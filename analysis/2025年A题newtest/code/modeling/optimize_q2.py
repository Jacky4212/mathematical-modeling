"""
Q2 改进优化：多起点 + 局部精化 + 物理引导初始化
"""
import numpy as np
from scipy.optimize import minimize, Bounds, differential_evolution
from core_model import *

D0 = DRONES['FY1']


def simulate_detailed(heading_angle, speed, t_release, t_det_delay):
    """详细模拟一次策略，返回遮蔽时长和起止时间"""
    heading = np.array([np.cos(heading_angle), np.sin(heading_angle), 0.0])
    drone_vel = speed * heading
    release_pos = D0 + drone_vel * t_release
    t_det = t_release + t_det_delay
    det_pos = bomb_position(release_pos, drone_vel, t_release, t_det)

    if det_pos[2] <= 0:
        return 0.0, 0, 0

    dt = 0.02
    shielded_count = 0
    t_start = None
    t_end = None
    t = t_det
    while t <= t_det + SMOKE_DURATION:
        M_pos = missile_position('M1', t)
        S_pos = smoke_center(det_pos, t_det, t)
        if is_shielded(M_pos, S_pos):
            if t_start is None:
                t_start = t
            t_end = t
            shielded_count += 1
        t += dt

    duration = shielded_count * dt
    return duration, t_start or 0, t_end or 0


def objective(x):
    return -simulate_detailed(*x)[0]


def optimize_q2_improved():
    """改进的Q2优化"""
    print("\n" + "=" * 60)
    print("Q2 改进优化：多策略")
    print("=" * 60)

    best_duration = 0
    best_result = None

    # 策略1: 朝假目标方向飞（近似Q1策略，但可调参数）
    print("\n[策略1] 朝假目标方向飞行")
    heading_to_decoy = -D0 / np.linalg.norm(D0)
    angle_to_decoy = np.arctan2(heading_to_decoy[1], heading_to_decoy[0])

    for speed in [80, 100, 120, 140]:
        for t_rel in [0.5, 1.0, 1.5, 2.0, 3.0]:
            for t_del in [1.0, 2.0, 3.6, 5.0, 7.0, 10.0]:
                dur, t1, t2 = simulate_detailed(angle_to_decoy, speed, t_rel, t_del)
                if dur > best_duration:
                    best_duration = dur
                    best_result = (angle_to_decoy, speed, t_rel, t_del, dur, t1, t2)

    print(f"  最佳: dur={best_duration:.4f}s")

    # 策略2: 朝真目标方向飞（偏一点）
    print("\n[策略2] 朝真目标方向飞行")
    T = REAL_TARGET
    to_target = T - D0
    to_target[2] = 0
    angle_to_target = np.arctan2(to_target[1], to_target[0])

    for angle_offset in np.linspace(-0.5, 0.5, 21):
        ang = angle_to_target + angle_offset
        for speed in [80, 100, 120, 140]:
            for t_rel in [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]:
                for t_del in [1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 15.0]:
                    dur, t1, t2 = simulate_detailed(ang, speed, t_rel, t_del)
                    if dur > best_duration:
                        best_duration = dur
                        best_result = (ang, speed, t_rel, t_del, dur, t1, t2)
    print(f"  最佳: dur={best_duration:.4f}s")

    # 策略3: 全角度扫描（粗粒度）
    print("\n[策略3] 全角度扫描")
    for ang in np.linspace(-np.pi, np.pi, 72):
        for speed in [80, 100, 120, 140]:
            for t_rel in [0.5, 1.0, 2.0, 3.0, 5.0, 8.0]:
                for t_del in [1.0, 3.0, 5.0, 7.0, 10.0, 15.0]:
                    dur, t1, t2 = simulate_detailed(ang, speed, t_rel, t_del)
                    if dur > best_duration:
                        best_duration = dur
                        best_result = (ang, speed, t_rel, t_del, dur, t1, t2)
    print(f"  最佳: dur={best_duration:.4f}s")

    # 策略4: 在最佳附近进行局部精细化
    print("\n[策略4] 局部精化")
    if best_result:
        ang0, sp0, tr0, td0, _, _, _ = best_result

        def local_obj(x):
            return -simulate_detailed(x[0], x[1], x[2], x[3])[0]

        for _ in range(20):
            x0 = np.array([
                ang0 + np.random.uniform(-0.3, 0.3),
                np.clip(sp0 + np.random.uniform(-20, 20), 70, 140),
                np.clip(tr0 + np.random.uniform(-1, 1), 0.1, 30),
                np.clip(td0 + np.random.uniform(-1, 1), 0.1, 20),
            ])
            bounds = Bounds(
                [x0[0]-0.5, 70, max(0.1, x0[2]-3), max(0.1, x0[3]-3)],
                [x0[0]+0.5, 140, min(30, x0[2]+3), min(20, x0[3]+3)]
            )
            try:
                res = minimize(local_obj, x0, method='L-BFGS-B',
                              bounds=bounds, options={'maxiter': 200})
                dur = -res.fun
                if dur > best_duration:
                    best_duration = dur
                    best_result = (res.x[0], res.x[1], res.x[2], res.x[3],
                                   dur, 0, 0)
                    _, t1, t2 = simulate_detailed(*res.x)
                    best_result = (res.x[0], res.x[1], res.x[2], res.x[3],
                                   dur, t1, t2)
            except:
                pass
    print(f"  最佳: dur={best_duration:.4f}s")

    # 输出最终结果
    print("\n" + "=" * 60)
    print("Q2 最终最优策略")
    print("=" * 60)
    ang, speed, t_rel, t_del, dur, t1, t2 = best_result

    heading = np.array([np.cos(ang), np.sin(ang), 0.0])
    drone_vel = speed * heading
    release_pos = D0 + drone_vel * t_rel
    t_det = t_rel + t_del
    det_pos = bomb_position(release_pos, drone_vel, t_rel, t_det)

    print(f"飞行方向角: {np.degrees(ang):.2f}°")
    print(f"飞行速度: {speed:.2f} m/s")
    print(f"投放时刻: {t_rel:.4f} s")
    print(f"起爆延迟: {t_del:.4f} s")
    print(f"投放点: ({release_pos[0]:.1f}, {release_pos[1]:.1f}, {release_pos[2]:.1f})")
    print(f"起爆点: ({det_pos[0]:.1f}, {det_pos[1]:.1f}, {det_pos[2]:.1f})")
    print(f"有效遮蔽时长: {dur:.4f} s")
    print(f"遮蔽时段: {t1:.4f}s ~ {t2:.4f}s")

    return {
        'heading_angle_deg': np.degrees(ang),
        'speed': speed,
        't_release': t_rel,
        't_det_delay': t_del,
        'max_duration': dur,
        't_shield_start': t1,
        't_shield_end': t2,
        'release_pos': release_pos.tolist(),
        'detonation_pos': det_pos.tolist(),
        't_det': t_det,
    }


if __name__ == '__main__':
    result = optimize_q2_improved()
