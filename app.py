import os
import random
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
# 必须配置，否则多人联机会卡死
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# --- 判定引擎：100% 还原你的规则 ---
class GameEngine:
    POINTS = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    
    @staticmethod
    def get_hand_type(hand):
        # 点数排序
        pts = sorted([GameEngine.POINTS[c['p']] for c in hand], reverse=True)
        suits = [c['s'] for c in hand]
        is_flush = len(set(suits)) == 1
        
        # 顺子判定 (包含 A23 最低顺子细节)
        is_straight = False
        comp_pts = pts
        if pts == [14, 3, 2]: # A23 
            is_straight = True
            comp_pts = [3, 2, 1] # 规则：A23是最小顺子
        elif pts[0]-pts[1] == 1 and pts[1]-pts[2] == 1:
            is_straight = True

        # 1. 豹子
        if len(set(pts)) == 1: return 6, pts
        # 2. 顺金
        if is_flush and is_straight: return 5, comp_pts
        # 3. 金花
        if is_flush: return 4, pts
        # 4. 顺子
        if is_straight: return 3, comp_pts
        # 5. 对子
        if len(set(pts)) == 2:
            p = max(set(pts), key=pts.count)
            s = min(set(pts), key=pts.count)
            return 2, [p, s]
        # 6. 特殊235 (不同花色)
        if set(pts) == {5, 3, 2} and not is_flush: return 0, pts
        # 7. 单张
        return 1, pts

    @staticmethod
    def compare(h1, h2, is_h1_initiator=True):
        t1, v1 = GameEngine.get_hand_type(h1)
        t2, v2 = GameEngine.get_hand_type(h2)
        # 235 杀 豹子 细节
        if t1 == 0 and t2 == 6: return 1
        if t2 == 0 and t1 == 6: return -1
        # 非对阵豹子时 235 是最小单张
        t1_f = 1 if t1 == 0 else t1
        t2_f = 1 if t2 == 0 else t2
        if t1_f != t2_f: return 1 if t1_f > t2_f else -1
        # 同牌型比点数
        for a, b in zip(v1, v2):
            if a != b: return 1 if a > b else -1
        # 平牌先手负 细节
        return -1 if is_h1_initiator else 1

# --- 多人房间管理 ---
rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    rid = data.get('room', 'default')
    join_room(rid)
    if rid not in rooms:
        rooms[rid] = {"pot": 0, "players": [], "turn": 0}
    rooms[rid]["players"].append({
        "sid": request.sid, "name": data.get('name', '玩家'),
        "chips": 1000, "hand": [], "is_seen": False, "status": "active"
    })
    sync(rid)

def sync(rid):
    room = rooms[rid]
    for p in room["players"]:
        socketio.emit('update', {
            "pot": room["pot"],
            "players": [{
                "name": o["name"], "chips": o["chips"], "status": o["status"],
                "hand": o["hand"] if (o["sid"] == p["sid"] and o["is_seen"]) else ["?", "?", "?"]
            } for o in room["players"]]
        }, room=p["sid"])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
