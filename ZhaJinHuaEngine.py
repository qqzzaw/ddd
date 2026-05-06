import random
import time

class ZhaJinHuaPro:
    """深度优化的核心判定与多人逻辑管理器"""
    
    def __init__(self):
        self.POINTS = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
                       '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        # 牌型等级定义
        self.LEVELS = {
            "LEOPARD": 6, "FLUSH_STRAIGHT": 5, "FLUSH": 4, 
            "STRAIGHT": 3, "PAIR": 2, "SINGLE": 1, "SPECIAL_235": 0
        }

    def evaluate_hand(self, hand):
        """核心细节1：牌型精确评估 (含A23、235逻辑)"""
        pts = sorted([self.POINTS[c['p']] for c in hand], reverse=True)
        suits = [c['s'] for c in hand]
        is_flush = len(set(suits)) == 1
        
        # 细节：A23顺子判定 (在顺子中A可最大也可最小)
        is_straight = False
        comp_pts = pts
        if pts == [14, 3, 2]: # A23
            is_straight = True
            comp_pts = [3, 2, 1] # 降级为最小顺子
        elif pts[0]-pts[1] == 1 and pts[1]-pts[2] == 1:
            is_straight = True

        # 判定牌型等级
        if len(set(pts)) == 1: return self.LEVELS["LEOPARD"], pts
        if is_flush and is_straight: return self.LEVELS["FLUSH_STRAIGHT"], comp_pts
        if is_flush: return self.LEVELS["FLUSH"], pts
        if is_straight: return self.LEVELS["STRAIGHT"], comp_pts
        if len(set(pts)) == 2:
            pair = max(set(pts), key=pts.count)
            single = min(set(pts), key=pts.count)
            return self.LEVELS["PAIR"], [pair, single]
        if set(pts) == {5, 3, 2} and not is_flush: 
            return self.LEVELS["SPECIAL_235"], pts
        return self.LEVELS["SINGLE"], pts

    def compare_players(self, p1, p2, initiator_sid):
        """核心细节2：比牌判定 (235克豹子、先手负)"""
        t1, v1 = self.evaluate_hand(p1['hand'])
        t2, v2 = self.evaluate_hand(p2['hand'])

        # 特殊细节：235 vs 豹子
        if t1 == self.LEVELS["SPECIAL_235"] and t2 == self.LEVELS["LEOPARD"]: return p1
        if t2 == self.LEVELS["SPECIAL_235"] and t1 == self.LEVELS["LEOPARD"]: return p2
        
        # 常规转换：235若没遇豹子则为最小单张
        t1_final = self.LEVELS["SINGLE"] if t1 == self.LEVELS["SPECIAL_235"] else t1
        t2_final = self.LEVELS["SINGLE"] if t2 == self.LEVELS["SPECIAL_235"] else t2

        if t1_final > t2_final: return p1
        if t1_final < t2_final: return p2

        # 细节：牌型点数完全一致，发起比牌者输 (先手负)
        for a, b in zip(v1, v2):
            if a > b: return p1
            if a < b: return p2
            
        return p2 if p1['sid'] == initiator_sid else p1

class MultiplayerRoom:
    """多人房间控制器 (支持多人轮转、状态同步、筹码倍率)"""
    
    def __init__(self, room_id, ante=10):
        self.room_id = room_id
        self.players = []       # 玩家对象列表
        self.pot = 0            # 底池
        self.current_bet = ante # 闷家基准单注
        self.active_idx = 0     # 当前该谁行动
        self.game_started = False
        self.engine = ZhaJinHuaPro()

    def sync_state(self, viewer_sid):
        """核心细节3：多人局脱敏推送 (防作弊)"""
        return {
            "room_id": self.room_id,
            "pot": self.pot,
            "active_name": self.players[self.active_idx]['name'] if self.game_started else "",
            "players": [{
                "name": p['name'],
                "chips": p['chips'],
                "is_seen": p['is_seen'],
                "status": p['status'],
                # 只有自己且看牌后才下发真实牌值，否则全部隐藏
                "hand": p['hand'] if p['sid'] == viewer_sid and p['is_seen'] else ["?", "?", "?"]
            } for p in self.players]
        }

    def perform_action(self, sid, action, amount=None):
        """核心细节4：多人下注逻辑 (闷看换算、比牌费)"""
        p = next(p for p in self.players if p['sid'] == sid)
        
        # 1. 倍率判定
        factor = 2 if p['is_seen'] else 1
        
        if action == "call":
            cost = self.current_bet * factor
            p['chips'] -= cost
            self.pot += cost
        elif action == "seen":
            p['is_seen'] = True
        elif action == "fold":
            p['status'] = "folded"
        elif action == "compare":
            # 细节：比牌费为当前注的2倍
            cost = self.current_bet * factor * 2
            p['chips'] -= cost
            self.pot += cost
            # ... 此处省略具体比牌对象选择逻辑 ...

        self.next_turn()

    def next_turn(self):
        """自动跳过弃牌和输家，寻找下一位操作者"""
        for _ in range(len(self.players)):
            self.active_idx = (self.active_idx + 1) % len(self.players)
            if self.players[self.active_idx]['status'] == "active":
                break

    def check_bonus(self, winner_p):
        """核心细节5：喜钱逻辑"""
        t, _ = self.engine.evaluate_hand(winner_p['hand'])
        if t >= 5: # 顺金或豹子
            return f"触发喜钱！{winner_p['name']} 额外获得奖励"
        return None
