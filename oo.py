# 这只是核心逻辑伪代码，说明如何实现隐私
@socketio.on('see_card')
def handle_see_card():
    user_id = request.sid
    player = room.get_player_by_sid(user_id)
    # 关键：服务器只把牌发给请求的那个人，不广播给所有人
    emit('your_hand_is', player.hand, room=user_id) 
    # 广播给其他人：某某人看牌了（但不发牌的内容）
    emit('player_status_change', {'id': player.id, 'status': 'seen'}, broadcast=True)

