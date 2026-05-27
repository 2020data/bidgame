import streamlit as st
import random
import time

# --- 1. 設定頁面 ---
st.set_page_config(page_title="多人線上比大小", page_icon="🎲", layout="centered")

# --- 2. 建立伺服器端「共享資料庫」（跨使用者共享） ---
@st.cache_resource
def get_shared_state():
    return {
        "banker_money": 100000,  # 莊家初始資金
        "active_players": {}     # 紀錄線上玩家 {名字: 金額}
    }

shared_data = get_shared_state()

st.title("🎲 多人線上比大小押注遊戲")
st.caption("所有連線玩家共享同一個莊家金庫！")

# --- 3. 玩家登入介面 ---
if "player_name" not in st.session_state:
    st.subheader("👋 歡迎！請先登入")
    name_input = st.text_input("請輸入您的暱稱:", max_chars=10).strip()
    
    if st.button("進入遊戲"):
        if name_input:
            if name_input in shared_data["active_players"]:
                st.error("這個名字已經有人用囉，換一個吧！")
            else:
                st.session_state.player_name = name_input
                # 隨機派發初始金錢 (1000 ~ 5000)
                st.session_state.player_money = random.randint(1000, 5000)
                # 註冊到共享資料庫
                shared_data["active_players"][name_input] = st.session_state.player_money
                st.rerun()
        else:
            st.warning("名字不能留白喔！")
    st.stop() # 未登入前不顯示後續內容

# --- 已登入後的變數同步 ---
player = st.session_state.player_name
# 確保本地金額與共享資料庫同步
st.session_state.player_money = shared_data["active_players"].get(player, st.session_state.player_money)

# --- 4. 側邊欄：即時線上玩家名單 & 狀態 ---
with st.sidebar:
    st.header("👥 線上玩家名單")
    for p_name, p_money in list(shared_data["active_players"].items()):
        st.write(f"• **{p_name}**: ${p_money}")
    
    st.divider()
    if st.button("🔴 登出 / 換人玩"):
        shared_data["active_players"].pop(player, None)
        del st.session_state.player_name
        st.rerun()

# --- 5. 遊戲主畫面 ---
col1, col2 = st.columns(2)
with col1:
    st.metric(label="💰 莊家當前總資產", value=f"${shared_data['banker_money']}")
with col2:
    st.metric(label=f"👤 您的資產 ({player})", value=f"${st.session_state.player_money}")

st.divider()

# 檢查玩家是不是破產了
if st.session_state.player_money <= 0:
    st.error("😭 您已經破產了！")
    if st.button("發放救濟金 ($1000)"):
        st.session_state.player_money = 1000
        shared_data["active_players"][player] = 1000
        st.rerun()
    st.stop()

# --- 6. 下注與遊戲邏輯 ---
st.write("### 🎰 開始下注")
bet = st.number_input("請輸入下注金額:", min_value=100, max_value=int(st.session_state.player_money), step=100)
guess = st.radio("請預測電腦莊家的數字大小 (以 500 為界):", ["大 (501 - 1000)", "小 (0 - 500)"], horizontal=True)

if st.button("🎲 開獎！", use_container_width=True):
    # 電腦莊家隨機產生 0 ~ 1000
    with st.spinner("莊家搖骰中..."):
        time.sleep(0.5)
        banker_number = random.randint(0, 1000)
    
    st.info(f"開獎結果莊家的數字是 {banker_number}")
    
    # 判斷大小
    is_big = banker_number > 500
    player_won = (guess.startswith("大") and is_big) or (guess.startswith("小") and not is_big)
    
    if player_won:
        st.success(f"🎉 恭喜贏了！獲得雙倍報酬 ${bet * 2}！")
        # 玩家贏：玩家加錢，莊家扣錢
        st.session_state.player_money += bet
        shared_data["banker_money"] -= bet
    else:
        st.error(f"❌ 殘念！您猜錯了，損失 ${bet}，金額被莊家收走。")
        # 玩家輸：玩家扣錢，莊家加錢累計
        st.session_state.player_money -= bet
        shared_data["banker_money"] += bet
        
    # 更新同步到共享資料庫
    shared_data["active_players"][player] = st.session_state.player_money
    
    # 強制重整畫面更新數據
    st.button("繼續下一把")
