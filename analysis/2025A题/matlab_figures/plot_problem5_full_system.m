%% plot_problem5_full_system.m
% 问题5: 5架无人机, 各1弹, 协同干扰M1+M2+M3
% 分配: M1←FY1, M2←FY2+FY4, M3←FY3+FY5
% 总遮蔽: 11.94s (M1=4.64 + M2=4.58 + M3=2.72)
clear; close all;

%% ===== 常数 =====
G = 9.8;  MISSILE_SPEED = 300;  CLOUD_RADIUS = 10;
CLOUD_SINK = 3;  CLOUD_DURATION = 20;
REAL_TARGET = [0, 200, 0];

% 导弹初始位置
M_init = containers.Map();
M_init('M1') = [20000, 0, 2000];
M_init('M2') = [19000, 600, 2100];
M_init('M3') = [18000, -600, 1900];

% 无人机初始位置
D_init = containers.Map();
D_init('FY1') = [17800, 0, 1800];
D_init('FY2') = [12000, 1400, 1400];
D_init('FY3') = [6000, -3000, 700];
D_init('FY4') = [11000, 2000, 1800];
D_init('FY5') = [13000, -2000, 1300];

% 问题5优化结果
allocation = {{'FY1'}, {'FY2','FY4'}, {'FY3','FY5'}};  % M1,M2,M3

drone_params = struct();
drone_params.FY1 = struct('hdg', deg2rad(178.3), 'spd', 93.0, ...
    'td', 0.100, 'tdl', 2.908, 'missile', 'M1');
drone_params.FY2 = struct('hdg', deg2rad(237.1), 'spd', 112.0, ...
    'td', 5.289, 'tdl', 5.286, 'missile', 'M2');
drone_params.FY3 = struct('hdg', deg2rad(153.4), 'spd', 120.0, ...
    'td', 3.000, 'tdl', 4.000, 'missile', 'M3');
drone_params.FY4 = struct('hdg', deg2rad(-169.7), 'spd', 120.0, ...
    'td', 3.000, 'tdl', 4.000, 'missile', 'M2');
drone_params.FY5 = struct('hdg', deg2rad(135.1), 'spd', 122.0, ...
    'td', 14.389, 'tdl', 4.428, 'missile', 'M3');

missile_colors = containers.Map({'M1','M2','M3'}, ...
    {[0.8 0.2 0.2], [0.9 0.5 0], [0.2 0.6 0.8]});
drone_colors = containers.Map({'FY1','FY2','FY3','FY4','FY5'}, ...
    {[0 0.4 0.8], [0.9 0.5 0], [0.2 0.7 0.2], [0.7 0.2 0.7], [0.2 0.7 0.7]});

%% ===== 计算 =====
drone_ids = {'FY1','FY2','FY3','FY4','FY5'};
missile_ids = {'M1','M2','M3'};

% 导弹轨迹
for m = 1:3
    mid = missile_ids{m};
    m0 = M_init(mid);
    t_hit(m) = norm(m0) / MISSILE_SPEED;
    v_m = -MISSILE_SPEED * m0 / norm(m0);
    missile_traj{m} = m0 + v_m .* linspace(0, t_hit(m), 300)';
    missile_v{m} = v_m;
end

% 无人机起爆信息
for d = 1:5
    did = drone_ids{d};
    p = drone_params.(did);
    d0 = D_init(did);
    v_d = p.spd * [cos(p.hdg), sin(p.hdg), 0];

    p_drop = d0 + v_d * p.td;
    p_burst = p_drop + v_d * p.tdl;
    p_burst(3) = p_burst(3) - 0.5*G*p.tdl^2;
    drone_params.(did).p_burst = p_burst;
    drone_params.(did).t_burst = p.td + p.tdl;
    drone_params.(did).v_d = v_d;
    drone_params.(did).d0 = d0;
end

% 遮蔽时长
cov_M1 = 4.640;  cov_M2 = 4.580;  cov_M3 = 2.720;

%% ====== Figure =====
figure('Position', [20, 20, 1800, 950]);

%% ---- 子图1: 系统全局 X-Y 俯视图 ----
subplot(2,3,1); hold on; grid on; axis equal;
title('全系统 X-Y 俯视图', 'FontSize', 13);

% 三条导弹轨迹
for m = 1:3
    traj = missile_traj{m};
    c = missile_colors(missile_ids{m});
    plot(traj(:,1), traj(:,2), '-', 'Color', c, 'LineWidth', 2, ...
        'DisplayName', [missile_ids{m} ' 轨迹']);
    plot(M_init(missile_ids{m})(1), M_init(missile_ids{m})(2), ...
        '^', 'Color', c, 'MarkerSize', 9, 'MarkerFaceColor', c);
end
plot(0,0,'kx','MarkerSize',14,'LineWidth',2,'DisplayName','假目标');
plot(REAL_TARGET(1), REAL_TARGET(2), 'gs','MarkerSize',12,...
    'MarkerFaceColor','g','DisplayName','真目标');

% 无人机 + 起爆点
for d = 1:5
    did = drone_ids{d};
    p = drone_params.(did);
    d0 = p.d0;
    c = drone_colors(did);
    c_m = missile_colors(p.missile);

    % 路径
    t_end = p.td + p.tdl + 3;
    path = d0 + p.v_d .* linspace(0, t_end, 100)';
    plot(path(:,1), path(:,2), '-', 'Color', c, 'LineWidth', 1.5, ...
        'DisplayName', [did '→' p.missile]);

    % 起点
    plot(d0(1), d0(2), 'o', 'Color', c, 'MarkerSize', 7, ...
        'MarkerFaceColor', c);

    % 起爆点 + 分配连线到对应导弹
    plot(p.p_burst(1), p.p_burst(2), 'd', 'Color', c_m, ...
        'MarkerSize', 8, 'MarkerFaceColor', c_m, 'LineWidth', 1.5);

    % 虚线连到目标导弹轨迹
    mid_traj = missile_traj{find(strcmp(missile_ids, p.missile))};
    [~, closest_idx] = min(vecnorm(mid_traj - p.p_burst, 2, 2));
    plot([p.p_burst(1), mid_traj(closest_idx,1)], ...
         [p.p_burst(2), mid_traj(closest_idx,2)], ...
         ':', 'Color', c_m, 'Alpha', 0.4);
end
xlabel('X (m)'); ylabel('Y (m)');
legend('Location', 'eastoutside', 'FontSize', 7);
xlim([-2000, 22000]); ylim([-5000, 4000]);

%% ---- 子图2: 遮蔽时长贡献 ----
subplot(2,3,2); hold on; grid on;
title('各导弹遮蔽时长', 'FontSize', 13);

covs_all = [cov_M1, cov_M2, cov_M3, cov_M1+cov_M2+cov_M3];
b = bar([1,2,3,4], covs_all, 0.5);
b.FaceColor = 'flat';
b.CData(1,:) = missile_colors('M1');
b.CData(2,:) = missile_colors('M2');
b.CData(3,:) = missile_colors('M3');
b.CData(4,:) = [0.3 0.3 0.3];
for i = 1:4
    text(i, covs_all(i)+0.3, sprintf('%.2fs', covs_all(i)), ...
        'HorizontalAlignment', 'center', 'FontSize', 12, 'FontWeight', 'bold');
end
set(gca, 'XTickLabel', {'M1', 'M2', 'M3', '总计'});
ylabel('遮蔽时长 (s)');

%% ---- 子图3: 分配表 ----
subplot(2,3,3); hold on; axis off;
title('无人机-导弹分配', 'FontSize', 13);
text(0.5, 0.95, 'M1 ← FY1           4.64s', 'FontSize', 14, ...
    'FontWeight', 'bold', 'Color', missile_colors('M1'), ...
    'HorizontalAlignment', 'center');
text(0.5, 0.65, 'M2 ← FY2 + FY4    4.58s', 'FontSize', 14, ...
    'FontWeight', 'bold', 'Color', missile_colors('M2'), ...
    'HorizontalAlignment', 'center');
text(0.5, 0.35, 'M3 ← FY3 + FY5    2.72s', 'FontSize', 14, ...
    'FontWeight', 'bold', 'Color', missile_colors('M3'), ...
    'HorizontalAlignment', 'center');
text(0.5, 0.10, sprintf('总遮蔽 = 11.94s'), 'FontSize', 16, ...
    'FontWeight', 'bold', 'HorizontalAlignment', 'center');
xlim([0,1]); ylim([0,1]);

%% ---- 子图4-6: 3D视图三个角度 ----
view_angles = {[90,0], [0,0], [35,20]};
view_names = {'3D俯视 (X-Y)', '3D正视 (X-Z)', '3D透视图'};
for vn = 1:3
    subplot(2,3,3+vn); hold on; grid on;
    view(view_angles{vn}(1), view_angles{vn}(2));
    title(view_names{vn}, 'FontSize', 12);

    % 导弹轨迹
    for m = 1:3
        traj = missile_traj{m};
        c = missile_colors(missile_ids{m});
        plot3(traj(:,1), traj(:,2), traj(:,3), '-', 'Color', c, ...
            'LineWidth', 1.5);
    end
    plot3(0,0,0,'kx','MarkerSize',10,'LineWidth',2);
    plot3(REAL_TARGET(1), REAL_TARGET(2), REAL_TARGET(3), ...
        'gs','MarkerSize',8,'MarkerFaceColor','g');

    % 无人机路径 + 起爆点
    for d = 1:5
        did = drone_ids{d};
        p = drone_params.(did);
        d0 = p.d0;
        c = drone_colors(did);
        t_end = p.td + p.tdl + 3;
        path = d0 + p.v_d .* linspace(0, t_end, 80)';
        plot3(path(:,1), path(:,2), path(:,3), '-', 'Color', c, ...
            'LineWidth', 1);
        plot3(d0(1), d0(2), d0(3), 'o', 'Color', c, ...
            'MarkerSize', 5, 'MarkerFaceColor', c);
        plot3(p.p_burst(1), p.p_burst(2), p.p_burst(3), 'o', ...
            'Color', missile_colors(p.missile), 'MarkerSize', 7, ...
            'MarkerFaceColor', missile_colors(p.missile));

        % 云团
        if p.missile == 'M1' || p.missile == 'M2'
            cloud_mid = p.p_burst + [0,0,-CLOUD_SINK*3];
            [Xs,Ys,Zs] = sphere(10);
            surf(cloud_mid(1)+CLOUD_RADIUS*Xs, ...
                 cloud_mid(2)+CLOUD_RADIUS*Ys, ...
                 cloud_mid(3)+CLOUD_RADIUS*Zs, ...
                 'FaceColor', missile_colors(p.missile), ...
                 'EdgeColor', 'none', 'FaceAlpha', 0.15);
        end
    end
    xlabel('X'); ylabel('Y'); zlabel('Z');
    xlim([-2000, 22000]); ylim([-5000, 5000]); zlim([0, 3000]);
end

sgtitle(sprintf(['问题5: 全系统协同\\rightarrow5机各1弹, M1+M2+M3 = 11.94s\\rm' ...
    '\n分配: M1←FY1 | M2←FY2+FY4 | M3←FY3+FY5']), ...
    'FontSize', 14, 'FontWeight', 'bold');
saveas(gcf, 'problem5_full_system.png');
fprintf('Figure saved: problem5_full_system.png\n');
