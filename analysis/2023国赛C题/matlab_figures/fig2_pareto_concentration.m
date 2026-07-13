%% fig2_pareto_concentration.m
% 图2: 单品销量集中度 — 帕累托图 + 品类 Gini 系数
% 数据来源: output/item_ranked.csv（246 个单品真实销量）
% Gini 系数从真实单品销量分组计算
clear; close all;

% ===== 读取真实数据 =====
items = readtable('../output/item_ranked.csv', 'VariableNamingRule', 'preserve');

% 按销量降序排列（CSV已经是降序，但确保一致）
item_sales = items.('销量_kg');
[item_sales, idx] = sort(item_sales, 'descend');
item_cats  = items.('分类名称');
item_cats  = item_cats(idx);
n_items = length(item_sales);
total_sales = sum(item_sales);

% 计算单品份额和累计份额
item_share = 100 * item_sales / total_sales;
cum_share  = 100 * cumsum(item_sales) / total_sales;

% Pareto 关键指标：真实计算 TOP-n 累计占比
top_thresholds = [10, 20, 30, 50, 100];
top_share = zeros(size(top_thresholds));
for i = 1:length(top_thresholds)
    top_share(i) = sum(item_sales(1:min(top_thresholds(i), n_items))) / total_sales * 100;
end

% ===== 按品类计算 Gini 系数（从真实单品销量） =====
cat_list = unique(items.('分类名称'), 'stable');
n_cats = length(cat_list);
gini_vals = zeros(n_cats, 1);
cat_item_counts = zeros(n_cats, 1);

for i = 1:n_cats
    mask = strcmp(item_cats, cat_list{i});
    sales_i = sort(item_sales(mask), 'ascend');  % Gini 需要升序
    n_i = length(sales_i);
    cat_item_counts(i) = n_i;
    if n_i > 1 && sum(sales_i) > 0
        % Gini = (2*sum(k*x_k) - (n+1)*sum(x_k)) / (n*sum(x_k))
        ranks = (1:n_i)';
        gini_vals(i) = (2 * sum(ranks .* sales_i) - (n_i + 1) * sum(sales_i)) ...
                     / (n_i * sum(sales_i));
    else
        gini_vals(i) = 0;
    end
end

% ===== 颜色方案 =====
colors = [
    0.20 0.60 0.80;   % 水生根茎类
    0.20 0.80 0.20;   % 花叶类
    0.90 0.50 0.00;   % 花菜类
    0.70 0.20 0.70;   % 茄类
    0.90 0.20 0.20;   % 辣椒类
    0.20 0.70 0.70;   % 食用菌
];

% ===== 确保 Gini 顺序与颜色一致 =====
cat_order = {'水生根茎类', '花叶类', '花菜类', '茄类', '辣椒类', '食用菌'};
gini_ordered = zeros(6, 1);
for i = 1:6
    idx_c = find(strcmp(cat_list, cat_order{i}));
    if ~isempty(idx_c)
        gini_ordered(i) = gini_vals(idx_c);
    end
end

% ===== 主图 =====
figure('Position', [0, 0, 1100, 500], 'Toolbar', 'figure', 'Menubar', 'figure');
movegui(gcf, 'center');

%% ---- 左: 全品类单品帕累托图 ----
subplot(1,2,1);
yyaxis left;
hold on; grid on;

% 蓝色柱状图 — 前 80 个单品（后面太矮看不清）
show_n = min(80, n_items);
bar(1:show_n, item_share(1:show_n), 1.0, ...
    'FaceColor', [0.25 0.50 0.70], 'EdgeColor', 'none');
ylabel('Individual Share (%)', 'FontSize', 12);
ylim([0, max(item_share)*1.15]);

% 红色累计曲线
yyaxis right;
plot(1:n_items, cum_share, 'r-', 'LineWidth', 2.5);
ylabel('Cumulative Share (%)', 'FontSize', 12);
ylim([0, 105]);

% 参考线
yline(50, 'k--', 'LineWidth', 1);
yline(80, 'k--', 'LineWidth', 1);

% 标注 TOP-n 累计占比
for i = 1:length(top_thresholds)
    if top_thresholds(i) <= n_items
        xline(top_thresholds(i), 'g--', 'LineWidth', 1.2);
        text(top_thresholds(i) + 2, top_share(i) + 2, ...
            sprintf('TOP%d: %.1f%%', top_thresholds(i), top_share(i)), ...
            'FontSize', 9, 'FontWeight', 'bold', 'Color', [0 0.5 0]);
    end
end

xlabel(sprintf('Item Rank (by total sales volume, n=%d)', n_items), 'FontSize', 12);
title('Pareto Chart: Item Sales Concentration', 'FontSize', 13, 'FontWeight', 'bold');
xlim([0, min(100, n_items)]);

%% ---- 右: 各品类 Gini 系数 ----
subplot(1,2,2); hold on; grid on;
b = bar(1:6, gini_ordered, 0.6, 'FaceColor', 'flat');
for i = 1:6; b.CData(i,:) = colors(i,:); end
for i = 1:6
    text(i, gini_ordered(i) + 0.015, sprintf('%.3f', gini_ordered(i)), ...
        'HorizontalAlignment', 'center', 'FontSize', 12, 'FontWeight', 'bold');
end
set(gca, 'XTick', 1:6, 'XTickLabel', cat_order, 'FontSize', 10);
xtickangle(25);
ylabel('Gini Coefficient', 'FontSize', 12);
title('Item Sales Concentration by Category (Gini)', 'FontSize', 13, 'FontWeight', 'bold');

% 参考线
yline(0.5, 'r--', 'LineWidth', 1.2);
text(0.4, 0.51, 'moderate (0.5)', 'FontSize', 8, 'Color', 'r');
yline(0.7, 'r--', 'LineWidth', 1.2);
text(0.4, 0.71, 'high (0.7)', 'FontSize', 8, 'Color', 'r');
ylim([0.5, 0.9]);

sgtitle('Problem 1A: Item Sales Concentration Analysis (computed from item\\_ranked.csv)', ...
    'FontSize', 14, 'FontWeight', 'bold');
saveas(gcf, 'fig2_pareto_concentration.png');
fprintf('Saved: fig2_pareto_concentration.png\n');
fprintf('  Gini computed from %d items across %d categories\n', n_items, n_cats);
for i = 1:6
    fprintf('  %s: Gini=%.4f (n=%d items)\n', cat_order{i}, gini_ordered(i), ...
        sum(strcmp(item_cats, cat_order{i})));
end
