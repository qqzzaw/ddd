import os
import random
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
# 关键：必须要用 eventlet 或 gevent 模式支持多人联机
socketio = SocketIO(app, cors_allowed_origins="*")

# --- 判定引擎：235杀豹子、A23最小顺子、先手负 ---
class GameEngine:
    POINTS = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    
    @staticmethod
    def get_type(hand):
        pts = sorted([GameEngine.POINTS[c['p']] for c in hand], reverse=True)
        suits = [c['s'] for c in hand]
        is_flush = len(set(suits)) == 1
        is_straight = False
        comp_pts = pts
        if pts == [14, 3, 2]: # A23顺子
            is_straight = True
            comp_pts = [3, 2, 1] # 设为最小
        elif pts[0]-pts[1] == 1 and pts[1]-pts[2] == 1:
            is_straight = True

        if len(set(pts)) == 1: return 6, pts  # 豹子
        if is_flush and is_straight: return 5, comp_pts # 顺金
        if is_flush: return 4, pts # 金花
        if is_straight: return 3, comp_pts # 顺子
        if len(set(pts)) == 2:
            p = max(set(pts), key=pts.count)
            s = min(set(pts), key=pts.count)
            return 2, [p, s] # 对子
        if set(pts) == {5, 3, 2} and not is_flush: return 0, pts # 特殊235
        return 1, pts # 单张

    @staticmethod
    def compare(h1, h2, is_h1_initiator=True):
        t1, v1 = GameEngine.get_type(h1)
        t2, v2 = GameEngine.get_type(h2)
        if t1 == 0 and t2 == 6: return 1  # 235杀豹子
        if t2 == 0 and t1 == 6: return -1
        t1_f = 1 if t1 == 0 else t1
        t2_f = 1 if t2 == 0 else t2
        if t1_f != t2_f: return 1 if t1_f > t2_f else -1
        for a, b in zip(v1, v2):
            if a != b: return 1 if a > b else -1
        return -1 if is_h1_initiator else 1 # 先手负

# --- 房间与流程控制 ---
rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def join(data):
    rid = data.get('room', 'default')
    name = data.get('name', '匿名王子')
    join_room(rid)
    if rid not in rooms:
        rooms[rid] = {"pot": 0, "players": [], "turn": 0}
    rooms[rid]["players"].append({
        "sid": request.sid, "name": name, "chips": 1000, 
        "hand": [], "is_seen": False, "status": "active"
    })
    sync(rid)

def sync(rid):
    room = rooms[rid]
    for p in room["players"]:
        # 数据脱敏推送：别人看不见你的牌
        data = {
            "pot": room["pot"],
            "players": [{
                "name": o["name"], "chips": o["chips"], "status": o["status"],
                "hand": o["hand"] if (o["sid"] == p["sid"] and o["is_seen"]) else ["?", "?", "?"]
            } for o in room["players"]]
        }
        socketio.emit('update', data, room=p["sid"])

if __name__ == '__main__':
    # 核心：读取云服务器分配的随机端口
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
