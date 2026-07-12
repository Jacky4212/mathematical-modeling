"""
通用数学优化器 — PSO / GA / SA

用于 2025 CUMCM A题 烟幕干扰弹投放策略优化
替换原有的 蒙特卡洛采样 + 贪心 方法

参考实现:
- PSO: Kennedy & Eberhart 1995, 惯性权重线性衰减
- GA:  SBX 交叉 (Deb & Agrawal 1995) + 多项式变异 + 锦标赛选择
- SA:  Kirkpatrick et al. 1983, 指数冷却

使用方式:
    from optimizers import PSO, GA, SA
    opt = PSO(bounds, n_particles=50)
    result = opt.optimize(objective_fn, max_iter=200)
"""

import numpy as np
import time
from typing import Callable, Optional


# ============================================================
# PSO — 粒子群优化 (Particle Swarm Optimization)
# ============================================================
class PSO:
    """粒子群优化器

    适用于连续参数空间的全局优化。
    每个粒子在搜索空间中飞行，受到自身历史最佳和群体最佳的双重吸引。

    Parameters
    ----------
    bounds : list of (low, high)
        每个维度的上下界
    n_particles : int
        粒子数量 (建议 30-100)
    w_start, w_end : float
        惯性权重起止值 (线性衰减，初期探索后期收敛)
    c1, c2 : float
        认知系数和社会系数
    """

    def __init__(self, bounds, n_particles=50, w_start=0.9, w_end=0.4, c1=2.0, c2=2.0):
        self.bounds = np.array(bounds, dtype=float)
        self.n_particles = n_particles
        self.w_start = w_start
        self.w_end = w_end
        self.c1 = c1
        self.c2 = c2
        self.dim = len(bounds)
        self._rng = np.random.RandomState()

    def optimize(self, objective_fn, max_iter=200, tol=1e-6,
                 verbose=True, early_stop_patience=40, seed_x=None):
        """运行 PSO 优化

        Parameters
        ----------
        objective_fn : callable
            接受 (dim,) 数组，返回标量适应度（最大化）
        max_iter : int
            最大迭代次数
        tol : float
            收敛容忍度
        verbose : bool
            是否打印进度
        early_stop_patience : int
            无改进则早停的迭代数
        seed_x : array or None
            注入到初始种群的已知可行解（解决冷启动问题）

        Returns
        -------
        dict with keys: x, fitness, history, n_evals
        """
        lb = self.bounds[:, 0]
        ub = self.bounds[:, 1]
        D = self.dim
        N = self.n_particles

        # 初始化
        X = self._rng.uniform(lb, ub, (N, D))
        # 注入seed: 替换第1个粒子 + 在seed附近扰动30%的粒子
        if seed_x is not None:
            X[0] = np.clip(seed_x, lb, ub)
            n_seed_vicinity = max(1, int(N * 0.3))
            for k in range(1, n_seed_vicinity + 1):
                perturbed = seed_x + self._rng.normal(0, 0.05, D) * (ub - lb)
                X[k] = np.clip(perturbed, lb, ub)
        V = self._rng.uniform(-0.1 * (ub - lb), 0.1 * (ub - lb), (N, D))

        # 边界 clamp
        X = np.clip(X, lb, ub)

        # 评估初始适应度
        pbest_X = X.copy()
        pbest_f = np.array([objective_fn(x) for x in X])
        gbest_idx = np.argmax(pbest_f)
        gbest_X = pbest_X[gbest_idx].copy()
        gbest_f = pbest_f[gbest_idx]

        history = [gbest_f]
        n_evals = N
        stagnant = 0

        t0 = time.time()
        for it in range(max_iter):
            # 线性衰减惯性权重
            w = self.w_start - (self.w_start - self.w_end) * it / max_iter

            # 更新速度
            r1 = self._rng.uniform(size=(N, D))
            r2 = self._rng.uniform(size=(N, D))
            V = (w * V
                 + self.c1 * r1 * (pbest_X - X)
                 + self.c2 * r2 * (gbest_X - X))

            # 更新位置
            X = X + V

            # 边界处理：反射 + 随机重置于边界内
            for d in range(D):
                below = X[:, d] < lb[d]
                above = X[:, d] > ub[d]
                X[below, d] = lb[d] + self._rng.uniform(size=below.sum()) * (ub[d] - lb[d]) * 0.05
                X[above, d] = ub[d] - self._rng.uniform(size=above.sum()) * (ub[d] - lb[d]) * 0.05
                V[below | above, d] *= -0.5
            X = np.clip(X, lb, ub)

            # 评估
            f = np.array([objective_fn(x) for x in X])
            n_evals += N

            # 更新个人最佳
            improved = f > pbest_f
            pbest_X[improved] = X[improved].copy()
            pbest_f[improved] = f[improved]

            # 更新全局最佳
            best_idx = np.argmax(pbest_f)
            if pbest_f[best_idx] > gbest_f + tol:
                gbest_X = pbest_X[best_idx].copy()
                gbest_f = pbest_f[best_idx]
                stagnant = 0
            else:
                stagnant += 1

            history.append(gbest_f)

            if verbose and ((it + 1) % 40 == 0 or it == 0):
                print(f"  [PSO] iter {it+1:4d}/{max_iter}  best={gbest_f:.4f}  "
                      f"pop_mean={f.mean():.4f}  w={w:.3f}")

            if stagnant >= early_stop_patience:
                if verbose:
                    print(f"  [PSO] 早停于 iter {it+1}（{early_stop_patience}代无改进）")
                break

        elapsed = time.time() - t0
        if verbose:
            print(f"  [PSO] 完成: best={gbest_f:.4f}, {n_evals}次评估, "
                  f"{len(history)}代, {elapsed:.1f}s")

        return {
            'x': gbest_X,
            'fitness': gbest_f,
            'history': history,
            'n_evals': n_evals,
            'elapsed_s': elapsed,
        }


# ============================================================
# GA — 遗传算法 (Genetic Algorithm)
# ============================================================
class GA:
    """实编码遗传算法 (Real-Coded GA)

    使用 SBX 交叉和多项式变异，适合连续参数空间的全局优化。
    锦标赛选择保持选择压力，精英保留防止最优解丢失。

    Parameters
    ----------
    bounds : list of (low, high)
        每个维度的上下界
    pop_size : int
        种群大小 (建议 80-200)
    crossover_rate : float
        交叉概率 (0.8-0.95)
    mutation_rate : float
        变异概率 (0.05-0.2)
    elite_ratio : float
        精英保留比例
    eta_c, eta_m : float
        SBX交叉和多项式变异的分布指数
    """

    def __init__(self, bounds, pop_size=120, crossover_rate=0.9, mutation_rate=0.1,
                 elite_ratio=0.05, eta_c=15, eta_m=20):
        self.bounds = np.array(bounds, dtype=float)
        self.pop_size = pop_size
        self.cr = crossover_rate
        self.mr = mutation_rate
        self.elite_count = max(1, int(pop_size * elite_ratio))
        self.eta_c = eta_c
        self.eta_m = eta_m
        self.dim = len(bounds)
        self._rng = np.random.RandomState()

    # -------- SBX 交叉 --------
    def _sbx_crossover(self, p1, p2):
        """模拟二进制交叉 (Simulated Binary Crossover)"""
        lb = self.bounds[:, 0]
        ub = self.bounds[:, 1]
        c1, c2 = p1.copy(), p2.copy()
        eta = self.eta_c

        for i in range(self.dim):
            if self._rng.random() < 0.5:  # 每维 50% 概率交叉
                if abs(p2[i] - p1[i]) > 1e-12:
                    y1 = min(p1[i], p2[i])
                    y2 = max(p1[i], p2[i])
                    yl, yu = lb[i], ub[i]

                    r = self._rng.random()

                    # 计算 beta_q
                    beta = 1.0 + 2.0 * (y1 - yl) / max(y2 - y1, 1e-10)
                    alpha = 2.0 - beta ** (-(eta + 1.0))

                    if r <= 1.0 / alpha:
                        betaq = (r * alpha) ** (1.0 / (eta + 1.0))
                    else:
                        betaq = (1.0 / (2.0 - r * alpha)) ** (1.0 / (eta + 1.0))

                    c1[i] = 0.5 * ((y1 + y2) - betaq * (y2 - y1))

                    # 另一侧
                    beta = 1.0 + 2.0 * (yu - y2) / max(y2 - y1, 1e-10)
                    alpha = 2.0 - beta ** (-(eta + 1.0))

                    if r <= 1.0 / alpha:
                        betaq = (r * alpha) ** (1.0 / (eta + 1.0))
                    else:
                        betaq = (1.0 / (2.0 - r * alpha)) ** (1.0 / (eta + 1.0))

                    c2[i] = 0.5 * ((y1 + y2) + betaq * (y2 - y1))

                    c1[i] = np.clip(c1[i], yl, yu)
                    c2[i] = np.clip(c2[i], yl, yu)

        return c1, c2

    # -------- 多项式变异 --------
    def _polynomial_mutation(self, x):
        """多项式变异 (Polynomial Mutation)"""
        lb = self.bounds[:, 0]
        ub = self.bounds[:, 1]
        mutant = x.copy()
        eta = self.eta_m

        for i in range(self.dim):
            r = self._rng.random()
            if r < self.mr / self.dim:  # 每维独立变异概率
                yl, yu = lb[i], ub[i]
                delta1 = (x[i] - yl) / max(yu - yl, 1e-10)
                delta2 = (yu - x[i]) / max(yu - yl, 1e-10)
                r = self._rng.random()

                if r < 0.5:
                    deltaq = ((2 * r + (1 - 2 * r) * (1 - delta1) ** (eta + 1))
                              ** (1 / (eta + 1)) - 1)
                else:
                    deltaq = (1 - (2 * (1 - r) + 2 * (r - 0.5) * (1 - delta2) ** (eta + 1))
                              ** (1 / (eta + 1)))

                mutant[i] = np.clip(x[i] + deltaq * (yu - yl), yl, yu)

        return mutant

    # -------- 锦标赛选择 --------
    def _tournament_select(self, pop, fitness, k=3):
        """锦标赛选择: 随机选k个, 返回适应度最高的"""
        idx = self._rng.choice(len(pop), k, replace=False)
        best = idx[np.argmax(fitness[idx])]
        return pop[best].copy()

    # -------- 主优化循环 --------
    def optimize(self, objective_fn, max_generations=300,
                 verbose=True, early_stop_patience=60):
        """运行 GA 优化

        Parameters
        ----------
        objective_fn : callable
            接受 (dim,) 数组，返回标量适应度（最大化）
        max_generations : int
            最大代数
        verbose : bool
        early_stop_patience : int

        Returns
        -------
        dict with keys: x, fitness, history, n_evals
        """
        lb = self.bounds[:, 0]
        ub = self.bounds[:, 1]

        # 初始化种群
        pop = self._rng.uniform(lb, ub, (self.pop_size, self.dim))
        fitness = np.array([objective_fn(x) for x in pop])
        n_evals = self.pop_size

        # 全局最佳
        best_idx = np.argmax(fitness)
        gbest_X = pop[best_idx].copy()
        gbest_f = fitness[best_idx]
        history = [gbest_f]
        stagnant = 0

        t0 = time.time()
        for gen in range(max_generations):
            # 精英保留
            elite_idx = np.argsort(fitness)[-self.elite_count:]
            new_pop = [pop[i].copy() for i in elite_idx]

            # 生成子代
            while len(new_pop) < self.pop_size:
                p1 = self._tournament_select(pop, fitness)
                p2 = self._tournament_select(pop, fitness)

                if self._rng.random() < self.cr:
                    c1, c2 = self._sbx_crossover(p1, p2)
                else:
                    c1, c2 = p1.copy(), p2.copy()

                c1 = self._polynomial_mutation(c1)
                c2 = self._polynomial_mutation(c2)

                new_pop.append(c1)
                if len(new_pop) < self.pop_size:
                    new_pop.append(c2)

            pop = np.array(new_pop[:self.pop_size])

            # 评估新一代
            fitness = np.array([objective_fn(x) for x in pop])
            n_evals += self.pop_size

            # 更新全局最佳
            best_idx = np.argmax(fitness)
            if fitness[best_idx] > gbest_f + 1e-6:
                gbest_X = pop[best_idx].copy()
                gbest_f = fitness[best_idx]
                stagnant = 0
            else:
                stagnant += 1

            history.append(gbest_f)

            if verbose and ((gen + 1) % 50 == 0 or gen == 0):
                print(f"  [GA]  gen {gen+1:4d}/{max_generations}  best={gbest_f:.4f}  "
                      f"pop_avg={fitness.mean():.4f}  pop_std={fitness.std():.4f}")

            if stagnant >= early_stop_patience:
                if verbose:
                    print(f"  [GA]  早停于 gen {gen+1}（{early_stop_patience}代无改进）")
                break

        elapsed = time.time() - t0
        if verbose:
            print(f"  [GA]  完成: best={gbest_f:.4f}, {n_evals}次评估, "
                  f"{len(history)}代, {elapsed:.1f}s")

        return {
            'x': gbest_X,
            'fitness': gbest_f,
            'history': history,
            'n_evals': n_evals,
            'elapsed_s': elapsed,
        }


# ============================================================
# SA — 模拟退火 (Simulated Annealing)
# ============================================================
class SA:
    """模拟退火优化器

    适合作为 GA/PSO 结果的局部精修 (polish)，或小规模问题的独立求解。

    Parameters
    ----------
    bounds : list of (low, high)
    T_start, T_end : float
        起始和终止温度
    cooling_rate : float
        冷却系数 (0.8-0.99)
    steps_per_T : int
        每个温度下的尝试步数
    """

    def __init__(self, bounds, T_start=100.0, T_end=0.01,
                 cooling_rate=0.95, steps_per_T=20):
        self.bounds = np.array(bounds, dtype=float)
        self.T_start = T_start
        self.T_end = T_end
        self.cooling_rate = cooling_rate
        self.steps_per_T = steps_per_T
        self.dim = len(bounds)
        self._rng = np.random.RandomState()

    def optimize(self, objective_fn, x0=None, verbose=True):
        """运行 SA 优化

        Parameters
        ----------
        objective_fn : callable
            接受 (dim,) 数组，返回标量适应度（最大化）
        x0 : array or None
            初始解，None则随机生成
        verbose : bool

        Returns
        -------
        dict
        """
        lb = self.bounds[:, 0]
        ub = self.bounds[:, 1]

        if x0 is None:
            x = self._rng.uniform(lb, ub)
        else:
            x = np.clip(np.array(x0, dtype=float), lb, ub)

        f_x = objective_fn(x)
        best_x = x.copy()
        best_f = f_x
        history = [best_f]
        n_evals = 1

        T = self.T_start
        t0 = time.time()
        iteration = 0

        while T > self.T_end:
            for _ in range(self.steps_per_T):
                # 在当前温度下扰动
                step = self._rng.normal(0, 0.1 * (ub - lb) * (T / self.T_start))
                x_new = np.clip(x + step, lb, ub)
                f_new = objective_fn(x_new)
                n_evals += 1

                delta = f_new - f_x
                if delta > 0 or self._rng.random() < np.exp(delta / max(T, 1e-10)):
                    x = x_new
                    f_x = f_new
                    if f_x > best_f:
                        best_x = x.copy()
                        best_f = f_x

            history.append(best_f)
            T *= self.cooling_rate
            iteration += 1

            if verbose and iteration % 20 == 0:
                print(f"  [SA]  T={T:.4f}  best={best_f:.4f}  current={f_x:.4f}")

        elapsed = time.time() - t0
        if verbose:
            print(f"  [SA]  完成: best={best_f:.4f}, {n_evals}次评估, {elapsed:.1f}s")

        return {
            'x': best_x,
            'fitness': best_f,
            'history': history,
            'n_evals': n_evals,
            'elapsed_s': elapsed,
        }


# ============================================================
# 简单测试
# ============================================================
if __name__ == '__main__':
    # 测试函数: Rastrigin (最小值在0)
    def rastrigin(x):
        return - (10 * len(x) + np.sum(x**2 - 10 * np.cos(2 * np.pi * x)))

    bounds = [(-5.12, 5.12)] * 5

    print("=" * 60)
    print("PSO 测试 (Rastrigin 5D)")
    pso = PSO(bounds, n_particles=40)
    r = pso.optimize(rastrigin, max_iter=100, verbose=True)
    print(f"  x={r['x']}, f={r['fitness']:.6f}")

    print("\n" + "=" * 60)
    print("GA 测试 (Rastrigin 5D)")
    ga = GA(bounds, pop_size=100)
    r = ga.optimize(rastrigin, max_generations=100, verbose=True)
    print(f"  x={r['x']}, f={r['fitness']:.6f}")

    print("\n" + "=" * 60)
    print("SA 测试 (Rastrigin 5D)")
    sa = SA(bounds, T_start=50)
    r = sa.optimize(rastrigin, verbose=True)
    print(f"  x={r['x']}, f={r['fitness']:.6f}")
