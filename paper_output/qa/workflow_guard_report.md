# Workflow Guard Report

- Target step: `S3`
- Status: `INCOMPLETE`
- Generated at: `2026-07-12T09:37:41`
- Current step: `S2`
- Next step: `S3`
- Recommended skill: `data-cleaning-and-visualization`
- Next action: 基于 input_manifest 与模型路线生成 data_plan、visualization_plan、figure_index 与 load_report。

## Steps
- S0 准入预检: `PASS`
- S1 审题分析: `PASS`
- S2 模型路线: `PASS`
- S3 数据与图表计划: `FAIL`
  - 缺少文件：analysis/2025年A题newtest/plan/data_plan.json
  - 缺少文件：analysis/2025年A题newtest/plan/visualization_plan.json
  - 缺少文件：analysis/2025年A题newtest/figure_index.json
  - 缺少文件：analysis/2025年A题newtest/data_cleaned/load_report.json
