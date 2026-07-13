%% fig3_stl_decomposition.m
% 图3: STL时间序列分解 — 趋势 + 周季节模式
% 数据来源: output/stl_flat.csv（1085天 × 6品类，period=365）
% 趋势变化率与 results_summary.md 一致
clear; close all;

% ===== 读取真实 STL 分解结果 =====
T = readtable('../output/stl_flat.csv', 'VariableNamingRule', 'preserve');

categories = {'花叶类', '辣椒类', '食用菌', '水生根茎类', '花菜类', '茄类'};
colors = [
    0.20 0.80 0.20;   % 花叶类     - green
    0.90 0.20 0.20;   % 辣椒类     - red
    0.20 0.70 0.70;   % 食用菌     - teal
    0.20 0.60 0.80;   % 水生根茎类 - blue
    0.90 0.50 0.00;   % 花菜类     - orange
    0.70 0.20 0.70;   % 茄类       - purple
];
n = length(categories);

%% ===== 图 3a: 6 品类趋势线（原始 vs 趋势） =====
figure('Position', [0, 0, 1200, 700], 'Toolbar', 'figure', 'Menubar', 'figure');
movegui(gcf, 'center');

for i = 1:n
    cat = categories{i};
    idx = strcmp(T.category, cat);
    dates = datetime(T.date(idx), 'InputFormat', 'yyyy-MM-dd');
    orig  = T.original(idx);
    trend = T.trend(idx);
    seasonal = T.seasonal(idx);

    subplot(3, 2, i); hold on; grid on;

    % 原始销量（浅色）
    plot(dates, orig, 'Color', [colors(i,:) 0.25], 'LineWidth', 0.5);

    % 趋势线（深色粗线）
    plot(dates, trend, 'Color', colors(i,:), 'LineWidth', 2.5);

    % 趋势变化率（从数据计算，非硬编码）
    trend_chg = (trend(end) / trend(1) - 1) * 100;

    % 季节强度 = 1 - Var(resid)/Var(seasonal+resid) 的近似
    % 用 Var(seasonal)/Var(original) 作为替代指标
    seasonal_strength = std(seasonal) / std(orig);

    title(sprintf('%s: trend %.1f→%.1f (%+.0f%%), season strength=%.2f', ...
        cat, trend(1), trend(end), trend_chg, seasonal_strength), ...
        'FontSize', 9.5, 'FontWeight', 'bold');
    xlabel('Date'); ylabel('Sales (kg)');
    legend({'Original', 'Trend'}, 'FontSize', 8, 'Location', 'best');
    datetick('x', 'yyyy-mm', 'keeplimits');
end

sgtitle('Problem 1A: STL Decomposition — Trend (period=365, from stl\\_flat.csv)', ...
    'FontSize', 14, 'FontWeight', 'bold');
saveas(gcf, 'fig3_stl_trend.png');
fprintf('Saved: fig3_stl_trend.png\n');

%% ===== 图 3b: 周季节模式对比（最后 28 天） =====
figure('Position', [0, 0, 1000, 350], 'Toolbar', 'figure', 'Menubar', 'figure');
movegui(gcf, 'center');
hold on; grid on;

legends = cell(n, 1);
for i = 1:n
    cat = categories{i};
    idx = strcmp(T.category, cat);
    seasonal = T.seasonal(idx);
    n_days = length(seasonal);

    % 取最后 28 天的季节分量
    if n_days >= 28
        plot(1:28, seasonal(n_days-27:n_days), '-', ...
            'Color', colors(i,:), 'LineWidth', 2.2);
    else
        plot(1:n_days, seasonal, '-', ...
            'Color', colors(i,:), 'LineWidth', 2.2);
    end
    legends{i} = cat;
end

legend(legends, 'FontSize', 9, 'Location', 'best');
xlabel('Day (last 28 days: 2023-06-03 to 2023-06-30)', 'FontSize', 12);
ylabel('Seasonal Component (kg)', 'FontSize', 12);
title('Weekly Seasonal Pattern Comparison (Last 4 Weeks, from stl\\_flat.csv)', ...
    'FontSize', 14, 'FontWeight', 'bold');
set(gca, 'XTick', 1:7:28);

saveas(gcf, 'fig3_seasonal_pattern.png');
fprintf('Saved: fig3_seasonal_pattern.png\n');
