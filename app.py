from flask import Flask, render_template, jsonify, request
import random

app = Flask(__name__)

# --- 之前的核心算法逻辑 (已适配 Web 状态) ---
class GameCore:
    POINTS = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    
    @staticmethod
    def analyze(hand):
        # hand: [{'p': 'A', 's': 'S'}, ...]
        pts = sorted([GameCore.POINTS[c['p']] for c in hand], reverse=True)
        suits = [c['s'] for c in hand]
        is_flush = len(set(suits)) == 1
        
        # 顺子逻辑 (包含 A23)
        is_straight = False
        comp_pts = pts
        if pts == [14, 3, 2]: 
            is_straight = True
            comp_pts = [3, 2, 1] # A23 设为最小
        elif pts[0]-pts[1] == 1 and pts[1]-pts[2] == 1:
            is_straight = True

        if len(set(pts)) == 1: return 6, pts # 豹子
        if is_flush and is_straight: return 5, comp_pts # 顺金
        if is_flush: return 4, pts # 金花
        if is_straight: return 3, comp_pts # 顺子
        if len(set(pts)) == 2:
            pair = max(set(pts), key=pts.count)
            single = min(set(pts), key=pts.count)
            return 2, [pair, single]
        if set(pts) == {5, 3, 2} and not is_flush: return 0, pts # 特殊235
        return 1, pts # 单张

# --- 模拟游戏全局状态 ---
game_state = {
    "players": [
        {"id": 0, "name": "你", "chips": 1000, "hand": [], "is_seen": False, "status": "active"},
        {"id": 1, "name": "AI 1", "chips": 1000, "hand": [], "is_seen": False, "status": "active"}
    ],
    "pot": 0,
    "current_bet": 10,
    "round": 1
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_game():
    deck = [{'p': p, 's': s} for p in "23456789TJQKA" for s in "SHDC"]
    random.shuffle(deck)
    
    game_state["pot"] = 0
    for p in game_state["players"]:
        p["hand"] = [deck.pop(), deck.pop(), deck.pop()]
        p["chips"] -= 10 # 扣底注
        p["status"] = "active"
        p["is_seen"] = False
        game_state["pot"] += 10
    return jsonify(game_state)

@app.route('/action', methods=['POST'])
def action():
    data = request.json
    action_type = data.get("type")
    # 这里可以添加具体的 跟注、看牌、比牌 逻辑处理
    # 为了演示，此处返回当前状态
    return jsonify(game_state)

if __name__ == '__main__':
    app.run(debug=True)
