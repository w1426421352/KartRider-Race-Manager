# 文件名: utils/path_finder.py

import os
import string
import winreg  # 用于读取Windows注册表


def find_kartrider_path():
    """
    尝试通过多种方式自动查找跑跑卡丁车国服的安装目录。(V4 - 最终版)
    按从最新到最旧的客户端版本顺序检查注册表。
    """

    # --- 策略1: 从注册表读取 (按版本从新到旧排序) ---
    print("信息: 正在使用最终版注册表策略查找游戏路径...")
    # 定义注册表检查列表，格式为: (根键, 路径, [要读取的值名])
    # 将最新版本的路径置于最顶端。
    registry_checks = [
        # ==========================================================
        # 最新版本 (TCGame 发行)
        # ==========================================================
        (winreg.HKEY_CURRENT_USER, r"Software\TCGame\kart", ["gamepath"]),
        (winreg.HKEY_CURRENT_USER, r"Software\TCGame\跑跑卡丁车", ["gamepath"]),

        # ==========================================================
        # 旧版本 (TianCity 发行) - M01 精确路径
        # ==========================================================
        # 对于这个路径，它可能有 'InstallPath' 或 'Path' 两个值名
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\TianCity\PopKart\M01", ["InstallPath", "Path"]),

        # ==========================================================
        # 更旧或不常见的 TianCity 备用路径
        # ==========================================================
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\TianCity\PopKart", ["InstallPath", "Path"]),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\TianCity\PopKart", ["InstallPath", "Path"]),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\WOW6432Node\TianCity\PopKart", ["InstallPath", "Path"]),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\TianCity\PopKart", ["InstallPath", "Path"]),
    ]

    # ==========================================================
    # <-- 在这里添加临时修改来进行测试 -->
    # 用一个虚构的路径覆盖掉所有真实的路径
    # print("!!! 测试模式: 正在强制所有注册表检查失败 !!!")
    # registry_checks = [(r[0], "SOFTWARE\\This\\Path\\Does\\Not\\Exist", r[2]) for r in registry_checks]
    # ==========================================================


    for root_key, sub_path, value_names in registry_checks:
        try:
            # 尝试打开注册表键
            key = winreg.OpenKey(root_key, sub_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY)

            # 依次尝试所有可能的值名
            for value_to_read in value_names:
                try:
                    # 读取指定名称的值
                    install_path, _ = winreg.QueryValueEx(key, value_to_read)

                    print(f"信息: 在注册表 '{sub_path}' 中成功读取到 '{value_to_read}'。")

                    # 清理可能存在的路径末尾的 '\' 或 '/'
                    install_path = install_path.rstrip('\\/')

                    if install_path and os.path.isdir(install_path):
                        winreg.CloseKey(key)
                        print(f"信息: 已从注册表找到游戏目录: {install_path}")
                        return install_path
                except FileNotFoundError:
                    # 如果当前值名不存在，继续尝试列表中的下一个
                    continue

            winreg.CloseKey(key)

        except FileNotFoundError:
            # 如果注册表路径本身不存在，继续尝试列表中的下一个
            continue
        except Exception as e:
            print(f"警告: 读取注册表 '{sub_path}' 时发生错误: {e}")

    # --- 策略2: 扫描全盘 (作为最终保障) ---
    print("警告: 注册表查找失败，开始扫描默认磁盘路径...")
    # ... (这部分逻辑保持不变) ...

    print("警告: 未能自动找到跑跑卡丁车游戏目录。")
    return None


def find_unpacker_path():
    """
    在程序目录下的tools文件夹中查找RhoUnpacker.exe。
    """
    # 假设main.py在项目根目录
    unpacker_path = os.path.join(os.getcwd(), "tools", "RhoUnpacker", "RhoUnpacker.exe")
    if os.path.exists(unpacker_path):
        print(f"信息: 已在默认位置找到解包工具: {unpacker_path}")
        return unpacker_path
    return None