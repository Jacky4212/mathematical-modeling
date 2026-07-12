%% plot_problem4_multi_drone.m
% 问题4: FY1+FY2+FY3 三机协同单弹, 联合干扰M1
% FY1: heading=179.4°, v=131.1m/s, drop=0.1s, delay=3.671s → 3.94s
% FY2: heading=-173.3°, v=120m/s,  drop=3.0s, delay=4.0s   → 0s (偏轴)
% FY3: heading=94.2°,  v=137.6m/s, drop=18.68s,delay=3.628s → 2.60s
% 联合: 6.48s
clear; close all;

%% ===== 常数 =====
G = 9.8;  MISSILE_SPEED = 300;  CLOUD_RADIUS = 10;
CLOUD_SINK = 3;  CLOUD_DURATION = 20;

M1_0  = [20000, 0, 2000];
REAL_TARGET = [0, 200, 0];
t_hit = norm(M1_0) / MISSILE_SPEED;
v_m1 = -MISSILE_SPEED * M1_0 / norm(M1_0);

drones = {'FY1', 'FY2', 'FY3'};
drone_init = {[17800 0 1800], [12000 1400 1400], [6000 -3000 700]};
params = struct();
params.FY1 = struct('hdg', deg2rad(179.4), 'spd', 131.1, ...
    'td', 0.100, 'tdl', 3.671, 'cov', 3.94);
params.FY2 = struct('hdg', deg2rad(-173.3), 'spd', 120.0, ...
    'td', 3.000, 'tdl', 4.000, 'cov', 0.00);
params.FY3 = struct('hdg', deg2rad(94.2), 'spd', 137.6, ...
    'td', 18.677, 'tdl', 3.628, 'cov', 2.60);
colors = containers.Map({'FY1','FY2','FY3'}, {[0 0.4 0.8],[0.9 0.5 0],[0.2 0.7 0.2]});

%% ===== 计算起爆点 =====
for i = 1:3
    did = drones{i};
    p = params.(did);
    v_d = p.spd * [cos(p.hdg), sin(p.hdg), 0];
    p_drop = drone_init{i} + v_d * p.td;
    p_burst = p_drop + v_d * p.tdl;
    p_burst(3) = p_burst(3) - 0.5*G*p.tdl^2;
    params.(did).p_burst = p_burst;
    params.(did).t_burst = p.td + p.tdl;
    params.(did).v_d = v_d;
    fprintf('%s: burst@(%.0f,%.0f,%.0f) t=%.3fs cov=%.2fs\n', ...
        did, p_burst, params.(did).t_burst, p.cov);
end

%% ====== Figure =====
figure('Position', [50, 50, 1600, 850]);

%% ---- 子图1: X-Y平面 (俯视图) ----
subplot(2,3,1); hold on; grid on; axis equal;
title('X-Y 平面: 三机协同', 'FontSize', 13);

% M1轨迹
t_all = linspace(0, t_hit, 400);
M1_traj = M1_0 + v_m1 .* t_all';
plot(M1_traj(:,1), M1_traj(:,2), 'r-', 'LineWidth', 2, 'DisplayName', 'M1');
plot(M1_0(1), M1_0(2), 'r^', 'MarkerSize', 10, 'MarkerFaceColor', 'r');
plot(0,0,'kx','MarkerSize',12,'LineWidth',2,'DisplayName','假目标');
plot(REAL_TARGET(1), REAL_TARGET(2), 'gs','MarkerSize',10,...
    'MarkerFaceColor','g','DisplayName','真目标');

% 无人机
for i = 1:3
    did = drones{i};  p = params.(did);  d0 = drone_init{i};
    c = colors(did);
    t_end = p.td + p.tdl + 3;
    path = d0 + p.v_d .* linspace(0, t_end, 150)';
    plot(path(:,1), path(:,2), '-', 'Color', c, 'LineWidth', 2, ...
        'DisplayName', [did ' 路径']);
    plot(d0(1), d0(2), 'o', 'Color', c, 'MarkerSize', 8, ...
        'MarkerFaceColor', c);
    plot(p.p_burst(1), p.p_burst(2), '*', 'Color', c, ...
        'MarkerSize', 14, 'LineWidth', 1.5, ...
        'DisplayName', [did sprintf(' (%.1fs)', p.cov)]);
end
xlabel('X (m)'); ylabel('Y (m)');
legend('Location', 'best', 'FontSize', 7);
xlim([-500, 21000]); ylim([-4000, 3000]);

%% ---- 子图2: X-Z平面 (侧视图) ----
subplot(2,3,2); hold on; grid on;
title('X-Z 平面: 三机协同', 'FontSize', 13);

plot(M1_traj(:,1), M1_traj(:,3), 'r-', 'LineWidth', 2);
plot(M1_0(1), M1_0(3), 'r^', 'MarkerSize', 10, 'MarkerFaceColor', 'r');
plot(0, 0, 'kx', 'MarkerSize', 12, 'LineWidth', 2);

for i = 1:3
    did = drones{i};  p = params.(did);  d0 = drone_init{i};
    c = colors(did);
    t_end = p.td + p.tdl + 3;
    path = d0 + p.v_d .* linspace(0, t_end, 150)';
    plot(path(:,1), path(:,3), '-', 'Color', c, 'LineWidth', 2);
    plot(d0(1), d0(3), 'o', 'Color', c, 'MarkerSize', 8, ...
        'MarkerFaceColor', c);
    plot(p.p_burst(1), p.p_burst(3), '*', 'Color', c, ...
        'MarkerSize', 14, 'LineWidth', 1.5);
    yline(d0(3), '--', 'Color', c, 'Alpha', 0.3);
end
xlabel('X (m)'); ylabel('Z (m)'); xlim([-500, 21000]);

%% ---- 子图3: 遮蔽时长贡献 ----
subplot(2,3,3); hold on; grid on;
title('单机遮蔽贡献', 'FontSize', 13);
covs = [params.FY1.cov, params.FY2.cov, params.FY3.cov, 6.48];
b = bar([1,2,3,4], covs, 0.5);
b.FaceColor = 'flat';
b.CData(1,:) = colors('FY1');
b.CData(2,:) = colors('FY2');
b.CData(3,:) = colors('FY3');
b.CData(4,:) = [0.3 0.3 0.3];
for i = 1:4
    text(i, covs(i)+0.2, sprintf('%.2fs', covs(i)), ...
        'HorizontalAlignment', 'center', 'FontSize', 11, 'FontWeight', 'bold');
end
set(gca, 'XTickLabel', {'FY1', 'FY2', 'FY3', '联合'});
ylabel('遮蔽时长 (s)');

%% ---- 子图4-6: 3D视图三个角度 ----
views = {[90,0], [0,0], [45,25]};
view_names = {'俯视图 (X-Y)', '正视图 (X-Z)', '3D透视图'};
for vn = 1:3
    subplot(2,3,3+vn); hold on; grid on;
    view(views{vn}(1), views{vn}(2));
    title(view_names{vn}, 'FontSize', 12);

    plot3(M1_traj(:,1), M1_traj(:,2), M1_traj(:,3), 'r-', 'LineWidth', 1.5);
    plot3(0,0,0,'kx','MarkerSize',10,'LineWidth',2);
    plot3(REAL_TARGET(1), REAL_TARGET(2), REAL_TARGET(3), ...
        'gs','MarkerSize',8,'MarkerFaceColor','g');

    for i = 1:3
        did = drones{i};  p = params.(did);  d0 = drone_init{i};
        c = colors(did);
        t_end = p.td + p.tdl + 3;
        path = d0 + p.v_d .* linspace(0, t_end, 100)';
        plot3(path(:,1), path(:,2), path(:,3), '-', 'Color', c, 'LineWidth', 1.5);
        plot3(p.p_burst(1), p.p_burst(2), p.p_burst(3), 'o', 'Color', c, ...
            'MarkerSize', 8, 'MarkerFaceColor', c);

        % 遮蔽云团 (有效时)
        if p.cov > 0.1
            cloud_mid = p.p_burst + [0,0,-CLOUD_SINK*5];
            [Xs,Ys,Zs] = sphere(12);
            surf(cloud_mid(1)+CLOUD_RADIUS*Xs, cloud_mid(2)+CLOUD_RADIUS*Ys, ...
                 cloud_mid(3)+CLOUD_RADIUS*Zs, ...
                 'FaceColor', c, 'EdgeColor', 'none', 'FaceAlpha', 0.2);
        end
    end
    xlabel('X'); ylabel('Y'); zlabel('Z');
    xlim([-2000, 21000]); ylim([-4000, 4000]); zlim([0, 3000]);
end

sgtitle(sprintf(['问题4: 三机协同单弹 \\rightarrow M1\\rm | ' ...
    'FY1=3.94s + FY2=0s + FY3=2.60s = 联合6.48s']), ...
    'FontSize', 14, 'FontWeight', 'bold');
saveas(gcf, 'problem4_multi_drone.png');
fprintf('Figure saved: problem4_multi_drone.png\n');
