%% fig1_descriptive_stats.m
% 图1: 蔬菜品类销量描述统计
% 数据来源: output/desc_stats.csv, output/daily_category_sales.csv
% 所有数据均从真实计算结果读取，无硬编码
clear; close all;

% ===== 读取真实数据 =====
desc = readtable('../output/desc_stats.csv', 'VariableNamingRule', 'preserve');

categories = desc.('分类名称');
daily_mean  = desc.('日均销量_kg');
daily_std   = desc.('标准差');
daily_cv    = desc.('变异系数CV');
skewness    = desc.('偏度');
kurtosis    = desc.('峰度');
total_share = desc.('销量占比');
n = length(categories);

% ===== 颜色方案（全系列统一） =====
colors = [
    0.20 0.60 0.80;   % 水生根茎类 - blue
    0.20 0.80 0.20;   % 花叶类     - green
    0.90 0.50 0.00;   % 花菜类     - orange
    0.70 0.20 0.70;   % 茄类       - purple
    0.90 0.20 0.20;   % 辣椒类     - red
    0.20 0.70 0.70;   % 食用菌     - teal
];

% ===== 主图：6 子图面板 =====
figure('Position', [0, 0, 1200, 650], 'Toolbar', 'figure', 'Menubar', 'figure');
movegui(gcf, 'center');

%% ---- 子图 1: 日均销量 ± 1σ ----
subplot(2,3,1); hold on; grid on;
b = bar(1:n, daily_mean, 0.6, 'FaceColor', 'flat');
for i = 1:n; b.CData(i,:) = colors(i,:); end
errorbar(1:n, daily_mean, daily_std, 'k.', 'LineWidth', 1.5, 'CapSize', 8);
for i = 1:n
    text(i, daily_mean(i) + daily_std(i) + max(daily_mean)*0.03, ...
        sprintf('%.1f', daily_mean(i)), ...
        'HorizontalAlignment', 'center', 'FontSize', 8, 'FontWeight', 'bold');
end
set(gca, 'XTick', 1:n, 'XTickLabel', categories, 'FontSize', 9);
xtickangle(30);
ylabel('Daily Sales (kg)', 'FontSize', 11);
title('(a) Avg Daily Sales \pm 1 Std', 'FontSize', 12, 'FontWeight', 'bold');

%% ---- 子图 2: 销量占比 ----
subplot(2,3,2); hold on; grid on;
b2 = bar(1:n, total_share, 0.6, 'FaceColor', 'flat');
for i = 1:n; b2.CData(i,:) = colors(i,:); end
for i = 1:n
    text(i, total_share(i) + 1, sprintf('%.1f%%', total_share(i)), ...
        'HorizontalAlignment', 'center', 'FontSize', 9, 'FontWeight', 'bold');
end
set(gca, 'XTick', 1:n, 'XTickLabel', categories, 'FontSize', 9);
xtickangle(30);
ylabel('Share of Total Sales (%)', 'FontSize', 11);
title('(b) Sales Share by Category', 'FontSize', 12, 'FontWeight', 'bold');

%% ---- 子图 3: 变异系数 CV ----
subplot(2,3,3); hold on; grid on;
b3 = bar(1:n, daily_cv, 0.6, 'FaceColor', 'flat');
for i = 1:n; b3.CData(i,:) = colors(i,:); end
for i = 1:n
    text(i, daily_cv(i) + 0.02, sprintf('%.3f', daily_cv(i)), ...
        'HorizontalAlignment', 'center', 'FontSize', 9, 'FontWeight', 'bold');
end
set(gca, 'XTick', 1:n, 'XTickLabel', categories, 'FontSize', 9);
xtickangle(30);
ylabel('Coefficient of Variation', 'FontSize', 11);
title('(c) CV = \sigma/\mu (lower = more stable)', 'FontSize', 12, 'FontWeight', 'bold');
yline(0.5, 'r--', 'LineWidth', 1.2);
text(0.3, 0.52, 'moderate threshold', 'FontSize', 8, 'Color', 'r');

%% ---- 子图 4: 偏度 ----
subplot(2,3,4); hold on; grid on;
b4 = bar(1:n, skewness, 0.6, 'FaceColor', 'flat');
for i = 1:n; b4.CData(i,:) = colors(i,:); end
for i = 1:n
    text(i, skewness(i) + 0.08, sprintf('%.2f', skewness(i)), ...
        'HorizontalAlignment', 'center', 'FontSize', 9, 'FontWeight', 'bold');
end
set(gca, 'XTick', 1:n, 'XTickLabel', categories, 'FontSize', 9);
xtickangle(30);
ylabel('Skewness', 'FontSize', 11);
title('(d) Skewness (>0 = right-tailed)', 'FontSize', 12, 'FontWeight', 'bold');
yline(0, 'k-', 'LineWidth', 1);

%% ---- 子图 5: 峰度（超额峰度） ----
subplot(2,3,5); hold on; grid on;
b5 = bar(1:n, kurtosis, 0.6, 'FaceColor', 'flat');
for i = 1:n; b5.CData(i,:) = colors(i,:); end
for i = 1:n
    text(i, kurtosis(i) + max(kurtosis)*0.02, sprintf('%.1f', kurtosis(i)), ...
        'HorizontalAlignment', 'center', 'FontSize', 9, 'FontWeight', 'bold');
end
set(gca, 'XTick', 1:n, 'XTickLabel', categories, 'FontSize', 9);
xtickangle(30);
ylabel('Excess Kurtosis', 'FontSize', 11);
title('(e) Kurtosis (>0 = heavy-tailed vs normal)', 'FontSize', 12, 'FontWeight', 'bold');
yline(0, 'k-', 'LineWidth', 1);  % 正态分布峰度为 0（超额）

%% ---- 子图 6: 汇总表格（text 手绘，避免 uitable 越界） ----
subplot(2,3,6); hold on;
axis([0 11 0 9]); axis off;
title('(f) Summary Statistics Table', 'FontSize', 12, 'FontWeight', 'bold');

% 表头和数据
col_headers = {'Category','Mean','Std','CV','Skew','Kurt','Share%'};
n_rows = n + 1;  % 表头 + 6 行数据
n_cols = length(col_headers);

% 列位置（x坐标）
col_x = [0.5, 2.3, 3.5, 4.5, 5.7, 6.7, 7.9, 9.8];  % 右边界

% 画表头
for c = 1:n_cols
    text(col_x(c), n_rows, col_headers{c}, ...
        'FontSize', 8, 'FontWeight', 'bold', ...
        'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle');
end

% 画数据行
for r = 1:n
    row_y = n_rows - r;
    % 行分隔线
    plot([0, 10], [row_y-0.5, row_y-0.5], '-', 'Color', [0.85 0.85 0.85], 'LineWidth', 0.5);

    % 品类名（颜色标记）
    text(col_x(1), row_y, categories{r}, ...
        'FontSize', 8, 'FontWeight', 'bold', 'Color', colors(r,:), ...
        'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle');

    % 数值
    vals = {sprintf('%.1f',daily_mean(r)),  sprintf('%.1f',daily_std(r)), ...
            sprintf('%.3f',daily_cv(r)),    sprintf('%.2f',skewness(r)), ...
            sprintf('%.1f',kurtosis(r)),    sprintf('%.1f%%',total_share(r))};
    for c = 2:n_cols
        text(col_x(c), row_y, vals{c-1}, ...
            'FontSize', 8, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle');
    end
end

% 顶部分隔线
plot([0, 10], [n_rows-0.5, n_rows-0.5], 'k-', 'LineWidth', 1);
% 底部分隔线
plot([0, 10], [0, 0], 'k-', 'LineWidth', 1);

sgtitle('Problem 1A: Sales Distribution by Category (all data from output/)', ...
    'FontSize', 14, 'FontWeight', 'bold');
saveas(gcf, 'fig1_descriptive_stats.png');
fprintf('Saved: fig1_descriptive_stats.png (all data from desc_stats.csv)\n');
