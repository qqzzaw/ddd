import os
import random
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- 核心引擎：100% 还原你提到的规则 ---
class GameEngine:
    POINTS = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    
    @staticmethod
    def get_hand_info(hand):
        """解析牌型：豹子、顺金、金花、顺子、对子、235"""
        pts = sorted([GameEngine.POINTS[c['p']] for c in hand], reverse=True)
        is_flush = len(set(c['s'] for c in hand)) == 1
        
        # 顺子逻辑 (含 A23 细节)
        is_straight = False
        comp_pts = pts
        if pts == [14, 3, 2]: # A23
            is_straight = True
            comp_pts = [3, 2, 1] # 规则：A23是最小顺子
        elif pts[0]-pts[1] == 1 and pts[1]-pts[2] == 1:
            is_straight = True

        if len(set(pts)) == 1: return 6, pts  # 豹子
        if is_flush and is_straight: return 5, comp_pts # 顺金
        if is_flush: return 4, pts # 金花
        if is_straight: return 3, comp_pts # 顺子
        if len(set(pts)) == 2:
            pair = max(set(pts), key=pts.count)
            single = min(set(pts), key=pts.count)
            return 2, [pair, single] # 对子
        if set(pts) == {5, 3, 2} and not is_flush: return 0, pts # 特殊235
        return 1, pts # 单张

    @staticmethod
    def compare(p1_hand, p2_hand, p1_is_initiator=True):
        """胜负判定：处理235克豹子、先手负细节"""
        t1, v1 = GameEngine.get_hand_info(p1_hand)
        t2, v2 = GameEngine.get_hand_info(p2_hand)

        # 细节：235 vs 豹子
        if t1 == 0 and t2 == 6: return 1
        if t2 == 0 and t1 == 6: return -1
        
        # 235非遇豹子按最小单张算
        t1_f = 1 if t1 == 0 else t1
        t2_f = 1 if t2 == 0 else t2

        if t1_f != t2_f: return 1 if t1_f > t2_f else -1
        
        # 牌型相同比点数
        for a, b in zip(v1, v2):
            if a != b: return 1 if a > b else -1
            
        # 细节：平牌先手负
        return -1 if p1_is_initiator else 1

# --- 房间状态管理 (多人模式) ---
rooms = {}

class Room:
    def __init__(self, room_id):
        self.id = room_id
        self.players = [] # 每个元素: {sid, name, chips, hand, is_seen, status}
        self.pot = 0
        self.current_bet = 10
        self.turn = 0
        self.round = 1

    def sync(self):
        """防作弊推送：只给玩家发自己的牌"""
        for p in self.players:
            # 脱敏后的玩家列表
            clean_players = []
            for other in self.players:
                clean_players.append({
                    "name": other['name'],
                    "chips": other['chips'],
                    "is_seen": other['is_seen'],
                    "status": other['status'],
                    "hand": other['hand'] if (other['sid'] == p['sid'] and other['is_seen']) else ["?", "?", "?"]
                })
            socketio.emit('update', {"pot": self.pot, "players": clean_players, "turn": self.turn}, room=p['sid'])

# --- 路由与Socket接口 ---
@app.route('/')
def index():
    return "<h1>服务器已部署，请连接WebSocket。</h1>"

@socketio.on('join')
def on_join(data):
    rid = data.get('room', 'default')
    join_room(rid)
    if rid not in rooms: rooms[rid] = Room(rid)
    rooms[rid].players.append({
        "sid": request.sid, "name": data['name'], "chips": 1000, 
        "hand": [], "is_seen": False, "status": "active"
    })
    rooms[rid].sync()

@socketio.on('action')
def on_action(data):
    # 处理：跟注(call)、看牌(seen)、比牌(compare)
    # 此处接入逻辑判断（根据闷家/看家倍率扣除筹码）
    pass

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
