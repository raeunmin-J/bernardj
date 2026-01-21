import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정: 여백을 0으로 만들어 꽉 찬 화면 구현
st.set_page_config(page_title="MTS Pro", layout="wide", initial_sidebar_state="collapsed")

# [핵심] 스크롤 제거 및 UI 밀착을 위한 강력한 CSS 주입
st.markdown("""
    <style>
    /* 메인 컨테이너 여백 제거 */
    .main .block-container { padding: 0rem 0.5rem; max-width: 100%; }
    /* 스크롤바 숨기기 및 전체 화면 고정 */
    html, body, [data-testid="stAppViewContainer"] { overflow: hidden; height: 100vh; }
    /* 탭 간격 줄이기 */
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { height: 35px; padding-top: 0px; padding-bottom: 0px; }
    /* 버튼 및 슬라이더 크기 최적화 */
    div[data-testid="stColumn"] { padding: 0px; }
    .stSlider { margin-top: -15px; }
    </style>
    """, unsafe_allow_html=True)

if 'file_index' not in st.session_state:
    st.session_state.file_index = 0

def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 MTS Login")
        password = st.text_input("Password", type="password")
        if st.button("Connect"):
            if password == st.secrets.get("MY_PASSWORD", "1234"):
                st.session_state["password_correct"] = True
                st.rerun()
        return False
    return True

if check_password():
    # 2. 데이터 처리 및 업로드 (사이드바는 가로모드 시 툴바 역할)
    with st.sidebar:
        st.header("⚙️ 툴바")
        uploaded_files = st.file_uploader("CSV", type=['csv', 'txt'], accept_multiple_files=True)
        if uploaded_files:
            st.info(f"Loaded: {len(uploaded_files)}")
            # 지표 설정을 사이드바로 이동 (가로모드 시 좌측 툴바 역할)
            st.divider()
            show_ma20 = st.toggle("MA20", False)
            show_ma100 = st.toggle("MA100", False)
            show_bb26 = st.checkbox("BB26", False)
            show_pc52 = st.checkbox("PC52", False)

    if uploaded_files:
        current_file = uploaded_files[st.session_state.file_index]
        df = pd.read_csv(current_file, encoding='utf-8-sig')
        
        # 종목명 추출
        comp_name = df['종목명'].iloc[0] if '종목명' in df.columns else ""
        title = f"[{comp_name}]" if comp_name else current_file.name

        # 데이터 정리
        rename_map = {'날짜': 'Date', '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close', '거래량': 'Volume'}
        df = df.rename(columns=rename_map)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df = df.sort_values('Date')

        # 3. 최상단 툴바 배치 (파일 이동 및 범위 조절)
        t1, t2, t3 = st.columns([1, 3, 1])
        with t1:
            if st.button("◀", use_container_width=True):
                st.session_state.file_index = (st.session_state.file_index - 1) % len(uploaded_files)
                st.rerun()
        with t2:
            zoom_val = st.select_slider("Range", options=[60, 100, 200, 300, 500, len(df)], value=100, label_visibility="collapsed")
        with t3:
            if st.button("▶", use_container_width=True):
                st.session_state.file_index = (st.session_state.file_index + 1) % len(uploaded_files)
                st.rerun()

        st.markdown(f"<center><small>{title}</small></center>", unsafe_allow_html=True)

        # 4. 차트 생성
        display_df = df.tail(zoom_val)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.75, 0.25])

        # 캔들스틱 & 지표
        fig.add_trace(go.Candlestick(
            x=display_df['Date'], open=display_df['Open'], high=display_df['High'],
            low=display_df['Low'], close=display_df['Close'], name="Price",
            increasing_line_color='#FF3232', decreasing_line_color='#0066FF'
        ), row=1, col=1)

        v_colors = ['#FF3232' if r['Close'] >= r['Open'] else '#0066FF' for _, r in display_df.iterrows()]
        fig.add_trace(go.Bar(x=display_df['Date'], y=display_df['Volume'], marker_color=v_colors), row=2, col=1)

        # 지표 추가 (실선)
        if show_ma20: fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA20'], line=dict(color='orange', width=1)), row=1, col=1)
        if show_ma100: fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA100'], line=dict(color='cyan', width=1)), row=1, col=1)

        # 휴장일 제거 및 우측 축 설정
        fig.update_xaxes(type='category', row=1, col=1)
        fig.update_xaxes(type='category', nticks=4, row=2, col=1)
        fig.update_yaxes(side="right", fixedrange=False, row=1, col=1)

        fig.update_layout(
            height=600, # 모바일 가로/세로 비율에 맞춘 고정 높이
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            margin=dict(l=5, r=40, t=10, b=10),
            showlegend=False,
            dragmode='zoom',
            hovermode='x unified',
            # 자동 맞춤 버튼
            updatemenus=[dict(
                type="buttons", showactive=False, x=0.01, y=0.99,
                buttons=[dict(label="FIT", method="relayout", args=[{"yaxis.autorange": True, "yaxis2.autorange": True}])]
            )]
        )

        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
    else:
        st.info("📂 사이드바를 열어 파일을 업로드하세요.")