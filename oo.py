import time
print(" 炸金花")
while True:
        print("1: 豹子")
        print("2: 同花顺")
        print("3: 同花顺")
        print("4: 顺子")
        print("5: 对子")
        print("6: 单张")
        牌面=input("(输入0 退出):")
        if 牌面=='0':
                print(" 胜利")
                break
        v=int(牌面)
        if v==1:
                print(">>> 萌萌跟")
        elif v==2:
                print(">>> 钓他")
        elif v==3:
                print(">>> 稳住")
        elif v==4:
                print(">>> 一般人.多就撤")
        elif v==5:
                print(">>> 反手开")
        elif v==6:
                print(">>> 对方没看就开")
        else:
                print(">>> 输入错误")