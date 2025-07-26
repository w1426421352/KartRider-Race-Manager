# 文件名: verify_backend_phase2.py (V2 - 修正版)

import os
import shutil
from core.map_manager import MapManager
from core.rule_engine import RuleEngine, GameState, PlayerState


def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title.upper()}")
    print("=" * 60)


# setup_dummy_xml_files 函数实际上已不再需要，因为我们是用真实文件测试
# 但为了脚本独立运行不报错，我们保留一个空函数
def setup_dummy_xml_files():
    """创建一个空的测试目录以供用户放入真实文件"""
    data_dir = 'data_test'
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def run_verification():
    print_header("阶段三: 验证地图管理服务 (MapManager)")

    test_data_dir = setup_dummy_xml_files()
    print(f"请确保您的真实XML文件已放入 '{test_data_dir}/' 目录。")

    map_manager = MapManager()
    aggregated_data = map_manager.import_maps_from_data_files(test_data_dir)

    print("\n--- 聚合结果抽样检查 (使用真实地图ID) ---")

    # 测试用例 1: 'village_R01'，在cn和tw文件中都存在
    village_map = aggregated_data.get('village_R01')
    if village_map and village_map['translations'].get('cn') and village_map['translations'].get('tw'):
        print("✅ 'village_R01' 的中/繁文名称已正确聚合。")
    else:
        print("❌ 'village_R01' 聚合失败。")

    # 测试用例 2: 'forest_I01'，在cn, tw, kr文件中都存在
    forest_map = aggregated_data.get('forest_I01')
    if forest_map and 'cn' in forest_map['translations'] and 'tw' in forest_map['translations'] and 'kr' in forest_map[
        'translations']:
        print("✅ 'forest_I01' (森林 木桶) 的中/繁/韩文名称已正确聚合。")
    else:
        print("❌ 'forest_I01' (森林 木桶) 聚合失败。")

    # 测试用例 3: 'korea_R01'，主要在kr文件中存在
    korea_map = aggregated_data.get('korea_R01')
    if korea_map and korea_map['translations'].get('kr'):
        print("✅ 'korea_R01' 韩文名称已正确解码并聚合。")
    else:
        print("❌ 'korea_R01' 聚合失败。")

    print_header("阶段四: 验证规则引擎 (RULEENGINE)")

    rule_engine = RuleEngine()

    players = [
        PlayerState(id="p1", name="老虎", rank=1, total_score=100),
        PlayerState(id="p2", name="辰辰", rank=2, total_score=90),
        PlayerState(id="p8", name="小草", rank=8, total_score=20, is_connected=False),
    ]
    sample_game_state = GameState(round_number=3, mode='individual', players=players)

    sample_ruleset = {
        "ruleset_name": "测试规则集",
        "map_selection_rules": [
            {
                "comment": "如果第一名掉线，则由第二名选图",
                "condition": "game_state.get_player_by_rank(1).is_connected == False",
                "action": {"type": "direct_choice", "who_selects": "game_state.get_player_by_rank(2)"}
            },
            {
                "comment": "常规情况：由第一名选图",
                "condition": "game_state.trigger == 'after_round'",
                "action": {"type": "direct_choice", "who_selects": "game_state.get_player_by_rank(1)"}
            }
        ]
    }

    print("\n--- 测试场景1: 常规情况 (第一名在线) ---")
    action1 = rule_engine.get_next_action(sample_ruleset, sample_game_state)
    if action1 and action1['who_selects'] == "game_state.get_player_by_rank(1)":
        print("✅ 规则引擎正确决策：由第一名选图。")
    else:
        print("❌ 规则引擎决策错误。")

    print("\n--- 测试场景2: 异常情况 (第一名掉线) ---")
    sample_game_state.get_player_by_rank(1).is_connected = False
    action2 = rule_engine.get_next_action(sample_ruleset, sample_game_state)
    if action2 and action2['who_selects'] == "game_state.get_player_by_rank(2)":
        print("✅ 规则引擎正确决策：由第二名选图。")
    else:
        print("❌ 规则引擎决策错误。")


if __name__ == '__main__':
    run_verification()
    if os.path.exists('data_test'):
        shutil.rmtree('data_test')
    print("\n测试目录已清理。")