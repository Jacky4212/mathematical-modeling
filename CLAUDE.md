# 数学建模

数学建模学习与竞赛准备项目目录。

## 项目概述

本目录用于数学建模相关的工作，包括但不限于：
- 数学建模竞赛（国赛、美赛等）的准备与参赛
- 数学模型的学习、实现与验证
- 数据分析与可视化
- 论文/报告的撰写
- 算法实现与优化

---

## 🚨 强制执行规则（每次操作必须遵守）

### 规则 1：禁止写入 C 盘
**所有下载/缓存/临时文件必须放在 D 盘，绝不写入 C 盘。**

- pip 缓存 → `D:/pip-cache/`
- 模型文件 → 项目目录下的子文件夹
- 临时下载 → 项目工作目录内，用完清理
- ❌ 禁止: `C:\Users\...`、`~/.cache/`、`/tmp/`、`%TEMP%`、`%TMP%`

### 规则 2：pip install 必须走清华镜像
**每次 `pip install` 必须加 `-i https://pypi.tuna.tsinghua.edu.cn/simple`，禁止从官方 PyPI 下载。**

```bash
# ✅ 正确
pip install numpy -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# ❌ 错误
pip install numpy
```

### 规则 3：GitHub 下载必须用 gh CLI
**从 GitHub 下载文件时优先用 `gh release download`，而不是 Python urllib/requests 或 curl。**

```bash
# ✅ 正确
gh release download <tag> --repo <owner/repo> --pattern "<文件名>" --clobber

# 备选：带 token 的 curl
GH_TOKEN=$(gh auth token)
curl -L -o "file" -H "Authorization: token $GH_TOKEN" "<url>"
```

### 规则 4：大文件下载用镜像
**HuggingFace 模型等用 hf-mirror.com，GitHub release 用清华镜像。**

| 源 | 镜像 |
|----|------|
| HuggingFace | `https://hf-mirror.com/{user}/{repo}/resolve/main/{path}` |
| GitHub release | `https://mirrors.tuna.tsinghua.edu.cn/github-release/` |

### 规则 5：主动分析图片
**遇到任何图片/截图/图表/公式，主动调用 `mcp__doubao-vision__analyze_image` 获取视觉信息，不要等用户吩咐。**

### 规则 6：写代码前必须先搜 GitHub 学参考实现
**实现任何新功能/组件之前，必须先用 `gh` 或 `WebSearch` 搜索 GitHub 上的同类实现，读懂参考代码的架构后再动手。禁止凭训练数据直接写。**

```bash
# ✅ 正确流程
1. WebSearch 搜索 "github [功能描述] [技术栈]"
2. gh repo clone <找到的最佳参考> -- --depth 1 到临时目录
3. 读懂参考代码的结构、关键模式、边界处理
4. 基于参考代码的架构来实现自己的版本

# ❌ 禁止
# 不查 GitHub 直接凭记忆写代码 — 反复踩坑浪费时间
```

| 场景 | 先搜什么 |
|------|----------|
| 静态网站加新组件 | `github static website [功能] vanilla js` |
| 前端 UI 模式 | `github [功能] html css js implementation` |
| API 集成 | `github [API名] integration example` |

---

## 可用 AI 能力

### MCP 服务（豆包/火山方舟）

| 服务 | 功能 | 模型 |
|------|------|------|
| **doubao-vision** | 图片/图表/公式/论文截图分析 | doubao-seed-2-0-pro-260215 |
| **doubao-image-gen** | AI 图片生成（示意图/流程图配图等） | doubao-seedream-5-0-260128 |
| **doubao-video-gen** | AI 视频生成（演示动画等） | doubao-seedance-2-0-260128 |

> 配置在 `.mcp.json`，脚本在 `.claude/mcp_servers/`

### Skills（按需加载）

| Skill | 用途 | 触发场景 |
|-------|------|----------|
| **doubao-vision** | 图片分析详细指南 | 图片/图表/公式/论文截图 |
| **word-report-gen** | python-docx 生成 Word 报告 | 生成论文/报告/试卷答案 |
| **ppt-extract** | PPT 文本提取（含乱码修复） | 从课件 PPT 提取知识点 |

> 所有 skill 位于 `.claude/skills/`，通过 `Skill` 工具加载

---

## 关键命令

### Python 环境
```bash
# 安装包（必须用清华镜像 — 见强制执行规则 2）
pip install <包名> -i https://pypi.tuna.tsinghua.edu.cn/simple

# 常用数学建模库
pip install numpy scipy matplotlib pandas sympy -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install jupyter notebook -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install python-docx openpyxl -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install scikit-learn cvxpy pulp -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Git 工作流
```bash
git init
git add .
git commit -m "feat: 描述"
git remote add origin <url>
git push -u origin main
```

---

## 注意事项

1. **数值稳定性**: 数学代码注意避免除零、log(0)、矩阵奇异等问题
2. **量纲一致性**: 建模时确保所有变量量纲统一
3. **代码可复现**: 设置随机种子，记录依赖版本
4. **论文写作**: 需要生成 Word 报告时调用 `word-report-gen` skill
5. **PPT 提取**: 需要从课件提取知识点时调用 `ppt-extract` skill

---

## MathModel Skill 工作流（数学建模竞赛）

当用户要求"开始生成""跑一下这个题""生成数学建模论文"时，按 MathModel Skill 工作流完成：

```
读题 -> 拆题 -> 模型路线 -> 判断附件性质 -> 生成/修改赛题专用代码 -> 运行代码 -> 真实图表/表格/结果 -> 证据门禁 -> 正式 outline -> Agent 全局写作 -> Word 排版 -> 格式门禁 -> 最终 QA
```

### Start Rule

任何数学建模论文任务都先读取总控 skill：

```
.claude/skills/paper-workflow-orchestrator/SKILL.md
```

### 输入输出约定

- 赛题与附件放入 `problem_files/`
- 外部补充数据放入 `crawled_data/`
- 当前赛题专用代码写入 `paper_output/code/`，不要写回 `.claude/skills/`
- 最终交付物：`paper_output/final_paper.docx`

### 执行规则

- 不要跳过 `quality-assurance-auditor`
- 证据门禁未通过（`evidence_status` 为 `missing`/`needs_real_modeling`/`scaffold_result_needs_review`），不得把 Word 称为最终稿
- 格式门禁未通过，不得把 Word 称为最终稿
- 正式赛题不要先跑 quickstart；quickstart 只用于安装验证

### 可选验证命令

```bash
# 安装验证（非正式比赛）
python .claude/skills/paper-workflow-orchestrator/scripts/quickstart_run.py

# 检查当前进度
python .claude/skills/paper-workflow-orchestrator/scripts/workflow_guard.py --status
```

### 已安装的 MathModel Skills（10个）

| Skill | 功能 |
|-------|------|
| `paper-workflow-orchestrator` | 总入口，S0-S8 阶段路由 |
| `problem-doc-model-selector` | 赛题解析 + 模型选型 |
| `modeling-paper-rubric-and-model-selector` | 模型路线 + 评分闭环 |
| `authoritative-data-harvester` | 权威数据采集 |
| `data-cleaning-and-visualization` | 数据清洗 + 论文图表 |
| `model-code-and-result-generator` | 建模代码 + 结果契约 |
| `quality-assurance-auditor` | 证据门禁 + 8维度审计 |
| `paper-formal-writer` | 正式成稿 + Word OMML 公式 |
| `paper-micro-unit-generator` | 微单元提示词资产 |
| `context-memory-keeper` | 断点记忆恢复 |
