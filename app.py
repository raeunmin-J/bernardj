import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정: 사이드바 버튼이 보이도록 헤더를 유지하고 기본 상태를 열림으로 설정
st.set_page_config(page_title="MTS Pro Detail", layout="wide", initial_sidebar_state="expanded")

# [가로 모드 대응 및 사이드바 복구 CSS]
st.markdown("""
    <style>
    /* 하단 푸터 숨김 */
    footer { visibility: hidden; }
    
    /* 전체 화면 고정 및 스크롤 차단 */
    html, body, [data-testid="stAppViewContainer"] { 
        overflow: hidden !important; 
        height: 100vh !important; 
        margin: 0; padding: 0;
    }
    
    /* 가로 모드에서 차트 밀림 방지 */
    @media (orientation: landscape) {
        .main .block-container { padding: 0px !important; }
        div[data-testid="stVerticalBlock"] { gap: 0rem !important; }
        h4 { font-size: 12px !important; margin: 0 !important; }
    }

    /* 메인 컨테이너 여백 최적화 */
    .main .block-container { padding: 0px 5px !important; max-width: 100% !important; }
    
    /* 사이드바 내부 스크롤 허용 */
    [data-testid="stSidebar"] { overflow-y: auto !important; }
    
    /* 간격 압축 */
    .stSlider { margin-top: -20px; }
    .stButton button { height: 35px; border-radius: 5px; }
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
    # 2. 좌측 사이드바 (지표 설정 및 툴바)
    with st.sidebar:
        st.title("🛠 Toolbar")
        uploaded_files = st.file_uploader("CSV", type=['csv', 'txt'], accept_multiple_files=True)
        if uploaded_files:
            st.divider()
            # 이동평균선
            st.subheader("MA Lines")
            show_ma20 = st.toggle("MA20", False)
            show_ma100 = st.toggle("MA100", False)

            # 볼린저 밴드 상세 (실선)
            st.subheader("Bollinger Bands")
            show_bb26 = st.checkbox("BB26 Upper", False)
            show_bb52 = st.checkbox("BB52 Upper", False)
            show_bb129 = st.checkbox("BB129 Upper", False)
            show_bb260 = st.checkbox("BB260 Upper", False)
            show_wbb52 = st.checkbox("WBB52 Upper", False)
            show_wbb129 = st.checkbox("WBB129 Upper", False)

            # 가격 채널 상세 (실선)
            st.subheader("Price Channels")
            show_pc52 = st.checkbox("PC52 Mid", False)
            show_pc129 = st.checkbox("PC129 Mid", False)
            show_pc260 = st.checkbox("PC260 Mid", False)
            show_pc645 = st.checkbox("PC645 Mid", False)
            
            st.divider()
            # 가로모드에서 차트가 잘 보이지 않으면 이 값을 조절하세요
            chart_height = st.slider("Chart Height", 200, 800, 420)

    if uploaded_files:
        current_file = uploaded_files[st.session_state.file_index]
        df = pd.read_csv(current_file, encoding='utf-8-sig')
        
        # 데이터 정리
        rename_map = {'날짜': 'Date', '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close', '거래량': 'Volume'}
        df = df.rename(columns=rename_map)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df = df.sort_values('Date')
        comp_name = df['종목명'].iloc[0] if '종목명' in df.columns else current_file.name

        # 3. 최상단 컨트롤러
        c1, c2, c3 = st.columns([1, 4, 1])
        with c1:
            if st.button("◀", use_container_width=True):
                st.session_state.file_index = (st.session_state.file_index - 1) % len(uploaded_files)
                st.rerun()
        with c2:
            zoom_val = st.select_slider("Range", options=[60, 100, 200, 300, 500, len(df)], value=100, label_visibility="collapsed")
        with c3:
            if st.button("▶", use_container_width=True):
                st.session_state.file_index = (st.session_state.file_index + 1) % len(uploaded_files)
                st.rerun()

        st.markdown(f"<center><h4 style='margin:-10px 0 5px 0;'>{comp_name}</h4></center>", unsafe_allow_html=True)

        # 4. 차트 생성
        display_df = df.tail(zoom_val)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.75, 0.25])

        # 캔들스틱 및 거래량
        fig.add_trace(go.Candlestick(x=display_df['Date'], open=display_df['Open'], high=display_df['High'], low=display_df['Low'], close=display_df['Close'], name="Price", increasing_line_color='#FF3232', decreasing_line_color='#0066FF'), row=1, col=1)
        v_colors = ['#FF3232' if r['Close'] >= r['Open'] else '#0066FF' for _, r in display_df.iterrows()]
        fig.add_trace(go.Bar(x=display_df['Date'], y=display_df['Volume'], marker_color=v_colors), row=2, col=1)

        # 지표 추가 (모두 실선 표시)
        if show_ma20: fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA20'], line=dict(color='orange', width=1.5)), row=1, col=1)
        if show_ma100: fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA100'], line=dict(color='cyan', width=1.5)), row=1, col=1)
        
        bb_list = [('BB26_Upper1', show_bb26, '#FFFF00'), ('BB52_Upper1', show_bb52, '#FF8C00'), ('BB129_Upper1', show_bb129, '#FF5722'), ('BB260_Upper1', show_bb260, '#E91E63'), ('WBB52_Upper1', show_wbb52, '#DDA0DD'), ('WBB129_Upper1', show_wbb129, '#EE82EE')]
        for col, show, color in bb_list:
            if show and col in display_df.columns:
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[col], name=col, line=dict(color=color, width=1.2)), row=1, col=1)

        pc_list = [('PC52_Mid', show_pc52, '#ADFF2F'), ('PC129_Mid', show_pc129, '#00FF7F'), ('PC260_Mid', show_pc260, '#00BFFF'), ('PC645_Mid', show_pc645, '#FFFFFF')]
        for col, show, color in pc_list:
            if show and col in display_df.columns:
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[col], name=col, line=dict(color=color, width=1.5)), row=1, col=1)

        # 휴장일 제거 및 축 설정
        fig.update_xaxes(type='category', row=1, col=1)
        fig.update_xaxes(type='category', nticks=4, row=2, col=1)
        fig.update_yaxes(side="right", gridcolor="#333", fixedrange=False, row=1, col=1)

        fig.update_layout(
            height=chart_height, template="plotly_dark", xaxis_rangeslider_visible=False,
            margin=dict(l=5, r=40, t=5, b=5), showlegend=False, dragmode='zoom', hovermode='x unified',
            updatemenus=[dict(type="buttons", showactive=False, x=0.01, y=0.99, buttons=[dict(label="FIT", method="relayout", args=[{"yaxis.autorange": True}])])]
        )

        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
    else:
        st.info("📂 사이드바를 열어 파일을 업로드하세요.")