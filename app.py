import os
import random
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
# 必须使用 eventlet 模式确保多人联机稳定
socketio = SocketIO(app, cors_allowed_origins="*")

# --- 核心引擎：100% 还原你提到的所有规矩 ---
class ZhaJinHuaEngine:
    POINTS = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    
    @staticmethod
    def get_hand_info(hand):
        # 细节：点数转换
        pts = sorted([ZhaJinHuaEngine.POINTS[c['p']] for c in hand], reverse=True)
        suits = [c['s'] for c in hand]
        is_flush = len(set(suits)) == 1
        
        # 细节：A23 顺子判定
        is_straight = False
        comp_pts = pts
        if pts == [14, 3, 2]: 
            is_straight = True
            comp_pts = [3, 2, 1] # 强制降级为最低顺子
        elif pts[0]-pts[1] == 1 and pts[1]-pts[2] == 1:
            is_straight = True

        # 判定牌型等级
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
        t1, v1 = ZhaJinHuaEngine.get_hand_info(h1)
        t2, v2 = ZhaJinHuaEngine.get_hand_info(h2)

        # 细节：235 vs 豹子 (反杀)
        if t1 == 0 and t2 == 6: return 1
        if t2 == 0 and t1 == 6: return -1
        
        # 非对阵豹子时，235 只是最小单张
        t1_final = 1 if t1 == 0 else t1
        t2_final = 1 if t2 == 0 else t2

        if t1_final != t2_final: return 1 if t1_final > t2_final else -1
        
        # 牌型相同比点数
        for a, b in zip(v1, v2):
            if a != b: return 1 if a > b else -1
            
        # 细节：平牌先手负
        return -1 if is_h1_initiator else 1

# --- 游戏房间管理 ---
rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    rid = data.get('room', 'default')
    join_room(rid)
    if rid not in rooms:
        rooms[rid] = {"pot": 0, "players": [], "turn": 0, "unit": 10}
    
    # 细节：初始筹码与状态
    rooms[rid]["players"].append({
        "sid": request.sid, "name": data.get('name', '玩家'), 
        "chips": 1000, "hand": [], "is_seen": False, "status": "active"
    })
    sync(rid)

def sync(rid):
    room = rooms[rid]
    for p in room["players"]:
        # 细节：防作弊脱敏，只发玩家自己的牌
        clean_players = []
        for o in room["players"]:
            clean_players.append({
                "name": o["name"], "chips": o["chips"], "status": o["status"], "is_seen": o["is_seen"],
                "hand": o["hand"] if (o["sid"] == p["sid"] and o["is_seen"]) else ["?", "?", "?"]
            })
        socketio.emit('update', {"pot": room["pot"], "players": clean_players, "turn": room["turn"]}, room=p["sid"])

if __name__ == '__main__':
    # 细节：必须适配云端 PORT
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
