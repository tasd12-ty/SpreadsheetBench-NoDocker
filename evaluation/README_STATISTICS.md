# SpreadsheetBench 评估统计工具

## 概述

本工具用于分析 SpreadsheetBench 评估结果,提供详细的统计报告,支持按 `instruction_type` 分类统计。

## 评估指标说明

### Soft Restriction (软限制)
- **定义**: 部分通过评分,遵循 IOI 的 OJ 系统评分原则
- **计算方式**: 通过的测试用例数 / 总测试用例数
- **取值范围**: 0.0 ~ 1.0
- **意义**: 当解决方案只通过部分测试用例时给予部分分数,适合评估部分正确的解决方案

### Hard Restriction (硬限制)
- **定义**: 完全通过评分,鼓励模型追求完美解决方案
- **计算方式**: 所有测试用例都通过为 1,否则为 0
- **取值范围**: 0 或 1
- **意义**: 要求所有测试用例都通过,评估解决方案在电子表格内容变化时的鲁棒性

### 指令类型 (Instruction Type)
- **Cell-Level Manipulation**: 单元格级别操作(如查找、提取、计算单个值)
- **Sheet-Level Manipulation**: 工作表级别操作(如高亮、删除行、修改格式)

## 评估结果文件格式

评估结果为 JSON 格式,每个任务包含以下字段:

```json
{
  "id": 59196,
  "instruction_type": "Cell-Level Manipulation",
  "test_case_results": [1, 1, 0],
  "soft_restriction": 0.6666666666666666,
  "hard_restriction": 0
}
```

字段说明:
- `id`: 任务唯一标识符
- `instruction_type`: 指令类型(Cell-Level 或 Sheet-Level)
- `test_case_results`: 测试用例结果列表(1表示通过,0表示失败)
- `soft_restriction`: 软限制分数(部分通过)
- `hard_restriction`: 硬限制分数(完全通过)

## 使用方法

### 基本用法

```bash
# 分析评估结果
python statistics.py --input ../outputs/eval_single_model.json

# 显示详细信息
python statistics.py --input ../outputs/eval_single_model.json --verbose

# 导出统计结果到 JSON
python statistics.py --input ../outputs/eval_single_model.json --export stats_output.json
```

### 命令行参数

| 参数 | 简写 | 必需 | 说明 |
|------|------|------|------|
| `--input` | `-i` | 是 | 评估结果 JSON 文件路径 |
| `--export` | `-e` | 否 | 导出统计结果到 JSON 文件 |
| `--verbose` | `-v` | 否 | 显示详细信息 |

## 统计报告说明

### 整体统计
- **总任务数**: 所有评估任务的数量
- **总测试用例数**: 所有测试用例的总数(通常是任务数 × 3)
- **通过测试用例数**: 通过的测试用例总数
- **软限制平均分**: 所有任务的软限制分数平均值
- **硬限制平均分**: 所有任务的硬限制分数平均值

### 按指令类型统计
分别统计 Cell-Level 和 Sheet-Level 操作的:
- 任务数量
- 测试用例数量
- 通过用例数量
- 软限制平均分
- 硬限制平均分

### 详细分析
为每种指令类型提供:
- 测试用例通过率
- 全部通过、部分通过、全部失败的任务分布

## 示例输出

```
===============================================================================================================
SpreadsheetBench 评估统计报告
===============================================================================================================

【整体统计】
  总任务数:          200
  总测试用例数:      600
  通过测试用例数:    450
  软限制平均分:      75.00%
  硬限制平均分:      60.00%

【按指令类型统计】
---------------------------------------------------------------------------------------------------------------
指令类型                          任务数            测试用例数          通过用例数          软限制(平均)           硬限制(平均)
---------------------------------------------------------------------------------------------------------------
Cell-Level Manipulation       120            360            300            83.33%            70.00%
Sheet-Level Manipulation      80             240            150            62.50%            45.00%
---------------------------------------------------------------------------------------------------------------

【详细分析】

  Cell-Level Manipulation:
    - 任务数: 120
    - 测试用例通过率: 300/360 = 83.33%
    - 软限制(部分通过): 83.33%
    - 硬限制(全部通过): 70.00%
    - 全部通过: 84 (70.00%)
    - 部分通过: 30 (25.00%)
    - 全部失败: 6 (5.00%)
...
```

## 导出的 JSON 格式

使用 `--export` 选项导出的 JSON 文件格式:

```json
{
  "overall": {
    "total_tasks": 200,
    "total_test_cases": 600,
    "passed_test_cases": 450,
    "soft_restriction_avg": 0.75,
    "hard_restriction_avg": 0.60
  },
  "by_instruction_type": {
    "Cell-Level Manipulation": {
      "total_tasks": 120,
      "total_test_cases": 360,
      "passed_test_cases": 300,
      "soft_restriction_avg": 0.8333,
      "hard_restriction_avg": 0.70
    },
    "Sheet-Level Manipulation": {
      "total_tasks": 80,
      "total_test_cases": 240,
      "passed_test_cases": 150,
      "soft_restriction_avg": 0.625,
      "hard_restriction_avg": 0.45
    }
  }
}
```

## 评估工作流程

1. **运行推理**: 使用 `inference_single.py` 或 `inference_multiple.py` 生成模型输出
2. **运行评估**: 使用 `evaluation.py` 评估模型输出(需要 Windows 环境)
3. **统计分析**: 使用 `statistics.py` 分析评估结果

## 参考文献

- **论文**: [SpreadsheetBench: Towards Challenging Real World Spreadsheet Manipulation](https://arxiv.org/abs/2406.14991)
- **项目主页**: https://spreadsheetbench.github.io/
- **GitHub**: https://github.com/RUCKBReasoning/SpreadsheetBench

## 注意事项

1. 评估结果文件必须是有效的 JSON 格式
2. 每个任务应包含 `id`, `instruction_type`, `test_case_results`, `soft_restriction`, `hard_restriction` 字段
3. `instruction_type` 通常为 "Cell-Level Manipulation" 或 "Sheet-Level Manipulation"
4. 如果遇到 JSON 解析错误,请检查文件格式是否正确
