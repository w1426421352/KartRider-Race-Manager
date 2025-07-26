# 文件名: verify_backend.py

import os
import json
import time

# 确保在运行此脚本之前，您已经将我们之前讨论的
# db_manager.py 和 auth_manager.py 两个文件
# 存放在名为 'core' 的子文件夹中。
from core.db_manager import DBManager
from core.auth_manager import AuthManager

# --- 测试配置 ---
TEST_DB_PATH = 'data/verification_test.db'


def print_header(title):
    """打印一个漂亮的标题头"""
    print("\n" + "=" * 60)
    print(f"  {title.upper()}")
    print("=" * 60)


def print_result(description, success, details=""):
    """打印单项测试的结果"""
    status = "✅ 成功" if success else "❌ 失败"
    print(f"- {description}: {status}")
    if details:
        print(f"  > {details}")


def cleanup():
    """清理测试产生的临时文件"""
    print_header("清理环境")
    try:
        if os.path.exists(TEST_DB_PATH):
            # 在删除前，需要确保所有连接已关闭
            # DBManager 和 AuthManager 的单例可能还持有连接
            # 一个简单的方法是直接获取实例并调用close
            db_instance = DBManager()
            db_instance.close()

            # 给他一点时间确保文件锁已释放
            time.sleep(0.1)

            os.remove(TEST_DB_PATH)
            print_result("移除测试数据库文件", True)
        else:
            print("- 测试数据库文件不存在，无需清理。")
    except Exception as e:
        print_result("清理测试数据库时发生错误", False, str(e))


def run_verification():
    """执行所有验证步骤"""

    # --- 1. 数据库管理器 (DBManager) 验证 ---
    print_header("阶段一: 验证数据库管理器 (DBManager)")

    try:
        db_manager = DBManager(TEST_DB_PATH)
        print_result("初始化DBManager并创建数据库文件", True, f"数据库位于: {TEST_DB_PATH}")
    except Exception as e:
        print_result("初始化DBManager", False, str(e))
        return  # 如果数据库创建失败，后续测试无法进行

    # 测试规则集存取
    print("\n--- 测试规则集功能 ---")
    sample_ruleset = {
        "ruleset_name": "测试规则集",
        "map_selection_rules": [{"condition": "game_state.round_number == 1", "action": "admin_choice"}]
    }

    db_manager.save_ruleset("Test Ruleset", "Verifier", sample_ruleset)
    print_result("保存一个新的规则集 'Test Ruleset'", True)

    retrieved_ruleset_data = db_manager.get_ruleset_by_name("Test Ruleset")
    is_retrieved_ok = retrieved_ruleset_data is not None and retrieved_ruleset_data['ruleset'] == sample_ruleset
    print_result("根据名称取回规则集", is_retrieved_ok)

    all_rulesets = db_manager.get_all_rulesets()
    is_list_ok = len(all_rulesets) > 0 and all_rulesets[0]['name'] == "Test Ruleset"
    print_result("获取所有规则集列表", is_list_ok, f"当前库中规则集数量: {len(all_rulesets)}")

    # --- 2. 认证服务 (AuthManager) 验证 ---
    print_header("阶段二: 验证认证服务 (AuthManager)")

    try:
        auth_manager = AuthManager()
        print_result("初始化AuthManager", True)
    except Exception as e:
        print_result("初始化AuthManager", False, str(e))
        return

    print("\n--- 测试账号创建功能 ---")
    creation_success = auth_manager.create_account("player_alpha", "Password123", display_name="阿尔法") is not None
    print_result("创建新账号 'player_alpha'", creation_success)

    duplicate_creation_success = auth_manager.create_account("player_alpha", "another_pass") is None
    print_result("阻止创建同名账号 'player_alpha'", duplicate_creation_success)

    print("\n--- 测试密码验证功能 ---")
    verify_correct = auth_manager.verify_password("player_alpha", "Password123")
    print_result("用正确密码验证 'player_alpha'", verify_correct)

    verify_incorrect = not auth_manager.verify_password("player_alpha", "WRONG_PASSWORD")
    print_result("用错误密码验证 'player_alpha'", verify_incorrect)

    verify_nonexistent = not auth_manager.verify_password("non_existent_user", "any_pass")
    print_result("验证不存在的用户 'non_existent_user'", verify_nonexistent)

    print("\n--- 测试会话令牌(Token)流程 ---")
    if verify_correct:
        token = auth_manager.generate_session_token("player_alpha")
        token_generated = token is not None
        print_result("为 'player_alpha' 生成会话令牌", token_generated)

        user_from_token = auth_manager.verify_session_token(token)
        token_verified = user_from_token == "player_alpha"
        print_result("验证会话令牌", token_verified, f"通过令牌找到用户: {user_from_token}")

        auth_manager.invalidate_session_token(token)
        token_invalidated = auth_manager.verify_session_token(token) is None
        print_result("使会话令牌失效后再次验证", token_invalidated)
    else:
        print("因为密码验证失败，跳过令牌流程测试。")


if __name__ == '__main__':
    # 每次运行前都确保环境是干净的
    cleanup()

    try:
        run_verification()
    finally:
        # 无论测试成功与否，都尝试清理
        cleanup()