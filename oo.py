<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>10人炸金花 - 网页版</title>
    <style>
        body { font-family: 'Microsoft YaHei', sans-serif; background-color: #1a472a; color: white; display: flex; flex-direction: column; align-items: center; margin: 0; }
        .table { position: relative; width: 900px; height: 500px; border: 15px solid #5d3a1a; border-radius: 250px; background-color: #2e7d32; margin-top: 50px; box-shadow: 0 0 50px rgba(0,0,0,0.5); }
        .pot-area { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }
        .pot-val { font-size: 24px; font-weight: bold; color: #ffeb3b; }
        
        /* 玩家位置排列 */
        .player { position: absolute; width: 100px; text-align: center; transition: all 0.3s; }
        .player.active { transform: scale(1.1); text-shadow: 0 0 10px yellow; }
        .player.folded { opacity: 0.4; filter: grayscale(1); }
        .dealer-badge { background: red; border-radius: 50%; padding: 2px 5px; font-size: 10px; margin-left: 5px; }
        
        .chips { color: #81c784; font-size: 14px; }
        .hand { font-size: 18px; margin-top: 5px; min-height: 25px; }

        /* 控制面板 */
        .controls { margin-top: 30px; display: flex; gap: 15px; background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px; }
        button { padding: 10px 25px; font-size: 18px; cursor: pointer; border: none; border-radius: 5px; transition: 0.2s; }
        .btn-see { background: #2196f3; color: white; }
        .btn-call { background: #4caf50; color: white; }
        .btn-fold { background: #f44336; color: white; }
        .btn-next { background: #ff9800; color: white; }
        button:hover { filter: brightness(1.2); }
        button:disabled { background: #666; cursor: not-allowed; }

        .log { margin-top: 20px; width: 600px; height: 100px; background: #000; overflow-y: auto; padding: 10px; font-size: 12px; opacity: 0.8; }
    </style>
</head>
<body>

<h1>炸金花大型房间 (10人局)</h1>

<div class="table" id="table">
    <div class="pot-area">
        <div>当前奖池</div>
        <div class="pot-val" id="potDisplay">0</div>
    </div>
</div>

<div class="controls">
    <button class="btn-see" onclick="seeHand()">👀 看牌</button>
    <button class="btn-call" onclick="call()">💰 跟注</button>
    <button class="btn-fold" onclick="fold()">🏳️ 弃牌</button>
    <button class="btn-next" onclick="nextRound()">🔄 下一局</button>
</div>

<div class="log" id="gameLog">游戏加载成功，点击“下一局”开始...</div>

<script>
    // 游戏状态
    let players = [];
    let dealerIdx = 0;
    let currentTurn = 0;
    let pot = 0;
    let baseBet = 100;
    const suits = ['♠','♥','♣','♦'];
    const ranks = ['2','3','4','5','6','7','8','9','10','J','Q','K','A'];

    // 初始化10个玩家
    function init() {
        const table = document.getElementById('table');
        for (let i = 0; i < 10; i++) {
            const p = {
                id: i,
                name: "玩家 " + (i + 1),
                chips: 10000,
                hand: [],
                isSeen: false,
                isFolded: false,
                scoreData: null
            };
            players.push(p);

            // 计算椭圆位置
            const angle = (i * 36) * (Math.PI / 180);
            const x = 400 * Math.cos(angle) + 400;
            const y = 200 * Math.sin(angle) + 200;

            const div = document.createElement('div');
            div.className = 'player';
            div.id = 'p-' + i;
            div.style.left = x + 'px';
            div.style.top = y + 'px';
            table.appendChild(div);
        }
        updateUI();
    }

    function getHandScore(hand) {
        let v = hand.map(c => c.val).sort((a,b) => b-a);
        let s = hand.map(c => c.suit);
        let isFlush = new Set(s).size === 1;
        let isStraight = (v[0]-v[1]==1 && v[1]-v[2]==1) || (JSON.stringify(v)==='[14,3,2]');
        
        let counts = {}; v.forEach(x => counts[x] = (counts[x]||0)+1);
        let cVals = Object.values(counts);
        
        if (cVals.includes(3)) return {lv: 6, name: "豹子", v};
        if (v.every(x => [5,3,2].includes(x)) && !isFlush) return {lv: 0.5, name: "235", v};
        if (isFlush && isStraight) return {lv: 5, name: "同花顺", v};
        if (isFlush) return {lv: 4, name: "同花", v};
        if (isStraight) return {lv: 3, name: "顺子", v: JSON.stringify(v)==='[14,3,2]'?[3,2,1]:v};
        if (cVals.includes(2)) return {lv: 2, name: "对子", v};
        return {lv: 1, name: "高牌", v};
    }

    function nextRound() {
        pot = 0;
        let deck = [];
        suits.forEach(s => ranks.forEach((r, i) => deck.push({suit:s, rank:r, val:i+2})));
        deck.sort(() => Math.random() - 0.5);

        players.forEach((p, i) => {
            p.isFolded = false;
            p.isSeen = false;
            p.hand = [deck.pop(), deck.pop(), deck.pop()];
            p.scoreData = getHandScore(p.hand);
            p.chips -= baseBet;
            pot += baseBet;
        });

        currentTurn = (dealerIdx + 1) % 10;
        log("📢 新局开始，由 " + players[dealerIdx].name + " 发牌！");
        updateUI();
    }

    function seeHand() {
        let p = players[currentTurn];
        p.isSeen = true;
        alert(p.name + " 的手牌: " + p.hand.map(c => c.suit + c.rank).join(' ') + "\n牌型: " + p.scoreData.name);
        updateUI();
    }

    function call() {
        let p = players[currentTurn];
        let cost = p.isSeen ? baseBet * 2 : baseBet;
        p.chips -= cost;
        pot += cost;
        nextTurn();
    }

    function fold() {
        players[currentTurn].isFolded = true;
        nextTurn();
    }

    function nextTurn() {
        let active = players.filter(p => !p.isFolded);
        if (active.length === 1) {
            settle(active[0]);
            return;
        }
        do {
            currentTurn = (currentTurn + 1) % 10;
        } while (players[currentTurn].isFolded);
        
        updateUI();
    }

    function settle(winner) {
        log("🏆 " + winner.name + " 赢得了奖池 " + pot);
        winner.chips += pot;
        dealerIdx = winner.id;
        pot = 0;
        updateUI();
    }

    function updateUI() {
        document.getElementById('potDisplay').innerText = pot;
        players.forEach(p => {
            const div = document.getElementById('p-' + p.id);
            div.className = 'player' + (p.id === currentTurn ? ' active' : '') + (p.isFolded ? ' folded' : '');
            let handHtml = p.isSeen ? p.hand.map(c => c.suit + c.rank).join(' ') : '???';
            div.innerHTML = `
                <div class="name">${p.name} ${p.id === dealerIdx ? '<span class="dealer-badge">庄</span>' : ''}</div>
                <div class="chips">💰 ${p.chips}</div>
                <div class="hand">${p.isFolded ? '已弃牌' : handHtml}</div>
            `;
        });
    }

    function log(m) {
        const l = document.getElementById('gameLog');
        l.innerHTML = m + "<br>" + l.innerHTML;
    }

    init();
</script>
</body>
</html>
