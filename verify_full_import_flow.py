# 文件名: verify_full_import_flow.py

import os
import shutil
from core.db_manager import DBManager
from core.map_manager import MapManager


def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title.upper()}")
    print("=" * 60)


def print_result(description, success, details=""):
    status = "✅ 成功" if success else "❌ 失败"
    print(f"- {description}: {status}")
    if details:
        print(f"  > {details}")


# --- !!! 关键配置 !!! ---
# --- 请在运行前，根据您的实际情况修改以下三个路径 ---

# 1. 跑跑卡丁车游戏主目录 (例如: "C:/Program Files (x86)/TianCity/PopKart")
GAME_PATH = "C:/Program Files (x86)/TianCity/PopKart/M01"

# 2. 我们编译好的 RhoUnpacker.exe 文件的完整路径
#    (例如: "C:/path/to/RhoUnpacker/bin/Release/net8.0/win-x64/publish/RhoUnpacker.exe")
UNPACKER_PATH = "C:/Users/asdf/PycharmProjects/kart_counter/RhoUnpacker.exe"

# 3. 测试用的数据库文件路径
TEST_DB_PATH = "data/full_flow_test.db"


def run_verification():
    print_header("最终端到端导入流程验证")

    if "YOUR/PATH/HERE" in GAME_PATH or "YOUR/UNPACKER/PATH/HERE" in UNPACKER_PATH:
        print("错误: 请先在脚本中设置正确的 GAME_PATH 和 UNPACKER_PATH 路径！")
        return

    # 1. 初始化环境
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    db_manager = DBManager(TEST_DB_PATH)
    map_manager = MapManager()

    # 2. 执行完整的导入流程
    map_count = map_manager.import_maps_from_game_files(GAME_PATH, UNPACKER_PATH)

    # 3. 从数据库中取回数据并验证
    print("\n--- 从数据库查询并验证聚合结果 ---")

    all_maps_structured = db_manager.get_all_maps_structured_by_theme()

    # 验证点1：是否成功导入了数据
    print_result("数据成功导入数据库", map_count > 0 and len(all_maps_structured) > 0,
                 f"数据库中总计 {map_count} 张地图。")

    # 验证点2：检查一张众所周知的地图的多语言名称
    village_maps = all_maps_structured.get("village", [])
    village_r01 = next((m for m in village_maps if m['id'] == 'village_R01'), None)

    if village_r01:
        cn_ok = village_r01.get('name_cn') == '城镇 高速公路'
        tw_ok = village_r01.get('name_tw') == '城鎮 高速公路'
        kr_ok = '빌리지' in (village_r01.get('name_kr') or '')
        print_result("验证 'village_R01' 多语言名称", cn_ok and tw_ok and kr_ok,
                     f"CN: {village_r01.get('name_cn')}, TW: {village_r01.get('name_tw')}, KR: {village_r01.get('name_kr')}")
    else:
        print_result("验证 'village_R01' 多语言名称", False, "在数据库中未找到该地图。")


if __name__ == '__main__':
    run_verification()
