"""更新知识库: 添加网站专属方法chunk"""
import json

new_chunks = [
    # ===== 插值与拟合 =====
    {'id':'插值与拟合-01','title':'Lagrange 拉格朗日插值','category':'插值与拟合',
     'keywords':['Lagrange','拉格朗日','插值','多项式插值'],
     'search_text':'Lagrange 拉格朗日插值: 通过n+1个已知点构造n次多项式。L(x)=sum y_i * l_i(x)。高次插值会产生Runge现象，点>10个建议分段低次。适用: 数据精确、点少(<10个)。',
     'context':'【Lagrange插值】通过n+1点构造n次多项式，L(x)=sum y_i*l_i(x)。Runge现象: 高次两端振荡。scipy.interpolate.lagrange。'},
    {'id':'插值与拟合-02','title':'三次样条插值 Cubic Spline','category':'插值与拟合',
     'keywords':['Spline','样条','三次样条','插值','光滑'],
     'search_text':'三次样条插值: 分段三次多项式，节点处C2连续(函数值+一阶导+二阶导均连续)。无Runge现象，竞赛最常用。边界条件: 自然样条/clamped。scipy.interpolate.CubicSpline。',
     'context':'【三次样条插值】分段C2连续多项式。无Runge现象。scipy.interpolate.CubicSpline 或 interp1d(kind="cubic")。'},
    {'id':'插值与拟合-03','title':'最小二乘拟合 Least Squares','category':'插值与拟合',
     'keywords':['最小二乘','拟合','OLS','多项式拟合','R方'],
     'search_text':'最小二乘拟合: 不要求经过所有点，使残差平方和最小。拟合优度R^2=1-SSres/SStot。非线性(指数/对数/幂函数)可线性化后OLS。与插值区别: 拟合允许误差(去噪)，插值精确经过点。',
     'context':'【最小二乘拟合】min sum(y_i - y_hat_i)^2。R^2衡量优度。scipy.optimize.curve_fit。'},

    # ===== 蒙特卡洛 =====
    {'id':'蒙特卡洛-01','title':'蒙特卡洛积分与随机采样','category':'蒙特卡洛',
     'keywords':['蒙特卡洛','MC','随机采样','积分','收敛'],
     'search_text':'蒙特卡洛积分: 用随机采样近似定积分。误差O(1/sqrt(N))，收敛慢但维度无关(高维优势)。经典案例: 投针求pi、Buffon问题、中子屏蔽、期权定价。竞赛适用: 复杂概率计算、高维积分、随机仿真。',
     'context':'【蒙特卡洛积分】随机采样近似积分，误差O(1/sqrt(N))。经典案例: 投针求pi。竞赛用于复杂概率、高维积分、仿真。'},

    # ===== 时间序列 =====
    {'id':'时间序列-01','title':'平稳性检验与白噪声检验','category':'时间序列',
     'keywords':['平稳性','ADF','白噪声','Ljung-Box','单位根'],
     'search_text':'平稳性检验(建模前必做): 1)时序图-在常数附近波动无趋势周期→平稳 2)ACF图-快速衰减到0→平稳 3)ADF单位根检验-p<0.05拒绝H0→平稳。白噪声检验: Ljung-Box Q统计量，建模前p<0.05→非白噪声有价值；建模后残差p>0.05→模型充分。statsmodels.tsa.stattools.adfuller, acorr_ljungbox。',
     'context':'【平稳性+白噪声检验】ADF(p<0.05→平稳)、LB(p<0.05→有价值)。建模后残差LB p>0.05模型充分。'},
    {'id':'时间序列-02','title':'指数平滑法 Holt/Winter','category':'时间序列',
     'keywords':['指数平滑','Holt','Winter','Holt-Winters','平滑系数'],
     'search_text':'指数平滑家族: 1)简单指数平滑(无趋势无季节) F_{t+1}=alpha*Y_t+(1-alpha)*F_t 2)Holt双参数(有趋势) 同时平滑水平和趋势 3)Winter三参数(有趋势+季节) 再加季节平滑。alpha越大近期权重越大。选最优参数: 最小化MSE。statsmodels.tsa.holtwinters。',
     'context':'【指数平滑法】简单(1参数)→Holt(2参数,有趋势)→Winter(3参数,有趋势+季节)。alpha/gamma/delta in (0,1)，MSE最小选参。'},
    {'id':'时间序列-03','title':'ARMA/ARIMA 定阶与建模','category':'时间序列',
     'keywords':['ARMA','ARIMA','ACF','PACF','定阶','Box-Jenkins'],
     'search_text':'ARMA/ARIMA定阶核心: ACF截尾+PACF拖尾→MA(q); ACF拖尾+PACF截尾→AR(p); 都拖尾→ARMA(p,q)用AIC/BIC选。建模六步: 平稳性→差分→白噪声→ACF/PACF定阶→MLE估计→残差诊断(残差LB p>0.05)。陷阱: 不检验平稳→伪回归; 不检验残差→信息未提完; n<30→用指数平滑。',
     'context':'【ARMA/ARIMA定阶】ACF截+PACF拖=MA; ACF拖+PACF截=AR; 都拖=ARMA。建模六步: 平稳→差分→白噪声→定阶→估计→残差。statsmodels.tsa.arima.model.ARIMA。'},

    # ===== 图与网络 =====
    {'id':'图与网络-01','title':'最短路算法 Dijkstra/Floyd','category':'图与网络',
     'keywords':['Dijkstra','Floyd','最短路','Bellman-Ford','SPFA'],
     'search_text':'最短路算法: Dijkstra(贪心+松弛,非负权,O((n+m)logn)堆优化),单源首选; Floyd(DP,O(n^3)),全源n<=200; Bellman-Ford(含负权,O(nm)); SPFA(队列优化,最坏O(nm))。竞赛选型: 单源非负→Dijkstra; 全源小规模→Floyd。networkx.dijkstra_path。',
     'context':'【最短路】Dijkstra(非负权堆优化)、Floyd(全源DP)、Bellman-Ford(含负权)。竞赛首选Dijkstra。'},
    {'id':'图与网络-02','title':'最小生成树 Kruskal/Prim','category':'图与网络',
     'keywords':['MST','Kruskal','Prim','最小生成树','并查集'],
     'search_text':'最小生成树MST: Kruskal(边贪心+并查集,O(mlogm))适合稀疏图; Prim(点贪心+优先队列,O((n+m)logn))适合稠密图。应用: 最优布线/管网设计/聚类/近似TSP。networkx.minimum_spanning_tree。',
     'context':'【MST】Kruskal(边贪心,稀疏)、Prim(点贪心,稠密)。应用: 布线/管网/聚类。'},
    {'id':'图与网络-03','title':'网络流 最大流/最小费用流','category':'图与网络',
     'keywords':['网络流','最大流','最小割','Dinic','Ford-Fulkerson'],
     'search_text':'网络流: 最大流(Ford-Fulkerson/EK/Dinic), Dinic实际最快O(n^2 m)。最小费用最大流: SPFA/Dijkstra找费用最小增广路。最大流=最小割容量。建模模式: 源→左→右→汇(二分图匹配); 源→仓库→中转→需求→汇(运输调度)。networkx.maximum_flow。',
     'context':'【网络流】最大流(Dinic)、最小费用最大流、最大流=最小割。二分图建模: 源→左→右→汇。'},
    {'id':'图与网络-04','title':'TSP/VRP 旅行商与车辆路径','category':'图与网络',
     'keywords':['TSP','VRP','旅行商','车辆路径','2-opt','NP-hard'],
     'search_text':'TSP(NP-Hard): n<=20用DP(Held-Karp O(n^2 2^n)); n<=200用GA/SA/2-opt启发式。VRP: 多车+容量约束的TSP扩展; 先聚类→逐车TSP→2-opt。变种: VRPTW(时间窗)/CVRP(容量)/SDVRP(拆分)。中国邮递员CPP: 遍历所有边，欧拉回路+奇度点匹配。ortools库。',
     'context':'【TSP/VRP】NP-Hard。n<20用DP，n>20用GA/SA/2-opt。VRP=聚类+TSP。ortools。'},
    {'id':'图与网络-05','title':'匈牙利算法(二分图匹配)','category':'图与网络',
     'keywords':['匈牙利算法','二分图','匹配','指派问题','KM算法'],
     'search_text':'匈牙利算法: 求二分图最大匹配,O(nm)。增广路: DFS找→反转→匹配+1。KM算法: 带权最优匹配(指派问题),O(n^3)。通过调整顶点标号扩大相等子图。应用: 任务分配/人员匹配/资源调度。scipy.optimize.linear_sum_assignment。',
     'context':'【匈牙利算法】最大匹配O(nm)，KM最优匹配O(n^3)。scipy.optimize.linear_sum_assignment。'},

    # ===== 主成分/因子 =====
    {'id':'主成分与因子-01','title':'KMO与Bartlett球形检验','category':'主成分与因子',
     'keywords':['KMO','Bartlett','球形检验','因子分析','适用性'],
     'search_text':'因子分析前适用性检验: KMO>0.9非常适合/>0.8适合/>0.7一般/<0.5不适合; Bartlett球形检验H0=变量独立,p<0.05→有相关性→适合因子分析。竞赛论文必须报告KMO值和Bartlett检验结果。factor_analyzer.calculate_kmo。',
     'context':'【KMO+Bartlett】因子分析前必做。KMO>0.7合格，Bartlett p<0.05合格。竞赛必须报告。'},
]

with open('knowledge-chunks.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

existing_ids = {c['id'] for c in chunks}
added = 0
for c in new_chunks:
    if c['id'] not in existing_ids:
        chunks.append(c)
        added += 1

with open('knowledge-chunks.json', 'w', encoding='utf-8') as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

cats = sorted(set(c['category'] for c in chunks))
print(f'Chunks: {len(chunks)} (added {added})')
print(f'Categories: {cats}')
