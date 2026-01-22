import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정
st.set_page_config(page_title="MTS Pro Final", layout="wide", initial_sidebar_state="expanded")

# [사이드바] 지표 세분화 및 높이 조절
with st.sidebar:
    st.title("?? MTS TOOLBAR")
    uploaded_files = st.file_uploader("Upload CSV", type=['csv', 'txt'], accept_multiple_files=True)
    
    # 수동 높이 조절 슬라이더 (CSS 변수로 활용됨)
    st.divider()
    st.subheader("Chart Height Settings")
    chart_h = st.slider("Portrait Height (세로)", 200, 1000, 480)
    landscape_h = st.slider("Landscape Height (가로)", 100, 600, 250)

    if uploaded_files:
        st.divider()
        st.subheader("Indicators (Solid Line)")
        show_ma = st.toggle("MA 20/100", True)
        
        st.info("Bollinger Bands")
        show_bb26 = st.checkbox("BB26 Up", False)
        show_bb52 = st.checkbox("BB52 Up", False)
        show_bb129 = st.checkbox("BB129 Up", False)
        show_bb260 = st.checkbox("BB260 Up", False)
        show_wbb52 = st.checkbox("WBB52 Up", False)
        
        st.info("Price Channels")
        show_pc52 = st.checkbox("PC52 Mid", False)
        show_pc129 = st.checkbox("PC129 Mid", False)
        show_pc260 = st.checkbox("PC260 Mid", False)
        show_pc645 = st.checkbox("PC645 Mid", False)

# [핵심] 스크롤 박멸 및 모드별 수동 높이 적용 CSS
# f-string 사용 시 CSS의 중괄호는 {{ }} 처럼 두 번 써야 에러가 나지 않습니다.
st.markdown(f"""
    <style>
    /* 1. 기본 UI 클리닝 */
    footer {{ visibility: hidden; }}
    header[data-testid="stHeader"] {{ background: transparent; }}
    
    /* 2. 전체 브라우저 스크롤 차단 (스크롤바 완전 제거) */
    html, body, [data-testid="stAppViewContainer"] {{ 
        overflow: hidden !important; 
        height: 100vh !important; 
        margin: 0; padding: 0;
        background-color: #0E1117;
        -ms-overflow-style: none; /* IE/Edge */
        scrollbar-width: none; /* Firefox */
    }}
    html::-webkit-scrollbar, body::-webkit-scrollbar {{
        display: none !important; /* Chrome/Safari */
    }}
    
    /* 3. 메인 컨테이너 고정 및 내부 스크롤 방지 */
    .main .block-container {{ 
        padding: 0px 5px !important; 
        max-width: 100% !important; 
        height: 100vh !important;
        display: flex;
        flex-direction: column;
        overflow: hidden !important;
    }}
    
    /* 4. 상단 컨트롤러바 고정 및 여백 최적화 */
    div[data-testid="stHorizontalBlock"] {{ align-items: center !important; gap: 0.3rem !important; }}
    .stSlider {{ margin-top: -15px; }}
    .stButton button {{ height: 40px; border-radius: 8px; font-weight: bold; background-color: #2B3139; color: white; border: none; }}
    
    /* 5. 사이드바는 메뉴 선택을 위해 스크롤 허용 */
    [data-testid="stSidebar"] {{ overflow-y: auto !important; }}
    
    /* 6. 가로/세로 모드별 차트 높이 수동 적용 */
    @media (orientation: landscape) {{
        .stPlotlyChart {{ height: {landscape_h}px !important; }}
        div[data-testid="stHorizontalBlock"] {{ margin-bottom: -10px !important; }}
        .stSlider {{ margin-top: -25px !important; }}
    }}
    @media (orientation: portrait) {{
        .stPlotlyChart {{ height: {chart_h}px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

if 'file_index' not in st.session_state:
    st.session_state.file_index = 0

def check_password():
    if "password_correct" not in st.session_state:
        st.title("?? MTS Connect")
        password = st.text_input("Access Key", type="password")
        if st.button("LOGIN"):
            if password == st.secrets.get("MY_PASSWORD", "1234"):
                st.session_state["password_correct"] = True
                st.rerun()
        return False
    return True

if check_password():
    if uploaded_files:
        current_file = uploaded_files[st.session_state.file_index]
        df = pd.read_csv(current_file, encoding='utf-8-sig')
        
        rename_map = {'날짜': 'Date', '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close', '거래량': 'Volume'}
        df = df.rename(columns=rename_map)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df = df.sort_values('Date')
        comp_name = df['종목명'].iloc[0] if '종목명' in df.columns else current_file.name

        t_col1, t_col2, t_col3, t_col4 = st.columns([0.6, 2.5, 3.5, 0.6])
        with t_col1:
            if st.button("◀"):
                st.session_state.file_index = (st.session_state.file_index - 1) % len(uploaded_files)
                st.rerun()
        with t_col2:
            st.markdown(f"<div style='text-align:center; line-height:40px; font-size:15px; color:#F0B90B;'><b>{comp_name}</b></div>", unsafe_allow_html=True)
        with t_col3:
            zoom_val = st.slider("R", 10, len(df), min(120, len(df)), step=10, label_visibility="collapsed")
        with t_col4:
            if st.button("▶"):
                st.session_state.file_index = (st.session_state.file_index + 1) % len(uploaded_files)
                st.rerun()

        display_df = df.tail(zoom_val)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.75, 0.25])

        fig.add_trace(go.Candlestick(
            x=display_df['Date'], open=display_df['Open'], high=display_df['High'],
            low=display_df['Low'], close=display_df['Close'], name="Price",
            increasing_line_color='#FF3232', decreasing_line_color='#0066FF'
        ), row=1, col=1)

        v_cols = ['#FF3232' if r['Close'] >= r['Open'] else '#0066FF' for _, r in display_df.iterrows()]
        fig.add_trace(go.Bar(x=display_df['Date'], y=display_df['Volume'], marker_color=v_cols), row=2, col=1)

        if show_ma:
            if 'MA20' in display_df.columns:
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA20'], name="MA20", line=dict(color='orange', width=1.5)), row=1, col=1)
            if 'MA100' in display_df.columns:
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA100'], name="MA100", line=dict(color='cyan', width=1.5)), row=1, col=1)
        
        bb_cfg = [('BB26_Upper1', show_bb26, '#FFFF00'), ('BB52_Upper1', show_bb52, '#FF8C00'), ('BB129_Upper1', show_bb129, '#FF5722'), ('BB260_Upper1', show_bb260, '#E91E63'), ('WBB52_Upper1', show_wbb52, '#DDA0DD')]
        for col, show, clr in bb_cfg:
            if show and col in display_df.columns:
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[col], name=col, line=dict(color=clr, width=1.2)), row=1, col=1)

        pc_cfg = [('PC52_Mid', show_pc52, '#ADFF2F'), ('PC129_Mid', show_pc129, '#00FF7F'), ('PC260_Mid', show_pc260, '#00BFFF'), ('PC645_Mid', show_pc645, '#FFFFFF')]
        for col, show, clr in pc_cfg:
            if show and col in display_df.columns:
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[col], name=col, line=dict(color=clr, width=1.5)), row=1, col=1)

        fig.update_xaxes(type='category', row=1, col=1)
        fig.update_xaxes(type='category', nticks=5, row=2, col=1)
        fig.update_yaxes(side="right", gridcolor="#333", autorange=True, fixedrange=False, row=1, col=1)

        fig.update_layout(
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            margin=dict(l=5, r=45, t=5, b=5),
            showlegend=False,
            dragmode='pan',
            hovermode='x unified',
            xaxis=dict(range=[-0.5, zoom_val - 0.5])
        )

        fig.update_layout(updatemenus=[dict(
            type="buttons", showactive=False, x=0.01, y=0.99,
            buttons=[dict(label="FIT", method="relayout", args=[{"yaxis.autorange": True}])]
        )])

        # CSS에서 높이를 강제하므로 여기서 height 인자는 생략합니다.
        st.plotly_chart(fig, use_container_width=True, config={
            'scrollZoom': True, 'displayModeBar': False, 'responsive': True, 'doubleClick': 'reset'
        })
    else:
        st.info("?? 사이드바(>)에서 파일을 업로드하세요.")
