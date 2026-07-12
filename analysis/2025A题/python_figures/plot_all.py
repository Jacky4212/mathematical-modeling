"""
2025 CUMCM A题 — Python 全套可视化(一键生成所有图)
运行: python plot_all.py
输出: 8张PNG图片到当前目录
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from core_model import *

# ===== 全局设置 =====
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 120

OUTPUT = os.path.dirname(os.path.abspath(__file__))

G, MISSILE_SPEED = 9.8, 300
CLOUD_RADIUS, CLOUD_SINK, CLOUD_DURATION = 10, 3, 20
REAL_TARGET = np.array([0., 200., 0.])
M1_0 = np.array([20000., 0., 2000.])
M2_0 = np.array([19000., 600., 2100.])
M3_0 = np.array([18000., -600., 1900.])
v_m1 = -MISSILE_SPEED * M1_0 / np.linalg.norm(M1_0)
v_m2 = -MISSILE_SPEED * M2_0 / np.linalg.norm(M2_0)
v_m3 = -MISSILE_SPEED * M3_0 / np.linalg.norm(M3_0)
T_HIT1 = np.linalg.norm(M1_0) / MISSILE_SPEED
T_HIT2 = np.linalg.norm(M2_0) / MISSILE_SPEED
T_HIT3 = np.linalg.norm(M3_0) / MISSILE_SPEED

M_COLORS = {'M1': '#E74C3C', 'M2': '#E67E22', 'M3': '#3498DB'}
D_COLORS = {'FY1': '#2980B9', 'FY2': '#E67E22', 'FY3': '#27AE60',
            'FY4': '#8E44AD', 'FY5': '#1ABC9C'}


def save(name):
    path = os.path.join(OUTPUT, name)
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'  ✓ {name}')


# ================================================================
# 图1: 问题1 — 轨迹 + 遮蔽时刻视线
# ================================================================
def plot_problem1():
    """问题1: M1轨迹 + FY1路径 + 起爆点 + 遮蔽时刻视线 + 云团"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    speed, heading = 120., np.pi
    v_d = speed * np.array([np.cos(heading), np.sin(heading), 0])
    t_drop, t_delay = 1.5, 3.6
    t_burst = t_drop + t_delay
    p_burst = bomb_burst_position('FY1', speed, heading, t_drop, t_delay)
    t_shield = 8.75  # 遮蔽中点

    # X-Y
    ax1.set_title('Problem 1: X-Y Plane (Top View)', fontsize=13, fontweight='bold')
    ts = np.linspace(0, T_HIT1, 500)
    m_traj = np.array([missile_position('M1', t) for t in ts])
    ax1.plot(m_traj[:,0], m_traj[:,1], 'r-', lw=2, label='M1 Trajectory')
    ax1.plot(M1_0[0], M1_0[1], 'r^', ms=10, label='M1 Start')
    ax1.plot(0, 0, 'kx', ms=12, mew=2, label='Decoy (0,0)')
    ax1.plot(REAL_TARGET[0], REAL_TARGET[1], 'gs', ms=10, label='Real Target')

    # FY1 path
    d0 = DRONES['FY1']
    d_path = np.array([drone_position('FY1', speed, heading, t) for t in np.linspace(0, 10, 100)])
    ax1.plot(d_path[:,0], d_path[:,1], 'b--', lw=1.5, label='FY1 Path')
    ax1.plot(d0[0], d0[1], 'bo', ms=8)

    # Burst + cloud
    ax1.plot(p_burst[0], p_burst[1], 'm*', ms=14, mew=1.5, label='Burst Point')
    cloud_c = cloud_center(p_burst, t_shield - t_burst)
    ax1.add_patch(Circle(cloud_c[:2], CLOUD_RADIUS, fc='none', ec='purple',
                          ls='--', lw=2, label='Cloud (t=8.75s)'))
    ax1.plot(cloud_c[0], cloud_c[1], 'mo', ms=8)

    # LOS at shield time
    m_shield = missile_position('M1', t_shield)
    ax1.plot([m_shield[0], REAL_TARGET[0]], [m_shield[1], REAL_TARGET[1]],
             'k-', lw=3, label='LOS (shielded)')
    ax1.plot(m_shield[0], m_shield[1], 'rd', ms=8, label=f'M1 t={t_shield}s')

    ax1.set_xlabel('X (m)'); ax1.set_ylabel('Y (m)')
    ax1.legend(fontsize=7, loc='upper right'); ax1.grid(alpha=0.3)
    ax1.set_xlim(-500, 21000); ax1.set_ylim(-500, 2500); ax1.set_aspect('equal')

    # X-Z
    ax2.set_title('Problem 1: X-Z Plane (Side View)', fontsize=13, fontweight='bold')
    ax2.plot(m_traj[:,0], m_traj[:,2], 'r-', lw=2)
    ax2.plot(M1_0[0], M1_0[2], 'r^', ms=10)
    ax2.plot(0, 0, 'kx', ms=12, mew=2)
    ax2.plot(d_path[:,0], d_path[:,2], 'b--', lw=1.5)
    ax2.plot(d0[0], d0[2], 'bo', ms=8)
    ax2.plot(p_burst[0], p_burst[2], 'm*', ms=14, mew=1.5)
    ax2.add_patch(Circle(cloud_c[::2], CLOUD_RADIUS, fc='none', ec='purple', ls='--', lw=2))
    ax2.plot(cloud_c[0], cloud_c[2], 'mo', ms=8)
    ax2.plot([m_shield[0], REAL_TARGET[0]], [m_shield[2], REAL_TARGET[2]], 'k-', lw=3)
    ax2.axhline(d0[2], color='b', ls=':', alpha=0.3)
    ax2.set_xlabel('X (m)'); ax2.set_ylabel('Z (m)')
    ax2.grid(alpha=0.3); ax2.set_xlim(-500, 21000)

    fig.suptitle(f'Problem 1: Coverage = 1.42s  [8.04, 9.46]  '
                 f'(heading=180°, v=120m/s, drop=1.5s, delay=3.6s)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    save('problem1_trajectory.png')
    plt.close()


# ================================================================
# 图2: 问题2 — 优化前后对比
# ================================================================
def plot_problem2():
    """问题2: 方案A(180°) vs 方案B(7.5°) 六图对比"""
    fig = plt.figure(figsize=(18, 9))

    # 方案A
    pA = {'hdg': np.pi, 'spd': 120., 'td': 1.5, 'tdl': 3.6, 'color': '#C0392B', 'label': 'A: 180°'}
    # 方案B
    pB = {'hdg': np.radians(7.5), 'spd': 70., 'td': 0.1, 'tdl': 1.04, 'color': '#2471A3', 'label': 'B: 7.5°'}

    cov_A = compute_coverage('M1', bomb_burst_position('FY1', pA['spd'], pA['hdg'], pA['td'], pA['tdl']),
                              pA['td']+pA['tdl'], dt=0.02)
    cov_B = compute_coverage('M1', bomb_burst_position('FY1', pB['spd'], pB['hdg'], pB['td'], pB['tdl']),
                              pB['td']+pB['tdl'], dt=0.02)

    # 子图1: X-Y轨迹
    ax1 = fig.add_subplot(2, 3, 1)
    ax1.set_title('X-Y: Trajectory Comparison', fontsize=11, fontweight='bold')
    ts = np.linspace(0, T_HIT1, 400)
    m_traj = np.array([missile_position('M1', t) for t in ts])
    ax1.plot(m_traj[:,0], m_traj[:,1], 'k-', lw=1.5, label='M1')
    ax1.plot(0, 0, 'kx', ms=10, mew=2)
    ax1.plot(REAL_TARGET[0], REAL_TARGET[1], 'gs', ms=8)
    for p in [pA, pB]:
        v_d = p['spd'] * np.array([np.cos(p['hdg']), np.sin(p['hdg']), 0])
        d0 = DRONES['FY1']
        path = np.array([d0 + v_d * t for t in np.linspace(0, min(15, p['td']+p['tdl']+3), 100)])
        ax1.plot(path[:,0], path[:,1], '-', color=p['color'], lw=2, label=p['label'])
        b = bomb_burst_position('FY1', p['spd'], p['hdg'], p['td'], p['tdl'])
        ax1.plot(b[0], b[1], '*', color=p['color'], ms=14, mew=1.5)
    ax1.plot(DRONES['FY1'][0], DRONES['FY1'][1], 'bo', ms=8, label='FY1')
    ax1.set_xlabel('X (m)'); ax1.set_ylabel('Y (m)')
    ax1.legend(fontsize=7); ax1.grid(alpha=0.3); ax1.set_aspect('equal')
    ax1.set_xlim(-500, 21000); ax1.set_ylim(-500, 2000)

    # 子图2: X-Z轨迹
    ax2 = fig.add_subplot(2, 3, 2)
    ax2.set_title('X-Z: Trajectory Comparison', fontsize=11, fontweight='bold')
    ax2.plot(m_traj[:,0], m_traj[:,2], 'k-', lw=1.5)
    for p in [pA, pB]:
        v_d = p['spd'] * np.array([np.cos(p['hdg']), np.sin(p['hdg']), 0])
        d0 = DRONES['FY1']
        path = np.array([d0 + v_d * t for t in np.linspace(0, min(15, p['td']+p['tdl']+3), 100)])
        ax2.plot(path[:,0], path[:,2], '-', color=p['color'], lw=2)
        b = bomb_burst_position('FY1', p['spd'], p['hdg'], p['td'], p['tdl'])
        ax2.plot(b[0], b[2], '*', color=p['color'], ms=14, mew=1.5)
        ax2.axhline(d0[2], color=p['color'], ls=':', alpha=0.3)
    ax2.set_xlabel('X (m)'); ax2.set_ylabel('Z (m)')
    ax2.grid(alpha=0.3); ax2.set_xlim(-500, 21000)

    # 子图3: 遮蔽信号时间线
    ax3 = fig.add_subplot(2, 3, 3)
    ax3.set_title('Coverage Signal Timeline', fontsize=11, fontweight='bold')
    for pi, p in enumerate([pB, pA]):
        t_b = p['td'] + p['tdl']
        pb = bomb_burst_position('FY1', p['spd'], p['hdg'], p['td'], p['tdl'])
        tvs = np.arange(max(0, t_b), min(T_HIT1, t_b+CLOUD_DURATION), 0.02)
        sig = np.array([is_shielded_at_time('M1', t, pb, t_b) for t in tvs])
        # 画遮蔽区块
        in_block = False; bs = 0
        y_off = (1-pi)*0.3 - 0.1
        for j in range(len(tvs)-1):
            if sig[j] and not in_block:
                bs = tvs[j]; in_block = True
            elif not sig[j] and in_block:
                ax3.fill_between([bs, tvs[j]], y_off-0.12, y_off+0.12,
                                 color=p['color'], alpha=0.7, ec='none')
                in_block = False
        if in_block:
            ax3.fill_between([bs, tvs[-1]], y_off-0.12, y_off+0.12,
                             color=p['color'], alpha=0.7, ec='none')
        cov = compute_coverage('M1', pb, t_b, dt=0.02)
        ax3.text(50, y_off, f'{p["label"]}: {cov:.2f}s', fontsize=10,
                 fontweight='bold', color=p['color'])
    ax3.set_xlabel('Time (s)'); ax3.set_xlim(0, 68); ax3.set_yticks([])

    # 子图4: 柱状图
    ax4 = fig.add_subplot(2, 3, 4)
    ax4.bar([1, 2], [cov_A, cov_B], color=[pA['color'], pB['color']], width=0.5)
    ax4.text(1, cov_A+0.15, f'{cov_A:.2f}s', ha='center', fontsize=12, fontweight='bold')
    ax4.text(2, cov_B+0.15, f'{cov_B:.2f}s', ha='center', fontsize=12, fontweight='bold')
    ax4.text(1.5, max(cov_A,cov_B)*0.5, f'+{(cov_B-cov_A)/cov_A*100:.0f}%',
             ha='center', fontsize=16, fontweight='bold', color='green')
    ax4.set_xticklabels(['', 'A: 180°\n(Problem 1)', '', 'B: 7.5°\n(Problem 2)'])
    ax4.set_ylabel('Coverage (s)'); ax4.set_title('Coverage Comparison', fontsize=11, fontweight='bold')
    ax4.grid(axis='y', alpha=0.3)

    # 子图5+6: 3D双视角
    for vi, (elev, azim, title) in enumerate([(30, -60, '3D View 1'), (90, -90, 'Top View')]):
        ax = fig.add_subplot(2, 3, 5+vi, projection='3d')
        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.plot3D(m_traj[:,0], m_traj[:,1], m_traj[:,2], 'k-', lw=1)
        for p in [pA, pB]:
            v_d = p['spd'] * np.array([np.cos(p['hdg']), np.sin(p['hdg']), 0])
            d0 = DRONES['FY1']
            path = np.array([d0 + v_d * t for t in np.linspace(0, 10, 80)])
            ax.plot3D(path[:,0], path[:,1], path[:,2], '-', color=p['color'], lw=1.5)
            b = bomb_burst_position('FY1', p['spd'], p['hdg'], p['td'], p['tdl'])
            ax.scatter(*b, c=p['color'], s=80, marker='*', edgecolors='black', linewidths=0.5)
            # 云团球体
            u = np.linspace(0, 2*np.pi, 15); v = np.linspace(0, np.pi, 10)
            cx, cy, cz = b + np.array([0, 0, -CLOUD_SINK * 3])
            x_s = cx + CLOUD_RADIUS * np.outer(np.cos(u), np.sin(v))
            y_s = cy + CLOUD_RADIUS * np.outer(np.sin(u), np.sin(v))
            z_s = cz + CLOUD_RADIUS * np.outer(np.ones_like(u), np.cos(v))
            ax.plot_surface(x_s, y_s, z_s, color=p['color'], alpha=0.15, linewidth=0)
        ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
        ax.view_init(elev, azim)

    fig.suptitle(f'Problem 2: Optimization — Why 7.5° beats 180° by +234%',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    save('problem2_optimization.png')
    plt.close()


# ================================================================
# 图3: 问题3 — 三弹时间线
# ================================================================
def plot_problem3():
    """问题3: FY1三弹遮蔽时间线 + 联合区间"""
    fig = plt.figure(figsize=(16, 8))

    theta, speed = np.radians(7.5), 70.
    bombs = [
        {'td': 0.100, 'tdl': 1.040, 'color': '#27AE60', 'label': 'Bomb 1'},
        {'td': 3.100, 'tdl': 3.000, 'color': '#E67E22', 'label': 'Bomb 2'},
        {'td': 6.100, 'tdl': 2.500, 'color': '#8E44AD', 'label': 'Bomb 3'},
    ]

    # 计算每弹遮蔽
    for b in bombs:
        b['pb'] = bomb_burst_position('FY1', speed, theta, b['td'], b['tdl'])
        b['tb'] = b['td'] + b['tdl']

    # 联合区间
    all_events = [(b['pb'], b['tb']) for b in bombs]
    union_cov = compute_multi_coverage('M1', all_events, dt=0.02)

    # 子图1: 遮蔽时间线 (甘特图风格)
    ax1 = fig.add_subplot(2, 1, 1)
    ax1.set_title(f'Problem 3: FY1 Three-Bomb Coverage Timeline  '
                  f'(Union = {union_cov:.2f}s)', fontsize=13, fontweight='bold')

    for bi, b in enumerate(bombs):
        tvs = np.arange(b['tb'], min(T_HIT1, b['tb']+CLOUD_DURATION), 0.02)
        sig = np.array([is_shielded_at_time('M1', t, b['pb'], b['tb']) for t in tvs])
        y = 2.5 - bi * 1.0
        in_block = False; bs = 0
        for j in range(len(tvs)-1):
            if sig[j] and not in_block:
                bs = tvs[j]; in_block = True
            elif not sig[j] and in_block:
                ax1.fill_between([bs, tvs[j]], y-0.35, y+0.35,
                                 color=b['color'], alpha=0.7, ec='white', lw=0.5)
                ax1.text((bs+tvs[j])/2, y, f'{tvs[j]-bs:.2f}s', ha='center',
                         va='center', fontsize=8, fontweight='bold', color='white')
                in_block = False
        single_cov = compute_coverage('M1', b['pb'], b['tb'], dt=0.02)
        ax1.text(62, y, f'{single_cov:.2f}s', fontsize=10, fontweight='bold', color=b['color'])
        ax1.axvline(b['tb'], color=b['color'], ls='--', alpha=0.4, lw=0.8)

    # 联合遮蔽
    t_min = min(b['tb'] for b in bombs)
    t_max = min(T_HIT1, max(b['tb']+CLOUD_DURATION for b in bombs))
    tvs_u = np.arange(t_min, t_max, 0.02)
    union_sig = np.array([any(is_shielded_at_time('M1', t, b['pb'], b['tb'])
                              for b in bombs) for t in tvs_u])
    in_block = False; bs = 0
    y_u = 3.5
    for j in range(len(tvs_u)-1):
        if union_sig[j] and not in_block:
            bs = tvs_u[j]; in_block = True
        elif not union_sig[j] and in_block:
            ax1.fill_between([bs, tvs_u[j]], y_u-0.35, y_u+0.35,
                             color='#2ECC71', alpha=0.6, ec='black', lw=1.5)
            ax1.text((bs+tvs_u[j])/2, y_u, f'{tvs_u[j]-bs:.2f}s', ha='center',
                     va='center', fontsize=10, fontweight='bold')
            in_block = False
    ax1.text(62, y_u+0.45, f'UNION = {union_cov:.2f}s', fontsize=14,
             fontweight='bold', color='#1E8449')

    ax1.set_xlabel('Time (s)'); ax1.set_xlim(0, 68)
    ax1.set_yticks([0.5, 1.5, 2.5, 3.8])
    ax1.set_yticklabels(['Bomb 3', 'Bomb 2', 'Bomb 1', 'UNION'], fontsize=11)
    ax1.grid(axis='x', alpha=0.3)

    # 子图2: 3D轨迹
    ax2 = fig.add_subplot(2, 1, 2, projection='3d')
    ax2.set_title('3D: FY1 Flight Path + Three Burst Points + Smoke Clouds', fontsize=12, fontweight='bold')
    ts = np.linspace(0, T_HIT1, 300)
    m_traj = np.array([missile_position('M1', t) for t in ts])
    ax2.plot3D(m_traj[:,0], m_traj[:,1], m_traj[:,2], 'r-', lw=1.5, label='M1')
    ax2.scatter(0, 0, 0, c='black', s=80, marker='x', linewidths=2)

    v_d = speed * np.array([np.cos(theta), np.sin(theta), 0])
    d0 = DRONES['FY1']
    path = np.array([d0 + v_d * t for t in np.linspace(0, 12, 120)])
    ax2.plot3D(path[:,0], path[:,1], path[:,2], 'b-', lw=2, label='FY1')
    ax2.scatter(*d0, c='blue', s=60)

    for b in bombs:
        ax2.scatter(*b['pb'], c=b['color'], s=100, marker='*',
                    edgecolors='black', linewidths=1, label=b['label'])
        # 半透明球体
        u = np.linspace(0, 2*np.pi, 12); vv = np.linspace(0, np.pi, 8)
        mid_c = b['pb'] + np.array([0, 0, -CLOUD_SINK * 3])
        xs = mid_c[0] + CLOUD_RADIUS * np.outer(np.cos(u), np.sin(vv))
        ys = mid_c[1] + CLOUD_RADIUS * np.outer(np.sin(u), np.sin(vv))
        zs = mid_c[2] + CLOUD_RADIUS * np.outer(np.ones_like(u), np.cos(vv))
        ax2.plot_surface(xs, ys, zs, color=b['color'], alpha=0.2, linewidth=0)

    ax2.set_xlabel('X'); ax2.set_ylabel('Y'); ax2.set_zlabel('Z')
    ax2.legend(fontsize=8, loc='upper left')
    ax2.view_init(25, -50)

    plt.tight_layout()
    save('problem3_multi_bomb.png')
    plt.close()


# ================================================================
# 图4: 问题4 — 三机协同
# ================================================================
def plot_problem4():
    """问题4: FY1+FY2+FY3 各1弹 → M1"""
    fig = plt.figure(figsize=(18, 9))

    drones_p4 = {
        'FY1': {'hdg': np.radians(179.4), 'spd': 131.1, 'td': 0.100, 'tdl': 3.671, 'cov': 3.94},
        'FY2': {'hdg': np.radians(-173.3), 'spd': 120., 'td': 3.000, 'tdl': 4.000, 'cov': 0.00},
        'FY3': {'hdg': np.radians(94.2), 'spd': 137.6, 'td': 18.677, 'tdl': 3.628, 'cov': 2.60},
    }
    for did, p in drones_p4.items():
        p['pb'] = bomb_burst_position(did, p['spd'], p['hdg'], p['td'], p['tdl'])
        p['tb'] = p['td'] + p['tdl']
    union_cov = compute_multi_coverage('M1',
        [(p['pb'], p['tb']) for p in drones_p4.values()], dt=0.02)

    # 子图1: X-Y
    ax1 = fig.add_subplot(2, 3, 1)
    ax1.set_title('X-Y: Three Drones → M1', fontsize=11, fontweight='bold')
    ts = np.linspace(0, T_HIT1, 400)
    m_traj = np.array([missile_position('M1', t) for t in ts])
    ax1.plot(m_traj[:,0], m_traj[:,1], 'r-', lw=2, label='M1')
    ax1.plot(0, 0, 'kx', ms=10, mew=2)
    ax1.plot(REAL_TARGET[0], REAL_TARGET[1], 'gs', ms=8)
    for did, p in drones_p4.items():
        c = D_COLORS[did]
        d0 = DRONES[did]
        v_d = p['spd'] * np.array([np.cos(p['hdg']), np.sin(p['hdg']), 0])
        path = np.array([d0 + v_d * t for t in np.linspace(0, p['td']+p['tdl']+3, 100)])
        alpha = 0.5 if p['cov'] < 0.01 else 1.0
        ax1.plot(path[:,0], path[:,1], '-', color=c, lw=2, alpha=alpha,
                 label=f'{did} ({p["cov"]:.1f}s)')
        ax1.plot(d0[0], d0[1], 'o', color=c, ms=7)
        ax1.plot(p['pb'][0], p['pb'][1], '*', color=c, ms=14, mew=1.5, alpha=alpha)
    ax1.set_xlabel('X'); ax1.set_ylabel('Y')
    ax1.legend(fontsize=7); ax1.grid(alpha=0.3); ax1.set_aspect('equal')
    ax1.set_xlim(-500, 21000); ax1.set_ylim(-4000, 3000)

    # 子图2: X-Z
    ax2 = fig.add_subplot(2, 3, 2)
    ax2.set_title('X-Z: Three Drones → M1', fontsize=11, fontweight='bold')
    ax2.plot(m_traj[:,0], m_traj[:,2], 'r-', lw=2)
    for did, p in drones_p4.items():
        c = D_COLORS[did]; d0 = DRONES[did]
        v_d = p['spd'] * np.array([np.cos(p['hdg']), np.sin(p['hdg']), 0])
        path = np.array([d0 + v_d * t for t in np.linspace(0, p['td']+p['tdl']+3, 100)])
        alpha = 0.5 if p['cov'] < 0.01 else 1.0
        ax2.plot(path[:,0], path[:,2], '-', color=c, lw=2, alpha=alpha)
        ax2.plot(p['pb'][0], p['pb'][2], '*', color=c, ms=14, mew=1.5, alpha=alpha)
        ax2.axhline(d0[2], color=c, ls=':', alpha=0.2)
    ax2.set_xlabel('X'); ax2.set_ylabel('Z')
    ax2.grid(alpha=0.3); ax2.set_xlim(-500, 21000)

    # 子图3: 贡献柱状图
    ax3 = fig.add_subplot(2, 3, 3)
    covs = [p['cov'] for p in drones_p4.values()] + [union_cov]
    colors_bar = [D_COLORS[d] for d in drones_p4] + ['#555555']
    bars = ax3.bar(range(4), covs, color=colors_bar, width=0.5)
    for i, v in enumerate(covs):
        ax3.text(i, v+0.2, f'{v:.2f}s', ha='center', fontsize=11, fontweight='bold')
    ax3.set_xticklabels(['', 'FY1', 'FY2', 'FY3', 'UNION'])
    ax3.set_ylabel('Coverage (s)'); ax3.set_title('Per-Drone Contribution', fontsize=11, fontweight='bold')
    ax3.grid(axis='y', alpha=0.3)

    # 子图4-6: 3D三视角
    for vi, (elev, azim, title) in enumerate([(90, -90, 'Top View'), (0, -90, 'Front View'), (30, -50, 'Perspective')]):
        ax = fig.add_subplot(2, 3, 4+vi, projection='3d')
        ax.set_title(title, fontsize=10)
        ax.plot3D(m_traj[:,0], m_traj[:,1], m_traj[:,2], 'r-', lw=1)
        ax.scatter(0, 0, 0, c='black', s=50, marker='x')
        ax.scatter(*REAL_TARGET, c='green', s=50, marker='s')
        for did, p in drones_p4.items():
            c = D_COLORS[did]; d0 = DRONES[did]; alpha = 0.5 if p['cov'] < 0.01 else 1.0
            v_d = p['spd'] * np.array([np.cos(p['hdg']), np.sin(p['hdg']), 0])
            path = np.array([d0 + v_d * t for t in np.linspace(0, p['td']+p['tdl']+3, 60)])
            ax.plot3D(path[:,0], path[:,1], path[:,2], '-', color=c, lw=1, alpha=alpha)
            ax.scatter(*p['pb'], c=c, s=60, marker='*', edgecolors='black', linewidths=0.5, alpha=alpha)
            if p['cov'] > 0.1:
                u = np.linspace(0, 2*np.pi, 10); vv = np.linspace(0, np.pi, 7)
                mc = p['pb'] + np.array([0, 0, -CLOUD_SINK*3])
                xs = mc[0] + CLOUD_RADIUS * np.outer(np.cos(u), np.sin(vv))
                ys = mc[1] + CLOUD_RADIUS * np.outer(np.sin(u), np.sin(vv))
                zs = mc[2] + CLOUD_RADIUS * np.outer(np.ones_like(u), np.cos(vv))
                ax.plot_surface(xs, ys, zs, color=c, alpha=0.15, linewidth=0)
        ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
        ax.view_init(elev, azim)

    fig.suptitle(f'Problem 4: Three-Drone Cooperation → M1  |  '
                 f'FY1={drones_p4["FY1"]["cov"]:.1f}s + FY2=0s + '
                 f'FY3={drones_p4["FY3"]["cov"]:.1f}s = UNION {union_cov:.2f}s',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    save('problem4_multi_drone.png')
    plt.close()


# ================================================================
# 图5: 问题5 — 全系统
# ================================================================
def plot_problem5():
    """问题5: 5机各1弹 → M1+M2+M3"""
    fig = plt.figure(figsize=(18, 9))

    # 完整参数
    p5 = {
        'FY1': {'hdg': np.radians(178.3), 'spd': 93., 'td': 0.100, 'tdl': 2.908, 'target': 'M1'},
        'FY2': {'hdg': np.radians(237.1), 'spd': 112., 'td': 5.289, 'tdl': 5.286, 'target': 'M2'},
        'FY3': {'hdg': np.radians(153.4), 'spd': 120., 'td': 3.000, 'tdl': 4.000, 'target': 'M3'},
        'FY4': {'hdg': np.radians(-169.7), 'spd': 120., 'td': 3.000, 'tdl': 4.000, 'target': 'M2'},
        'FY5': {'hdg': np.radians(135.1), 'spd': 122., 'td': 14.389, 'tdl': 4.428, 'target': 'M3'},
    }
    for did, p in p5.items():
        p['pb'] = bomb_burst_position(did, p['spd'], p['hdg'], p['td'], p['tdl'])
        p['tb'] = p['td'] + p['tdl']

    cov_M1 = 4.640; cov_M2 = 4.580; cov_M3 = 2.720

    # 子图1: 全局X-Y俯视图
    ax1 = fig.add_subplot(2, 3, 1)
    ax1.set_title('Full System: X-Y Overview', fontsize=11, fontweight='bold')
    missile_data = [('M1', M1_0, v_m1, T_HIT1), ('M2', M2_0, v_m2, T_HIT2), ('M3', M3_0, v_m3, T_HIT3)]
    for mid, m0, vm, th in missile_data:
        traj = np.array([m0 + vm * t for t in np.linspace(0, th, 300)])
        ax1.plot(traj[:,0], traj[:,1], '-', color=M_COLORS[mid], lw=2, label=f'{mid}')
        ax1.plot(m0[0], m0[1], '^', color=M_COLORS[mid], ms=8)
    ax1.plot(0, 0, 'kx', ms=12, mew=2, label='Decoy')
    ax1.plot(REAL_TARGET[0], REAL_TARGET[1], 'gs', ms=10, label='Real Target')

    for did, p in p5.items():
        c = D_COLORS[did]; mc = M_COLORS[p['target']]; d0 = DRONES[did]
        v_d = p['spd'] * np.array([np.cos(p['hdg']), np.sin(p['hdg']), 0])
        path = np.array([d0 + v_d * t for t in np.linspace(0, p['td']+p['tdl']+2, 80)])
        ax1.plot(path[:,0], path[:,1], '-', color=c, lw=1.2)
        ax1.plot(d0[0], d0[1], 'o', color=c, ms=6)
        ax1.plot(p['pb'][0], p['pb'][1], 'D', color=mc, ms=8, mew=1)
    ax1.set_xlabel('X'); ax1.set_ylabel('Y')
    ax1.legend(fontsize=6, ncol=2, loc='upper right'); ax1.grid(alpha=0.3)
    ax1.set_aspect('equal'); ax1.set_xlim(-2000, 22000); ax1.set_ylim(-5000, 4000)

    # 子图2: 遮蔽贡献
    ax2 = fig.add_subplot(2, 3, 2)
    covs_all = [cov_M1, cov_M2, cov_M3, cov_M1+cov_M2+cov_M3]
    colors_all = [M_COLORS['M1'], M_COLORS['M2'], M_COLORS['M3'], '#555']
    ax2.bar(range(4), covs_all, color=colors_all, width=0.5)
    for i, v in enumerate(covs_all):
        ax2.text(i, v+0.3, f'{v:.2f}s', ha='center', fontsize=12, fontweight='bold')
    ax2.set_xticklabels(['', 'M1', 'M2', 'M3', 'TOTAL']); ax2.set_ylabel('Coverage (s)')
    ax2.set_title('Coverage by Missile', fontsize=11, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)

    # 子图3: 分配表
    ax3 = fig.add_subplot(2, 3, 3)
    ax3.axis('off')
    ax3.set_title('Drone-Missile Allocation', fontsize=11, fontweight='bold')
    lines = [
        ('M1 ← FY1', M_COLORS['M1'], '4.64s'),
        ('M2 ← FY2 + FY4', M_COLORS['M2'], '4.58s'),
        ('M3 ← FY3 + FY5', M_COLORS['M3'], '2.72s'),
        ('', 'gray', ''),
        ('TOTAL = 11.94s', '#000000', ''),
    ]
    for i, (txt, c, cov) in enumerate(lines):
        if not txt:
            continue
        fontsize = 16 if 'TOTAL' in txt else 14
        y = 0.9 - i*0.2
        ax3.text(0.5, y, txt, ha='center', fontsize=fontsize,
                 fontweight='bold', color=c, transform=ax3.transAxes)
        if cov:
            ax3.text(0.5, y-0.08, cov, ha='center', fontsize=11,
                     color=c, transform=ax3.transAxes)

    # 子图4-6: 3D
    for vi, (elev, azim, title) in enumerate([(90, -90, 'Top'), (0, -90, 'Front'), (30, -55, 'Perspective')]):
        ax = fig.add_subplot(2, 3, 4+vi, projection='3d')
        ax.set_title(title, fontsize=10)
        for mid, m0, vm, th in missile_data:
            traj = np.array([m0 + vm * t for t in np.linspace(0, th, 200)])
            ax.plot3D(traj[:,0], traj[:,1], traj[:,2], '-', color=M_COLORS[mid], lw=1.2)
        ax.scatter(0, 0, 0, c='black', s=40, marker='x')
        for did, p in p5.items():
            c = D_COLORS[did]; d0 = DRONES[did]
            v_d = p['spd'] * np.array([np.cos(p['hdg']), np.sin(p['hdg']), 0])
            path = np.array([d0 + v_d * t for t in np.linspace(0, p['td']+p['tdl']+2, 50)])
            ax.plot3D(path[:,0], path[:,1], path[:,2], '-', color=c, lw=0.8)
            ax.scatter(*p['pb'], c=M_COLORS[p['target']], s=40, marker='D', edgecolors='black', linewidths=0.3)
        ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
        ax.view_init(elev, azim)

    fig.suptitle(f'Problem 5: Full System — 5 Drones × 1 Bomb → M1+M2+M3 = 11.94s\n'
                 f'M1←FY1 | M2←FY2+FY4 | M3←FY3+FY5',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    save('problem5_full_system.png')
    plt.close()


# ================================================================
# 图6: 五题汇总
# ================================================================
def plot_coverage_summary():
    """五题结果汇总条状图"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    labels = ['P1', 'P2', 'P3', 'P4', 'P5']
    descs = ['FY1×1\n(given)', 'FY1×1\n(optimized)', 'FY1×3\n(sequential)',
             '3 drones\n→M1', '5 drones\n→M1+M2+M3']
    covs = [1.42, 4.74, 4.74, 6.48, 11.94]
    colors_bar = ['#95A5A6', '#2980B9', '#27AE60', '#E67E22', '#C0392B']

    # 左: 柱状图
    ax1.bar(range(5), covs, color=colors_bar, width=0.5, edgecolor='white', lw=1)
    ax1.plot(range(5), covs, 'k-o', lw=2, ms=8, mfc='black')
    for i, (v, d) in enumerate(zip(covs, descs)):
        ax1.text(i, v+0.4, f'{v:.2f}s', ha='center', fontsize=13, fontweight='bold', color=colors_bar[i])
        ax1.text(i, v/2, d, ha='center', fontsize=8, color='white', fontweight='bold')
    ax1.set_xticklabels([''] + labels); ax1.set_ylabel('Coverage (s)', fontsize=13)
    ax1.set_title('Coverage Duration by Problem', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3); ax1.set_ylim(0, 14)

    # 右: 改进百分比
    improvements = [0, 234, 234, 356, 741]
    ax2.bar(range(5), improvements, color=colors_bar, width=0.5, edgecolor='white', lw=1)
    ax2.fill_between(np.linspace(0, 4, 50),
                     np.interp(np.linspace(0, 4, 50), range(5), improvements),
                     alpha=0.15, color='green')
    for i, v in enumerate(improvements):
        lbl = 'baseline' if i == 0 else f'+{v}%'
        ax2.text(i, v+30, lbl, ha='center', fontsize=13, fontweight='bold', color=colors_bar[i])
    ax2.set_xticklabels([''] + labels); ax2.set_ylabel('Improvement vs P1 (%)', fontsize=13)
    ax2.set_title('Improvement over Problem 1 (1.42s)', fontsize=14, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)

    fig.suptitle('2025 CUMCM Problem A — Results Summary', fontsize=16, fontweight='bold')
    plt.tight_layout()
    save('coverage_summary.png')
    plt.close()


# ================================================================
# 图7: 时间线甘特图
# ================================================================
def plot_timeline_gantt():
    """所有问题遮蔽区间在时间轴上的全景"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 7), gridspec_kw={'height_ratios': [3, 1]})

    # 遮蔽区间数据
    intervals_data = [
        ('P1: FY1×1 (given)', [('M1', [(8.04, 9.46)])]),
        ('P2: FY1×1 (optimized)', [('M1', [(1.20, 5.94)])]),
        ('P3: FY1×3', [('M1', [(1.20, 5.94)])]),
        ('P4: 3 drones', [('M1', [(3.77, 8.0), (20.0, 22.6)])]),
        ('P5: Full system', [('M1', [(3.00, 7.64)]), ('M2', [(10.50, 15.08)]), ('M3', [(14.0, 16.72)])]),
    ]

    y_pos = 0
    y_ticks, y_labels = [], []
    for prob_name, missile_intervals in intervals_data:
        y_pos += 0.3
        y_ticks.append(y_pos); y_labels.append('')
        for mid, intvs in missile_intervals:
            y_pos += 0.45
            y_ticks.append(y_pos)
            y_labels.append(f'{prob_name[:12]} | {mid}')
            for s, e in intvs:
                dur = e - s
                ax1.barh(y_pos, dur, left=s, height=0.35, color=M_COLORS[mid],
                         alpha=0.75, edgecolor='black', lw=0.8)
                if dur > 0.3:
                    ax1.text(s+dur/2, y_pos, f'{dur:.2f}s', ha='center', va='center',
                             fontsize=7, fontweight='bold', color='white')
        y_pos += 0.2

    # 导弹命中线
    for mid, th, ls in [('M1', 67.0, '-'), ('M2', 63.75, '--'), ('M3', 60.37, ':')]:
        ax1.axvline(th, color=M_COLORS[mid], ls=ls, alpha=0.6, lw=1.5)
        ax1.text(th+0.2, y_pos-0.3, f'{mid} impact\n{th:.0f}s', fontsize=7,
                 color=M_COLORS[mid], fontweight='bold')

    ax1.set_yticks(y_ticks); ax1.set_yticklabels(y_labels, fontsize=8)
    ax1.set_xlabel('Time (s)', fontsize=12); ax1.set_xlim(0, 72)
    ax1.set_title('Coverage Timeline — All Problems (Gantt View)', fontsize=14, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)
    ax1.invert_yaxis()

    # 底部: 总时长对比
    total_covs = [1.42, 4.74, 4.74, 6.48, 11.94]
    colors_bar = ['#95A5A6', '#2980B9', '#27AE60', '#E67E22', '#C0392B']
    ax2.bar(range(5), total_covs, color=colors_bar, width=0.5)
    for i, v in enumerate(total_covs):
        ax2.text(i, v+0.3, f'{v:.2f}s', ha='center', fontsize=12, fontweight='bold')
    ax2.set_xticklabels(['', 'P1', 'P2', 'P3', 'P4', 'P5'])
    ax2.set_ylabel('Total Coverage (s)', fontsize=12)
    ax2.set_title('Total Coverage by Problem', fontsize=13)
    ax2.grid(axis='y', alpha=0.3)

    fig.suptitle('2025 CUMCM Problem A — Coverage Timeline Panorama', fontsize=15, fontweight='bold')
    plt.tight_layout()
    save('timeline_gantt.png')
    plt.close()


# ================================================================
# 图8: 核心几何洞察
# ================================================================
def plot_geometry_insight():
    """航向角如何影响遮蔽: LOS扫描 + 云团位置"""
    fig = plt.figure(figsize=(18, 9))

    # 主图: X-Y 几何分析
    ax_main = fig.add_axes([0.05, 0.08, 0.62, 0.88])
    ax_main.set_title('Why Heading Angle Matters: LOS Sweep Geometry', fontsize=14, fontweight='bold')
    ax_main.set_aspect('equal')

    ts = np.linspace(0, T_HIT1, 500)
    m_traj = np.array([missile_position('M1', t) for t in ts])
    ax_main.plot(m_traj[:,0], m_traj[:,1], 'k-', lw=3, label='M1 Trajectory (300 m/s)')
    ax_main.plot(M1_0[0], M1_0[1], 'k^', ms=14, label='M1 Start (20000,0)')
    ax_main.plot(0, 0, 'kx', ms=16, mew=3, label='Decoy (origin)')
    ax_main.plot(REAL_TARGET[0], REAL_TARGET[1], 'gs', ms=14, label='Real Target (0,200)')
    ax_main.plot(DRONES['FY1'][0], DRONES['FY1'][1], 'bo', ms=10, label='FY1 Start')

    # 多组LOS (导弹→真目标), 展示扫描效果
    los_times = [3, 8, 15, 30, 50]
    alphas = [0.1, 0.2, 0.35, 0.55, 0.75]
    for ti, t_los in enumerate(los_times):
        m_pos = missile_position('M1', t_los)
        ax_main.plot([m_pos[0], REAL_TARGET[0]], [m_pos[1], REAL_TARGET[1]],
                     color='#922B21', lw=1.5, ls=':', alpha=alphas[ti])
        ax_main.plot(m_pos[0], m_pos[1], 'r.', ms=10)
        ax_main.annotate(f't={t_los}s', (m_pos[0]+400, m_pos[1]+150), fontsize=8,
                         color='#922B21', fontweight='bold')

    # 方案A: 180°
    pA = {'hdg': np.pi, 'spd': 120., 'td': 1.5, 'tdl': 3.6, 'color': '#C0392B', 'label': 'A: heading=180°'}
    pB = {'hdg': np.radians(7.5), 'spd': 70., 'td': 0.1, 'tdl': 1.04, 'color': '#2471A3', 'label': 'B: heading=7.5°'}

    d0 = DRONES['FY1']
    for p in [pA, pB]:
        v_d = p['spd'] * np.array([np.cos(p['hdg']), np.sin(p['hdg']), 0])
        path = np.array([d0 + v_d * t for t in np.linspace(p['td']-0.5, p['td']+p['tdl']+5, 120)])
        ax_main.plot(path[:,0], path[:,1], '-', color=p['color'], lw=2.5, label=p['label'],
                     path_effects=[pe.Stroke(linewidth=3, foreground='white'), pe.Normal()])
        b = bomb_burst_position('FY1', p['spd'], p['hdg'], p['td'], p['tdl'])
        ax_main.plot(b[0], b[1], '*', color=p['color'], ms=18, mew=2,
                     label=f'{p["label"]} burst')
        # 云团圆
        ax_main.add_patch(Circle(b[:2], CLOUD_RADIUS, fc='none', ec=p['color'], ls='--', lw=2.5))

        # 标注云团半径箭头
        cov = compute_coverage('M1', b, p['td']+p['tdl'], dt=0.02)
        ax_main.annotate(f'{p["label"]}\nCoverage: {cov:.2f}s',
                         (b[0], b[1]), (b[0]-3000, b[1]-600),
                         arrowprops=dict(arrowstyle='->', color=p['color'], lw=2),
                         fontsize=11, fontweight='bold', color=p['color'],
                         bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=p['color'], alpha=0.9))

    ax_main.set_xlabel('X (m)', fontsize=12); ax_main.set_ylabel('Y (m)', fontsize=12)
    ax_main.legend(fontsize=8, loc='lower left')
    ax_main.grid(alpha=0.3)
    ax_main.set_xlim(-2000, 22000); ax_main.set_ylim(-1200, 3000)

    # 右上: 时长对比
    ax_r1 = fig.add_axes([0.72, 0.58, 0.25, 0.35])
    ax_r1.bar([1, 2], [1.42, 4.74], color=[pA['color'], pB['color']], width=0.5)
    ax_r1.text(1, 1.8, '1.42s', ha='center', fontsize=13, fontweight='bold', color=pA['color'])
    ax_r1.text(2, 5.1, '4.74s', ha='center', fontsize=13, fontweight='bold', color=pB['color'])
    ax_r1.text(1.5, 3.0, '+234%', ha='center', fontsize=18, fontweight='bold', color='green')
    ax_r1.set_xticklabels(['', '180°\n(P1)', '', '7.5°\n(P2)']); ax_r1.set_ylabel('Coverage (s)')
    ax_r1.set_title('Coverage Comparison', fontsize=12, fontweight='bold')
    ax_r1.grid(axis='y', alpha=0.3)

    # 右下: 文字解释
    ax_r2 = fig.add_axes([0.72, 0.08, 0.25, 0.45])
    ax_r2.axis('off')
    ax_r2.set_title('Geometric Principle', fontsize=12, fontweight='bold')
    explanation = (
        '· LOS = line from missile\n'
        '  to real target (0,200,0)\n\n'
        '· As missile approaches,\n'
        '  LOS sweeps through space\n'
        '  (red dotted lines)\n\n'
        '· Cloud must lie within\n'
        '  this sweeping path for\n'
        '  the LOS to intersect it\n\n'
        '· A (180°): cloud directly\n'
        '  ahead → LOS only hits\n'
        '  late in flight\n\n'
        '· B (7.5°): cloud offset\n'
        '  sideways → LOS enters\n'
        '  cloud much earlier →\n'
        '  3.3× longer coverage!'
    )
    ax_r2.text(0.02, 0.98, explanation, fontsize=10, va='top', fontfamily='monospace',
               bbox=dict(boxstyle='round', fc='#F8F9F9', ec='#BDC3C7', alpha=0.9))

    fig.suptitle('Key Insight: Why 7.5° Heading Gives 3.3× More Coverage Than 180°',
                 fontsize=15, fontweight='bold', y=0.98)
    save('geometry_insight.png')
    plt.close()


# ================================================================
# 主入口
# ================================================================
if __name__ == '__main__':
    print('Generating all Python figures...')
    print('='*50)

    plot_problem1()
    plot_problem2()
    plot_problem3()
    plot_problem4()
    plot_problem5()
    plot_coverage_summary()
    plot_timeline_gantt()
    plot_geometry_insight()

    print('='*50)
    print(f'All 8 figures saved to: {OUTPUT}/')
    print('Done!')
