import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="My Stock App", layout="wide")

# 1. 보안 설정 (Secrets 연동)
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 주식 앱 로그인")
        password = st.text_input("비밀번호를 입력하세요", type="password")
        if st.button("로그인"):
            # Streamlit Cloud의 Secrets에 저장된 비번과 비교
            if password == st.secrets["MY_PASSWORD"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
        return False
    return True

# 2. 메인 앱 실행
if check_password():
    st.title("📈 나의 모바일 주식 차트")
    
    # 사이드바: 파일 업로드
    uploaded_file = st.sidebar.file_uploader("CSV 파일 업로드", type=['csv'])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        # 날짜 컬럼 표준화
        df.columns = [c.strip().capitalize() for c in df.columns]
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])

        # 차트 생성 (Plotly 사용 - 모바일 터치 최적화)
        fig = go.Figure(data=[go.Candlestick(
            x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            increasing_line_color='red', decreasing_line_color='blue'
        )])
        
        fig.update_layout(
            template="plotly_dark",
            height=600,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_rangeslider_visible=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("왼쪽 메뉴에서 CSV 파일을 업로드해 주세요.")