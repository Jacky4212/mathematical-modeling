"""
问题1：确定性遮蔽时长计算
===========================
FY1 以 120 m/s 朝向假目标飞行，
受领任务1.5s后投放1枚烟幕干扰弹，间隔3.6s后起爆。
计算对M1的有效遮蔽时长。
"""
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core_model import *

# ============================================================
# 给定参数
# ============================================================
DRONE_ID = 'FY1'
MISSILE_ID = 'M1'
SPEED = 120.0              # m/s, 朝向假目标
T_DROP = 1.5               # 受领任务后投放时刻 (s)
T_DELAY = 3.6              # 投放→起爆延迟 (s)

# ============================================================
# 计算流程
# ============================================================

def solve_problem1():
    """问题1求解"""

    # 1. 航向角：朝向假目标(原点)
    heading = heading_toward_origin(DRONE_ID)
    print(f"FY1 航向角: {np.degrees(heading):.2f}° ({heading:.4f} rad)")

    # 2. 投放点位置
    p_drop = drone_position(DRONE_ID, SPEED, heading, T_DROP)
    print(f"投放点 (t={T_DROP}s): ({p_drop[0]:.1f}, {p_drop[1]:.1f}, {p_drop[2]:.1f})")

    # 3. 起爆点位置
    p_burst = bomb_burst_position(DRONE_ID, SPEED, heading, T_DROP, T_DELAY)
    t_burst = T_DROP + T_DELAY
    print(f"起爆点 (t={t_burst}s): ({p_burst[0]:.1f}, {p_burst[1]:.1f}, {p_burst[2]:.1f})")

    # 4. 导弹M1命中时间
    t_hit = missile_hit_time(MISSILE_ID)
    print(f"M1 命中假目标时间: {t_hit:.2f} s")
    print(f"烟幕有效截止时间: {t_burst + CLOUD_DURATION:.2f} s")

    # 5. 遮蔽时长计算
    coverage = compute_coverage(MISSILE_ID, p_burst, t_burst, dt=0.01)
    intervals = find_coverage_intervals(MISSILE_ID, p_burst, t_burst, dt=0.01)

    # 6. 详细报告
    print_coverage_report(MISSILE_ID, p_burst, t_burst, "问题1")

    # 7. 关键几何分析
    print(f"\n--- 几何分析 ---")
    # 导弹轨迹关键时间点
    for t_check in np.arange(t_burst, min(t_burst + CLOUD_DURATION, t_hit), 5.0):
        m_pos = missile_position(MISSILE_ID, t_check)
        r_pos = REAL_TARGET
        cloud = cloud_center(p_burst, t_check - t_burst)
        dist_to_los = np.linalg.norm(
            np.cross(r_pos - m_pos, cloud - m_pos)
        ) / np.linalg.norm(r_pos - m_pos)
        shielded = is_shielded_at_time(MISSILE_ID, t_check, p_burst, t_burst)
        print(f"  t={t_check:5.1f}s  导弹({m_pos[0]:.0f},{m_pos[1]:.0f},{m_pos[2]:.0f})  "
              f"云团({cloud[0]:.0f},{cloud[1]:.0f},{cloud[2]:.0f})  "
              f"视线距={dist_to_los:.1f}m  {'[遮蔽]' if shielded else '[未遮蔽]'}")

    return coverage


if __name__ == '__main__':
    result = solve_problem1()
    print(f"\n{'='*60}")
    print(f"问题1 答案: 有效遮蔽时长 = {result:.4f} s")
    print(f"{'='*60}")
