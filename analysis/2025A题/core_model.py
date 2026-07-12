"""
2025 CUMCM A题：烟幕干扰弹投放策略 — 核心物理模型
====================================================
导弹/无人机/干扰弹/烟幕云团的运动模型 + 遮蔽检测引擎
"""
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional

# ============================================================
# 物理常数
# ============================================================
G = 9.8                # 重力加速度 (m/s^2)
MISSILE_SPEED = 300    # 导弹速度 (m/s)
DRONE_SPEED_MIN = 70   # 无人机最小速度
DRONE_SPEED_MAX = 140  # 无人机最大速度
CLOUD_RADIUS = 10      # 烟幕云团半径 (m)
CLOUD_SINK_SPEED = 3   # 云团下沉速度 (m/s)
CLOUD_DURATION = 20    # 起爆后有效遮蔽时长 (s)
BOMB_INTERVAL_MIN = 1  # 同机两弹最小投放间隔 (s)
FAKE_TARGET = np.array([0.0, 0.0, 0.0])     # 假目标（导弹瞄准点）
REAL_TARGET = np.array([0.0, 200.0, 0.0])   # 真目标下底面圆心

# ============================================================
# 初始条件
# ============================================================
MISSILES = {
    'M1': np.array([20000.0, 0.0, 2000.0]),
    'M2': np.array([19000.0, 600.0, 2100.0]),
    'M3': np.array([18000.0, -600.0, 1900.0]),
}

DRONES = {
    'FY1': np.array([17800.0, 0.0, 1800.0]),
    'FY2': np.array([12000.0, 1400.0, 1400.0]),
    'FY3': np.array([6000.0, -3000.0, 700.0]),
    'FY4': np.array([11000.0, 2000.0, 1800.0]),
    'FY5': np.array([13000.0, -2000.0, 1300.0]),
}

# ============================================================
# 运动模型
# ============================================================

def missile_position(missile_id: str, t: float) -> np.ndarray:
    """
    导弹在时刻t的位置。
    导弹以300 m/s朝向假目标(0,0,0)直线飞行。
    """
    p0 = MISSILES[missile_id]
    direction = -p0 / np.linalg.norm(p0)  # 指向原点
    return p0 + MISSILE_SPEED * direction * t


def missile_hit_time(missile_id: str) -> float:
    """导弹命中假目标所需时间"""
    return np.linalg.norm(MISSILES[missile_id]) / MISSILE_SPEED


def drone_position(drone_id: str, speed: float, heading_angle: float, t: float) -> np.ndarray:
    """
    无人机在时刻t的位置。
    speed: 飞行速度 (m/s)，范围[70, 140]
    heading_angle: 航向角 (rad)，水平面内从x轴正方向逆时针旋转
    t: 受领任务后的时间 (s)
    无人机等高度匀速直线飞行。
    """
    p0 = DRONES[drone_id]
    vx = speed * np.cos(heading_angle)
    vy = speed * np.sin(heading_angle)
    return np.array([p0[0] + vx * t, p0[1] + vy * t, p0[2]])


def bomb_burst_position(drone_id: str, speed: float, heading_angle: float,
                         t_drop: float, t_delay: float) -> np.ndarray:
    """
    烟幕干扰弹起爆点位置。
    t_drop: 投放时刻（受领任务后）
    t_delay: 投放→起爆的延迟时间 (s)

    干扰弹脱离无人机后做抛体运动：
    - 水平方向保持无人机速度分量
    - 垂直方向受重力加速
    - 无人机等高度飞行，所以 v_dz = 0
    """
    p_drop = drone_position(drone_id, speed, heading_angle, t_drop)
    vx = speed * np.cos(heading_angle)
    vy = speed * np.sin(heading_angle)
    # 抛体运动
    x = p_drop[0] + vx * t_delay
    y = p_drop[1] + vy * t_delay
    z = p_drop[2] - 0.5 * G * t_delay**2
    return np.array([x, y, z])


def cloud_center(burst_pos: np.ndarray, t_since_burst: float) -> np.ndarray:
    """
    烟幕云团中心位置。
    t_since_burst: 起爆后经过的时间 (s)
    云团以3 m/s匀速下沉。
    """
    return burst_pos + np.array([0.0, 0.0, -CLOUD_SINK_SPEED * t_since_burst])

# ============================================================
# 遮蔽检测
# ============================================================

def line_sphere_intersection(p1: np.ndarray, p2: np.ndarray,
                              sphere_center: np.ndarray, sphere_radius: float) -> bool:
    """
    判断线段p1→p2是否穿过球体。

    参数:
        p1: 线段起点（导弹位置）
        p2: 线段终点（真目标位置）
        sphere_center: 球心（烟幕云团中心）
        sphere_radius: 球半径

    返回: True 如果线段与球相交
    """
    v = p2 - p1
    w = sphere_center - p1

    # 投影参数 t_proj (0~1 表示投影在线段内)
    v_dot_v = np.dot(v, v)
    if v_dot_v < 1e-12:
        # p1 ≈ p2，退化为点
        return np.linalg.norm(w) <= sphere_radius

    t_proj = np.dot(w, v) / v_dot_v
    t_proj = np.clip(t_proj, 0.0, 1.0)

    # 线段上离球心最近的点
    closest_point = p1 + t_proj * v

    # 最近距离
    dist = np.linalg.norm(closest_point - sphere_center)
    return dist <= sphere_radius


def is_shielded_at_time(missile_id: str, t: float,
                         burst_pos: np.ndarray, t_burst: float) -> bool:
    """
    判断在时刻t，导弹→真目标的视线是否被烟幕遮挡。

    参数:
        missile_id: 导弹编号
        t: 当前时刻（从受领任务算起）
        burst_pos: 起爆点位置
        t_burst: 起爆时刻

    返回: True 如果视线被遮挡
    """
    # 烟幕有效期检查
    t_since_burst = t - t_burst
    if t_since_burst < 0 or t_since_burst > CLOUD_DURATION:
        return False

    # 云团当前位置
    cloud = cloud_center(burst_pos, t_since_burst)

    # 导弹当前位置
    missile = missile_position(missile_id, t)

    # 线段-球体相交检测
    return line_sphere_intersection(missile, REAL_TARGET, cloud, CLOUD_RADIUS)


def compute_coverage(missile_id: str,
                      burst_pos: np.ndarray,
                      t_burst: float,
                      t_start: float = 0.0,
                      t_end: float = None,
                      dt: float = 0.02) -> float:
    """
    计算单枚烟幕弹对指定导弹的有效遮蔽总时长。

    参数:
        missile_id: 导弹编号
        burst_pos: 起爆点位置
        t_burst: 起爆时刻
        t_start, t_end: 考察时间范围（默认从起爆到导弹命中假目标）
        dt: 时间步长 (s)

    返回: 有效遮蔽时长 (s)
    """
    if t_end is None:
        t_end = missile_hit_time(missile_id)

    # 遮蔽只在起爆后CLOUD_DURATION内有效
    t_check_start = max(t_start, t_burst)
    t_check_end = min(t_end, t_burst + CLOUD_DURATION)

    if t_check_start >= t_check_end:
        return 0.0

    coverage = 0.0
    t = t_check_start
    while t < t_check_end:
        if is_shielded_at_time(missile_id, t, burst_pos, t_burst):
            coverage += dt
        t += dt

    return coverage


def compute_multi_coverage(missile_id: str,
                            burst_events: List[Tuple[np.ndarray, float]],
                            t_start: float = 0.0,
                            t_end: float = None,
                            dt: float = 0.02) -> float:
    """
    计算多枚烟幕弹对指定导弹的联合有效遮蔽总时长（取并集）。

    参数:
        missile_id: 导弹编号
        burst_events: [(起爆点位置, 起爆时刻), ...]
        t_start, t_end: 考察时间范围
        dt: 时间步长

    返回: 联合遮蔽时长 (s)
    """
    if not burst_events:
        return 0.0

    if t_end is None:
        t_end = missile_hit_time(missile_id)

    # 确定整体检查范围
    t_min = max(t_start, min(t_burst for _, t_burst in burst_events))
    t_max = min(t_end, max(t_burst + CLOUD_DURATION for _, t_burst in burst_events))

    if t_min >= t_max:
        return 0.0

    coverage = 0.0
    t = t_min
    while t < t_max:
        # 任意一枚弹在此刻提供遮蔽即可
        shielded = False
        for burst_pos, t_burst in burst_events:
            if is_shielded_at_time(missile_id, t, burst_pos, t_burst):
                shielded = True
                break
        if shielded:
            coverage += dt
        t += dt

    return coverage


def find_coverage_intervals(missile_id: str,
                             burst_pos: np.ndarray,
                             t_burst: float,
                             t_start: float = 0.0,
                             t_end: float = None,
                             dt: float = 0.02) -> List[Tuple[float, float]]:
    """
    找出遮蔽的时间区间（用于详细分析）。
    返回: [(start1, end1), (start2, end2), ...] 每个元组为一个连续遮蔽区间
    """
    if t_end is None:
        t_end = missile_hit_time(missile_id)

    intervals = []
    in_coverage = False
    segment_start = 0.0

    t_check_start = max(t_start, t_burst)
    t_check_end = min(t_end, t_burst + CLOUD_DURATION)

    t = t_check_start
    while t < t_check_end:
        shielded = is_shielded_at_time(missile_id, t, burst_pos, t_burst)
        if shielded and not in_coverage:
            segment_start = t
            in_coverage = True
        elif not shielded and in_coverage:
            intervals.append((segment_start, t))
            in_coverage = False
        t += dt

    if in_coverage:
        intervals.append((segment_start, t_check_end))

    return intervals


# ============================================================
# 辅助函数
# ============================================================

def heading_toward_point(drone_id: str, target_point: np.ndarray) -> float:
    """
    计算无人机朝向某点的航向角（水平面内投影）。
    返回: 航向角 (rad)，从x轴正方向逆时针旋转
    """
    p0 = DRONES[drone_id]
    dx = target_point[0] - p0[0]
    dy = target_point[1] - p0[1]
    return np.arctan2(dy, dx)


def heading_toward_origin(drone_id: str) -> float:
    """计算无人机朝向假目标(原点)的航向角"""
    return heading_toward_point(drone_id, FAKE_TARGET)


def print_coverage_report(missile_id: str, burst_pos: np.ndarray,
                           t_burst: float, label: str = ""):
    """打印遮蔽效果报告"""
    duration = compute_coverage(missile_id, burst_pos, t_burst)
    intervals = find_coverage_intervals(missile_id, burst_pos, t_burst)
    t_hit = missile_hit_time(missile_id)

    print(f"\n{'='*60}")
    print(f"遮蔽效果报告 {label}")
    print(f"{'='*60}")
    print(f"导弹 {missile_id}: 命中假目标时间 = {t_hit:.2f} s")
    print(f"起爆点: ({burst_pos[0]:.1f}, {burst_pos[1]:.1f}, {burst_pos[2]:.1f})")
    print(f"起爆时刻: {t_burst:.2f} s")
    print(f"总遮蔽时长: {duration:.4f} s")
    print(f"遮蔽区间 ({len(intervals)}段):")
    for i, (s, e) in enumerate(intervals, 1):
        print(f"  区间{i}: [{s:.2f}, {e:.2f}] 持续 {e-s:.4f} s")


if __name__ == '__main__':
    # 快速自测：打印各导弹命中时间
    print("导弹飞行时间:")
    for mid in ['M1', 'M2', 'M3']:
        t = missile_hit_time(mid)
        print(f"  {mid}: {t:.2f} s (位置 {MISSILES[mid]})")

    print("\n无人机初始位置:")
    for did in ['FY1', 'FY2', 'FY3', 'FY4', 'FY5']:
        p = DRONES[did]
        dist = np.linalg.norm(p)
        print(f"  {did}: ({p[0]:.0f}, {p[1]:.0f}, {p[2]:.0f}), 距原点 {dist:.0f} m")
