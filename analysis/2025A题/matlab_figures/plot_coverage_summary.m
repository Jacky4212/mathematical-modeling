%% plot_coverage_summary.m
% 五题结果汇总对比: 柱状图 + 改进百分比
clear; close all;

problems = {'问题1', '问题2', '问题3', '问题4', '问题5'};
descriptions = {
    'FY1单弹\n(给定参数)';
    'FY1单弹\n(优化航向)';
    'FY1三弹\n(序贯优化)';
    '三机协同\n(FY1+2+3)';
    '全系统\n(5机×3弹)'};
coverages = [1.42, 4.74, 4.74, 6.48, 11.94];
improvements = [0, 234, 234, 356, 741];  % vs 问题1 baseline
colors = [
    0.7 0.7 0.7;   % 问题1: gray
    0.2 0.5 0.8;   % 问题2: blue
    0.2 0.7 0.2;   % 问题3: green
    0.9 0.5 0.0;   % 问题4: orange
    0.7 0.2 0.2;   % 问题5: red
];

figure('Position', [100, 100, 1500, 600]);

%% ---- 左: 遮蔽时长柱状图 ----
subplot(1,2,1); hold on; grid on;
b = bar(1:5, coverages, 0.6);
b.FaceColor = 'flat';
for i = 1:5; b.CData(i,:) = colors(i,:); end

% 在柱子上标注数值
for i = 1:5
    text(i, coverages(i) + 0.4, sprintf('%.2f s', coverages(i)), ...
        'HorizontalAlignment', 'center', 'FontSize', 14, ...
        'FontWeight', 'bold', 'Color', colors(i,:));
end

% 连接线显示增长趋势
plot(1:5, coverages, 'k-o', 'LineWidth', 2, 'MarkerSize', 8, ...
    'MarkerFaceColor', 'k');

set(gca, 'XTick', 1:5, 'XTickLabel', problems, 'FontSize', 11);
ylabel('遮蔽时长 (s)', 'FontSize', 13);
title('2025 CUMCM A题: 五题遮蔽时长汇总', 'FontSize', 15, ...
    'FontWeight', 'bold');
ylim([0, 14]);

% 为每根柱子添加文字描述
for i = 1:5
    text(i, coverages(i)/2, descriptions{i}, ...
        'HorizontalAlignment', 'center', 'FontSize', 9, ...
        'Color', 'white', 'FontWeight', 'bold');
end

%% ---- 右: 相对问题1的改进百分比 ----
subplot(1,2,2); hold on; grid on;
b2 = bar(1:5, improvements, 0.6);
b2.FaceColor = 'flat';
for i = 1:5; b2.CData(i,:) = colors(i,:); end

for i = 1:5
    lbl = sprintf('+%d%%', improvements(i));
    if i == 1; lbl = '基准'; end
    text(i, improvements(i) + 30, lbl, ...
        'HorizontalAlignment', 'center', 'FontSize', 13, ...
        'FontWeight', 'bold', 'Color', colors(i,:));
end

% 填充面积图显示累积进步
xx = 1:0.1:5;
yy = interp1(1:5, improvements, xx, 'pchip');
fill([xx, fliplr(xx)], [yy, zeros(size(yy))], [0.5 0.8 0.5], ...
    'FaceAlpha', 0.15, 'EdgeColor', 'none');

set(gca, 'XTick', 1:5, 'XTickLabel', problems, 'FontSize', 11);
ylabel('相对问题1改进 (%)', 'FontSize', 13);
title('遮蔽时长改进幅度 (vs 问题1=1.42s)', 'FontSize', 15, ...
    'FontWeight', 'bold');

sgtitle('2025 CUMCM A题 — 烟幕干扰弹投放策略 结果汇总', ...
    'FontSize', 16, 'FontWeight', 'bold');
saveas(gcf, 'coverage_summary.png');
fprintf('Figure saved: coverage_summary.png\n');
