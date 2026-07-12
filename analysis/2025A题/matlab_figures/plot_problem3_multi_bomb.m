%% plot_problem3_multi_bomb.m
% 问题3: FY1三弹时序 + 联合遮蔽区间时间线
% 参数: heading=7.5°, v=70m/s
% 弹1: drop=0.100s delay=1.040s → 遮蔽4.74s
% 弹2: drop=3.100s delay=3.000s → 无增量
% 弹3: drop=6.100s delay=2.500s → 无增量
clear; close all;

%% ===== 常数 =====
G = 9.8;  MISSILE_SPEED = 300;  CLOUD_RADIUS = 10;
CLOUD_SINK = 3;  CLOUD_DURATION = 20;

M1_0  = [20000, 0, 2000];
FY1_0 = [17800, 0, 1800];
REAL_TARGET = [0, 200, 0];
t_hit = norm(M1_0) / MISSILE_SPEED;
v_m1  = -MISSILE_SPEED * M1_0 / norm(M1_0);

%% ===== 三枚弹参数 =====
heading = deg2rad(7.50);
speed   = 70;
v_drone = speed * [cos(heading), sin(heading), 0];

bombs = struct();
bombs(1).t_drop  = 0.100;   bombs(1).t_delay  = 1.040;
bombs(2).t_drop  = 3.100;   bombs(2).t_delay  = 3.000;
bombs(3).t_drop  = 6.100;   bombs(3).t_delay  = 2.500;
colors = {[0.2 0.6 0.2], [0.8 0.4 0], [0.6 0.2 0.6]};  % green, orange, purple

%% ===== 计算每枚弹的起爆信息和遮蔽 =====
for i = 1:3
    p_drop_i = FY1_0 + v_drone * bombs(i).t_drop;
    p_burst  = p_drop_i + v_drone * bombs(i).t_delay;
    p_burst(3) = p_burst(3) - 0.5 * G * bombs(i).t_delay^2;
    bombs(i).p_burst  = p_burst;
    bombs(i).t_burst  = bombs(i).t_drop + bombs(i).t_delay;

    % 遮蔽区间计算 (dt=0.02s)
    t_vals = bombs(i).t_burst : 0.02 : min(t_hit, bombs(i).t_burst+CLOUD_DURATION);
    shielded = false(size(t_vals));
    for j = 1:length(t_vals)
        t = t_vals(j);
        cloud = p_burst + [0, 0, -CLOUD_SINK*(t - bombs(i).t_burst)];
        shielded(j) = line_sphere_hit(M1_0+v_m1*t, REAL_TARGET, cloud, CLOUD_RADIUS);
    end
    bombs(i).shielded = shielded;
    bombs(i).t_vals   = t_vals;
    bombs(i).coverage = sum(shielded) * 0.02;
end

% 联合遮蔽: 任意一弹遮蔽即算遮蔽
t_min = min([bombs.t_burst]);
t_max = min(t_hit, max([bombs.t_burst] + CLOUD_DURATION));
t_union = t_min:0.02:t_max;
union_shielded = false(size(t_union));
for j = 1:length(t_union)
    t = t_union(j);
    for i = 1:3
        if t >= bombs(i).t_burst && t <= bombs(i).t_burst + CLOUD_DURATION
            cloud = bombs(i).p_burst + [0, 0, -CLOUD_SINK*(t - bombs(i).t_burst)];
            if line_sphere_hit(M1_0+v_m1*t, REAL_TARGET, cloud, CLOUD_RADIUS)
                union_shielded(j) = true; break;
            end
        end
    end
end
union_cov = sum(union_shielded) * 0.02;

fprintf('弹1: 遮蔽 %.2fs\n', bombs(1).coverage);
fprintf('弹2: 遮蔽 %.2fs\n', bombs(2).coverage);
fprintf('弹3: 遮蔽 %.2fs\n', bombs(3).coverage);
fprintf('联合: %.2fs\n', union_cov);

%% ====== Figure: 综合视图 =====
figure('Position', [50, 50, 1600, 800]);

%% ---- 子图1: 遮蔽时间线 ----
subplot(4,1,[1,2]); hold on; grid on;
title(sprintf(['问题3: FY1三弹联合遮蔽 \\rm (联合=%.2fs, ' ...
    'heading=%.1f°, v=%.0fm/s)'], union_cov, rad2deg(heading), speed), ...
    'FontSize', 14);

% 每枚弹的遮蔽区块
y_positions = [2.7, 1.6, 0.5];  % Y偏移
for i = 1:3
    tv = bombs(i).t_vals;
    sh = bombs(i).shielded;
    % 画遮蔽信号
    in_block = false;  block_start = 0;
    for j = 1:length(tv)-1
        if sh(j) && ~in_block
            block_start = tv(j); in_block = true;
        elseif ~sh(j) && in_block
            patch([block_start tv(j) tv(j) block_start], ...
                  [y_positions(i)-0.35 y_positions(i)-0.35 ...
                   y_positions(i)+0.35 y_positions(i)+0.35], ...
                  colors{i}, 'EdgeColor', 'none', 'FaceAlpha', 0.7);
            in_block = false;
        end
    end
    if in_block
        patch([block_start tv(end) tv(end) block_start], ...
              [y_positions(i)-0.35 y_positions(i)-0.35 ...
               y_positions(i)+0.35 y_positions(i)+0.35], ...
              colors{i}, 'EdgeColor', 'none', 'FaceAlpha', 0.7);
    end

    % 标注
    text(62, y_positions(i), sprintf('弹%d: %.2fs', i, bombs(i).coverage), ...
        'FontSize', 10, 'FontWeight', 'bold', 'Color', colors{i});
    % 起爆竖线
    xline(bombs(i).t_burst, '--', 'Color', colors{i}, 'Alpha', 0.5);
end

% 联合遮蔽 (最上方)
in_block = false;  block_start = 0;
for j = 1:length(t_union)-1
    if union_shielded(j) && ~in_block
        block_start = t_union(j); in_block = true;
    elseif ~union_shielded(j) && in_block
        patch([block_start t_union(j) t_union(j) block_start], ...
              [3.5 3.5 4.2 4.2], [0.2 0.7 0.2], ...
              'EdgeColor', 'black', 'LineWidth', 1.5, 'FaceAlpha', 0.5);
        text((block_start+t_union(j))/2, 3.85, ...
            sprintf('%.2fs', t_union(j)-block_start), ...
            'HorizontalAlignment', 'center', 'FontSize', 9, ...
            'FontWeight', 'bold');
        in_block = false;
    end
end
text(62, 4.1, sprintf('联合遮蔽: %.2fs', union_cov), 'FontSize', 14, ...
    'FontWeight', 'bold', 'Color', [0 0.5 0]);

yticks([0.5, 1.6, 2.7, 4.0]);
yticklabels({'弹3', '弹2', '弹1', '联合'});
xlabel('时间 (s)'); xlim([0, 68]);

%% ---- 子图2: 3D轨迹 ----
subplot(4,1,[3,4]); hold on; grid on; view(40, 25);
title('3D 轨迹: FY1飞行路径 + 三弹起爆点 + 遮蔽云团');

% M1轨迹
t_all = linspace(0, t_hit, 300);
M1_traj = M1_0 + v_m1 .* t_all';
plot3(M1_traj(:,1), M1_traj(:,2), M1_traj(:,3), 'r-', 'LineWidth', 2);
plot3(M1_0(1), M1_0(2), M1_0(3), 'r^', 'MarkerSize', 10, 'MarkerFaceColor', 'r');
plot3(0, 0, 0, 'kx', 'MarkerSize', 12, 'LineWidth', 2);
plot3(REAL_TARGET(1), REAL_TARGET(2), REAL_TARGET(3), 'gs', ...
    'MarkerSize', 10, 'MarkerFaceColor', 'g');

% FY1飞行路径
d_path = FY1_0 + v_drone .* linspace(0, 12, 200)';
plot3(d_path(:,1), d_path(:,2), d_path(:,3), 'b-', 'LineWidth', 2);
plot3(FY1_0(1), FY1_0(2), FY1_0(3), 'bo', 'MarkerSize', 8, 'MarkerFaceColor', 'b');

% 每枚弹的起爆点和云团
for i = 1:3
    b = bombs(i).p_burst;
    plot3(b(1), b(2), b(3), 'o', 'Color', colors{i}, ...
        'MarkerSize', 10, 'MarkerFaceColor', colors{i});
    text(b(1), b(2), b(3)+30, sprintf('弹%d', i), ...
        'FontSize', 9, 'Color', colors{i}, 'FontWeight', 'bold');

    % 遮蔽中点时刻云团
    idx = find(bombs(i).shielded, 1, 'first');
    if ~isempty(idx)
        t_mid = bombs(i).t_vals(idx + round(sum(bombs(i).shielded)/2));
        cloud = b + [0, 0, -CLOUD_SINK*(t_mid - bombs(i).t_burst)];
        [Xs, Ys, Zs] = sphere(15);
        surf(cloud(1)+CLOUD_RADIUS*Xs, cloud(2)+CLOUD_RADIUS*Ys, ...
             cloud(3)+CLOUD_RADIUS*Zs, ...
             'FaceColor', colors{i}, 'EdgeColor', 'none', 'FaceAlpha', 0.25);
    end
end

xlabel('X (m)'); ylabel('Y (m)'); zlabel('Z (m)');
legend({'M1轨迹', 'M1起点', '假目标', '真目标', 'FY1路径', 'FY1起点', ...
    '弹1起爆', '弹2起爆', '弹3起爆'}, 'Location', 'best', 'FontSize', 8);
xlim([-2000, 21000]); ylim([-2000, 2000]); zlim([0, 2500]);

saveas(gcf, 'problem3_multi_bomb.png');
fprintf('Figure saved: problem3_multi_bomb.png\n');

%% ===== 辅助函数 =====
function hit = line_sphere_hit(p1, p2, center, r)
    v = p2 - p1;  w = center - p1;
    vdv = dot(v, v);
    if vdv < 1e-12; hit = norm(w) <= r; return; end
    t_proj = max(0, min(1, dot(w,v)/vdv));
    hit = norm(p1 + t_proj*v - center) <= r;
end
