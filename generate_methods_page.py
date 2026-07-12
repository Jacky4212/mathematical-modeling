"""生成 数学建模方法大全 HTML 页面 — 格式完全匹配现有网站"""
import json, os

# ============================================================
# 完整方法数据（74种，来自知识库 + PPT提取）
# ============================================================
METHODS = {
    "综合评价方法": {
        "icon": "📊", "intro": "综合评价方法用于对多个方案/对象在多个指标下进行综合排序或分级。核心流程为：指标构建→赋权→聚合排序。赋权分为主观赋权（AHP）、客观赋权（熵值法/CRITIC）和组合赋权三类。",
        "methods": [
            {"name":"层次分析法(AHP)","formula":"$AW=\\lambda_{max}W,\\ CR=CI/RI$",
             "principle":"通过Saaty 1-9标度法两两比较构造判断矩阵，求最大特征值对应特征向量为权重，CR<0.1通过一致性检验。",
             "scenarios":"多准则决策（选址、供应商评估）|需专家经验的定性+定量评价|与TOPSIS组合使用",
             "adv":"结构化，定性定量结合|层次清晰易理解|可检验一致性",
             "dis":"主观性强|指标多时判断矩阵易不一致"},
            {"name":"熵值法","formula":"$e_j=-\\frac{1}{\\ln m}\\sum p_{ij}\\ln p_{ij},\\ w_j=\\frac{1-e_j}{\\sum(1-e_j)}$",
             "principle":"基于Shannon信息熵客观赋权。指标变异越大→熵越小→权重越大。完全数据驱动。",
             "scenarios":"需完全客观赋权|与TOPSIS组合（熵值法赋权+TOPSIS排序）|指标独立的评价",
             "adv":"完全客观，消除主观偏差|计算简单|理论基础扎实",
             "dis":"忽视指标实际含义|不能反映指标间相关性|对零值敏感"},
            {"name":"TOPSIS优劣解距离法","formula":"$C_i=S_i^-/(S_i^++S_i^-)$",
             "principle":"最优方案距正理想解最近、距负理想解最远。计算各方案相对接近度排序。",
             "scenarios":"多方案多指标排名|与熵值法/AHP组合作为排序引擎|有明确指标方向的评价",
             "adv":"充分利用原始数据|几何意义直观|对样本量无要求",
             "dis":"权重需预先给定|受异常值影响|新增方案需重算"},
            {"name":"CRITIC权重法","formula":"$C_j=\\sigma_j\\cdot\\sum(1-|r_{jk}|),\\ w_j=C_j/\\sum C_j$",
             "principle":"同时考虑对比强度（标准差）和冲突性（1-相关性）。信息量=变异度×冲突性。惩罚冗余指标。",
             "scenarios":"指标间有相关性的场景|需惩罚冗余信息|学术论文",
             "adv":"同时考虑变异度和相关性|惩罚冗余指标",
             "dis":"只捕捉线性相关|样本少时相关系数不稳定"},
            {"name":"变异系数法","formula":"$w_j=v_j/\\sum v_k,\\ v_j=\\sigma_j/\\bar{y}_j$",
             "principle":"以变异系数(标准差/均值)衡量指标区分能力，CV越大权重越大。最简单的客观赋权法。",
             "scenarios":"快速初步评价|指标量纲差异大|纯客观无先验",
             "adv":"原理极简，计算最快|无需归一化|适合快速筛选",
             "dis":"只利用一阶和二阶信息|忽略指标间相关性|均值趋0时CV→∞"},
            {"name":"模糊综合评价","formula":"$B=A\\circ R,\\ Score=\\sum b_j\\cdot s_j$",
             "principle":"基于Zadeh模糊集，用[0,1]隶属度处理边界模糊的评价。五要素：因素集、评语集、权重、模糊矩阵、合成算子。",
             "scenarios":"定性+定量混合|满意度/风险评估|教学质量评价",
             "adv":"处理模糊边界|定性定量信息综合利用|结果信息丰富",
             "dis":"隶属函数选择主观|评语集划分影响结果|指标多时可能'淹没'"},
            {"name":"灰色关联分析(GRA)","formula":"$\\zeta_i(k)=\\frac{\\Delta_{min}+\\rho\\Delta_{max}}{\\Delta_{0i}+\\rho\\Delta_{max}},\\ \\gamma=\\frac{1}{n}\\sum\\zeta_i(k)$",
             "principle":"比较序列曲线几何相似度。Deng's GRA通过灰关联系数衡量各点差异，分辨系数ρ=0.5。",
             "scenarios":"小样本(n<10)评价|贫信息系统|多因素影响分析",
             "adv":"对数据量和分布无要求|计算量小|适合小样本",
             "dis":"ρ选取缺客观标准|不反映负相关|多因素时关联度趋近"},
            {"name":"数据包络分析(DEA)","formula":"$\\min\\theta\\ s.t.\\ \\sum\\lambda_j y_{rj}\\ge y_{rk},\\ \\sum\\lambda_j x_{ij}\\le\\theta x_{ik}$",
             "principle":"非参数LP方法，评价多投入多产出DMU相对效率。CCR(CRS)+BCC(VRS)，TE=PTE×SE。",
             "scenarios":"银行/医院/学校效率评价|标杆分析|资源优化配置",
             "adv":"无需预设生产函数|多投入多产出同时处理|提供改进方向",
             "dis":"DMU≥2×(投入+产出)|对异常值敏感|无法处理负值"},
            {"name":"秩和比法(RSR)","formula":"$RSR_i=\\sum_j R_{ij}/(m\\cdot n),\\ RSR=a+b\\cdot Probit$",
             "principle":"秩转换→RSR统计量→Probit回归→排序分档。非参数方法，对离群值不敏感。",
             "scenarios":"多指标综合评价|分类鉴别(优/中/差)|含离群值数据",
             "adv":"对离群值不敏感|可同时排序分档|非参数，不依赖分布",
             "dis":"秩替代损失信息|需正态检验|分档阈值主观"},
            {"name":"耦合协调度模型","formula":"$D=\\sqrt{C\\times T},\\ C_n=[\\frac{\\prod U_i}{(\\frac{1}{n}\\sum U_i)^n}]^{1/n}$",
             "principle":"量化子系统间相互作用强度(C)和发展协调水平(T)。D=√(C×T)衡量协调发展。注意C值虚高问题。",
             "scenarios":"经济-社会-环境三元评价|产业融合分析|时空演化",
             "adv":"同时衡量耦合和协调|可用于时空演化|框架完整",
             "dis":"C值低水平'虚高'|权重α主观|对归一化敏感"},
            {"name":"解释结构模型(ISM)","formula":"$R=(A+I)^k,\\ R(i)\\cap A(i)=R(i)$",
             "principle":"邻接矩阵→可达矩阵(Boolean)→层级划分(迭代剥离)→MICMAC分析(驱动力vs依赖性)。",
             "scenarios":"事故致因分析|供应链风险层级|安全管理",
             "adv":"定性→定量→可视化|不需大量数据|层次清晰",
             "dis":"依赖主观判断|二元关系粗糙(0/1)|无法表达强度"},
            {"name":"主成分分析(PCA)","formula":"$S\\cdot v_k=\\lambda_k v_k,\\ Score_i=\\sum\\eta_k F_{ik}$",
             "principle":"协方差矩阵特征分解→方差最大化投影方向→累计贡献率≥80%选主成分→方差贡献率加权综合得分。",
             "scenarios":"多指标综合评价|高维可视化|消除共线性|p>n降维",
             "adv":"客观赋权|消除共线性|降维可视化",
             "dis":"只保留线性结构|主成分意义难解释|对异常值敏感"},
        ]
    },
    "预测方法": {
        "icon": "🔮", "intro": "预测方法用于基于历史数据推断未来趋势。按数据特征可分为：小样本灰色预测、平稳时序ARIMA、季节时序SARIMA、波动率GARCH、多变量VAR、非线性ML集成、S曲线Logistic等。",
        "methods": [
            {"name":"灰色预测GM(1,1)","formula":"$\\hat{x}^{(1)}(k+1)=[x^{(0)}(1)-b/a]e^{-ak}+b/a$",
             "principle":"1-AGO累加生成消除随机波动→一阶白化微分方程→最小二乘估计→累减还原。需级比检验。",
             "scenarios":"小样本(4-10点)|近似指数增长(GDP/电力)|中短期预测",
             "adv":"样本需求极小(4点即可)|不需概率分布假设|计算简单",
             "dis":"只适合指数增长|对转折点无能为力|长期精度急剧下降"},
            {"name":"ARIMA(p,d,q)","formula":"$y_t=c+\\phi_1 y_{t-1}+\\cdots+\\phi_p y_{t-p}+\\varepsilon_t+\\theta_1\\varepsilon_{t-1}+\\cdots$",
             "principle":"AR(p)+I(d)+MA(q)。差分→平稳，ACF/PACF定阶，AIC/BIC选优，Ljung-Box白噪声检验。",
             "scenarios":"平稳/可差分平稳的单变量时序|经济指标|销售预测",
             "adv":"理论基础坚实|提供预测区间|可解释性强",
             "dis":"无法捕捉非线性|多步预测误差累积快|定阶主观"},
            {"name":"SARIMA(P,D,Q,s)","formula":"$\\Phi_P(B^s)\\phi_p(B)(1-B)^d(1-B^s)^D y_t=\\Theta_Q(B^s)\\theta_q(B)\\varepsilon_t$",
             "principle":"ARIMA+季节性成分(P,D,Q,s)。同时捕捉趋势和周期波动。需3-4完整季节周期。",
             "scenarios":"有明显季节性的时序|电力负荷|零售销售|旅游客流",
             "adv":"能捕捉季节性|统计性质明确|自动搜索可用",
             "dis":"参数多(7个)|需≥3完整季节周期|P+Q过大易过拟合"},
            {"name":"GARCH(p,q)","formula":"$\\sigma^2_t=\\omega+\\alpha\\varepsilon^2_{t-1}+\\beta\\sigma^2_{t-1}$",
             "principle":"方差建模为过去残差²+过去方差自身。GARCH(1,1)最常用。α+β→1=波动持续。可扩展EGARCH(杠杆效应)。",
             "scenarios":"金融收益率波动率|VaR风险度量|期权定价",
             "adv":"捕捉波动聚集和尖峰厚尾|GARCH(1,1)简洁有效",
             "dis":"对称处理正负冲击|无法解释波动来源|多步预测→无条件方差"},
            {"name":"VAR向量自回归","formula":"$Y_t=c+\\Pi_1 Y_{t-1}+\\cdots+\\Pi_p Y_{t-p}+\\varepsilon_t$",
             "principle":"多变量AR系统，不预设内生/外生。配套：Granger因果检验、IRF脉冲响应、FEVD方差分解。",
             "scenarios":"多变量互影响系统|宏观经济分析|货币政策传导",
             "adv":"不预设内生/外生|丰富分析工具(IRF/FEVD)|优于单变量",
             "dis":"参数多(k²p个)维度诅咒|IRF依赖变量排序|需全平稳或协整"},
            {"name":"马尔可夫预测","formula":"$P_{ij}=P(X_{n+1}=j|X_n=i),\\ P^{(n)}=P^n,\\ \\pi P=\\pi$",
             "principle":"下一状态仅依赖当前状态。转移概率矩阵P→n步转移→稳态分布π。无记忆性假设。",
             "scenarios":"天气/信用预测|市场占有率|用户行为转换|排队系统",
             "adv":"简单直观|矩阵运算高效|稳态分析洞察长期",
             "dis":"无记忆假设常违反|状态划分主观|无法处理连续变量"},
            {"name":"Logistic模型(S曲线)","formula":"$P(t)=\\frac{KP_0 e^{rt}}{K+P_0(e^{rt}-1)},\\ dP/dt=rP(1-P/K)$",
             "principle":"Verhulst方程→有限资源S形增长。三参数：K(容量)、r(增长率)、P0(初值)。拐点P=K/2。",
             "scenarios":"人口增长|传染病累计感染|市场渗透率|技术S曲线",
             "adv":"有生物学/经济学理论基础|参数含义直观|仅3参数",
             "dis":"对称假设(实际常不对称)|无法解释多波|拐点固定"},
            {"name":"双重差分(DID)","formula":"$ATT=(\\bar{Y}_{T,Post}-\\bar{Y}_{T,Pre})-(\\bar{Y}_{C,Post}-\\bar{Y}_{C,Pre})$",
             "principle":"处理组vs对照组在政策前后差分→因果效应δ。核心假设：平行趋势。需事件研究+安慰剂检验。",
             "scenarios":"政策效果评估|自然实验|有处理/对照组面板数据",
             "adv":"概念直观|控制固定差异和共同趋势|回归框架简洁",
             "dis":"平行趋势不可直接检验|对对照组质量依赖|无法处理时变混淆"},
            {"name":"PSM倾向得分匹配","formula":"$e(X)=P(T=1|X),\\ ATT=E[Y(1)-Y(0)|T=1,e(X)]$",
             "principle":"为处理组找倾向得分最近的对照组'替身'。Logit/Probit估计→最近邻/卡尺/核匹配→ATT→平衡性检验。",
             "scenarios":"非随机分配的政策评估|医学治疗效果|营销归因",
             "adv":"不依赖函数形式|平衡性检验可验证|概念直观",
             "dis":"只控制可观测混淆|倾向得分模型误设敏感|匹配过程主观"},
            {"name":"BP神经网络预测","formula":"$h=\\sigma(W_1 x+b_1),\\ \\hat{y}=W_2 h+b_2$",
             "principle":"万能逼近定理→单隐藏层+Sigmoid→反向传播+链式法则→权重更新。ReLU/Dropout/EarlyStopping防过拟合。",
             "scenarios":"非线性复杂预测|多输入多输出|模式识别",
             "adv":"非线性万能逼近|处理复杂多变量|框架灵活",
             "dis":"需大量数据|可解释性极差(黑箱)|超参数多|小样本过拟合"},
            {"name":"集成学习(XGBoost/LightGBM/CatBoost/RF)","formula":"$\\hat{y}_{RF}=\\frac{1}{B}\\sum T_b(x),\\ \\hat{y}_{GB}=\\sum\\eta f_m(x)$",
             "principle":"RF(Bagging):并行多树→投票/均值。XGBoost/LGB/CatBoost(Boosting):串行拟合残差+正则化。表格数据瑞士军刀。",
             "scenarios":"结构化表格数据—通用|大数据(>10万→LGB)|多类别特征(→CatBoost)|快速基线(→RF)",
             "adv":"精度极高(Boosting)|自动处理缺失/类别|抗过拟合|特征重要性",
             "dis":"可解释弱于统计模型|LGB小样本过拟合|XGB调参复杂"},
            {"name":"Holt双参数指数平滑","formula":"$F_{t+m}=S_t+m\\cdot b_t,\\ S_t=\\alpha Y_t+(1-\\alpha)(S_{t-1}+b_{t-1})$",
             "principle":"在简单指数平滑基础上增加趋势分量bt递归更新。双参数(α,γ)分别控制水平和趋势平滑。解决有趋势序列预测滞后问题。",
             "scenarios":"含常数增减趋势的时序|产量/销量递增递减|ARIMA的轻量替代",
             "adv":"简单直观|双参数灵活|解决趋势序列预测滞后",
             "dis":"无季节成分|对突变敏感|不能自动选择参数"},
        ]
    },
    "优化与规划方法": {
        "icon": "🎯", "intro": "优化方法用于在约束条件下寻找最优决策方案。从线性规划到智能优化，涵盖了确定性优化（LP/NLP/DP）和启发式优化（GA/PSO/SA/ACO）两大类。知识库推荐决策路径：线性→单纯形法；整数→分支定界；多阶段→DP；复杂非线性→GA/PSO/SA。",
        "methods": [
            {"name":"线性规划(LP)","formula":"$\\min c^T x\\ s.t.\\ Ax\\le b,\\ x\\ge 0$",
             "principle":"目标函数和约束均为线性的优化问题。单纯形法在顶点间迭代，内点法穿越内部。对偶理论提供影子价格。",
             "scenarios":"资源分配|生产计划|运输问题|投资组合",
             "adv":"求解极高效(万级变量秒解)|理论完整(对偶/灵敏度)|全局最优保证",
             "dis":"只能处理线性关系|连续变量假设|现实问题常非线性"},
            {"name":"整数规划(IP/MIP)","formula":"$\\min c^T x\\ s.t.\\ Ax\\le b,\\ x_i\\in\\mathbb{Z}$",
             "principle":"变量含整数约束。分支定界法：LP松弛→分支→剪枝。0-1规划(BinPacking/背包/KP)。",
             "scenarios":"选址|排班|背包问题|设施布局|物流配送(VRP)",
             "adv":"可建模离散决策|分支定界保证最优|Branch-and-Cut高效",
             "dis":"NP-hard(大规模极慢)|分支策略影响效率|MIP gap可能很大"},
            {"name":"非线性规划(NLP)","formula":"$\\min f(x)\\ s.t.\\ g_i(x)\\le 0,\\ h_j(x)=0$",
             "principle":"目标/约束含非线性。SQP(序列二次规划)最通用。KKT条件是一阶必要条件。凸规划保证全局最优。",
             "scenarios":"参数估计|最优控制|工程设计|化学反应优化",
             "adv":"建模能力强|SQP/SLSP/IPOPT成熟|凸问题全局最优",
             "dis":"非凸→局部最优陷阱|需梯度信息|初始点敏感"},
            {"name":"动态规划(DP)","formula":"$V(s)=\\max_a\\{R(s,a)+\\gamma\\sum P(s'|s,a)V(s')\\}$",
             "principle":"多阶段决策的最优子结构：问题分解为子问题，状态转移+Bellman最优方程。记忆化搜索避免重复计算。",
             "scenarios":"最短路径|背包问题|资源分配|序列决策|库存管理",
             "adv":"保证全局最优|避免重复计算|理论最优子结构清晰",
             "dis":"维度诅咒(状态×动作组合爆炸)|需精确状态定义|连续状态需离散化"},
            {"name":"多目标优化(NSGA-II/Pareto)","formula":"$\\min\\{f_1(x),f_2(x),...,f_k(x)\\}$",
             "principle":"Pareto最优：无法在不损害其他目标下改进任一目标。NSGA-II：非支配排序+拥挤距离+精英保留。",
             "scenarios":"成本vs质量|风险vs收益|环保vs经济|多目标决策",
             "adv":"承认目标冲突现实|Pareto前沿提供决策信息|NSGA-II成熟高效",
             "dis":"前沿可视化困难(k>3)|权重法依赖先验|Pareto解集可能很大"},
            {"name":"图论与网络优化","formula":"$d[v]=\\min(d[v],d[u]+w(u,v))$（Dijkstra）",
             "principle":"涵盖Dijkstra(最短路径)、Bellman-Ford(负权)、Floyd-Warshall(全源)、Ford-Fulkerson(最大流)、Prim/Kruskal(MST)。",
             "scenarios":"路径规划|网络流分配|通信网络|物流配送|社交网络",
             "adv":"算法成熟效率高|NetworkX库实现完善|可视化直观",
             "dis":"大规模图效率下降|动态图算法复杂|NP-hard变体多(TSP)"},
            {"name":"遗传算法(GA)","formula":"$P(new)=select\\circ crossover\\circ mutate(P)$",
             "principle":"模拟自然选择。编码→选择(锦标赛/轮盘赌)→交叉(SBX/单点)→变异(多项式/位翻转)→精英保留。",
             "scenarios":"复杂非线性不可导|组合优化|多目标优化|参数调优",
             "adv":"全局搜索|不依赖梯度|并行化容易|适应任意目标函数",
             "dis":"收敛慢|早熟收敛|参数(交叉率/变异率)敏感|理论上弱"},
            {"name":"粒子群优化(PSO)","formula":"$v_i^{k+1}=w v_i^k+c_1 r_1(pbest_i-x_i^k)+c_2 r_2(gbest-x_i^k)$",
             "principle":"模拟鸟群觅食。粒子速度=惯性+个体认知+社会学习。w线性衰减(0.9→0.4)。适合连续空间优化。",
             "scenarios":"连续参数优化|神经网络训练|工程设计|天线阵列",
             "adv":"收敛快|参数少|连续空间高效|实现简单",
             "dis":"早熟收敛(全局模型)|参数敏感|离散版性能差|理论上弱"},
            {"name":"模拟退火(SA)","formula":"$P(accept)=\\min(1,\\exp(\\Delta E/T))$",
             "principle":"模拟金属退火。高温→接受劣解概率高(探索)；低温→趋近贪心(收敛)。T_k=α·T_{k-1}指数冷却。",
             "scenarios":"组合优化|VLSI布局|TSP问题|局部精修(polish)",
             "adv":"可跳出局部最优|理论收敛到全局最优|实现极简(~10行)",
             "dis":"冷却策略敏感|调参困难|收敛速度慢|连续域效率低"},
            {"name":"蚁群优化(ACO)","formula":"$p_{ij}^k=\\frac{[\\tau_{ij}]^\\alpha[\\eta_{ij}]^\\beta}{\\sum[\\tau_{il}]^\\alpha[\\eta_{il}]^\\beta}$",
             "principle":"模拟蚁群觅食。信息素τ沉积+挥发，启发式信息η引导。正反馈强化好路径。适合组合优化(路径/分配)。",
             "scenarios":"TSP最短路径|车辆路径VRP|任务分配|网络路由",
             "adv":"正反馈自组织|分布式并行|组合优化优秀|可结合局部搜索",
             "dis":"不适合连续优化(用PSO/GA)|收敛分析困难|参数多(α,β,ρ,Q)"},
            {"name":"混合整数线性规划(MILP)","formula":"$\\min c^T x+d^T y\\ s.t.\\ Ax+By\\le b,\\ x\\in\\mathbb{Z},\\ y\\in\\mathbb{R}$",
             "principle":"LP+整数变量。分支定界+割平面+启发式。Gurobi/CPLEX是最强求解器。学术可用SCIP/PuLP。",
             "scenarios":"设施选址+分配|生产排程|能源调度|供应链优化",
             "adv":"建模表达力强|求解器成熟高效|可求最优性gap",
             "dis":"大规模NP-hard|整数变量多→极慢|商业求解器昂贵"},
            {"name":"蒙特卡洛优化","formula":"$\\hat{\\theta}=\\arg\\min_{\\theta}\\frac{1}{N}\\sum_{i=1}^N f(x_i;\\theta)$",
             "principle":"随机采样+统计估计在决策空间搜索最优解。与MC积分的区别：目标是优化而非估计。适合黑箱优化。",
             "scenarios":"黑箱函数优化|仿真优化|参数调优|可行域极窄的优化",
             "adv":"不需梯度|适应任意目标|实现简单|维度无关",
             "dis":"收敛慢O(1/√N)|高维效率低|随机性导致结果不稳定"},
        ]
    },
    "统计分析与机器学习": {
        "icon": "🤖", "intro": "从经典统计推断到现代机器学习的完整谱系。涵盖假设检验、回归分析(OLS/Ridge/Lasso/Logistic)、聚类(K-Means/DBSCAN/分层)、分类(RF/SVM/KNN/NB)、降维(PCA/FA)和问卷分析。方法论核心：特征工程→多模型对比→交叉验证→可解释性。",
        "methods": [
            {"name":"OLS线性回归","formula":"$\\hat{\\beta}=(X^TX)^{-1}X^T y,\\ R^2=1-SS_{res}/SS_{tot}$",
             "principle":"最小化残差平方和，闭式解。五大经典假设：线性、严格外生、无完全多重共线(VIF<10)、球面误差(同方差+无自相关)、正态性。",
             "scenarios":"线性关系预测|因果推断(控制变量)|基准模型baseline",
             "adv":"可解释性最强|闭式解快速|统计推断完善(t/F检验)",
             "dis":"只捕捉线性关系|对异常值和共线性敏感|严格假设常不满足"},
            {"name":"Ridge回归(L2)","formula":"$\\hat{\\beta}=(X^TX+\\lambda I)^{-1}X^T y$",
             "principle":"L2正则化惩罚系数平方和。所有系数收缩但不归零。λ通过交叉验证选。解决多重共线性。",
             "scenarios":"多重共线性严重|p接近n|需保留所有特征|预测导向",
             "adv":"解决共线性|保留所有特征|闭式解稳定",
             "dis":"无法特征选择|λ选择需CV|系数全非零→模型不稀疏"},
            {"name":"Lasso回归(L1)","formula":"$\\hat{\\beta}=\\arg\\min\\{\\|y-X\\beta\\|^2+\\lambda\\sum|\\beta_j|\\}$",
             "principle":"L1正则化→某些系数精确归零→自动特征选择。λ越大越稀疏。LARS算法高效求解。",
             "scenarios":"高维特征选择(p>>n)|需稀疏模型|可解释性重要",
             "adv":"自动特征选择(稀疏解)|降维+预测一步完成|可解释",
             "dis":"共线性→随机选一个|λ选择需CV|预测精度可能不如Ridge"},
            {"name":"Logistic回归","formula":"$P(y=1|x)=1/(1+e^{-(\\beta_0+\\beta^Tx)}),\\ AUC$评估",
             "principle":"Sigmoid函数→[0,1]概率输出。极大似然估计(梯度下降/Newton-Raphson)。决策边界=线性超平面。AUC评估判别力。",
             "scenarios":"二分类预测|信用评分|医学诊断|流失预测",
             "adv":"输出概率(非硬分类)|可解释|统计推断完善(OR)",
             "dis":"线性决策边界|需特征工程|对类别不平衡敏感"},
            {"name":"K-Means聚类","formula":"$\\min\\sum_{k=1}^K\\sum_{x\\in C_k}\\|x-\\mu_k\\|^2$",
             "principle":"最小化簇内平方和(WCSS)。Lloyd算法：初始化→分配→更新→迭代。肘部法则+轮廓系数确定K。",
             "scenarios":"客户分群|图像分割|异常检测|球形簇数据",
             "adv":"简单快速O(nKId)|可扩展( MiniBatch K-Means)|几何直观",
             "dis":"需预知K|假设球形簇(各向同性)|对初始化和异常值敏感"},
            {"name":"DBSCAN密度聚类","formula":"$N_\\varepsilon(p)=\\{q|dist(p,q)\\le\\varepsilon\\},\\ |N|\\ge minPts$",
             "principle":"密度直达→密度可达→密度相连。核心点(ε邻域≥minPts)、边界点、噪声点。自动发现任意形状簇。",
             "scenarios":"任意形状簇|含噪声数据|地理/空间数据|异常检测",
             "adv":"不需预知簇数|发现任意形状|天然抗噪声",
             "dis":"密度差异大→参数难选|高维性能差(维度诅咒)|ε/minPts敏感"},
            {"name":"分层聚类","formula":"$d(A,B)=\\min_{a\\in A,b\\in B}d(a,b)$（single-linkage）",
             "principle":"自底向上(Agglomerative)或自顶向下(Divisive)。Linkage：single/complete/average/Ward树状图可视化。",
             "scenarios":"需要层次结构(分类树)|中等规模数据|基因序列分析",
             "adv":"树状图直观|不预设簇数|各类linkage灵活",
             "dis":"O(n³)→大规模慢|一旦合并不可撤销|linkage选择影响结果"},
            {"name":"决策树","formula":"$Gini=1-\\sum p_k^2,\\ Entropy=-\\sum p_k\\log p_k$",
             "principle":"递归二分特征空间。CART(Gini)+C4.5(信息增益比)。剪枝防过拟合。白箱模型可解释。",
             "scenarios":"需可解释分类/回归|特征重要性排序|规则提取",
             "adv":"可解释(白箱)|不需特征缩放|自动处理非线性|缺失值容忍",
             "dis":"易过拟合(需剪枝)|不稳定(数据微小变化→树大变)|偏向多值特征"},
            {"name":"随机森林(RF)","formula":"$\\hat{y}=\\frac{1}{B}\\sum_{b=1}^B T_b(x),\\ OOB\\ error$估计泛化",
             "principle":"Bagging+随机子空间。Bootstrap采样(≈63%进入训练)→多棵树独立训练→投票/均值。OOB误差≈CV。",
             "scenarios":"分类/回归通用|特征重要性|高维数据|需要稳健baseline",
             "adv":"抗过拟合|不需特征缩放|OOB误差内置验证|可并行",
             "dis":"可解释弱于单棵树|高维稀疏→效果差|比Boosting精度低"},
            {"name":"SVM支持向量机","formula":"$\\min\\frac{1}{2}\\|w\\|^2+C\\sum\\xi_i,\\ K(x,z)=\\phi(x)^T\\phi(z)$",
             "principle":"最大化间隔→凸二次规划。软间隔(C控制)。核技巧(Kernel Trick)：RBF/多项式/Sigmoid→隐式高维映射。",
             "scenarios":"高维数据|小样本|文本分类|图像识别",
             "adv":"高维表现好|核技巧处理非线性|凸优化→全局最优",
             "dis":"大数据O(n²~n³)慢|核函数选择主观|概率输出需额外校准"},
            {"name":"KNN最近邻","formula":"$\\hat{y}=mode\\{y_i|x_i\\in N_k(x)\\}$",
             "principle":"惰性学习：无训练阶段，预测时找k个最近邻居投票/均值。距离度量(欧氏/曼哈顿/余弦)。k通过CV选。",
             "scenarios":"小数据集快速原型|推荐系统(collaborative filtering)|多分类",
             "adv":"简单直观|无训练时间|非线性决策边界天然|新增数据不需重训",
             "dis":"预测慢(需扫描全训练集)|维度诅咒(高维距离失效)|存储全训练集"},
            {"name":"朴素贝叶斯","formula":"$P(C_k|x)\\propto P(C_k)\\prod P(x_i|C_k)$",
             "principle":"Bayes定理+特征条件独立假设(朴素)。Gaussian NB(连续)/Multinomial NB(文本计数)/Bernoulli NB(二元)。",
             "scenarios":"文本分类(垃圾邮件)|实时预测|基准模型|特征独立假设近似成立",
             "adv":"极快(训练+预测)|小数据有效|概率输出|增量学习",
             "dis":"'朴素'假设常不成立|零概率问题(需Laplace平滑)|连续特征需分布假设"},
            {"name":"因子分析(FA)","formula":"$X=\\mu+\\Lambda F+\\varepsilon,\\ \\Lambda$为载荷矩阵",
             "principle":"假设存在不可观测的公共因子F驱动观测变量X。Varimax旋转使因子可解释。KMO>0.5+Bartlett Sig<0.05适用。",
             "scenarios":"潜在构念挖掘|问卷效度验证|综合评价(PCA替代)|特征工程(因子得分)",
             "adv":"因子可命名(业务解释)|不改变共同度|因子得分可用作新变量",
             "dis":"需KMO/Bartlett适用性检验|因子数确定主观|旋转方法选择影响结果"},
        ]
    },
    "插值与拟合": {
        "icon": "📈", "intro": "插值与拟合是数据处理的两大基本工具。插值要求曲线严格通过所有已知点；拟合追求整体误差最小，允许不通过任何已知点。拉格朗日插值、三次样条插值为经典插值方法；多项式最小二乘和非线性自定义函数拟合为常用拟合方法。",
        "methods": [
            {"name":"拉格朗日插值","formula":"$P_n(x)=\\sum_{i=0}^n y_i L_i(x),\\ L_i(x)=\\prod_{j\\neq i}\\frac{x-x_j}{x_i-x_j}$",
             "principle":"n次多项式唯一通过n+1个点。Lagrange基函数Li(xj)=δij(Kronecker δ)。高次→Runge现象(边缘震荡)，实际推荐≤5次。",
             "scenarios":"已知离散点求中间值|数据缺失填充|函数表查询|二维网格插值",
             "adv":"理论优美|严格通过所有已知点|公式简洁",
             "dis":"高次Runge现象|新增点需重算全部基函数|等距节点→边缘震荡严重"},
            {"name":"三次样条插值","formula":"$S_i(x)=a_i+b_i(x-x_i)+c_i(x-x_i)^2+d_i(x-x_i)^3$",
             "principle":"分段三次多项式，节点处二阶连续可导(C²光滑)。自然边界S''=0。MATLAB: interp1(...,'spline')。",
             "scenarios":"光滑曲线插值(推荐首选)|CAD/CAM曲面|动画关键帧",
             "adv":"光滑(C²连续)|避免Runge现象|MATLAB一行搞定",
             "dis":"计算量大于分段线性|端点处理需边界条件|非单调数据可能过冲"},
            {"name":"多项式最小二乘拟合","formula":"$\\min_\\theta\\sum(y_i-f(x_i;\\theta))^2,\\ \\theta=(X^TX)^{-1}X^Ty$",
             "principle":"m次多项式逼近数据→OLS闭式解→R²评估拟合优度。m通过交叉验证选。可加Ridge(L2)/Lasso(L1)正则化。",
             "scenarios":"数据呈曲线趋势|短期外推|基线对比|实验数据平滑",
             "adv":"理论简单计算快速|闭式解|Ridge/Lasso正则化",
             "dis":"高阶过拟合|外推差|无法捕捉周期和突变"},
            {"name":"非线性最小二乘拟合","formula":"$\\min_\\theta\\sum[y_i-f(x_i;\\theta)]^2$",
             "principle":"已知函数形式(指数/对数/幂函数等)但参数未知→迭代优化求解。MATLAB: lsqcurvefit/lsqnonlin/nlinfit。需合理初值。",
             "scenarios":"物理/化学模型参数标定|S曲线/指数衰减拟合|自定义函数拟合",
             "adv":"可拟合任意函数形式|MATLAB工具箱成熟|统计诊断丰富",
             "dis":"需合理初值→否则局部最优|迭代收敛不稳定|对噪声敏感"},
        ]
    },
    "图与网络优化": {
        "icon": "🕸️", "intro": "图论是离散优化的核心工具，用节点和边建模关系网络。涵盖最短路径、网络流、匹配和遍历四大经典问题。竞赛中常用于路径规划、物流配送和网络设计。MATLAB有graph/digraph对象，Python推荐NetworkX库。",
        "methods": [
            {"name":"Dijkstra最短路径","formula":"$d[v]=\\min(d[v],d[u]+w(u,v)),\\ w\\ge 0$",
             "principle":"贪心+BFS→优先队列(O((V+E)logV))。仅非负权。从源点逐步扩展最短路径树。",
             "scenarios":"GPS导航|网络路由|物流最短路径|地图规划",
             "adv":"非负权最优O(ElogV)|实现简单|单源→全目标一次",
             "dis":"不能处理负权(用Bellman-Ford)|大规模图空间占用大|动态图需重算"},
            {"name":"Floyd-Warshall全源最短路径","formula":"$d[i][j]=\\min(d[i][j],d[i][k]+d[k][j])$",
             "principle":"三重循环DP→任意两点最短路径。O(V³)。可检测负环(d[i][i]<0)。",
             "scenarios":"任意两点最短距离|小图(V≤500)|负权(无负环)|传递闭包",
             "adv":"全源一次求出|实现极简(5行)|负权支持|传递闭包可用",
             "dis":"O(V³)→大图极慢|空间O(V²)|Dijkstra运行V次更优"},
            {"name":"Ford-Fulkerson最大流","formula":"$\\sum f(s,v)=\\sum f(v,t),\\ 0\\le f(e)\\le c(e)$",
             "principle":"增广路+残余网络→DFS/BFS找增广路→增加流量。Edmonds-Karp(BFS版)为O(VE²)。最大流=最小割。",
             "scenarios":"网络带宽分配|二分图匹配|运输调度|项目选择",
             "adv":"理论优美(最大流=最小割)|Edmonds-Karp多项式|Dinic高效",
             "dis":"浮点权可能不终止|增广路顺序影响效率|大规模→Dinic必需"},
            {"name":"最小生成树(MST)","formula":"$MST\\in\\arg\\min_{T\\subseteq G}\\sum_{e\\in T}w(e),\\ |T|=V-1$",
             "principle":"Prim(稠密图O(V²))：从一个点出发逐步加最小权边。Kruskal(稀疏图O(ElogE))：边排序+并查集防环。",
             "scenarios":"网络布线|电路设计|聚类(Single-linkage)|最小成本连通",
             "adv":"Prim/Kruskal高效|并查集实现优雅|MST唯一性易判",
             "dis":"不能有负环|动态图需重新计算|约束MST→NP-hard"},
        ]
    },
    "竞赛方法论": {
        "icon": "🏆", "intro": "数学建模竞赛不仅需要模型知识，还需要系统性方法论。本章涵盖AI工具使用策略、模型组合拳、论文撰写规范和竞赛时间管理，帮助参赛者高效组织建模过程并产出高质量论文。",
        "methods": [
            {"name":"四阶段AI提示词框架","formula":"$Prompt=Identity+Task+Format+Constraint$",
             "principle":"将AI工具嵌入数学建模全流程：①赛题结构化分析→思维导图 ②模型构建→五维评估(原理/场景/创新/局限/流程) ③数据全自动获取→可复用代码 ④模型求解→有效性/鲁棒性/对比验证。核心原则：AI是协作者而非代笔。",
             "scenarios":"2025+竞赛AI新规下合规使用AI|快速获取建模灵感|代码生成与调试|论文润色",
             "adv":"系统性降低认知负荷|多工具协同(ChatGPT/DeepSeek/豆包)|创新三选一(算法改进/跨域迁移/多模型融合)",
             "dis":"AI输出需人工验证|不可盲目照搬|核心建模必须独立完成|竞赛合规要求标注AI使用"},
            {"name":"\"组合拳\"建模策略","formula":"$Baseline(统计模型)\\to Optimized(ML模型)\\to Compare(可视化)$",
             "principle":"传统模型做baseline基准→神经网络/ML优化→量化对比(RMSE/准确率/AUC)→可视化论证(Loss曲线+对比图)。论文核心叙事：'为何需复杂模型→如何改进→改进了多少'。",
             "scenarios":"需要体现模型优越性的论文|评审期望看到方法对比|任何可同时用传统+ML的预测/分类题",
             "adv":"论文叙事逻辑强|量化比较有说服力|评审喜欢baseline vs improved范式",
             "dis":"增加工作量|对编程能力要求高|不适合纯机理分析题"},
        ]
    },
}

# 对比表（相近方法）
COMPARISONS = [
    {"title":"PCA vs 因子分析(FA)", "headers":["维度","PCA","因子分析(FA)"],
     "rows":[["目标","降维，最大化方差","挖掘潜在公共因子"],
             ["数学模型","$X=PY$($P$正交)","$X=\\mu+\\Lambda F+\\varepsilon$"],
             ["方差解释","解释观测变量的总方差","仅解释公共方差(不含特殊方差)"],
             ["因子可解释性","差(主成分=变量线性组合)","好(旋转后因子可命名)"],
             ["适用性检验","KMO+Bartlett","KMO+Bartlett"],
             ["下游应用","降维+综合评价","潜在构念+因子得分+综合评价"]]},
    {"title":"Ridge(L2) vs Lasso(L1)", "headers":["维度","Ridge(L2)","Lasso(L1)"],
     "rows":[["惩罚项","$\\lambda\\sum\\beta_j^2$","$\\lambda\\sum|\\beta_j|$"],
             ["系数行为","收缩但不归零","部分精确归零→稀疏解"],
             ["特征选择","✗(保留全部特征)","✓(自动特征选择)"],
             ["共线性处理","均匀收缩相关变量系数","随机选一个→不稳定"],
             ["适用场景","预测导向/共线性严重","特征选择/p>>n/可解释性"]]},
    {"title":"K-Means vs DBSCAN vs 分层聚类", "headers":["维度","K-Means","DBSCAN","分层聚类"],
     "rows":[["簇形状","球形","任意形状","取决于linkage"],
             ["需预设K?","是(肘部法则辅助)","否(ε+minPts决定)","否(树状图截断)"],
             ["噪声处理","所有点强制归类","天然抗噪声(标注为-1)","所有点最终合并"],
             ["时间复杂度","O(nKId)","O(n log n)(空间索引)","O(n³)"],
             ["适用场景","球形簇/已知K","含噪声/任意形状","需层次结构/树状图"]]},
    {"title":"PSO vs GA vs SA vs DE", "headers":["维度","PSO","GA","SA","DE"],
     "rows":[["搜索机制","群体+速度更新","群体+交叉变异","单点+温度退火","群体+差分向量"],
             ["适合空间","连续","连续+离散","离散+连续","连续(稀疏可行域)"],
             ["收敛速度","快","中","慢","中"],
             ["参数敏感度","中(w,c1,c2)","高(cr,mr,pop)","高(T0,α)","低"],
             ["冷启动","难(需命中可行区)","难","中","好(差分向量探索强)"],
             ["知识库编号","#9","#7","#8","#8(DE)"]]},
    {"title":"ARIMA vs GARCH vs GM(1,1)", "headers":["维度","ARIMA","GARCH","GM(1,1)"],
     "rows":[["建模对象","均值(水平)","方差(波动率)","累加序列(趋势)"],
             ["数据需求","≥50点","≥100点(金融)","≥4点(极少!)"],
             ["季节处理","SARIMA扩展","不适用","不适用"],
             ["预测区间","有(基于正态假设)","有","无(点预测)"],
             ["适用场景","平稳/可差分平稳","金融波动率","小样本指数型"]]},
]

# ============================================================
# HTML 生成（格式完全匹配现有网站）
# ============================================================
def gen_html():
    sections_html = ""
    nav_items = ""
    chap_nav = ""
    sec_num = 0

    for cat_name, cat_data in METHODS.items():
        sec_num += 1
        sec_id = f"sec{sec_num}"
        icon = cat_data["icon"]

        # 侧栏导航 + 章内导航
        nav_items += f'<div class="group-label">{icon} {cat_name}</div>\n'
        chap_nav += f'<div class="nav-section">{cat_name}</div>\n'

        # 章节内容
        sections_html += f'\n<div class="section" id="{sec_id}">\n'
        sections_html += f'<h2>{icon} {cat_name}</h2>\n'
        sections_html += f'<p>{cat_data["intro"]}</p>\n'

        for m in cat_data["methods"]:
            m_id = m["name"].replace(" ", "_").replace("(","").replace(")","").replace("/","_")[:30]
            nav_items += f'<a href="#{m_id}" style="padding-left:28px;font-size:.82em">{m["name"][:20]}</a>\n'
            chap_nav += f'<a href="#{m_id}" style="padding-left:12px;font-size:.82em"><span class="num">·</span>{m["name"][:18]}</a>\n'

            sections_html += f'\n<h3 id="{m_id}">{m["name"]}</h3>\n'

            # 定义
            sections_html += f'<div class="def-box"><div class="def-title">核心原理</div><p>{m["principle"]}</p></div>\n'

            # 公式
            if m.get("formula"):
                sections_html += f'<div class="formula">$${m["formula"]}$$</div>\n'

            # 场景+优缺点 表格
            sc = m["scenarios"].split("|")
            ad = m["adv"].split("|")
            di = m["dis"].split("|")
            max_rows = max(len(sc), len(ad), len(di))

            sections_html += '<table><tr><th style="width:25%">适用场景</th><th style="width:37%">优点</th><th style="width:38%">缺点</th></tr>\n'
            for i in range(max_rows):
                s = sc[i] if i < len(sc) else ""
                a = ad[i] if i < len(ad) else ""
                d = di[i] if i < len(di) else ""
                sections_html += f'<tr><td>{s}</td><td>{a}</td><td>{d}</td></tr>\n'
            sections_html += '</table>\n'

        # 添加对比表（如果该类别有）
        for comp in COMPARISONS:
            if any(m["name"].startswith(comp["title"].split(" vs ")[0][:8]) for m in cat_data["methods"]):
                sections_html += f'\n<h3>📊 对比：{comp["title"]}</h3>\n'
                sections_html += '<table><tr>'
                for h in comp["headers"]:
                    sections_html += f'<th>{h}</th>'
                sections_html += '</tr>\n'
                for row in comp["rows"]:
                    sections_html += '<tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>\n'
                sections_html += '</table>\n'

        sections_html += '</div>\n'

    # 方法总数统计
    total = sum(len(cat["methods"]) for cat in METHODS.values())

    # 组装完整HTML
    # 读取现有页面模板（从蒙特卡洛.html复制结构）
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>数学建模方法大全 — 学习平台</title>
<script>
MathJax = {{ tex: {{ inlineMath: [['$','$'],['\\(','\\)']], displayMath: [['$$','$$'],['\\[','\\]']], processEscapes: true }} }};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js" async></script>
<style>
/* ===== CSS Variables ===== */
:root {{
  --paper: #fdf6e3; --paper-dark: #f3e8d0; --ink: #3d3525; --ink-light: #6b5f48;
  --accent: #2d7fc1; --accent-hover: #1d4ed8; --divider: #d9c9a0;
  --card-bg: #fef9ee; --card-border: #e5d5b5;
  --sidebar-bg: #f5ebd5; --sidebar-border: #e5d5b5;
  --code-bg: #ede0c5; --highlight-bg: #fefce8;
  --highlight-border: #eab308; --highlight-strong: #92400e;
  --tag-must-bg: #dbeafe; --tag-must-color: #1e40af;
  --tag-key-bg: #fef3c7; --tag-key-color: #92400e;
  --tag-freq-bg: #dbeafe; --tag-freq-color: #1e40af;
  --tag-info-bg: #f0fdf4; --tag-info-color: #166534;
  --heading-color: #1a3a5c; --code-text: #8a4b1e;
  --radius: 8px; --font: "Microsoft YaHei","PingFang SC","Noto Sans SC",sans-serif;
}}
.dark-mode {{
  --paper: #1a1a2e; --paper-dark: #22223a; --ink: #e0e0ec; --ink-light: #8888aa;
  --accent: #6a82f0; --accent-hover: #5a72e0; --divider: #2d2d45;
  --card-bg: #24243a; --card-border: #33334d;
  --sidebar-bg: #1a1a2e; --sidebar-border: #2d2d45;
  --code-bg: #2a2a3e; --highlight-bg: #1e2a3a;
  --highlight-border: #6a82f0; --highlight-strong: #8ab8f0;
  --tag-must-bg: #1a2a3d; --tag-must-color: #80b8e0;
  --tag-key-bg: #1e2a3d; --tag-key-color: #80b8e0;
  --tag-freq-bg: #1a2a3d; --tag-freq-color: #80b8e0;
  --tag-info-bg: #1a3d2a; --tag-info-color: #80c090;
  --heading-color: var(--ink); --code-text: #8ab8c0;
  background-color: var(--paper);
}}

/* ===== Reset & Base ===== */
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:var(--font);font-size:12pt;font-weight:500;line-height:1.8;color:var(--ink);background:var(--paper);display:flex;min-height:100vh}}
a{{color:var(--accent);text-decoration:none;transition:color .2s}}
a:hover{{color:var(--accent-hover)}}
ul,ol{{padding-left:1.5em}}
li{{margin-bottom:.3em}}
table{{border-collapse:collapse;width:100%;margin:12px 0;font-size:.95em}}
th,td{{border:1px solid var(--card-border);padding:8px 12px;text-align:center}}
th{{background:var(--paper-dark);font-weight:600}}
td{{background:var(--card-bg)}}
::-webkit-scrollbar{{width:6px}}
::-webkit-scrollbar-thumb{{background:var(--ink-light);border-radius:3px}}

/* ===== Sidebar ===== */
.sidebar{{position:fixed;top:0;left:0;width:210px;height:100vh;background:var(--sidebar-bg);border-right:1px solid var(--sidebar-border);overflow-y:auto;z-index:100;padding:0 0 20px}}
.sidebar-header{{padding:22px 16px 16px;border-bottom:1px solid var(--sidebar-border)}}
.sidebar-header .site-name{{font-size:1.15em;font-weight:700;color:var(--accent)}}
.sidebar-header .site-sub{{font-size:.75em;color:var(--ink-light);margin-top:2px}}
.sidebar-nav{{padding:8px 0}}
.sidebar-nav .group-label{{font-size:.7em;text-transform:uppercase;letter-spacing:1px;color:var(--ink-light);padding:12px 16px 4px;font-weight:600}}
.sidebar-nav a{{display:flex;align-items:center;padding:7px 16px;font-size:.9em;color:var(--ink);gap:8px;border-left:3px solid transparent;transition:background .15s,border-color .15s}}
.sidebar-nav a:hover{{background:var(--paper-dark);color:var(--accent)}}
.sidebar-nav a.current{{background:var(--highlight-bg);border-left-color:var(--accent);color:var(--accent);font-weight:600}}
.sidebar-nav .tag{{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;background:var(--paper-dark);font-size:.75em;font-weight:600;flex-shrink:0}}
.sidebar-nav a.current .tag{{background:var(--accent);color:#fff}}

/* ===== Theme Toggle ===== */
.theme-toggle{{position:fixed;top:56px;right:20px;z-index:200;background:var(--card-bg);border:1px solid var(--card-border);border-radius:50%;width:38px;height:38px;font-size:1.1em;cursor:pointer;line-height:1;transition:transform .2s}}
.theme-toggle:hover{{transform:scale(1.1)}}

/* ===== Main Area ===== */
.main-wrap{{flex:1;margin-left:210px;display:flex;flex-direction:column;min-height:100vh}}

/* ===== Topbar ===== */
.topbar{{position:sticky;top:0;z-index:90;background:linear-gradient(135deg, #1a3a5c, var(--accent));padding:0}}
.topbar-inner{{max-width:1100px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;padding:14px 28px}}
.topbar-inner h2{{color:#fff;font-size:1.15em;font-weight:600}}
.topbar-inner a{{color:rgba(255,255,255,.85);font-size:.9em;padding:5px 12px;border-radius:4px;transition:background .2s}}
.topbar-inner a:hover{{background:rgba(255,255,255,.15);color:#fff}}

/* ===== Container ===== */
.container{{max-width:1100px;margin:0 auto;padding:28px 28px 40px;width:100%}}

/* ===== Content Blocks ===== */
.section{{background:var(--card-bg);border:1px solid var(--card-border);border-radius:var(--radius);padding:24px 28px;margin-bottom:22px;box-shadow:0 1px 3px rgba(0,0,0,.04)}}
.section h2{{font-size:1.3em;color:var(--heading-color);margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid var(--divider)}}
.section h3{{font-size:1.08em;color:var(--accent);margin:20px 0 10px;padding-bottom:6px;border-bottom:1px dashed var(--divider)}}
.section h4{{font-size:1em;color:var(--ink);font-weight:600;margin:14px 0 6px}}
.section p{{margin-bottom:10px}}

.highlight{{background:var(--highlight-bg);border-left:4px solid var(--highlight-border);padding:12px 16px;margin:14px 0;border-radius:0 6px 6px 0;font-size:.95em}}
.highlight strong{{color:var(--highlight-strong)}}

.def-box{{background:var(--code-bg);border:1px solid var(--card-border);border-radius:6px;padding:14px 18px;margin:12px 0}}
.def-box .def-title{{font-weight:700;color:var(--accent);margin-bottom:4px;font-size:.92em}}

.formula{{text-align:center;background:var(--code-bg);padding:12px 20px;margin:14px 0;border-radius:6px}}
mjx-container[display="true"]{{max-width:100%;overflow-x:auto;overflow-y:hidden}}

.code-block{{background:var(--code-bg);border:1px solid var(--card-border);border-radius:6px;padding:16px 20px;margin:12px 0;overflow-x:auto;font-family:"Cascadia Code","Consolas","Courier New",monospace;font-size:.88em;line-height:1.65;color:var(--ink);white-space:pre}}

code{{font-family:"Cascadia Code","JetBrains Mono","Consolas",monospace;font-size:.88em;background:var(--code-bg);color:var(--code-text);padding:1px 6px;border-radius:4px}}

.tag-must,.tag-key,.tag-freq,.tag-info{{display:inline-block;padding:1px 8px;border-radius:3px;font-size:.8em;font-weight:600;margin:0 2px}}
.tag-must{{background:var(--tag-must-bg);color:var(--tag-must-color)}}
.tag-key{{background:var(--tag-key-bg);color:var(--tag-key-color)}}
.tag-freq{{background:var(--tag-freq-bg);color:var(--tag-freq-color)}}
.tag-info{{background:var(--tag-info-bg);color:var(--tag-info-color)}}

/* ===== Bottom Nav ===== */
.nav-links{{display:flex;justify-content:space-between;align-items:center;margin-top:30px;padding:16px 0}}
.nav-links a{{padding:8px 18px;border:1px solid var(--card-border);border-radius:6px;background:var(--card-bg);font-size:.9em;transition:all .2s}}
.nav-links a:hover{{background:var(--accent);color:#fff;border-color:var(--accent)}}

/* ===== Back to Top ===== */
.back2top{{position:fixed;right:24px;bottom:30px;z-index:90;width:42px;height:42px;background:linear-gradient(135deg, #1a3a5c, var(--accent));color:#fff;border:none;border-radius:50%;font-size:1.2em;cursor:pointer;opacity:.75;transition:all .2s;box-shadow:0 2px 10px rgba(0,0,0,.18)}}
.back2top:hover{{opacity:1}}

/* ===== Chapter Nav Panel (right slide-in) ===== */
.chapter-nav-toggle{{position:fixed;right:0;top:50%;transform:translateY(-50%);z-index:95;background:linear-gradient(135deg, #1a3a5c, var(--accent));color:#fff;border:none;border-radius:8px 0 0 8px;padding:14px 8px;font-size:1.1em;cursor:pointer;writing-mode:vertical-lr;letter-spacing:2px;opacity:.8;transition:all .2s;box-shadow:-2px 0 10px rgba(0,0,0,.15)}}
.chapter-nav-panel{{position:fixed;right:-260px;top:0;width:250px;height:100vh;z-index:150;background:var(--sidebar-bg);border-left:1px solid var(--sidebar-border);overflow-y:auto;transition:right .35s cubic-bezier(.4,0,.2,1);padding:20px 0}}
.chapter-nav-panel.open{{right:0}}
.chapter-nav-panel .nav-header{{padding:12px 20px 16px;border-bottom:1px solid var(--sidebar-border);font-weight:700;color:var(--accent);font-size:1.05em}}
.chapter-nav-panel .nav-section{{padding:8px 20px 2px;font-size:.7em;text-transform:uppercase;letter-spacing:1px;color:var(--ink-light);font-weight:600}}
.chapter-nav-panel a{{display:flex;align-items:center;padding:7px 20px;font-size:.9em;color:var(--ink);gap:8px;transition:background .15s}}
.chapter-nav-panel a:hover{{background:var(--paper-dark);color:var(--accent)}}
.chapter-nav-panel a.current{{color:var(--accent);font-weight:600}}
.chapter-nav-panel .num{{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;background:var(--paper-dark);font-size:.75em;font-weight:600;flex-shrink:0}}

/* ===== Footer ===== */
.footer{{text-align:center;padding:20px;color:var(--ink-light);font-size:.82em;border-top:1px solid var(--divider);margin-top:auto}}

/* ===== Responsive ===== */
@media(max-width:768px){{.sidebar{{display:none}}.main-wrap{{margin-left:0}}body{{font-size:10.5pt}}}}
@media(max-width:640px){{.section{{padding:18px 16px}}.topbar-inner h2{{font-size:1em}}.topbar-inner{{padding:10px 14px}}.chapter-nav-panel{{width:200px}}table{{font-size:.85em}}th,td{{padding:5px 8px}}.back2top{{right:10px;bottom:20px;width:38px;height:38px}}.container{{padding:16px 12px 30px}}}}
@media print{{.sidebar,.topbar,.theme-toggle,.chapter-nav-toggle,.chapter-nav-panel,.back2top,.nav-links,.footer{{display:none}}.main-wrap{{margin-left:0}}}}
</style>
</head>
<body>

<!-- ===== Sidebar ===== -->
<nav class="sidebar">
  <div class="sidebar-header">
    <div class="site-name">📐 数学建模</div>
    <div class="site-sub">学习平台</div>
  </div>
  <div class="sidebar-nav">
    <div class="group-label">核心方法</div>
    <a href="插值与拟合.html"><span class="tag">1</span>插值与拟合</a>
    <a href="蒙特卡洛.html"><span class="tag">2</span>蒙特卡洛方法</a>
    <a href="线性回归.html"><span class="tag">3</span>线性回归</a>
    <a href="主成分与因子分析.html"><span class="tag">5</span>主成分与因子分析</a>
    <a href="时间序列.html"><span class="tag">6</span>时间序列分析</a>
    <a href="图与网络.html"><span class="tag">7</span>图与网络</a>
    <div class="group-label">综合专题</div>
    <a href="AI与建模.html"><span class="tag">4</span>AI与数学建模</a>
    <a href="方法大全.html" class="current"><span class="tag">★</span>方法大全({total}种)</a>
    <a href="index.html" style="margin-top:6px;border-top:1px solid var(--sidebar-border);padding-top:8px"><span class="tag">⌂</span>返回首页</a>
  </div>
</nav>

<button class="theme-toggle no-print" onclick="toggleTheme()" title="切换暗黑模式">🌙</button>

<div class="main-wrap">

<div class="topbar">
  <div class="topbar-inner">
    <a href="AI与建模.html">← AI与建模</a>
    <h2>★ 数学建模方法大全（{total}种方法）</h2>
    <a href="index.html">返回首页 →</a>
  </div>
</div>

<div class="container">

<div class="section">
  <h2>📖 关于本章</h2>
  <p>本章系统收录<strong>{total}种数学建模方法</strong>，涵盖综合评价、预测、优化规划、统计分析与机器学习、插值拟合、图论网络和竞赛方法论七大类。每种方法包含<strong>核心原理、数学公式、适用场景、优点和缺点</strong>。相近方法之间提供<strong>对比表格</strong>，帮助快速选择合适方法。</p>
  <p>方法来源：知识库58种方法 + learning文件夹PPT/PDF讲义提取。右侧面板可快速导航至任意章节和具体方法。</p>
</div>

{sections_html}

<div class="nav-links">
  <a href="AI与建模.html">← AI与数学建模</a>
  <a href="#" onclick="window.scrollTo({{top:0,behavior:'smooth'}});return false">↑ 回到顶部</a>
  <a href="index.html">返回首页 →</a>
</div>

</div>

<div class="footer">📐 数学建模学习平台 · 方法大全 · 共{total}种方法</div>
</div>

<button class="back2top no-print" onclick="window.scrollTo({{top:0,behavior:'smooth'}})" title="回到顶部">↑</button>

<button class="chapter-nav-toggle no-print" id="chapterNavToggle" onclick="toggleChapterNav()">章 节 导 航</button>
<nav class="chapter-nav-panel" id="chapterNavPanel">
  <div class="nav-header">方法大全 — 目录</div>
  {chap_nav}
</nav>

<script>
const STORAGE_KEY = 'mathmodel_dark_mode';

function toggleTheme() {{
  const b = document.body;
  const btn = document.querySelector('.theme-toggle');
  b.classList.toggle('dark-mode');
  const isDark = b.classList.contains('dark-mode');
  localStorage.setItem(STORAGE_KEY, isDark ? '1' : '0');
  btn.textContent = isDark ? '☀️' : '🌙';
}}

(function() {{
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === '1') {{
    document.body.classList.add('dark-mode');
    document.querySelector('.theme-toggle').textContent = '☀️';
  }}
}})();

function toggleChapterNav() {{
  document.getElementById('chapterNavPanel').classList.toggle('open');
}}

document.getElementById('chapterNavPanel').addEventListener('click', function(e) {{
  if (e.target.tagName === 'A') {{
    this.classList.remove('open');
  }}
}});

// 点页面空白关闭导航
document.addEventListener('click', function(e) {{
  const panel = document.getElementById('chapterNavPanel');
  const toggle = document.getElementById('chapterNavToggle');
  if (!panel.contains(e.target) && e.target !== toggle) {{
    panel.classList.remove('open');
  }}
}});
</script>

</body>
</html>'''

    return html

# ============================================================
# 写入文件
# ============================================================
if __name__ == '__main__':
    html = gen_html()
    path = '方法大全.html'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    size_kb = os.path.getsize(path) / 1024
    total = sum(len(cat["methods"]) for cat in METHODS.values())
    print(f'生成: {path} ({size_kb:.0f} KB)')
    print(f'收录: {total} 种方法, {len(METHODS)} 大类')
    print(f'对比表: {len(COMPARISONS)} 张')
