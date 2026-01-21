import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정 (모바일 최적화 여백 제거)
st.set_page_config(page_title="MTS 주식 분석", layout="wide", initial_sidebar_state="collapsed")

# 모바일 화면에서 불필요한 여백을 줄이는 CSS 주입
st.markdown("""
    <style>
    .main .block-container { padding-top: 1rem; padding-bottom: 1rem; padding-left: 0.5rem; padding-right: 0.5rem; }
    div[data-testid="stExpander"] { margin-top: -1rem; }
    </style>
    """, unsafe_allow_html=True)

# 2. 세션 상태 초기화
if 'file_index' not in st.session_state:
    st.session_state.file_index = 0

def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 MTS 로그인")
        password = st.text_input("Access Password", type="password")
        if st.button("로그인"):
            if password == st.secrets.get("MY_PASSWORD", "1234"):
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
        return False
    return True

if check_password():
    # 상단 메뉴 간소화
    tab1, tab2, tab3 = st.tabs(["📊 차트", "🛠 설정", "📂 파일"])

    with tab3:
        uploaded_files = st.file_uploader("CSV 선택", type=['csv', 'txt'], accept_multiple_files=True)
        if uploaded_files:
            if 'last_upload_count' not in st.session_state or st.session_state.last_upload_count != len(uploaded_files):
                st.session_state.file_index = 0
                st.session_state.last_upload_count = len(uploaded_files)

    if uploaded_files:
        current_file = uploaded_files[st.session_state.file_index]
        df = pd.read_csv(current_file, encoding='utf-8-sig')
        
        # 종목명 추출
        file_display_name = current_file.name
        if '종목명' in df.columns and not df['종목명'].empty:
            file_display_name = f"[{df['종목명'].iloc[0]}]"
        
        rename_map = {'날짜': 'Date', '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close', '거래량': 'Volume'}
        df = df.rename(columns=rename_map)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df = df.sort_values('Date')

        with tab2:
            st.info("지표 설정")
            c1, c2 = st.columns(2)
            with c1:
                show_ma20 = st.toggle("MA20", False); show_ma100 = st.toggle("MA100", False)
                show_bb26 = st.checkbox("BB26", False); show_bb52 = st.checkbox("BB52", False)
            with c2:
                show_pc52 = st.checkbox("PC52", False); show_pc129 = st.checkbox("PC129", False)
                show_pc260 = st.checkbox("PC260", False); show_pc645 = st.checkbox("PC645", False)

        with tab1:
            # 내비게이션바 한 줄 구성 (공간 절약)
            col_prev, col_info, col_next = st.columns([1, 2, 1])
            with col_prev: 
                if st.button("◀", use_container_width=True):
                    st.session_state.file_index = (st.session_state.file_index - 1) % len(uploaded_files)
                    st.rerun()
            with col_info: 
                st.markdown(f"<center><b>{file_display_name}</b></center>", unsafe_allow_html=True)
            with col_next: 
                if st.button("▶", use_container_width=True):
                    st.session_state.file_index = (st.session_state.file_index + 1) % len(uploaded_files)
                    st.rerun()

            # 보기 범위 조절
            zoom_val = st.select_slider("보기 범위", options=[30, 60, 100, 200, 300, 500], value=100)
            display_df = df.tail(zoom_val)

            # 차트 구성
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])

            # 캔들스틱
            fig.add_trace(go.Candlestick(
                x=display_df['Date'], open=display_df['Open'], high=display_df['High'],
                low=display_df['Low'], close=display_df['Close'], name="가격",
                increasing_line_color='#FF3232', decreasing_line_color='#0066FF'
            ), row=1, col=1)

            # 거래량
            v_colors = ['#FF3232' if r['Close'] >= r['Open'] else '#0066FF' for _, r in display_df.iterrows()]
            fig.add_trace(go.Bar(x=display_df['Date'], y=display_df['Volume'], marker_color=v_colors), row=2, col=1)

            # 지표 (선택 시 실선 표시)
            if show_ma20: fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA20'], line=dict(color='orange', width=1)), row=1, col=1)
            if show_ma100: fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA100'], line=dict(color='cyan', width=1)), row=1, col=1)
            
            # 레이아웃 최적화 (핵심: 높이 조절)
            fig.update_xaxes(type='category', row=1, col=1)
            fig.update_xaxes(type='category', nticks=4, row=2, col=1)
            fig.update_yaxes(side="right", fixedrange=False, row=1, col=1)
            fig.update_yaxes(side="right", fixedrange=False, row=2, col=1)

            fig.update_layout(
                height=500, # 핸드폰 화면 세로 모드에 최적화된 높이
                template="plotly_dark",
                xaxis_rangeslider_visible=False, # 공간 확보를 위해 하단 슬라이더 제거
                margin=dict(l=5, r=40, t=5, b=5),
                showlegend=False,
                dragmode='zoom',
                hovermode='x unified',
                updatemenus=[dict(
                    type="buttons", showactive=False, x=0.01, y=0.99,
                    buttons=[dict(label="Fit", method="relayout", args=[{"yaxis.autorange": True, "yaxis2.autorange": True}])]
                )]
            )

            # 핀치 줌 및 자동 맞춤 설정 적용
            st.plotly_chart(fig, use_container_width=True, config={
                'scrollZoom': True, 
                'displayModeBar': False,
                'responsive': True
            })
    else:
        st.info("📂 '파일' 탭에서 데이터를 업로드하세요.")