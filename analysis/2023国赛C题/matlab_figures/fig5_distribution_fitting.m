%% fig5_distribution_fitting.m
% 图5: 日销量分布拟合 — 对数正态分布 + KS 检验
% 数据来源: output/daily_category_sales.csv
% 对数正态参数 + KS p 值均从真实数据实时计算
clear; close all;

% ===== 读取日销量数据 =====
T = readtable('../output/daily_category_sales.csv', 'VariableNamingRule', 'preserve');

% 品类顺序（与图1一致）
categories = {'花叶类', '花菜类', '茄类', '辣椒类', '食用菌', '水生根茎类'};
colors = [
    0.20 0.80 0.20;   % 花叶类     - green
    0.90 0.50 0.00;   % 花菜类     - orange
    0.70 0.20 0.70;   % 茄类       - purple
    0.90 0.20 0.20;   % 辣椒类     - red
    0.20 0.70 0.70;   % 食用菌     - teal
    0.20 0.60 0.80;   % 水生根茎类 - blue
];
n = length(categories);

figure('Position', [0, 0, 1200, 700], 'Toolbar', 'figure', 'Menubar', 'figure');
movegui(gcf, 'center');

for i = 1:n
    subplot(3, 2, i); hold on; grid on;

    cat = categories{i};
    data = T.(cat);
    data = data(data > 0);  % 排除零销量日

    % ===== 直方图（密度归一化） =====
    histogram(data, 40, 'Normalization', 'pdf', ...
        'FaceColor', colors(i,:), 'FaceAlpha', 0.45, 'EdgeColor', 'none');

    % ===== 拟合对数正态分布（参数从数据估计） =====
    logdata = log(data);
    mu_hat  = mean(logdata);
    sigma_hat = std(logdata);
    x_vals  = linspace(min(data), max(data), 200);
    pdf_vals = lognpdf(x_vals, mu_hat, sigma_hat);
    plot(x_vals, pdf_vals, 'Color', colors(i,:), 'LineWidth', 2.5);

    % ===== 均值和中位数标注 =====
    data_mean = mean(data);
    data_median = median(data);
    xline(data_mean, 'r--', 'LineWidth', 1.5);
    xline(data_median, 'b--', 'LineWidth', 1.5);

    % ===== KS 检验（真实计算，使用分布对象兼容新版 kstest） =====
    pd = makedist('Lognormal', 'mu', mu_hat, 'sigma', sigma_hat);
    [h_ks, p_ks, ks_stat] = kstest(data, 'CDF', pd);

    if p_ks > 0.05
        p_status = sprintf('PASS (p=%.4f)', p_ks);
    else
        p_status = sprintf('REJECT (p=%.4f)', p_ks);
    end

    % 理论均值和中位数（对数正态）
    theory_mean = exp(mu_hat + sigma_hat^2 / 2);
    theory_median = exp(mu_hat);

    title(sprintf('%s:  LN(%.2f, %.2f)  KS %s  D=%.4f', ...
        cat, mu_hat, sigma_hat, p_status, ks_stat), ...
        'FontSize', 9.5, 'FontWeight', 'bold');
    xlabel('Daily Sales (kg)', 'FontSize', 10);
    ylabel('Density', 'FontSize', 10);

    if i == 1
        legend({'Histogram (n=' num2str(length(data)) ')', ...
            'Lognormal fit', ...
            sprintf('Mean=%.1f', data_mean), ...
            sprintf('Median=%.1f', data_median)}, ...
            'FontSize', 8, 'Location', 'northeast');
    end
end

sgtitle('Problem 1A: Distribution Fitting — Daily Sales ~ Lognormal (KS computed from data)', ...
    'FontSize', 14, 'FontWeight', 'bold');
saveas(gcf, 'fig5_distribution_fitting.png');
fprintf('Saved: fig5_distribution_fitting.png\n');
fprintf('  KS test computed from daily_category_sales.csv (1085 days)\n');
for i = 1:n
    cat = categories{i};
    data = T.(cat);
    data = data(data > 0);
    logdata = log(data);
    mu_hat = mean(logdata);
    sigma_hat = std(logdata);
    pd = makedist('Lognormal', 'mu', mu_hat, 'sigma', sigma_hat);
    [~, p_ks] = kstest(data, 'CDF', pd);
    fprintf('  %s: LN(%.2f, %.2f)  KS p=%.4f\n', cat, mu_hat, sigma_hat, p_ks);
end
