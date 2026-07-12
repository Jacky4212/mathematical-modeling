%% plot_problem2_optimization.m
% 问题2: 问题1参数 vs 优化参数 对比 — 航向角的关键影响
% 问题1: heading=180°, v=120m/s, drop=1.5s, delay=3.6s → 遮蔽1.42s
% 问题2: heading=7.5°,  v=70m/s,  drop=0.1s, delay=1.04s → 遮蔽4.74s
clear; close all;

%% ===== 物理常数 =====
G = 9.8;  MISSILE_SPEED = 300;  CLOUD_RADIUS = 10;
CLOUD_SINK = 3;  CLOUD_DURATION = 20;

M1_0  = [20000, 0, 2000];
FY1_0 = [17800, 0, 1800];
REAL_TARGET = [0, 200, 0];
t_hit  = norm(M1_0) / MISSILE_SPEED;

%% ===== 两组参数 =====
% 方案A: 问题1 (原始)
pA.heading = pi;           pA.speed = 120;
pA.t_drop = 1.5;           pA.t_delay = 3.6;
pA.label  = '问题1: θ=180°, v=120m/s';
pA.color  = [0.8 0.2 0.2];  % red

% 方案B: 问题2 (优化)
pB.heading = deg2rad(7.50); pB.speed = 70;
pB.t_drop = 0.100;          pB.t_delay = 1.040;
pB.label  = '问题2: θ=7.5°, v=70m/s';
pB.color  = [0.2 0.5 0.8];  % blue

%% ===== 计算函数 =====
v_m1 = -MISSILE_SPEED * M1_0 / norm(M1_0);

compute_burst = @(p) deal( ...
    FY1_0 + p.speed*[cos(p.heading), sin(p.heading), 0]*p.t_drop + ...
    p.speed*[cos(p.heading), sin(p.heading), 0]*p.t_delay - ...
    [0, 0, 0.5*G*p.t_delay^2], ...
    p.t_drop + p.t_delay);

is_shielded_at = @(p_burst, t_burst, t) ...
    (t >= t_burst) && (t <= t_burst + CLOUD_DURATION) && ...
    line_sphere_hit(M1_0+v_m1*t, REAL_TARGET, ...
    p_burst+[0,0,-CLOUD_SINK*(t-t_burst)], CLOUD_RADIUS);

%% ===== 离散化遮蔽计算 =====
dt = 0.02;
for s = {'A','B'}
    p = eval(['p' s{1}]);
    [p_burst, t_burst] = compute_burst(p);
    eval([s{1} '_burst = p_burst;']);
    eval([s{1} '_t_burst = t_burst;']);

    t_vals = max(0, t_burst):dt:min(t_hit, t_burst+CLOUD_DURATION);
    shielded = false(size(t_vals));
    for i = 1:length(t_vals)
        shielded(i) = is_shielded_at(p_burst, t_burst, t_vals(i));
    end
    eval([s{1} '_t_vals = t_vals;']);
    eval([s{1} '_shielded = shielded;']);
    eval([s{1} '_cov = sum(shielded)*dt;']);
end

fprintf('方案A (问题1): 遮蔽 %.2fs\n', A_cov);
fprintf('方案B (问题2): 遮蔽 %.2fs\n', B_cov);
fprintf('改进: +%.0f%%\n', (B_cov - A_cov)/A_cov * 100);

%% ====== Figure 2: 并排对比 =====
figure('Position', [50, 50, 1600, 750]);

%% ---- 子图1: X-Y平面轨迹对比 ----
subplot(2,3,1); hold on; grid on; axis equal;
title('X-Y 平面: 轨迹对比', 'FontSize', 12);

% M1轨迹
t_all = linspace(0, t_hit, 500);
M1_traj = M1_0 + v_m1 .* t_all';
plot(M1_traj(:,1), M1_traj(:,2), 'k-', 'LineWidth', 1.5, ...
    'DisplayName', 'M1 轨迹');
plot(M1_0(1), M1_0(2), 'k^', 'MarkerSize', 10, 'MarkerFaceColor', 'k');
plot(0, 0, 'kx', 'MarkerSize', 12, 'LineWidth', 2);
plot(REAL_TARGET(1), REAL_TARGET(2), 'gs', 'MarkerSize', 10, ...
    'MarkerFaceColor', 'g');

% 两组方案的无人机轨迹 & 起爆点
for s = {'A','B'}
    p = eval(['p' s{1}]);
    v_d = p.speed * [cos(p.heading), sin(p.heading), 0];
    t_end_plot = min(15, p.t_drop + p.t_delay + 5);
    d_path = FY1_0 + v_d .* linspace(0, t_end_plot, 200)';
    plot(d_path(:,1), d_path(:,2), '-', 'Color', p.color, ...
        'LineWidth', 2, 'DisplayName', [p.label ' 飞行路径']);
    plot(FY1_0(1), FY1_0(2), 'o', 'Color', p.color, ...
        'MarkerSize', 8, 'MarkerFaceColor', p.color);
    b = eval([s{1} '_burst']);
    plot(b(1), b(2), '*', 'Color', p.color, 'MarkerSize', 14, ...
        'LineWidth', 1.5, 'DisplayName', [p.label ' 起爆点']);
end
xlabel('X (m)'); ylabel('Y (m)'); legend('Location', 'best', 'FontSize', 7);
xlim([-500, 21000]); ylim([-500, 2500]);

%% ---- 子图2: X-Z平面轨迹对比 ----
subplot(2,3,2); hold on; grid on;
title('X-Z 平面: 轨迹对比', 'FontSize', 12);

plot(M1_traj(:,1), M1_traj(:,3), 'k-', 'LineWidth', 1.5);
plot(M1_0(1), M1_0(3), 'k^', 'MarkerSize', 10, 'MarkerFaceColor', 'k');
plot(0, 0, 'kx', 'MarkerSize', 12, 'LineWidth', 2);

for s = {'A','B'}
    p = eval(['p' s{1}]);
    v_d = p.speed * [cos(p.heading), sin(p.heading), 0];
    t_end = min(15, p.t_drop + p.t_delay + 5);
    d_path = FY1_0 + v_d .* linspace(0, t_end, 200)';
    plot(d_path(:,1), d_path(:,3), '-', 'Color', p.color, ...
        'LineWidth', 2);
    b = eval([s{1} '_burst']);
    plot(b(1), b(3), '*', 'Color', p.color, 'MarkerSize', 14, ...
        'LineWidth', 1.5);
    % 等高度虚线
    yline(FY1_0(3), '--', 'Color', p.color, 'Alpha', 0.3);
end
xlabel('X (m)'); ylabel('Z (m)');
legend({'M1', '', '假目标', '', 'A:问题1', '', 'B:问题2', ''}, ...
    'Location', 'best', 'FontSize', 7);
xlim([-500, 21000]);

%% ---- 子图3: 遮蔽信号时间线 ----
subplot(2,3,3); hold on; grid on;
title('遮蔽信号时间线', 'FontSize', 12);

offset_B = -0.15;  offset_A = 0.15;

% 方案B (在上面)
for i = 1:length(B_t_vals)-1
    if B_shielded(i)
        patch([B_t_vals(i) B_t_vals(i+1) B_t_vals(i+1) B_t_vals(i)], ...
              [offset_B-0.12 offset_B-0.12 offset_B+0.12 offset_B+0.12], ...
              pB.color, 'EdgeColor', 'none', 'FaceAlpha', 0.7);
    end
end
% 方案A (在下面)
for i = 1:length(A_t_vals)-1
    if A_shielded(i)
        patch([A_t_vals(i) A_t_vals(i+1) A_t_vals(i+1) A_t_vals(i)], ...
              [offset_A-0.12 offset_A-0.12 offset_A+0.12 offset_A+0.12], ...
              pA.color, 'EdgeColor', 'none', 'FaceAlpha', 0.7);
    end
end

text(40, offset_B, sprintf('问题2: %.2fs', B_cov), 'FontSize', 11, ...
    'FontWeight', 'bold', 'Color', pB.color);
text(40, offset_A, sprintf('问题1: %.2fs', A_cov), 'FontSize', 11, ...
    'FontWeight', 'bold', 'Color', pA.color);

xlabel('时间 (s)'); ylim([-0.6, 0.6]);
yticks([]);

%% ---- 子图4: 遮蔽时长对比柱状图 ----
subplot(2,3,4); hold on; grid on;
bar([1, 2], [A_cov, B_cov], 0.5);
bar(1, A_cov, 0.5, 'FaceColor', pA.color);
bar(2, B_cov, 0.5, 'FaceColor', pB.color);
text(1, A_cov+0.15, sprintf('%.2fs', A_cov), 'HorizontalAlignment', 'center', ...
    'FontSize', 12, 'FontWeight', 'bold');
text(2, B_cov+0.15, sprintf('%.2fs', B_cov), 'HorizontalAlignment', 'center', ...
    'FontSize', 12, 'FontWeight', 'bold');
text(1.5, max(A_cov,B_cov)*0.5, sprintf('+%.0f%%', (B_cov-A_cov)/A_cov*100), ...
    'HorizontalAlignment', 'center', 'FontSize', 14, 'FontWeight', 'bold', ...
    'Color', [0 0.6 0]);
set(gca, 'XTickLabel', {'问题1 (原始)', '问题2 (优化)'});
ylabel('遮蔽时长 (s)'); title('遮蔽时长对比', 'FontSize', 12);

%% ---- 子图5: 遮蔽时刻3D示意图 ----
subplot(2,3,[5,6]); hold on; grid on; view(45, 25);
title('3D 视图: 遮蔽时刻对比', 'FontSize', 12);

% 导弹轨迹
plot3(M1_traj(:,1), M1_traj(:,2), M1_traj(:,3), 'k-', 'LineWidth', 1);
plot3(M1_0(1), M1_0(2), M1_0(3), 'k^', 'MarkerSize', 10, 'MarkerFaceColor', 'k');
plot3(0, 0, 0, 'kx', 'MarkerSize', 12, 'LineWidth', 2);

% 两组方案的无人机和云团
for s = {'A','B'}
    p = eval(['p' s{1}]);
    b = eval([s{1} '_burst']);
    tb = eval([s{1} '_t_burst']);
    v_d = p.speed * [cos(p.heading), sin(p.heading), 0];

    % 无人机飞行路径
    d_path = FY1_0 + v_d .* linspace(0, min(15, tb+3), 100)';
    plot3(d_path(:,1), d_path(:,2), d_path(:,3), '-', 'Color', p.color, ...
        'LineWidth', 1.5);

    % 起爆点
    plot3(b(1), b(2), b(3), '*', 'Color', p.color, 'MarkerSize', 14, ...
        'LineWidth', 1.5);

    % 遮蔽中点时刻的云团 (球形)
    t_mid_s = eval([s{1} '_t_vals']);
    t_mid_sh = eval([s{1} '_shielded']);
    mid_idx = find(t_mid_sh, 1, 'first');
    if ~isempty(mid_idx)
        t_mid = t_mid_s(mid_idx + round(sum(t_mid_sh)/2));
        cloud = b + [0, 0, -CLOUD_SINK*(t_mid - tb)];
        [X_s, Y_s, Z_s] = sphere(20);
        surf(cloud(1) + CLOUD_RADIUS*X_s, ...
             cloud(2) + CLOUD_RADIUS*Y_s, ...
             cloud(3) + CLOUD_RADIUS*Z_s, ...
             'FaceColor', p.color, 'EdgeColor', 'none', ...
             'FaceAlpha', 0.3);
    end
end

xlabel('X (m)'); ylabel('Y (m)'); zlabel('Z (m)');
legend({'M1轨迹', 'M1起点', '假目标', ...
    pA.label, [pA.label ' 起爆'], 'A云团', ...
    pB.label, [pB.label ' 起爆'], 'B云团'}, ...
    'Location', 'best', 'FontSize', 7);
xlim([-2000, 22000]); ylim([-2000, 3000]); zlim([0, 2500]);

sgtitle('问题2: 航向角优化 — 为什么7.5°比180°遮蔽长3.3倍?', ...
    'FontSize', 14, 'FontWeight', 'bold');
saveas(gcf, 'problem2_optimization.png');
fprintf('Figure saved: problem2_optimization.png\n');

%% ===== 辅助函数 =====
function hit = line_sphere_hit(p1, p2, center, r)
    v = p2 - p1;
    w = center - p1;
    vdv = dot(v, v);
    if vdv < 1e-12
        hit = norm(w) <= r; return;
    end
    t_proj = max(0, min(1, dot(w,v)/vdv));
    closest = p1 + t_proj * v;
    hit = norm(closest - center) <= r;
end
