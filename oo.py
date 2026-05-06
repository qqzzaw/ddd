import random

class ZhaJinHuaEngine:
    # 牌型定义
    TYPE_SPECIAL_235 = 0
    TYPE_SINGLE = 1
    TYPE_PAIR = 2
    TYPE_STRAIGHT = 3
    TYPE_FLUSH = 4
    TYPE_FLUSH_STRAIGHT = 5
    TYPE_LEOPARD = 6

    def __init__(self):
        self.points_map = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
                           '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

    def get_hand_info(self, hand):
        """
        解析手牌并返回：(牌型等级, 排序后的点数列表)
        hand: [('2', 'S'), ('3', 'H'), ('5', 'D')]
        """
        pts = sorted([self.points_map[c[0]] for c in hand], reverse=True)
        suits = [c[1] for c in hand]
        is_flush = len(set(suits)) == 1
        
        # 顺子判断 (包含 A23 最小顺子)
        is_straight = False
        if pts == [14, 3, 2]: # A23 逻辑
            is_straight = True
            compare_pts = [3, 2, 1] # 用于比较时设为最低
        elif pts[0] - pts[1] == 1 and pts[1] - pts[2] == 1:
            is_straight = True
            compare_pts = pts
        else:
            compare_pts = pts

        # 1. 豹子
        if len(set(pts)) == 1:
            return self.TYPE_LEOPARD, pts
        # 2. 顺金
        if is_flush and is_straight:
            return self.TYPE_FLUSH_STRAIGHT, compare_pts
        # 3. 金花
        if is_flush:
            return self.TYPE_FLUSH, pts
        # 4. 顺子
        if is_straight:
            return self.TYPE_STRAIGHT, compare_pts
        # 5. 对子
        if len(set(pts)) == 2:
            pair_val = max(set(pts), key=pts.count)
            single_val = min(set(pts), key=pts.count)
            return self.TYPE_PAIR, [pair_val, single_val]
        # 6. 特殊 235 (不同花色)
        if set(pts) == {5, 3, 2} and not is_flush:
            return self.TYPE_SPECIAL_235, pts
        # 7. 单张
        return self.TYPE_SINGLE, pts

    def compare_hands(self, player_a, player_b, is_a_initiator=True):
        """
        核心比较逻辑
        player_a/b 格式: {'hand': [...], 'name': 'xxx'}
        返回: 赢家数据对象
        """
        type_a, val_a = self.get_hand_info(player_a['hand'])
        type_b, val_b = self.get_hand_info(player_b['hand'])

        # 规则细节：仅当场上有豹子时，235 > 豹子
        if type_a == self.TYPE_SPECIAL_235 and type_b == self.TYPE_LEOPARD:
            return player_a
        if type_b == self.TYPE_SPECIAL_235 and type_a == self.TYPE_LEOPARD:
            return player_b
        
        # 235若没遇到豹子，就是最小单张
        type_a_final = self.TYPE_SINGLE if type_a == self.TYPE_SPECIAL_235 else type_a
        type_b_final = self.TYPE_SINGLE if type_b == self.TYPE_SPECIAL_235 else type_b

        if type_a_final > type_b_final: return player_a
        if type_a_final < type_b_final: return player_b

        # 牌型相同时比点数
        for a, b in zip(val_a, val_b):
            if a > b: return player_a
            if a < b: return player_b

        # 细节：全等则发起比牌方输 (先手负)
        return player_b if is_a_initiator else player_a

class GameSession:
    def __init__(self, player_names, ante=10):
        self.engine = ZhaJinHuaEngine()
        self.players = [{
            'name': name, 
            'chips': 1000, 
            'is_seen': False, 
            'is_folded': False,
            'is_out': False, # 比牌输掉的人
            'hand': []
        } for name in player_names]
        self.pot = 0
        self.ante = ante
        self.current_unit = ante # 闷家单注基准
        self.round_count = 1

    def start_game(self):
        # 强制底注
        for p in self.players:
            p['chips'] -= self.ante
            self.pot += self.ante
        print(f"游戏开始，底池: {self.pot}")

    def get_bet_amount(self, player, action_type="call"):
        """
        细节：看家投入必须是闷家的2倍
        action_type: "call" (跟) 或 "compare" (比)
        """
        factor = 2 if player['is_seen'] else 1
        if action_type == "compare":
            return self.current_unit * factor * 2 # 比牌费是当前注的2倍
        return self.current_unit * factor

    def handle_compare(self, initiator_idx, target_idx):
        """发起比牌流程"""
        p1 = self.players[initiator_idx]
        p2 = self.players[target_idx]
        
        # 1. 检查比牌门槛（细节：第2轮后，支付双倍费用）
        if self.round_count < 2:
            return "未到比牌轮数"
        
        cost = self.get_bet_amount(p1, "compare")
        p1['chips'] -= cost
        self.pot += cost
        
        # 2. 比较
        winner = self.engine.compare_hands(p1, p2, is_a_initiator=True)
        loser = p2 if winner == p1 else p1
        loser['is_out'] = True
        
        # 3. 喜钱细节 (如果是豹子/顺金赢)
        hand_type, _ = self.engine.get_hand_info(winner['hand'])
        bonus_msg = ""
        if hand_type >= self.engine.TYPE_FLUSH_STRAIGHT:
            bonus_msg = "触发喜钱！其他玩家需额外支付一份筹码。"

        return f"比牌结束，{winner['name']} 胜，{loser['name']} 出局。{bonus_msg}"

# --- 模拟运行 ---
game = GameSession(["玩家A", "玩家B", "玩家C"])
game.start_game()

# 模拟A闷牌，B看牌
game.players[1]['is_seen'] = True 
print(f"B看牌了，他跟注需要支付: {game.get_bet_amount(game.players[1])}")

# 模拟发放特殊牌型测试逻辑
game.players[0]['hand'] = [('A', 'S'), ('A', 'H'), ('A', 'D')] # 豹子AAA
game.players[1]['hand'] = [('2', 'S'), ('3', 'H'), ('5', 'D')] # 不同花色235
game.round_count = 2 # 进入第二轮

result = game.handle_compare(1, 0) # 玩家B(235) 向 玩家A(豹子) 发起比牌
print(result) # 预期输出：玩家B 胜 (235克制豹子)
