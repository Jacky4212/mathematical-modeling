%% fig6_cross_correlation.m
% 图6: 品类间互相关分析 (CCF) — 领先/滞后关系
% 数据来源: output/daily_category_sales.csv
% CCF 从真实日销量时间序列实时计算（非模拟/高斯函数伪造）
clear; close all;

% ===== 读取日销量数据 =====
T = readtable('../output/daily_category_sales.csv', 'VariableNamingRule', 'preserve');

cat_order = {'水生根茎类', '花叶类', '花菜类', '茄类', '辣椒类', '食用菌'};
cat_short = {'水生根茎', '花叶类', '花菜类', '茄类', '辣椒类', '食用菌'};
n_cats = length(cat_order);

% 提取 6 列时间序列
ts_data = zeros(height(T), n_cats);
for i = 1:n_cats
    ts_data(:, i) = T.(cat_order{i});
end

% ===== 选择展示的品类对 =====
% 基于 Pearson 相关 + 茄类的先行指标特征，选择 8 组
pairs = {
    '花叶类',     '辣椒类';     % Pearson 0.660, 强同期
    '花叶类',     '花菜类';     % Pearson 0.628
    '花叶类',     '食用菌';     % Pearson 0.631
    '辣椒类',     '食用菌';     % Pearson 0.687, 最强同期
    '水生根茎类', '食用菌';     % Pearson 0.670
    '水生根茎类', '花叶类';     % Pearson 0.561
    '茄类',       '食用菌';     % 茄类独立品类, 探索领先滞后
    '茄类',       '水生根茎类'; % 茄类独立品类, 探索领先滞后
};
n_pairs = size(pairs, 1);

% ===== 对所有 15 对计算 CCF =====
all_ccf = cell(n_cats, n_cats);
max_lag = 14;  % ±14 天

fprintf('Computing CCF for all %d category pairs (lag +/-%d days)...\n', ...
    n_cats*(n_cats-1)/2, max_lag);
for i = 1:n_cats
    for j = i+1:n_cats
        fprintf('  Computing: %s vs %s\n', cat_order{i}, cat_order{j});
        [ccf_v, lags] = compute_ccf(ts_data(:,i), ts_data(:,j), max_lag);
        all_ccf{i, j} = struct('ccf', ccf_v, 'lags', lags);
        all_ccf{j, i} = all_ccf{i, j};
        [max_val, max_idx] = max(abs(ccf_v));
        fprintf('    max|CCF|=%.3f at lag=%d\n', max_val, lags(max_idx));
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

% ===== 主图: 8 组 CCF 茎叶图 =====
figure('Position', [0, 0, 1200, 650], 'Toolbar', 'figure', 'Menubar', 'figure');
movegui(gcf, 'center');

for k = 1:n_pairs
    subplot(2, 4, k); hold on; grid on;

    catA = pairs{k, 1};
    catB = pairs{k, 2};
    idxA = find(strcmp(cat_order, catA));
    idxB = find(strcmp(cat_order, catB));

    ccf_result = all_ccf{idxA, idxB};
    ccf_vals = ccf_result.ccf;
    lags = ccf_result.lags;

    [max_abs_ccf, max_idx] = max(abs(ccf_vals));
    best_lag = lags(max_idx);
    best_ccf = ccf_vals(max_idx);

    n_obs = height(T);
    threshold = 2 / sqrt(n_obs);

    % 画所有 CCF 柱子（显著=深蓝，不显著=灰）
    for li = 1:length(lags)
        if abs(ccf_vals(li)) > threshold
            bar_color = [0.15 0.40 0.65];
        else
            bar_color = [0.70 0.70 0.70];
        end
        bar(lags(li), ccf_vals(li), 0.7, ...
            'FaceColor', bar_color, 'EdgeColor', 'none');
    end

    % 高亮最优滞后（红色）
    bar(best_lag, best_ccf, 0.7, ...
        'FaceColor', [0.85 0.15 0.15], 'EdgeColor', 'none');

    % 显著性阈值
    yline( threshold, 'r--', 'LineWidth', 1);
    yline(-threshold, 'r--', 'LineWidth', 1);

    title(sprintf('%s vs %s', catA, catB), ...
        'FontSize', 10, 'FontWeight', 'bold');
    xlabel('Lag (days)'); ylabel('CCF');
    xlim([-max_lag-1, max_lag+1]);

    % 文字说明
    if best_lag == 0
        note = '同期';
    elseif best_lag > 0
        note = sprintf('%s->%s(领先%d天)', catA, catB, best_lag);
    else
        note = sprintf('%s->%s(领先%d天)', catB, catA, -best_lag);
    end

    if best_ccf > 0
        text_y = best_ccf * 0.5;
    else
        text_y = best_ccf * 1.3;
    end
    text(0, text_y, sprintf('max|CCF|=%.3f   lag=%d (%s)', ...
        max_abs_ccf, best_lag, note), ...
        'FontSize', 8, 'FontWeight', 'bold', ...
        'BackgroundColor', [1 1 1 0.8], 'EdgeColor', [0.5 0.5 0.5]);
end

sgtitle(sprintf('Problem 1B: Cross-Correlation Analysis (CCF) — Real CCF from daily data (n=%d days)', n_obs), ...
    'FontSize', 13, 'FontWeight', 'bold');
saveas(gcf, 'fig6_cross_correlation.png');
fprintf('Saved: fig6_cross_correlation.png\n');
fprintf('  CCF computed from real time series data (not simulated)\n');
fprintf('  All %d pairs computed; 8 most informative pairs shown\n', n_cats*(n_cats-1)/2);

% ============================================================
% 局部函数：手写 CCF（必须在脚本末尾，避免依赖 Econometrics Toolbox）
% CCF 公式: r_xy(k) = c_xy(k) / sqrt(c_xx(0) * c_yy(0))
% ============================================================
function [ccf_vals, lags] = compute_ccf(x, y, max_lag)
    x = x(:); y = y(:);
    n = length(x);
    x_dm = x - mean(x, 'omitnan');
    y_dm = y - mean(y, 'omitnan');
    c0 = mean(x_dm.^2, 'omitnan') * mean(y_dm.^2, 'omitnan');
    denom = sqrt(c0);

    lags = -max_lag:max_lag;
    ccf_vals = zeros(size(lags));

    for idx = 1:length(lags)
        k = lags(idx);
        if k >= 0
            c_xy = mean(x_dm(1:n-k) .* y_dm(1+k:n), 'omitnan');
        else
            kk = -k;
            c_xy = mean(y_dm(1:n-kk) .* x_dm(1+kk:n), 'omitnan');
        end
        ccf_vals(idx) = c_xy / denom;
    end
end
