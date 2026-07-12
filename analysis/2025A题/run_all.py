"""
2025 CUMCM A题：烟幕干扰弹投放策略 — 最终集成脚本
===================================================
运行所有5个问题，输出结果汇总，生成可视化。
"""
import numpy as np
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core_model import *

from problem1 import solve_problem1
from problem2 import solve_problem2
from problem3 import solve_problem3
from problem4 import solve_problem4
from problem5 import solve_problem5
from generate_excel import generate_result1, generate_result2, generate_result3

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

# 中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def plot_coverage_timeline(results_dict, output_file='coverage_timeline.png'):
    """
    绘制遮蔽时间线图：每条导弹的遮蔽区间
    results_dict: {problem_label: {missile_id: {'intervals': [(s,e),...], 'coverage': float}}}
    """
    fig, axes = plt.subplots(len(results_dict), 1, figsize=(14, 3 * len(results_dict)))
    if len(results_dict) == 1:
        axes = [axes]

    colors = {'M1': '#2196F3', 'M2': '#FF9800', 'M3': '#4CAF50'}

    for ax, (label, missile_data) in zip(axes, results_dict.items()):
        ax.set_title(f'{label}', fontsize=12, fontweight='bold')
        ax.set_xlabel('时间 (s)')
        ax.set_ylabel('导弹')
        ax.set_xlim(0, 70)
        ax.set_ylim(-0.5, 3.5)
        ax.set_yticks([0, 1, 2])
        ax.set_yticklabels(['M1', 'M2', 'M3'])
        ax.grid(True, alpha=0.3)

        for mid, data in missile_data.items():
            if mid == 'M1':
                y = 0
            elif mid == 'M2':
                y = 1
            else:
                y = 2

            color = colors.get(mid, '#999')
            for s, e in data.get('intervals', []):
                ax.barh(y, e - s, left=s, height=0.6, color=color, alpha=0.7,
                        edgecolor='white')
                ax.text((s + e) / 2, y, f'{e-s:.2f}s', ha='center', va='center',
                        fontsize=7, fontweight='bold')

            # 标注总遮蔽时长
            ax.text(68, y, f'∑={data["coverage"]:.2f}s', va='center',
                    fontsize=9, fontweight='bold', color=color)

        # 标注导弹命中时间
        for mid, t_hit in [('M1', 67.00), ('M2', 63.75), ('M3', 60.37)]:
            y = 0 if mid == 'M1' else (1 if mid == 'M2' else 2)
            ax.axvline(x=t_hit, ymin=0, ymax=1, color='red', linestyle='--',
                       alpha=0.5, linewidth=0.8)

    plt.tight_layout()
    filepath = os.path.join(OUTPUT_DIR, output_file)
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'[OK] {filepath}')


def plot_trajectory_2d(problem_label, drone_specs, missile_id='M1',
                       output_file='trajectory.png'):
    """
    绘制无人机和导弹的2D轨迹（x-y平面和x-z平面）
    drone_specs: {drone_id: {theta, speed, drops: [(t_drop, t_delay, burst_pos), ...]}}
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # x-y 平面
    # 导弹轨迹
    t_max = missile_hit_time(missile_id)
    ts = np.linspace(0, t_max, 200)
    m_positions = np.array([missile_position(missile_id, t) for t in ts])

    ax1.plot(m_positions[:, 0], m_positions[:, 1], 'r-', linewidth=2,
             label=f'{missile_id} trajectory', alpha=0.7)
    ax1.scatter(*MISSILES[missile_id][:2], c='red', s=80, marker='^',
                label=f'{missile_id} start', zorder=5)
    ax1.scatter(0, 0, c='black', s=120, marker='x', label='Decoy (0,0)', zorder=5)
    ax1.scatter(REAL_TARGET[0], REAL_TARGET[1], c='green', s=120, marker='s',
                label='Real Target', zorder=5)

    # 无人机轨迹和起爆点
    drone_colors = {'FY1': '#2196F3', 'FY2': '#FF9800', 'FY3': '#4CAF50',
                    'FY4': '#9C27B0', 'FY5': '#00BCD4'}
    for did, spec in drone_specs.items():
        theta, speed = spec['theta'], spec['speed']
        d0 = DRONES[did]
        # 无人机飞行路径（到最后一枚弹的起爆时刻）
        max_t = max(drop + delay for drop, delay, _ in spec['drops']) + 2
        dt = np.linspace(0, max_t, 100)
        d_path = np.array([drone_position(did, speed, theta, t) for t in dt])
        color = drone_colors.get(did, '#999')
        ax1.plot(d_path[:, 0], d_path[:, 1], '-', color=color, linewidth=1.5,
                 alpha=0.6, label=f'{did} path')
        ax1.scatter(*d0[:2], c=color, s=60, marker='o', zorder=4)
        ax1.annotate(did, (d0[0], d0[1]), textcoords="offset points",
                     xytext=(5, 5), fontsize=8, color=color)

        # 起爆点
        for drop, delay, bpos in spec['drops']:
            ax1.scatter(bpos[0], bpos[1], c=color, s=50, marker='*',
                        edgecolors='black', linewidths=0.5, zorder=6)

    ax1.set_xlabel('X (m)')
    ax1.set_ylabel('Y (m)')
    ax1.set_title(f'{problem_label} — X-Y Plane')
    ax1.legend(loc='upper right', fontsize=7)
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')

    # x-z 平面
    ax2.plot(m_positions[:, 0], m_positions[:, 2], 'r-', linewidth=2,
             alpha=0.7)
    ax2.scatter(*MISSILES[missile_id][::2], c='red', s=80, marker='^', zorder=5)
    ax2.scatter(0, 0, c='black', s=120, marker='x', zorder=5)

    for did, spec in drone_specs.items():
        theta, speed = spec['theta'], spec['speed']
        d0 = DRONES[did]
        max_t = max(drop + delay for drop, delay, _ in spec['drops']) + 2
        dt = np.linspace(0, max_t, 100)
        d_path = np.array([drone_position(did, speed, theta, t) for t in dt])
        color = drone_colors.get(did, '#999')
        ax2.plot(d_path[:, 0], d_path[:, 2], '-', color=color, linewidth=1.5, alpha=0.6)
        ax2.scatter(*d0[::2], c=color, s=60, marker='o', zorder=4)
        # z恒定线
        ax2.axhline(y=d0[2], color=color, linestyle=':', alpha=0.3)

        for drop, delay, bpos in spec['drops']:
            ax2.scatter(bpos[0], bpos[2], c=color, s=50, marker='*',
                        edgecolors='black', linewidths=0.5, zorder=6)

    ax2.set_xlabel('X (m)')
    ax2.set_ylabel('Z (m)')
    ax2.set_title(f'{problem_label} — X-Z Plane')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    filepath = os.path.join(OUTPUT_DIR, output_file)
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'[OK] {filepath}')


def main():
    print("="*60)
    print("2025 CUMCM A题 — 完整求解与结果汇总")
    print("="*60)
    start_time = time.time()

    # ====================================================
    # 问题1
    # ====================================================
    print("\n" + "="*60)
    print("问题1: 确定性计算")
    print("="*60)
    cov1 = solve_problem1()

    # ====================================================
    # 问题2
    # ====================================================
    print("\n" + "="*60)
    print("问题2: 单机单弹优化")
    print("="*60)
    x2_opt, cov2 = solve_problem2()
    theta2, speed2, t_drop2, t_delay2 = x2_opt

    # ====================================================
    # 问题3
    # ====================================================
    print("\n" + "="*60)
    print("问题3: 单机三弹优化")
    print("="*60)
    theta3, speed3, t_drops3, t_delays3, cov3 = solve_problem3()

    # ====================================================
    # 问题4
    # ====================================================
    print("\n" + "="*60)
    print("问题4: 三机协同")
    print("="*60)
    results4, cov4, _ = solve_problem4()

    # ====================================================
    # 问题5
    # ====================================================
    print("\n" + "="*60)
    print("问题5: 全系统协同")
    print("="*60)
    all_results5, cov5 = solve_problem5()

    # ====================================================
    # 生成 Excel
    # ====================================================
    print("\n" + "="*60)
    print("生成 Excel 文件")
    print("="*60)
    generate_result1(theta3, speed3, t_drops3, t_delays3, cov3, OUTPUT_DIR)
    generate_result2(results4, cov4, OUTPUT_DIR)
    generate_result3(all_results5, cov5, OUTPUT_DIR)

    # ====================================================
    # 结果汇总
    # ====================================================
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"结果汇总 (总耗时 {elapsed:.1f}s)")
    print(f"{'='*60}")
    print(f"{'问题':<12} {'描述':<24} {'遮蔽时长':>12}")
    print(f"{'-'*50}")
    print(f"{'问题1':<12} {'FY1单弹(给定参数)':<24} {cov1:>10.4f}s")
    print(f"{'问题2':<12} {'FY1单弹(优化)':<24} {cov2:>10.4f}s")
    print(f"{'问题3':<12} {'FY1三弹(优化)':<24} {cov3:>10.4f}s")
    print(f"{'问题4':<12} {'三机协同单弹':<24} {cov4:>10.4f}s")
    print(f"{'问题5':<12} {'全系统协同':<24} {cov5:>10.4f}s")
    print(f"{'-'*50}")

    # 保存汇总到文本文件
    with open(os.path.join(OUTPUT_DIR, 'results_summary.txt'), 'w', encoding='utf-8') as f:
        f.write("2025 CUMCM A题 求解结果汇总\n")
        f.write("="*50 + "\n\n")
        f.write(f"问题1 (FY1单弹, 给定参数): {cov1:.4f} s\n")
        f.write(f"问题2 (FY1单弹, 优化): {cov2:.4f} s\n")
        f.write(f"  航向角={np.degrees(theta2):.2f}°, 速度={speed2:.1f}m/s, "
                f"投放={t_drop2:.3f}s, 延迟={t_delay2:.3f}s\n\n")
        f.write(f"问题3 (FY1三弹): {cov3:.4f} s\n")
        for i in range(3):
            f.write(f"  弹{i+1}: 投放={t_drops3[i]:.3f}s, 延迟={t_delays3[i]:.3f}s\n")
        f.write(f"\n问题4 (三机协同): {cov4:.4f} s\n")
        for did in ['FY1', 'FY2', 'FY3']:
            r = results4[did]
            f.write(f"  {did}: 航向={r['heading_deg']:.1f}°, 速度={r['speed']:.1f}m/s\n")
        f.write(f"\n问题5 (全系统): {cov5:.4f} s\n")
        f.write(f"总运行时间: {elapsed:.1f}s\n")

    print(f"\n结果已保存到 results_summary.txt")


if __name__ == '__main__':
    main()
