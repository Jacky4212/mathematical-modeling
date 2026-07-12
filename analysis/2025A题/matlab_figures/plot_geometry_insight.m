%% plot_geometry_insight.m
% 核心几何洞察: 为什么航向角从180°改为7.5°能让遮蔽时长提升234%?
%
% 关键: 烟幕云团需要在导弹→真目标的视线(LOS)上
% LOS 随导弹位置变化而"扫过"不同空间区域
% 航向180°(朝原点): 云团在导弹正前方, 导弹飞近后LOS才穿过云团 → 覆盖短
% 航向7.5°(东偏北): 云团偏在导弹飞行路径侧面, LOS更早穿过云团 → 覆盖长
clear; close all;

%% ===== 常数 =====
G = 9.8;  MISSILE_SPEED = 300;  CLOUD_RADIUS = 10;
CLOUD_SINK = 3;  CLOUD_DURATION = 20;

M1_0  = [20000, 0, 2000];
FY1_0 = [17800, 0, 1800];
REAL_TARGET = [0, 200, 0];
t_hit = norm(M1_0) / MISSILE_SPEED;
v_m1 = -MISSILE_SPEED * M1_0 / norm(M1_0);

%% ===== 两组方案 =====
% 方案A: heading=180° (问题1)
A.hdg = pi;   A.spd = 120;  A.td = 1.5;  A.tdl = 3.6;
A.color = [0.8 0.2 0.2];  A.name = '方案A: 180° (朝原点)';

% 方案B: heading=7.5° (问题2最优)
B.hdg = deg2rad(7.5);  B.spd = 70;  B.td = 0.1;  B.tdl = 1.04;
B.color = [0.2 0.5 0.8];  B.name = '方案B: 7.5° (最优)';

%% ===== 计算 =====
for s = {'A','B'}
    p = eval([s{1}]);
    v_d = p.spd * [cos(p.hdg), sin(p.hdg), 0];
    p_drop = FY1_0 + v_d * p.td;
    p_burst = p_drop + v_d * p.tdl;
    p_burst(3) = p_burst(3) - 0.5*G*p.tdl^2;
    eval([s{1} '.burst = p_burst;']);
    eval([s{1} '.t_burst = p.td + p.tdl;']);
    eval([s{1} '.v_d = v_d;']);
end

%% ====== Figure =====
figure('Position', [30, 30, 1700, 900]);

%% ---- 大图: X-Y平面 几何分析 ----
ax1 = subplot(2,3,[1,2,4,5]); hold on; grid on; axis equal;
title({'航向角如何影响遮蔽: 几何分析'; ...
    '导弹从右向左飞行, LOS从导弹→真目标(绿框)扫过空间, 云团需在扫描路径上'}, ...
    'FontSize', 13);

% M1轨迹
t_all = linspace(0, t_hit, 500);
M1_traj = M1_0 + v_m1 .* t_all';
plot(M1_traj(:,1), M1_traj(:,2), 'k-', 'LineWidth', 3, ...
    'DisplayName', 'M1导弹轨迹 (300 m/s → 假目标)');
plot(M1_0(1), M1_0(2), 'k^', 'MarkerSize', 14, 'MarkerFaceColor', 'k', ...
    'DisplayName', 'M1初始 (20000,0)');
plot(0, 0, 'kx', 'MarkerSize', 16, 'LineWidth', 3, ...
    'DisplayName', '假目标 (原点)');
plot(REAL_TARGET(1), REAL_TARGET(2), 'gs', 'MarkerSize', 14, ...
    'MarkerFaceColor', 'g', 'LineWidth', 2, ...
    'DisplayName', '真目标 (0, 200)');
plot(FY1_0(1), FY1_0(2), 'bo', 'MarkerSize', 10, 'MarkerFaceColor', 'b');

% 画多组"导弹→真目标"的视线 (展示LOS扫描)
t_demo = [5, 15, 30, 50];  % 4个代表性时刻
los_alpha = [0.15, 0.25, 0.45, 0.7];
for i = 1:4
    m_pos = M1_0 + v_m1 * t_demo(i);
    plot([m_pos(1), REAL_TARGET(1)], [m_pos(2), REAL_TARGET(2)], ...
        'Color', [0.5 0.2 0.2], 'LineWidth', 1.5, ...
        'LineStyle', ':', 'Alpha', los_alpha(i));
    plot(m_pos(1), m_pos(2), 'r.', 'MarkerSize', 12);
    text(m_pos(1)+300, m_pos(2)+100, sprintf('t=%ds', t_demo(i)), ...
        'FontSize', 8, 'Color', [0.5 0.2 0.2]);
end

% 两组方案
for s = {'A','B'}
    p = eval([s{1}]);

    % 无人机飞行路径 (从投放开始到起爆)
    t_start_path = max(0, p.td - 1);
    t_end_path = p.td + p.tdl + 5;
    d_path = FY1_0 + p.v_d .* linspace(t_start_path, t_end_path, 150)';

    plot(d_path(:,1), d_path(:,2), '-', 'Color', p.color, ...
        'LineWidth', 2.5, 'DisplayName', p.name);

    % 投放点
    p_drop_pt = FY1_0 + p.v_d * p.td;
    plot(p_drop_pt(1), p_drop_pt(2), 's', 'Color', p.color, ...
        'MarkerSize', 10, 'LineWidth', 1.5);

    % 起爆点
    plot(p.burst(1), p.burst(2), 'p', 'Color', p.color, ...
        'MarkerSize', 16, 'LineWidth', 2, ...
        'MarkerFaceColor', p.color);

    % 标注云团覆盖范围(圆)和遮蔽区间文字
    viscircles(p.burst(1:2), CLOUD_RADIUS, 'Color', p.color, ...
        'LineWidth', 2, 'LineStyle', '--');

    % 从起爆点画空心箭头指向说明
    quiver(p.burst(1), p.burst(2), ...
        (FY1_0(1)-p.burst(1))*0.3, (FY1_0(2)-p.burst(2))*0.3, ...
        0, 'Color', p.color, 'LineWidth', 1.5, 'MaxHeadSize', 0.5, ...
        'AutoScale', 'off');
end

% 标注距离参考线: FY1到真目标的y偏移
plot([FY1_0(1), REAL_TARGET(1)], [FY1_0(2), REAL_TARGET(2)], ...
    'g--', 'LineWidth', 1, 'Alpha', 0.4);
text(FY1_0(1)+500, FY1_0(2)+50, 'FY1→真目标 y=200m偏移', ...
    'FontSize', 8, 'Color', [0 0.5 0]);

xlabel('X (m)', 'FontSize', 12);
ylabel('Y (m)', 'FontSize', 12);
legend('Location', 'northeast', 'FontSize', 8);
xlim([-2000, 21000]); ylim([-1000, 2500]);

%% ---- 右上: 遮蔽时长对比 ----
subplot(2,3,3); hold on; grid on;
bar([1,2], [1.42, 4.74], 0.5, 'FaceColor', 'flat');
bar(1, 1.42, 0.5, 'FaceColor', A.color);
bar(2, 4.74, 0.5, 'FaceColor', B.color);
text(1, 1.8, '1.42s', 'FontSize', 14, 'FontWeight', 'bold', ...
    'HorizontalAlignment', 'center', 'Color', A.color);
text(2, 5.1, '4.74s', 'FontSize', 14, 'FontWeight', 'bold', ...
    'HorizontalAlignment', 'center', 'Color', B.color);
text(1.5, 3, '+234%', 'FontSize', 16, 'FontWeight', 'bold', ...
    'HorizontalAlignment', 'center', 'Color', [0 0.6 0]);
set(gca, 'XTickLabel', {'180° (问题1)', '7.5° (问题2)'});
ylabel('遮蔽时长 (s)');
title('遮蔽时长对比', 'FontSize', 13);

%% ---- 右下: 几何原理说明 ----
subplot(2,3,6); hold on; axis off;
title('几何原理解释', 'FontSize', 13);

insight_text = {
    '■ 方案A (180°朝原点): ';
    '  无人机朝原点直飞, 云团在导弹正前方';
    '  导弹→真目标的LOS在飞行末段';
    '  才接近云团, 遮蔽窗口极短(1.42s)';
    '';
    '■ 方案B (7.5°东偏北): ';
    '  无人机向东微偏飞行, 云团偏在导弹';
    '  飞行路径侧面(LOS扫描路径上)';
    '  LOS更早进入云团范围, 遮蔽窗口长(4.74s)';
    '';
    '■ 核心结论: ';
    '  遮蔽优化的本质是找到云团放置点,';
    '  使其位于导弹LOS的长时间"扫描带"上,';
    '  而非简单朝向导弹或原点飞行';
};

y_pos = 0.95;
for i = 1:length(insight_text)
    line_text = insight_text{i};
    if startsWith(line_text, '■')
        text(0.02, y_pos, line_text, 'FontSize', 10.5, ...
            'FontWeight', 'bold', 'VerticalAlignment', 'top');
    elseif startsWith(line_text, '  无人机')
        text(0.08, y_pos, line_text, 'FontSize', 9.5, ...
            'Color', [0.17 0.31 0.61], 'VerticalAlignment', 'top');
    else
        text(0.08, y_pos, line_text, 'FontSize', 9.5, ...
            'VerticalAlignment', 'top');
    end
    y_pos = y_pos - 0.065;
end

sgtitle('关键几何洞察: 航向角 → 云团位置 → LOS扫描窗口', ...
    'FontSize', 15, 'FontWeight', 'bold');
saveas(gcf, 'geometry_insight.png');
fprintf('Figure saved: geometry_insight.png\n');
