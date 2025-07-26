# 文件名: core/rule_engine.py

from asteval import Interpreter
from dataclasses import dataclass, field
from typing import List, Optional


# --- 定义用于承载比赛状态的数据结构 ---

@dataclass
class PlayerState:
    """单个选手在某一时刻的状态"""
    id: str
    name: str
    rank: int
    total_score: int
    is_connected: bool = True
    team_id: Optional[str] = None


@dataclass
class GameState:
    """完整的比赛实时状态，将作为API暴露给规则表达式"""
    round_number: int
    mode: str  # 'individual' or 'team'
    players: List[PlayerState]
    trigger: str = 'after_round'  # 触发时机

    def get_player_by_rank(self, rank: int) -> Optional[PlayerState]:
        """根据排名获取选手对象"""
        for p in self.players:
            if p.rank == rank:
                return p
        return None

    # 未来可以添加更多便捷方法，如 get_winning_team(), get_player_by_name() 等


class RuleEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RuleEngine, cls).__new__(cls)
            # 创建一个安全的ASTEVAL解释器实例
            cls._instance.interp = Interpreter()
        return cls._instance

    def _evaluate_expression(self, expression_str: str, game_state: GameState) -> bool:
        """
        在安全环境中执行单个条件表达式。
        """
        # 将 game_state 对象注入到解释器的"符号表"中
        # 这样表达式字符串中就可以直接使用 'game_state' 这个变量了
        self.interp.symtable['game_state'] = game_state
        try:
            result = self.interp.eval(expression_str)
            return bool(result)
        except Exception as e:
            print(f"错误: 规则表达式 '{expression_str}' 执行失败: {e}")
            return False

    def get_next_action(self, ruleset: dict, game_state: GameState):
        """
        遍历规则集，找到第一个满足条件的规则，并返回其动作。
        这是对外暴露的主接口。
        """
        rules = ruleset.get("map_selection_rules", [])

        for rule in rules:
            condition = rule.get("condition")
            if not condition:
                continue

            if self._evaluate_expression(condition, game_state):
                # 找到第一个满足条件的规则，立即返回其动作
                print(f"规则匹配成功: {rule.get('comment', '无注释')}")

                # 此处可以增加对 action 的解析和标准化，例如递归处理 if-then-else
                return rule.get("action")

        print("未匹配到任何规则，将使用默认动作。")
        return {"type": "default", "message": "无匹配规则，由管理员选图"}