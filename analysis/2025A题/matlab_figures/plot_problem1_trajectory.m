%% plot_problem1_trajectory.m
% 问题1: M1导弹轨迹 + FY1无人机路径 + 烟幕云团 + 遮蔽时刻视线
% 给定参数: FY1航向180°(朝原点), 速度120m/s, 投放1.5s, 延迟3.6s
clear; close all;

%% ===== 物理常数 =====
G = 9.8;  MISSILE_SPEED = 300;  CLOUD_RADIUS = 10;
CLOUD_SINK = 3;  CLOUD_DURATION = 20;

%% ===== 初始位置 =====
M1_0  = [20000, 0, 2000];
FY1_0 = [17800, 0, 1800];
REAL_TARGET = [0, 200, 0];
FAKE_TARGET = [0, 0, 0];

%% ===== 问题1参数 =====
speed   = 120;          % m/s
heading = pi;           % 朝向原点(180°)
t_drop  = 1.5;          % 投放时刻(s)
t_delay = 3.6;          % 起爆延迟(s)
t_burst = t_drop + t_delay;  % 5.1s
t_hit   = norm(M1_0) / MISSILE_SPEED;  % 67.00s

%% ===== 计算无人机轨迹 =====
% 无人机等高度匀速直线飞行
v_drone = speed * [cos(heading), sin(heading), 0];

% 投放点
p_drop = FY1_0 + v_drone * t_drop;

% 起爆点: 抛体运动, v_dz=0
p_burst = p_drop + v_drone * t_delay;
p_burst(3) = p_burst(3) - 0.5 * G * t_delay^2;

fprintf('投放点 (t=%.1fs): (%.1f, %.1f, %.1f)\n', t_drop, p_drop);
fprintf('起爆点 (t=%.1fs): (%.1f, %.1f, %.1f)\n', t_burst, p_burst);

%% ===== 导弹轨迹离散化 =====
t_vals = linspace(0, t_hit, 500);
M1_traj = zeros(length(t_vals), 3);
v_m1 = -MISSILE_SPEED * M1_0 / norm(M1_0);  % 指向原点
for i = 1:length(t_vals)
    M1_traj(i,:) = M1_0 + v_m1 * t_vals(i);
end

%% ===== 遮蔽时刻计算 =====
% 遮蔽区间: t∈[8.04, 9.46], 取中点8.75s
t_shield = 8.75;
t_since  = t_shield - t_burst;
cloud_center = p_burst + [0, 0, -CLOUD_SINK * t_since];
m_pos_shield = M1_0 + v_m1 * t_shield;

fprintf('遮蔽时刻 t=%.2fs: 云团中心 (%.1f, %.1f, %.1f)\n', ...
    t_shield, cloud_center);

%% ====== Figure 1: X-Y 平面 =====
figure('Position', [100, 100, 1400, 600]);

subplot(1,2,1); hold on; grid on; axis equal;
title('问题1: X-Y 平面 (俯视图)', 'FontSize', 14);

% 导弹轨迹
plot(M1_traj(:,1), M1_traj(:,2), 'r-', 'LineWidth', 2, ...
    'DisplayName', 'M1 导弹轨迹');
plot(M1_0(1), M1_0(2), 'r^', 'MarkerSize', 10, 'MarkerFaceColor', 'r', ...
    'DisplayName', 'M1 初始位置');

% 假目标 & 真目标
plot(0, 0, 'kx', 'MarkerSize', 12, 'LineWidth', 2, ...
    'DisplayName', '假目标(原点)');
plot(REAL_TARGET(1), REAL_TARGET(2), 'gs', 'MarkerSize', 10, ...
    'MarkerFaceColor', 'g', 'DisplayName', '真目标(0,200)');

% FY1无人机飞行路径
FY1_path_end = FY1_0 + v_drone * 10;  % 飞到t=10s
plot([FY1_0(1), FY1_path_end(1)], [FY1_0(2), FY1_path_end(2)], ...
    'b--', 'LineWidth', 1.5, 'DisplayName', 'FY1 飞行路径');
plot(FY1_0(1), FY1_0(2), 'bo', 'MarkerSize', 8, 'MarkerFaceColor', 'b', ...
    'DisplayName', 'FY1 初始位置');
plot(p_burst(1), p_burst(2), 'm*', 'MarkerSize', 12, 'LineWidth', 1.5, ...
    'DisplayName', '起爆点');

% 遮蔽时刻: 云团投影(圆) + 视线
viscircles(cloud_center(1:2), CLOUD_RADIUS, 'Color', [0.5 0 0.5], ...
    'LineWidth', 1.5, 'LineStyle', '--');
plot(cloud_center(1), cloud_center(2), 'mo', 'MarkerSize', 8, ...
    'MarkerFaceColor', 'm', 'DisplayName', '云团中心');

% 遮蔽时刻视线(导弹→真目标)
plot([m_pos_shield(1), REAL_TARGET(1)], ...
     [m_pos_shield(2), REAL_TARGET(2)], ...
     'k-', 'LineWidth', 3, 'DisplayName', '视线 (t=8.75s)');
plot(m_pos_shield(1), m_pos_shield(2), 'rd', 'MarkerSize', 8, ...
    'MarkerFaceColor', 'y', 'DisplayName', 'M1 (t=8.75s)');

xlabel('X (m)'); ylabel('Y (m)');
legend('Location', 'best', 'FontSize', 8);
xlim([-500, 21000]); ylim([-500, 2500]);

%% ====== Figure 1 右: X-Z 平面 =====
subplot(1,2,2); hold on; grid on;
title('问题1: X-Z 平面 (侧视图)', 'FontSize', 14);

plot(M1_traj(:,1), M1_traj(:,3), 'r-', 'LineWidth', 2, ...
    'DisplayName', 'M1 导弹轨迹');
plot(M1_0(1), M1_0(3), 'r^', 'MarkerSize', 10, 'MarkerFaceColor', 'r');
plot(0, 0, 'kx', 'MarkerSize', 12, 'LineWidth', 2, ...
    'DisplayName', '假目标');
plot(REAL_TARGET(1), REAL_TARGET(3), 'gs', 'MarkerSize', 10, ...
    'MarkerFaceColor', 'g');

% FY1等高度飞行
plot([FY1_0(1), FY1_path_end(1)], [FY1_0(3), FY1_path_end(3)], ...
    'b--', 'LineWidth', 1.5);
plot(FY1_0(1), FY1_0(3), 'bo', 'MarkerSize', 8, 'MarkerFaceColor', 'b');
plot(p_burst(1), p_burst(3), 'm*', 'MarkerSize', 12, 'LineWidth', 1.5);

% 遮蔽时刻云团(圆形投影到XZ平面)
viscircles(cloud_center([1,3]), CLOUD_RADIUS, 'Color', [0.5 0 0.5], ...
    'LineWidth', 1.5, 'LineStyle', '--');
plot(cloud_center(1), cloud_center(3), 'mo', 'MarkerSize', 8, ...
    'MarkerFaceColor', 'm');

% 遮蔽时刻视线
plot([m_pos_shield(1), REAL_TARGET(1)], ...
     [m_pos_shield(3), REAL_TARGET(3)], ...
     'k-', 'LineWidth', 3);
plot(m_pos_shield(1), m_pos_shield(3), 'rd', 'MarkerSize', 8, ...
    'MarkerFaceColor', 'y');

xlabel('X (m)'); ylabel('Z (m)');
legend('Location', 'best', 'FontSize', 8);
xlim([-500, 21000]);

sgtitle(sprintf(['问题1: 遮蔽时长=1.42s, 区间[8.04,9.46]\\n' ...
    'FY1航向=180°, v=120m/s, 投放=1.5s, 延迟=3.6s']), ...
    'FontSize', 13);
saveas(gcf, 'problem1_trajectory.png');
fprintf('Figure saved: problem1_trajectory.png\n');
