%% fig4_correlation_heatmap.m
% 图4: 品类间相关系数热力图 — Pearson + Spearman
% 数据来源: output/pearson_corr.csv + output/daily_category_sales.csv
% Pearson 从 CSV 读取，Spearman 从日销量数据实时计算
clear; close all;

% ===== 读取 Pearson 相关系数矩阵 =====
T_pearson = readtable('../output/pearson_corr.csv', 'VariableNamingRule', 'preserve');
% 第一列是分类名称，其余 6 列是相关系数
var_names = T_pearson.Properties.VariableNames;
cat_names_pearson = var_names(2:end);  % 品类名（列标题）
pearson_cats = T_pearson{:, 1};        % 品类名（行标题）
pearson_mat = T_pearson{:, 2:7};       % 6×6 矩阵

% 确保品类顺序一致
cat_order = {'水生根茎类', '花叶类', '花菜类', '茄类', '辣椒类', '食用菌'};
cat_short  = {'水生根茎', '花叶类', '花菜类', '茄类', '辣椒类', '食用菌'};
n = 6;

% 按统一顺序重排 Pearson 矩阵
pearson_ordered = zeros(n, n);
for i = 1:n
    for j = 1:n
        row_i = find(strcmp(pearson_cats, cat_order{i}));
        col_j = find(strcmp(cat_names_pearson, cat_order{j}));
        if ~isempty(row_i) && ~isempty(col_j)
            pearson_ordered(i, j) = pearson_mat(row_i, col_j);
        end
    end
end

% ===== 从日销量数据计算 Spearman 秩相关系数 =====
sales = readtable('../output/daily_category_sales.csv', 'VariableNamingRule', 'preserve');
% 提取 6 列销量数据
sales_mat = zeros(height(sales), n);
for i = 1:n
    sales_mat(:, i) = sales.(cat_order{i});
end

% 计算 Spearman 相关矩阵
spearman_mat = corr(sales_mat, 'Type', 'Spearman');

% ===== 颜色方案 =====
colors = [
    0.20 0.60 0.80;   % 水生根茎类
    0.20 0.80 0.20;   % 花叶类
    0.90 0.50 0.00;   % 花菜类
    0.70 0.20 0.70;   % 茄类
    0.90 0.20 0.20;   % 辣椒类
    0.20 0.70 0.70;   % 食用菌
];

figure('Position', [0, 0, 1100, 500], 'Toolbar', 'figure', 'Menubar', 'figure');
movegui(gcf, 'center');

%% ---- 左: Pearson 热力图 ----
subplot(1,2,1);
imagesc(pearson_ordered);
colormap(gca, flipud(bone));
clim([0 1]);
cb = colorbar;
cb.Label.String = 'Pearson r';
title('Pearson Correlation (linear)', 'FontSize', 13, 'FontWeight', 'bold');

% 在每个格子标注数值 + 显著性标记
for i = 1:n
    for j = 1:n
        val = pearson_ordered(i, j);
        if val >= 0.6
            txt_color = 'w';  % 深色背景用白字
        else
            txt_color = 'k';
        end
        % 显著性：|r| > 2/sqrt(n_obs)=2/sqrt(1085)≈0.061 即显著
        sig_mark = '';
        if i ~= j && abs(val) > 0.061
            sig_mark = '*';
        end
        text(j, i, sprintf('%.3f%s', val, sig_mark), ...
            'HorizontalAlignment', 'center', ...
            'FontSize', 12, 'FontWeight', 'bold', 'Color', txt_color);
    end
end

% 高亮茄类的低相关行
hold on;
for j = 1:n
    rectangle('Position', [j-0.5, 3.5, 1, 1], ...
        'EdgeColor', 'r', 'LineWidth', 2.5);
end

set(gca, 'XTick', 1:n, 'XTickLabel', cat_short, 'FontSize', 10);
set(gca, 'YTick', 1:n, 'YTickLabel', cat_short, 'FontSize', 10);
xtickangle(30);

%% ---- 右: Spearman 热力图 ----
subplot(1,2,2);
imagesc(spearman_mat);
colormap(gca, flipud(bone));
clim([-0.3 1]);
cb = colorbar;
cb.Label.String = 'Spearman \rho';
title('Spearman Correlation (monotonic)', 'FontSize', 13, 'FontWeight', 'bold');

for i = 1:n
    for j = 1:n
        val = spearman_mat(i, j);
        if val > 0.5
            txt_color = 'w';
        elseif val < -0.1
            txt_color = 'r';  % 负相关用红色标注
        else
            txt_color = 'k';
        end
        sig_mark = '';
        if i ~= j && abs(val) > 0.061
            sig_mark = '*';
        end
        text(j, i, sprintf('%.3f%s', val, sig_mark), ...
            'HorizontalAlignment', 'center', ...
            'FontSize', 12, 'FontWeight', 'bold', 'Color', txt_color);
    end
end

% 标注负相关格子（茄类 vs 水生根茎、食用菌）
hold on;
neg_pairs = {[4, 1], [4, 6]};  % 茄类行 × 水生根茎列, 茄类行 × 食用菌列
for k = 1:length(neg_pairs)
    r = neg_pairs{k}(1);
    c = neg_pairs{k}(2);
    rectangle('Position', [c-0.5, r-0.5, 1, 1], ...
        'EdgeColor', 'r', 'LineWidth', 2.5, 'LineStyle', '--');
end

set(gca, 'XTick', 1:n, 'XTickLabel', cat_short, 'FontSize', 10);
set(gca, 'YTick', 1:n, 'YTickLabel', cat_short, 'FontSize', 10);
xtickangle(30);

sgtitle({'Problem 1B: Category Sales Correlation Analysis', ...
    ['Pearson from pearson\_corr.csv | Spearman from daily\_category\_sales.csv', ...
     ' (* p<0.05, n=1085 days)']}, ...
    'FontSize', 11, 'FontWeight', 'bold');
saveas(gcf, 'fig4_correlation_heatmap.png');
fprintf('Saved: fig4_correlation_heatmap.png\n');
fprintf('  Pearson: read from pearson_corr.csv\n');
fprintf('  Spearman: computed from 1085-day sales matrix\n');
