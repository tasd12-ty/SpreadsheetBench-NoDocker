#!/usr/bin/env python3
"""
SpreadsheetBench 评估统计可视化工具
生成统计图表,支持多个模型对比
"""
import os
import json
import argparse
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# 设置中文字体支持
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


def load_eval_results(file_path: str) -> List[Dict[str, Any]]:
    """加载评估结果文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_statistics(eval_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算统计数据"""
    if not eval_results:
        return {
            'total_tasks': 0,
            'soft_restriction_avg': 0.0,
            'hard_restriction_avg': 0.0,
        }

    total_tasks = len(eval_results)
    soft_restriction_avg = sum(r['soft_restriction'] for r in eval_results) / total_tasks
    hard_restriction_avg = sum(r['hard_restriction'] for r in eval_results) / total_tasks

    # 按类型分组
    stats_by_type = {}
    from collections import defaultdict
    results_by_type = defaultdict(list)

    for result in eval_results:
        instruction_type = result.get('instruction_type', 'Unknown')
        results_by_type[instruction_type].append(result)

    for instruction_type, results in results_by_type.items():
        stats_by_type[instruction_type] = {
            'total_tasks': len(results),
            'soft_restriction_avg': sum(r['soft_restriction'] for r in results) / len(results),
            'hard_restriction_avg': sum(r['hard_restriction'] for r in results) / len(results),
        }

    return {
        'overall': {
            'total_tasks': total_tasks,
            'soft_restriction_avg': soft_restriction_avg,
            'hard_restriction_avg': hard_restriction_avg,
        },
        'by_type': stats_by_type
    }


def plot_comparison_bar(stats_dict: Dict[str, Dict], output_path: str):
    """
    绘制对比柱状图

    Args:
        stats_dict: {model_name: stats_data}
        output_path: 输出图片路径
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    models = list(stats_dict.keys())
    soft_scores = [stats_dict[m]['overall']['soft_restriction_avg'] * 100 for m in models]
    hard_scores = [stats_dict[m]['overall']['hard_restriction_avg'] * 100 for m in models]

    x = np.arange(len(models))
    width = 0.35

    # 左图: 软限制 vs 硬限制
    ax1.bar(x - width/2, soft_scores, width, label='Soft Restriction', color='skyblue')
    ax1.bar(x + width/2, hard_scores, width, label='Hard Restriction', color='coral')
    ax1.set_ylabel('Accuracy (%)', fontsize=12)
    ax1.set_title('Overall Performance: Soft vs Hard Restriction', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(models, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_ylim([0, 100])

    # 添加数值标签
    for i, (soft, hard) in enumerate(zip(soft_scores, hard_scores)):
        ax1.text(i - width/2, soft + 1, f'{soft:.1f}%', ha='center', fontsize=9)
        ax1.text(i + width/2, hard + 1, f'{hard:.1f}%', ha='center', fontsize=9)

    # 右图: 按类型对比(仅显示第一个模型)
    if models:
        first_model = models[0]
        by_type = stats_dict[first_model]['by_type']
        types = list(by_type.keys())
        soft_by_type = [by_type[t]['soft_restriction_avg'] * 100 for t in types]
        hard_by_type = [by_type[t]['hard_restriction_avg'] * 100 for t in types]

        x2 = np.arange(len(types))
        ax2.bar(x2 - width/2, soft_by_type, width, label='Soft Restriction', color='skyblue')
        ax2.bar(x2 + width/2, hard_by_type, width, label='Hard Restriction', color='coral')
        ax2.set_ylabel('Accuracy (%)', fontsize=12)
        ax2.set_title(f'Performance by Instruction Type ({first_model})', fontsize=14, fontweight='bold')
        ax2.set_xticks(x2)
        ax2.set_xticklabels([t.replace(' Manipulation', '\nManipulation') for t in types], fontsize=10)
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)
        ax2.set_ylim([0, 100])

        # 添加数值标签
        for i, (soft, hard) in enumerate(zip(soft_by_type, hard_by_type)):
            ax2.text(i - width/2, soft + 1, f'{soft:.1f}%', ha='center', fontsize=9)
            ax2.text(i + width/2, hard + 1, f'{hard:.1f}%', ha='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ 对比图已保存至: {output_path}")


def plot_distribution_pie(eval_results: List[Dict[str, Any]], output_path: str, model_name: str):
    """
    绘制任务完成分布饼图

    Args:
        eval_results: 评估结果列表
        output_path: 输出图片路径
        model_name: 模型名称
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 整体分布
    perfect = sum(1 for r in eval_results if r['hard_restriction'] == 1)
    partial = sum(1 for r in eval_results if 0 < r['soft_restriction'] < 1)
    failed = sum(1 for r in eval_results if r['soft_restriction'] == 0)

    sizes = [perfect, partial, failed]
    labels = [f'Perfect\n({perfect})', f'Partial\n({partial})', f'Failed\n({failed})']
    colors = ['#66c2a5', '#fc8d62', '#e78ac3']
    explode = (0.05, 0, 0)

    ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=90, textprops={'fontsize': 11})
    ax1.set_title(f'Task Completion Distribution - Overall\n({model_name})',
                  fontsize=13, fontweight='bold')

    # 按类型分布
    from collections import defaultdict
    type_stats = defaultdict(lambda: {'perfect': 0, 'partial': 0, 'failed': 0})

    for r in eval_results:
        inst_type = r.get('instruction_type', 'Unknown')
        if r['hard_restriction'] == 1:
            type_stats[inst_type]['perfect'] += 1
        elif 0 < r['soft_restriction'] < 1:
            type_stats[inst_type]['partial'] += 1
        else:
            type_stats[inst_type]['failed'] += 1

    # 绘制堆叠柱状图
    types = list(type_stats.keys())
    perfects = [type_stats[t]['perfect'] for t in types]
    partials = [type_stats[t]['partial'] for t in types]
    faileds = [type_stats[t]['failed'] for t in types]

    x = np.arange(len(types))
    width = 0.5

    ax2.bar(x, perfects, width, label='Perfect', color='#66c2a5')
    ax2.bar(x, partials, width, bottom=perfects, label='Partial', color='#fc8d62')
    ax2.bar(x, faileds, width, bottom=np.array(perfects) + np.array(partials),
            label='Failed', color='#e78ac3')

    ax2.set_ylabel('Number of Tasks', fontsize=12)
    ax2.set_title('Task Distribution by Instruction Type', fontsize=13, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([t.replace(' Manipulation', '\nManipulation') for t in types], fontsize=10)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ 分布图已保存至: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='SpreadsheetBench 评估结果可视化工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单个模型分析
  python statistics_visual.py --input ../outputs/eval_single_model.json --output stats_plots

  # 多个模型对比
  python statistics_visual.py --input ../outputs/eval_model1.json ../outputs/eval_model2.json \\
                               --labels "Model-1" "Model-2" --output comparison_plots
        """
    )

    parser.add_argument(
        '--input', '-i',
        type=str,
        nargs='+',
        required=True,
        help='评估结果JSON文件路径(支持多个文件)'
    )

    parser.add_argument(
        '--labels', '-l',
        type=str,
        nargs='+',
        default=None,
        help='模型标签(与input文件一一对应)'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default='statistics_output',
        help='输出目录前缀'
    )

    args = parser.parse_args()

    # 检查文件
    for file_path in args.input:
        if not os.path.exists(file_path):
            print(f"错误: 文件不存在: {file_path}")
            return

    # 生成标签
    if args.labels:
        if len(args.labels) != len(args.input):
            print("错误: labels 数量必须与 input 文件数量一致")
            return
        labels = args.labels
    else:
        labels = [os.path.basename(f).replace('.json', '') for f in args.input]

    # 加载数据
    print(f"正在加载 {len(args.input)} 个评估结果文件...")
    stats_dict = {}
    eval_results_dict = {}

    for file_path, label in zip(args.input, labels):
        eval_results = load_eval_results(file_path)
        eval_results_dict[label] = eval_results
        stats_dict[label] = calculate_statistics(eval_results)
        print(f"  ✓ {label}: {len(eval_results)} 条记录")

    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)

    # 生成对比图
    comparison_path = os.path.join(args.output, 'comparison.png')
    plot_comparison_bar(stats_dict, comparison_path)

    # 为每个模型生成分布图
    for label, eval_results in eval_results_dict.items():
        distribution_path = os.path.join(args.output, f'distribution_{label}.png')
        plot_distribution_pie(eval_results, distribution_path, label)

    print(f"\n✓ 所有图表已生成至目录: {args.output}/")


if __name__ == '__main__':
    main()
