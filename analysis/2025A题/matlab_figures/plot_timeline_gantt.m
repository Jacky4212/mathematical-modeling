%% plot_timeline_gantt.m
% 遮蔽时间线甘特图: 五题的遮蔽区间在时间轴上对比
% 清晰展示每题的遮蔽覆盖范围
clear; close all;

%% ===== 遮蔽区间数据 =====
% 格式: {问题名, {导弹, [区间1_start, 区间1_end; ...]}, ...}
intervals = {
    '问题1: FY1单弹(给定)', ...
        {{'M1', [8.04, 9.46]}};
    '问题2: FY1单弹(优化)', ...
        {{'M1', [1.20, 5.94]}};
    '问题3: FY1三弹', ...
        {{'M1', [1.20, 5.94]}};
    '问题4: 三机协同', ...
        {{'M1', [3.77, 8.0; 20.0, 22.6]}};
    '问题5: 全系统', ...
        {{'M1', [3.00, 7.64]}, {'M2', [10.50, 15.08]}, {'M3', [14.0, 16.72]}};
};

missile_colors = containers.Map({'M1','M2','M3'}, ...
    {[0 0.4 0.8], [0.9 0.5 0], [0.2 0.7 0.2]});
total_cov = [1.42, 4.74, 4.74, 6.48, 11.94];

figure('Position', [50, 50, 1600, 750]);

%% ===== 主体: 甘特图 =====
subplot(5,1,[1,4]); hold on; grid on;
title('遮蔽时间线 (甘特图)', 'FontSize', 15, 'FontWeight', 'bold');

% 纵轴: 每个问题一行+导弹子行
y_tick_labels = {};
y_tick_pos = [];
y_current = 0.5;

for p = 1:5
    prob_name = intervals{p,1};
    missile_data = intervals{p,2};
    n_missiles = length(missile_data);

    % 问题标签行
    y_problem = y_current + 0.3;
    y_tick_labels{end+1} = '';
    y_tick_pos(end+1) = y_problem;

    for m = 1:n_missiles
        mid = missile_data{m}{1};
        intvs = missile_data{m}{2};  % [N×2] matrix
        c = missile_colors(mid);

        y_mid = y_current;
        y_tick_labels{end+1} = [prob_name(1:6) ' | ' mid];
        y_tick_pos(end+1) = y_mid;

        % 画每个遮蔽区间 (甘特条)
        for r = 1:size(intvs, 1)
            t_start = intvs(r,1);
            t_end   = intvs(r,2);
            duration = t_end - t_start;

            rectangle('Position', [t_start, y_mid-0.22, duration, 0.44], ...
                'FaceColor', c, 'EdgeColor', 'k', 'LineWidth', 1, ...
                'Curvature', 0.1);

            % 标注时长
            if duration > 0.3
                text(t_start + duration/2, y_mid, sprintf('%.2fs', duration), ...
                    'HorizontalAlignment', 'center', 'FontSize', 8, ...
                    'FontWeight', 'bold', 'Color', 'white');
            end
        end

        % 标注总遮蔽时长（右侧）
        cov_val = 0;
        for r = 1:size(intvs, 1)
            cov_val = cov_val + intvs(r,2) - intvs(r,1);
        end
        text(70, y_mid, sprintf('%.2fs', cov_val), ...
            'FontSize', 9, 'FontWeight', 'bold', 'Color', c, ...
            'HorizontalAlignment', 'left');

        y_current = y_current + 0.55;
    end
    y_current = y_current + 0.25;
end

% 导弹命中线
t_hit_vals = [67.00, 63.75, 60.37];
hit_styles = {'-', '--', ':'};
for m = 1:3
    xline(t_hit_vals(m), hit_styles{m}, ...
        sprintf('M%d命中 %.0fs', m, t_hit_vals(m)), ...
        'Color', missile_colors(['M' num2str(m)]), 'Alpha', 0.6, ...
        'LineWidth', 1.5);
end

xlabel('时间 (s)', 'FontSize', 13);
xlim([0, 72]);
yticks(y_tick_pos);
yticklabels(y_tick_labels);
set(gca, 'FontSize', 9);

%% ---- 底部: 总遮蔽时长对比 ----
subplot(5,1,5); hold on; grid on;
b = bar(1:5, total_cov, 0.5, 'FaceColor', [0.3 0.5 0.7]);
for i = 1:5
    text(i, total_cov(i)+0.3, sprintf('%.2fs', total_cov(i)), ...
        'HorizontalAlignment', 'center', 'FontSize', 12, ...
        'FontWeight', 'bold');
end
set(gca, 'XTick', 1:5, 'XTickLabel', ...
    {'问题1','问题2','问题3','问题4','问题5'}, 'FontSize', 11);
ylabel('总遮蔽 (s)', 'FontSize', 12);
title('各题总遮蔽时长', 'FontSize', 13);

sgtitle('2025 CUMCM A题 — 遮蔽时间线全景', ...
    'FontSize', 16, 'FontWeight', 'bold');
saveas(gcf, 'timeline_gantt.png');
fprintf('Figure saved: timeline_gantt.png\n');
