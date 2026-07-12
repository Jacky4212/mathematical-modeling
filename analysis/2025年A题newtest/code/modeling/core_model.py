"""
核心物理模型 — 2025 CUMCM A题：烟幕干扰弹投放策略

坐标系：以假目标为原点，xy平面为水平面，z轴向上
- 假目标（decoy）：原点 (0,0,0)，圆柱形，半径7m，高10m
- 真目标（real target）：下底面圆心 (0, 200, 0)
- 导弹速度：300 m/s，方向指向假目标（原点）
- 烟幕弹起爆后：球状云团，半径10m内有效，以3 m/s匀速下沉，有效20s
- 无人机：速度70-140 m/s，等高度匀速直线飞行
"""
import numpy as np
from scipy.optimize import minimize, differential_evolution
from scipy.spatial.distance import cdist
from dataclasses import dataclass
from typing import List, Tuple, Optional

# ============================================================
# 常量
# ============================================================
G = 9.8                     # 重力加速度 m/s²
MISSILE_SPEED = 300.0       # 导弹速度 m/s
SMOKE_SINK_SPEED = 3.0      # 烟幕下沉速度 m/s
SMOKE_RADIUS = 10.0         # 烟幕有效半径 m
SMOKE_DURATION = 20.0       # 烟幕有效时间 s
DRONE_SPEED_MIN = 70.0      # 无人机最小速度
DRONE_SPEED_MAX = 140.0     # 无人机最大速度
BOMB_INTERVAL = 1.0         # 同机投放最小间隔 s

# 真目标位置
REAL_TARGET = np.array([0.0, 200.0, 0.0])
# 假目标（原点）
DECOY_TARGET = np.array([0.0, 0.0, 0.0])

# 导弹初始位置 (x, y, z)
MISSILES = {
    'M1': np.array([20000.0, 0.0, 2000.0]),
    'M2': np.array([19000.0, 600.0, 2100.0]),
    'M3': np.array([18000.0, -600.0, 1900.0]),
}

# 无人机初始位置 (x, y, z)
DRONES = {
    'FY1': np.array([17800.0, 0.0, 1800.0]),
    'FY2': np.array([12000.0, 1400.0, 1400.0]),
    'FY3': np.array([6000.0, -3000.0, 700.0]),
    'FY4': np.array([11000.0, 2000.0, 1800.0]),
    'FY5': np.array([13000.0, -2000.0, 1300.0]),
}


def missile_position(missile_id: str, t: float) -> np.ndarray:
    """计算导弹在时刻t的位置（直线飞向假目标原点）"""
    M0 = MISSILES[missile_id]
    dist = np.linalg.norm(M0)
    if dist == 0:
        return M0.copy()
    direction = -M0 / dist  # 指向原点
    return M0 + MISSILE_SPEED * t * direction


def drone_position(drone_id: str, t: float, heading: np.ndarray, speed: float) -> np.ndarray:
    """计算无人机在时刻t的位置（等高度匀速直线飞行）"""
    D0 = DRONES[drone_id]
    return D0 + speed * t * heading


def bomb_position(release_pos: np.ndarray, drone_velocity: np.ndarray,
                  t_release: float, t: float) -> np.ndarray:
    """计算烟幕弹投放后在时刻t的位置（重力作用，忽略空气阻力）

    Args:
        release_pos: 投放点位置
        drone_velocity: 投放时无人机的速度向量 (vx, vy, 0)
        t_release: 投放时刻
        t: 当前时刻 (t >= t_release)
    """
    dt = t - t_release
    pos = release_pos.copy().astype(float)
    pos[0] += drone_velocity[0] * dt
    pos[1] += drone_velocity[1] * dt
    pos[2] += drone_velocity[2] * dt - 0.5 * G * dt**2
    return pos


def smoke_center(detonation_pos: np.ndarray, t_det: float, t: float) -> np.ndarray:
    """计算烟幕云团中心在时刻t的位置（从起爆点以3m/s匀速下沉）

    Args:
        detonation_pos: 起爆点位置
        t_det: 起爆时刻
        t: 当前时刻 (t >= t_det)
    """
    dt = t - t_det
    return detonation_pos + np.array([0.0, 0.0, -SMOKE_SINK_SPEED * dt])


def point_to_line_distance(point: np.ndarray, line_p1: np.ndarray, line_p2: np.ndarray) -> float:
    """计算点到线段的最短距离（3D）"""
    v = line_p2 - line_p1
    w = point - line_p1
    t = np.dot(w, v) / np.dot(v, v) if np.dot(v, v) > 0 else 0
    t = np.clip(t, 0, 1)
    projection = line_p1 + t * v
    return np.linalg.norm(point - projection)


def is_shielded(missile_pos: np.ndarray, smoke_pos: np.ndarray,
                target: np.ndarray = REAL_TARGET) -> bool:
    """判断导弹视线是否被烟幕遮蔽

    条件：烟幕中心到导弹→真目标连线的最短距离 ≤ 10m
    """
    dist = point_to_line_distance(smoke_pos, missile_pos, target)
    return dist <= SMOKE_RADIUS


def calc_shielding_duration_q1() -> dict:
    """问题1：给定参数计算有效遮蔽时长

    FY1: 速度120 m/s，朝向假目标（原点），受领1.5s后投放，间隔3.6s起爆
    """
    print("=" * 60)
    print("Q1: 给定参数计算有效遮蔽时长")
    print("=" * 60)

    # 无人机FY1初始位置
    D0 = DRONES['FY1']  # (17800, 0, 1800)

    # FY1朝向假目标（原点）
    heading = -D0 / np.linalg.norm(D0)
    heading[2] = 0  # 保持高度飞行，heading在xy平面
    # 重新归一化
    h_xy = heading[:2] / np.linalg.norm(heading[:2])
    heading = np.array([h_xy[0], h_xy[1], 0.0])

    speed = 120.0

    # 投放时刻：t=1.5s
    t_release = 1.5
    release_pos = drone_position('FY1', t_release, heading, speed)
    drone_vel = speed * heading

    # 起爆时刻：t=1.5+3.6=5.1s
    t_det = t_release + 3.6

    # 起爆时炸弹位置（重力作用）
    det_pos = bomb_position(release_pos, drone_vel, t_release, t_det)

    print(f"投放点: ({release_pos[0]:.1f}, {release_pos[1]:.1f}, {release_pos[2]:.1f})")
    print(f"起爆点: ({det_pos[0]:.1f}, {det_pos[1]:.1f}, {det_pos[2]:.1f})")
    print(f"起爆时刻: t={t_det:.1f}s")

    # 逐时间步长检查遮蔽
    dt = 0.02  # 时间步长 0.02s（与 Q2-Q5 统一）
    t_max = 150.0  # 模拟总时长

    shielded_times = []
    t = t_det
    while t <= t_det + SMOKE_DURATION:
        M_pos = missile_position('M1', t)
        S_pos = smoke_center(det_pos, t_det, t)

        if is_shielded(M_pos, S_pos):
            shielded_times.append(t)

        t += dt

    if shielded_times:
        duration = len(shielded_times) * dt
        t_start_shield = shielded_times[0]
        t_end_shield = shielded_times[-1]
    else:
        duration = 0
        t_start_shield = t_end_shield = 0

    print(f"有效遮蔽时长: {duration:.4f} s")
    print(f"遮蔽时段: {t_start_shield:.4f}s ~ {t_end_shield:.4f}s")

    result = {
        'duration': duration,
        't_start': t_start_shield,
        't_end': t_end_shield,
        'release_pos': release_pos.tolist(),
        'detonation_pos': det_pos.tolist(),
        't_release': t_release,
        't_det': t_det,
    }

    # 计算遮蔽详情
    print(f"\n导弹轨迹分析:")
    M_start = missile_position('M1', 0)
    M_at_det = missile_position('M1', t_det)
    print(f"  导弹初始: ({M_start[0]:.0f}, {M_start[1]:.0f}, {M_start[2]:.0f})")
    print(f"  起爆时导弹: ({M_at_det[0]:.0f}, {M_at_det[1]:.0f}, {M_at_det[2]:.0f})")
    print(f"  导弹到原点距离: {np.linalg.norm(M_start):.0f}m")
    print(f"  导弹飞行时间(到原点): {np.linalg.norm(M_start)/MISSILE_SPEED:.1f}s")

    return result


def optimize_q2() -> dict:
    """问题2：优化FY1的飞行方向、速度、投放点、起爆点，最大化遮蔽时长

    优化变量：
    - heading_angle: 飞行方向角（xy平面，弧度）
    - speed: 飞行速度 (70-140 m/s)
    - t_release: 投放时刻
    - t_det_delay: 投放后起爆延迟

    约束：
    - 速度 ∈ [70, 140]
    - 投放后起爆延迟 ≥ 0
    - 起爆时炸弹z ≥ 0（不能炸到地面以下）
    """
    print("\n" + "=" * 60)
    print("Q2: 优化FY1飞行策略最大化遮蔽时长")
    print("=" * 60)

    D0 = DRONES['FY1']

    def simulate(heading_angle, speed, t_release, t_det_delay):
        """模拟一次策略的遮蔽时长"""
        heading = np.array([np.cos(heading_angle), np.sin(heading_angle), 0.0])
        drone_vel = speed * heading

        # 投放点
        release_pos = D0 + drone_vel * t_release

        t_det = t_release + t_det_delay

        # 起爆时炸弹位置
        det_pos = bomb_position(release_pos, drone_vel, t_release, t_det)

        # 起爆点必须在地面以上
        if det_pos[2] <= 0:
            return 0.0

        # 计算遮蔽时长
        dt = 0.02
        shielded_count = 0
        t = t_det
        while t <= t_det + SMOKE_DURATION:
            M_pos = missile_position('M1', t)
            S_pos = smoke_center(det_pos, t_det, t)
            if is_shielded(M_pos, S_pos):
                shielded_count += 1
            t += dt

        return shielded_count * dt

    # 使用差分进化全局优化
    bounds = [
        (-np.pi, np.pi),      # heading_angle
        (DRONE_SPEED_MIN, DRONE_SPEED_MAX),  # speed
        (0.5, 10.0),          # t_release
        (0.5, 10.0),          # t_det_delay
    ]

    def objective(x):
        return -simulate(*x)  # 负值用于最小化

    print("运行差分进化优化...")
    result = differential_evolution(
        objective, bounds,
        seed=42, maxiter=500,
        popsize=30, tol=1e-6,
        polish=True
    )

    heading_angle, speed, t_release, t_det_delay = result.x
    max_duration = -result.fun

    heading = np.array([np.cos(heading_angle), np.sin(heading_angle), 0.0])
    release_pos = D0 + speed * heading * t_release
    t_det = t_release + t_det_delay
    det_pos = bomb_position(release_pos, speed * heading, t_release, t_det)

    print(f"\n最优策略:")
    print(f"  飞行方向角: {np.degrees(heading_angle):.2f}°")
    print(f"  飞行速度: {speed:.2f} m/s")
    print(f"  投放时刻: {t_release:.4f} s")
    print(f"  起爆延迟: {t_det_delay:.4f} s")
    print(f"  投放点: ({release_pos[0]:.1f}, {release_pos[1]:.1f}, {release_pos[2]:.1f})")
    print(f"  起爆点: ({det_pos[0]:.1f}, {det_pos[1]:.1f}, {det_pos[2]:.1f})")
    print(f"  最大遮蔽时长: {max_duration:.4f} s")

    return {
        'heading_angle_deg': np.degrees(heading_angle),
        'speed': speed,
        't_release': t_release,
        't_det_delay': t_det_delay,
        'max_duration': max_duration,
        'release_pos': release_pos.tolist(),
        'detonation_pos': det_pos.tolist(),
        't_det': t_det,
    }


if __name__ == '__main__':
    q1_result = calc_shielding_duration_q1()
    q2_result = optimize_q2()

    print("\n" + "=" * 60)
    print("对比总结")
    print("=" * 60)
    print(f"Q1 (固定策略) 遮蔽时长: {q1_result['duration']:.4f} s")
    print(f"Q2 (优化策略) 遮蔽时长: {q2_result['max_duration']:.4f} s")
    print(f"改善: {q2_result['max_duration'] - q1_result['duration']:.4f} s")
