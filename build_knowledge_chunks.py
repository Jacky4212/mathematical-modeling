"""
Parse the 4 mathematical modeling markdown guides and generate
knowledge-chunks.json for the RAG retrieval engine.
"""
import json
import re
import os

BASE = os.path.dirname(os.path.abspath(__file__))

FILES = [
    ("综合评价方法完全指南.md", "综合评价"),
    ("预测方法完全指南.md", "预测模型"),
    ("12种优化与规划求解方法完全指南.md", "优化规划"),
    ("统计分析与机器学习方法完全指南.md", "统计与机器学习"),
]

def extract_chunks(filepath, category):
    """Extract method-level chunks from a markdown guide."""
    fullpath = os.path.join(BASE, filepath)
    if not os.path.exists(fullpath):
        print(f"WARNING: {filepath} not found, skipping")
        return []

    with open(fullpath, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = []
    # Split by ## Numbered sections (## 1. / ## 2. etc)
    # Also handle ### subsections that are method headers
    sections = re.split(r'\n(?=## \d+\. )', text)
    # If no ## sections found (e.g., 统计与ML uses ###), try ### split
    if len(sections) <= 1:
        sections = re.split(r'\n(?=### \d+\. )', text)

    for section in sections:
        # Extract title
        title_match = re.match(r'#{2,3} \d+\.\s*(.+?)(?:\n|$)', section)
        if not title_match:
            continue
        title = title_match.group(1).strip()

        # Skip non-method sections (like 方法选型速查表, 参考资源)
        skip_keywords = ['方法选型', '参考资源', '参考来源', '方法总览', '总览']
        if any(kw in title for kw in skip_keywords):
            continue

        # Extract key subsections
        principles = ""
        scenarios = ""
        pros = ""
        cons = ""
        params = ""
        code = ""
        notes = ""

        # --- 数学原理 ---
        m = re.search(r'#{2,4}\s*数学原理\s*\n(.*?)(?=\n#{2,4}\s|\n##\s|\Z)', section, re.DOTALL)
        if m:
            principles = m.group(1).strip()[:2000]

        # --- 适用/不适用场景 ---
        m = re.search(r'###?\s*适用场景\s*\n(.*?)(?=\n#{2,4}\s|\n##\s|\Z)', section, re.DOTALL)
        if m:
            scenarios = m.group(1).strip()[:1500]
        # Also try "不适用场景"
        m2 = re.search(r'###?\s*不适[用合]场景\s*\n(.*?)(?=\n#{2,4}\s|\n##\s|\Z)', section, re.DOTALL)
        if m2:
            scenarios += "\n\n不适用场景：\n" + m2.group(1).strip()[:800]

        # --- 优缺点 ---
        m = re.search(r'###?\s*优缺点\s*\n(.*?)(?=\n#{2,4}\s|\n##\s|\Z)', section, re.DOTALL)
        if m:
            pros_cons_text = m.group(1).strip()[:1500]
            # Try to split into pros and cons from table
            pros_rows = re.findall(r'\|\s*(优点|[^|]+)\s*\|\s*([^|]+)\s*\|', pros_cons_text)
            if pros_rows:
                for label, detail in pros_rows:
                    if '优点' in label:
                        pros = detail.strip()
                    elif '缺点' in label:
                        cons = detail.strip()
            # Also look for list format
            p_match = re.search(r'\|?\s*优点\s*\|?\s*(.*?)(?=\n\|?\s*缺点|\Z)', pros_cons_text, re.DOTALL)
            if p_match:
                pros = p_match.group(1).strip()[:1000]
            c_match = re.search(r'\|?\s*缺点\s*\|?\s*(.*?)$', pros_cons_text, re.DOTALL)
            if c_match:
                cons = c_match.group(1).strip()[:1000]

        # --- 关键参数 ---
        m = re.search(r'###?\s*关键参数\s*\n(.*?)(?=\n#{2,4}\s|\n##\s|\Z)', section, re.DOTALL)
        if m:
            params = m.group(1).strip()[:1200]

        # --- 参考代码 ---
        m = re.search(r'###?\s*(?:参考|关键)?代码\s*\n(.*?)(?=\n#{2,4}\s|\n##\s|\Z)', section, re.DOTALL)
        if m:
            code = m.group(1).strip()[:2500]

        # --- 实现注意事项 ---
        m = re.search(r'###?\s*(?:实现)?注意事项\s*\n(.*?)(?=\n#{2,4}\s|\n##\s|\Z)', section, re.DOTALL)
        if m:
            notes = m.group(1).strip()[:1200]

        # Build searchable text (for TF-IDF retrieval)
        search_text = f"{title}\n{principles[:800]}\n{scenarios[:600]}"
        # Fallback: if extraction failed, use raw section content
        if len(search_text.strip()) < 50:
            # Remove markdown syntax, keep raw text
            raw = re.sub(r'[#*`|>\-]', ' ', section[:2000])
            raw = re.sub(r'\s+', ' ', raw).strip()
            search_text = f"{title}\n{raw[:1500]}"

        # Build full context (for prompt injection)
        full_context = f"【{title}】（{category}）\n"
        if principles:
            full_context += f"原理：{principles[:1500]}\n"
        if scenarios:
            full_context += f"适用场景：{scenarios[:1000]}\n"
        if params:
            full_context += f"关键参数：{params[:800]}\n"
        if notes:
            full_context += f"注意事项：{notes[:800]}\n"
        if code:
            full_context += f"参考代码：\n{code[:2000]}\n"

        chunks.append({
            "id": f"{category}-{len(chunks)+1:02d}",
            "title": title,
            "category": category,
            "keywords": extract_keywords(title, principles, scenarios),
            "search_text": search_text,
            "context": full_context,
        })

    return chunks


def extract_keywords(title, principles, scenarios):
    """Extract keywords from title + principles + scenarios text."""
    text = title + " " + principles[:500] + " " + scenarios[:500]

    # Common mathematical modeling keywords
    keyword_list = [
        # Evaluation
        "AHP", "层次分析", "TOPSIS", "优劣解距离", "熵值法", "熵权法", "CRITIC",
        "变异系数", "模糊综合评价", "模糊评价", "灰色关联", "GRA", "DEA", "数据包络",
        "秩和比", "RSR", "耦合协调", "ISM", "解释结构", "PCA", "主成分", "因子分析",
        # Prediction
        "GM(1,1)", "灰色预测", "ARIMA", "时间序列", "SARIMA", "季节性", "GARCH",
        "波动率", "VAR", "向量自回归", "马尔可夫", "状态转移", "多项式拟合", "最小二乘",
        "Logistic", "S曲线", "DID", "双重差分", "PSM", "倾向得分", "BP神经网络",
        "神经网络", "XGBoost", "LightGBM", "CatBoost", "随机森林", "集成学习",
        # Optimization
        "单纯形", "内点法", "线性规划", "整数规划", "分支定界", "动态规划", "多目标",
        "Pareto", "遗传算法", "GA", "粒子群", "PSO", "模拟退火", "SA", "蒙特卡洛",
        "蒙特卡罗", "梯度下降", "SGD", "Adam", "BFGS", "拟牛顿", "拉格朗日",
        "KKT", "Dijkstra", "最短路径", "最大流", "最小生成树",
        # Statistics
        "Pearson", "Spearman", "Kendall", "相关性", "T检验", "ANOVA", "方差分析",
        "卡方检验", "Mann-Whitney", "Kruskal-Wallis", "线性回归", "OLS", "R²",
        "VIF", "多重共线性", "Ridge", "岭回归", "Lasso", "逻辑回归", "AUC",
        "ROC", "分层回归", "K-Means", "聚类", "分层聚类", "DBSCAN", "密度聚类",
        "决策树", "SVM", "支持向量机", "KNN", "K近邻", "朴素贝叶斯", "信度分析",
        "Cronbach", "效度分析", "KMO", "Bartlett", "中介效应", "Bootstrap",
        # General
        "综合评价", "预测", "优化", "规划", "分类", "回归", "降维", "赋权",
        "权重", "排序", "效率评价", "评分", "打分", "因果推断", "政策效应",
    ]

    found = []
    text_lower = text.lower()
    for kw in keyword_list:
        if kw.lower() in text_lower:
            found.append(kw)

    return found[:15]  # Limit keywords


def main():
    all_chunks = []
    for filename, category in FILES:
        print(f"Processing {filename}...")
        chunks = extract_chunks(filename, category)
        print(f"  → Found {len(chunks)} method chunks")
        all_chunks.extend(chunks)

    output_path = os.path.join(BASE, "knowledge-chunks.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    total_size = os.path.getsize(output_path)
    print(f"\nDone! {len(all_chunks)} chunks written to {output_path}")
    print(f"File size: {total_size/1024:.1f} KB")

    # Print summary
    print("\n--- Category Summary ---")
    from collections import Counter
    cats = Counter(c["category"] for c in all_chunks)
    for cat, count in cats.items():
        print(f"  {cat}: {count} methods")


if __name__ == "__main__":
    main()
