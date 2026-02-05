# 快速开始: 评估统计分析

## 一分钟上手

```bash
# 1. 运行统计分析
python statistics.py --input ../outputs/eval_single_model.json

# 2. 生成可视化图表
python statistics_visual.py --input ../outputs/eval_single_model.json --output ./plots

# 3. 导出统计数据
python statistics.py --input ../outputs/eval_single_model.json --export stats.json
```

## 完整工作流示例

### 场景 1: 单个模型评估分析

```bash
# Step 1: 运行推理 (在 inference 目录)
cd ../inference
python inference_single.py --model Qwen/Qwen-7B-Chat \
                           --api_key dummy \
                           --base_url http://localhost:8000/v1 \
                           --dataset sample_data_200

# Step 2: 运行评估 (需要 Windows 环境)
cd ../evaluation
python evaluation.py --model Qwen_Qwen-7B-Chat \
                     --setting single \
                     --dataset sample_data_200

# 这会生成: ../outputs/eval_single_Qwen_Qwen-7B-Chat.json

# Step 3: 统计分析
python statistics.py --input ../outputs/eval_single_Qwen_Qwen-7B-Chat.json

# Step 4: 生成可视化
python statistics_visual.py --input ../outputs/eval_single_Qwen_Qwen-7B-Chat.json \
                             --labels "Qwen-7B-Chat" \
                             --output ./plots_qwen7b
```

### 场景 2: 多个模型对比分析

```bash
# 假设你已经有多个模型的评估结果
python statistics_visual.py \
    --input ../outputs/eval_single_model1.json \
            ../outputs/eval_single_model2.json \
            ../outputs/eval_single_model3.json \
    --labels "GPT-4" "Claude-3" "Qwen-7B" \
    --output ./comparison_plots

# 这会生成:
# - comparison_plots/comparison.png (整体对比图)
# - comparison_plots/distribution_GPT-4.png (GPT-4 分布图)
# - comparison_plots/distribution_Claude-3.png (Claude-3 分布图)
# - comparison_plots/distribution_Qwen-7B.png (Qwen-7B 分布图)
```

### 场景 3: 不同设置对比

```bash
# 对比单轮和多轮设置
python statistics_visual.py \
    --input ../outputs/eval_single_model.json \
            ../outputs/eval_multi_react_exec_model.json \
            ../outputs/eval_multi_row_react_exec_model.json \
    --labels "Single-Round" "Multi-Round-ReAct" "Multi-Round-ReAct-Row" \
    --output ./setting_comparison
```

## 输出示例

### 控制台输出

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
...
```

### 导出的 JSON

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
    ...
  }
}
```

## 可视化图表说明

### 1. comparison.png - 模型对比图
- **左子图**: 各模型的软限制 vs 硬限制对比
- **右子图**: 第一个模型按指令类型的性能分解

### 2. distribution_*.png - 任务分布图
- **左子图**: 任务完成分布饼图(完美/部分/失败)
- **右子图**: 按指令类型的任务分布堆叠柱状图

## 常见问题

### Q1: 如何解释软限制和硬限制的差异?

**A**:
- 软限制 - 硬限制 的差值反映了**部分正确解决方案的比例**
- 差值越大,说明模型生成的解决方案在不同测试用例下的鲁棒性越差
- 理想情况下,两者应该接近(说明解决方案要么完全正确,要么完全错误)

### Q2: Cell-Level 和 Sheet-Level 哪个更难?

**A**:
- 通常 Sheet-Level 操作更难,因为涉及更复杂的格式化和批量操作
- 查看统计报告中的硬限制分数对比可以了解相对难度

### Q3: 如何判断模型表现是否良好?

**A**: 参考基准:
- **硬限制分数 > 60%**: 良好
- **硬限制分数 40-60%**: 中等
- **硬限制分数 < 40%**: 需要改进

### Q4: 可视化需要安装什么依赖?

**A**:
```bash
pip install matplotlib numpy
```

## 进阶使用

### 批量分析所有评估结果

```bash
# 创建批量分析脚本
cat > batch_analyze.sh << 'EOF'
#!/bin/bash

for eval_file in ../outputs/eval_*.json; do
    filename=$(basename "$eval_file" .json)
    echo "Analyzing $filename..."

    # 生成统计报告
    python statistics.py --input "$eval_file" \
                         --export "stats_${filename}.json"

    # 生成可视化
    python statistics_visual.py --input "$eval_file" \
                                 --labels "$filename" \
                                 --output "plots_${filename}"
done

echo "All analyses complete!"
EOF

chmod +x batch_analyze.sh
./batch_analyze.sh
```

### 自定义可视化

编辑 `statistics_visual.py` 中的颜色、字体、图表样式等参数:

```python
# 修改配色方案
colors = ['#66c2a5', '#fc8d62', '#e78ac3']  # 自定义颜色

# 修改图表尺寸
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))  # 调整大小

# 修改字体大小
matplotlib.rcParams['font.size'] = 14  # 全局字体大小
```

## 参考资料

- [SpreadsheetBench 论文](https://arxiv.org/abs/2406.14991)
- [详细统计说明](./README_STATISTICS.md)
- [项目主页](https://spreadsheetbench.github.io/)
