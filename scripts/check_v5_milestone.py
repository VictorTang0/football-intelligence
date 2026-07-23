import json
import os
import re

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blueprint_path = os.path.join(base_dir, "data", "v5_milestone_blueprint.json")
weights_path = os.path.join(base_dir, "data", "weights.json")
history_path = os.path.join(base_dir, "data", "history.json")

def audit_v5_milestone():
    if not os.path.exists(blueprint_path):
        print("❌ Error: v5_milestone_blueprint.json not found!")
        return

    with open(blueprint_path, "r", encoding="utf-8") as f:
        blueprint = json.load(f)

    weights_version = "v1.0"
    if os.path.exists(weights_path):
        with open(weights_path, "r", encoding="utf-8") as f:
            w_data = json.load(f)
            weights_version = w_data.get("version", "v1.0")

    dir_acc = 0.0
    score_acc = 0.0
    total_matches = 0
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            h_data = json.load(f)
            total_matches = h_data.get("total_predictions", 0)
            dir_acc = h_data.get("accuracy_rate", 0.0)
            score_acc = h_data.get("score_accuracy_rate", 0.0)

    target_dir_acc = blueprint["benchmarks"]["accuracy_targets"]["direction_accuracy_target"]
    target_score_acc = blueprint["benchmarks"]["accuracy_targets"]["score_accuracy_target"]

    print("=" * 60)
    print("🏆 MATCH IQ v5.0 里程碑对比与验收审计报告 (v5.0 Audit Report)")
    print("=" * 60)
    print(f"📌 当前模型版本: {weights_version} (标杆目标: v5.0)")
    print(f"📊 已验证完赛场次: {total_matches} 场")
    print(f"🎯 胜平负/方向准确率: {dir_acc * 100:.2f}% (v5.0 标杆目标: {target_dir_acc * 100:.1f}%)")
    print(f"🎯 最可能比分命中率: {score_acc * 100:.2f}% (v5.0 标杆目标: {target_score_acc * 100:.1f}%)")
    print("-" * 60)

    ver_match = re.search(r'v(\d+)\.(\d+)', weights_version)
    current_major = int(ver_match.group(1)) if ver_match else 1

    if current_major < 5:
        print(f"ℹ️ 当前版本为 {weights_version}，尚未达到 v5.0 终极里程碑。已预先比对基准数据。")
        print("💡 建议行动：继续积累完赛样本，并在演化过程中逐步引入 Meta-RL 与全流式资金监控。")
        print("=" * 60)
        return

    # Compare targets for v5.0+
    exceeded_items = []
    fell_short_items = []

    if dir_acc >= target_dir_acc:
        exceeded_items.append(f"方向准确率到达 {dir_acc * 100:.2f}%，超过/达成 65.0% 标杆目标！")
    else:
        fell_short_items.append(f"方向准确率为 {dir_acc * 100:.2f}%，距离 65.0% 标杆目标尚差 {(target_dir_acc - dir_acc) * 100:.2f}%。")

    if score_acc >= target_score_acc:
        exceeded_items.append(f"比分命中率到达 {score_acc * 100:.2f}%，超过/达成 30.0% 标杆目标！")
    else:
        fell_short_items.append(f"比分命中率为 {score_acc * 100:.2f}%，距离 30.0% 标杆目标尚差 {(target_score_acc - score_acc) * 100:.2f}%。")

    print("\n📋 详细比对结论 (Detailed Comparison Results):")
    if exceeded_items:
        print("✅ 达成/超越指标:")
        for item in exceeded_items:
            print(f"   • {item}")
    if fell_short_items:
        print("⚠️ 未达标指标:")
        for item in fell_short_items:
            print(f"   • {item}")

    print("\n🚀 终极评估与下一步指导建议 (Evaluation & Next Action):")
    if not fell_short_items:
        print("🎉 结论：项目已全面超越/达到 v5.0 的预设终极标杆！")
        print("🛠️ 应该怎么做：建议开启 v6.0 全球实盘自动化交易控制台计划，扩展至更多微观二级联赛。")
    else:
        print("⚡ 结论：项目已进化至 v5.0 版本号，但在部分量化指标上仍有未达标项。")
        print("🛠️ 应该怎么做：")
        print("   1. 检查是否存在诱盘拦截失效或某些特殊联赛降维不够；")
        print("   2. 进一步引入必发/Pinnacle 资金背离剪刀差指标（Orderflow Tracker）；")
        print("   3. 调整 Poisson 比分期望参数，压缩比分高频泛化区间。")

    print("=" * 60)

if __name__ == "__main__":
    audit_v5_milestone()
