import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정: 사이드바 버튼이 보이도록 헤더를 유지하고 기본 상태를 열림으로 설정
st.set_page_config(page_title="MTS Pro Final", layout="wide", initial_sidebar_state="expanded")

# [핵심] 스크롤 완전 박멸 및 UI 고정 CSS
st.markdown("""
    <style>
    /* 1. 하단 푸터 숨김 및 상단 헤더 투명화 (사이드바 버튼 유지) */
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }
    
    /* 2. 전체 브라우저 스크롤 차단 (물리적으로 스크롤 안 됨) */
    html, body, [data-testid="stAppViewContainer"] { 
        overflow: hidden !important; 
        height: 100vh !important; 
        margin: 0; padding: 0;
        background-color: #0E1117;
    }
    
    /* 3. 메인 컨테이너 여백 제로화 및 한 화면 고정 */
    .main .block-container { 
        padding: 0px 5px !important; 
        max-width: 100% !important; 
        height: calc(100vh - 50px) !important;
        display: flex;
        flex-direction: column;
    }
    
    /* 4. 상단 컨트롤러바 한 줄 배열 고정 스타일 */
    div[data-testid="stHorizontalBlock"] { align-items: center !important; gap: 0.3rem !important; }
    .stSlider { margin-top: -15px; }
    .stButton button { height: 40px; border-radius: 8px; font-weight: bold; background-color: #2B3139; color: white; border: none; }
    
    /* 5. 사이드바 내부 스크롤 허용 (지표 선택용) */
    [data-testid="stSidebar"] { overflow-y: auto !important; }
    
    /* 6. 가로 모드 시 상단 여백 추가 압축 */
    @media (orientation: landscape) {
        .main .block-container { padding-top: 0px !important; }
        h4 { font-size: 14px !important; margin: 0 !important; }
    }
    </style>
    """, unsafe_allow_html=True)

if 'file_index' not in st.session_state:
    st.session_state.file_index = 0

def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 MTS Connect")
        password = st.text_input("Access Key", type="password")
        if st.button("LOGIN"):
            if password == st.secrets.get("MY_PASSWORD", "1234"):
                st.session_state["password_correct"] = True
                st.rerun()
        return False
    return True

if check_password():
    # [사이드바] 지표 세분화 및 높이 조절
    with st.sidebar:
        st.title("🛠 MTS TOOLBAR")
        uploaded_files = st.file_uploader("Upload CSV", type=['csv', 'txt'], accept_multiple_files=True)
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
            
            st.divider()
            chart_h = st.slider("Chart height", 200, 800, 480)

    if uploaded_files:
        current_file = uploaded_files[st.session_state.file_index]
        df = pd.read_csv(current_file, encoding='utf-8-sig')
        
        # 데이터 전처리 및 날짜 카테고리화 (공백 제거)
        rename_map = {'날짜': 'Date', '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close', '거래량': 'Volume'}
        df = df.rename(columns=rename_map)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df = df.sort_values('Date')
        comp_name = df['종목명'].iloc[0] if '종목명' in df.columns else current_file.name

        # [최상단 고정 툴바: < 회사명 슬라이더 > 한 줄 배열]
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

        # 데이터 슬라이싱 (캔들 없는 영역 이탈 방지용)
        display_df = df.tail(zoom_val)

        # 차트 생성 (2단 구성)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.75, 0.25])

        # 캔들스틱 (항상 데이터 범위 내 고정)
        fig.add_trace(go.Candlestick(
            x=display_df['Date'], open=display_df['Open'], high=display_df['High'],
            low=display_df['Low'], close=display_df['Close'], name="Price",
            increasing_line_color='#FF3232', decreasing_line_color='#0066FF'
        ), row=1, col=1)

        v_cols = ['#FF3232' if r['Close'] >= r['Open'] else '#0066FF' for _, r in display_df.iterrows()]
        fig.add_trace(go.Bar(x=display_df['Date'], y=display_df['Volume'], marker_color=v_cols), row=2, col=1)

        # [지표 레이어 - 모두 실선]
        if show_ma:
            fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA20'], name="MA20", line=dict(color='orange', width=1.5)), row=1, col=1)
            fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA100'], name="MA100", line=dict(color='cyan', width=1.5)), row=1, col=1)
        
        # 볼린저 밴드 실선 목록
        bb_cfg = [('BB26_Upper1', show_bb26, '#FFFF00'), ('BB52_Upper1', show_bb52, '#FF8C00'), ('BB129_Upper1', show_bb129, '#FF5722'), ('BB260_Upper1', show_bb260, '#E91E63'), ('WBB52_Upper1', show_wbb52, '#DDA0DD')]
        for col, show, clr in bb_cfg:
            if show and col in display_df.columns:
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[col], name=col, line=dict(color=clr, width=1.2)), row=1, col=1)

        # 가격 채널 실선 목록
        pc_cfg = [('PC52_Mid', show_pc52, '#ADFF2F'), ('PC129_Mid', show_pc129, '#00FF7F'), ('PC260_Mid', show_pc260, '#00BFFF'), ('PC645_Mid', show_pc645, '#FFFFFF')]
        for col, show, clr in pc_cfg:
            if show and col in display_df.columns:
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[col], name=col, line=dict(color=clr, width=1.5)), row=1, col=1)

        # [MTS 조작 최적화]
        fig.update_xaxes(type='category', row=1, col=1) # 휴장일 공백 제거
        fig.update_xaxes(type='category', nticks=5, row=2, col=1)
        
        # 우측 가격축 & Y축 높낮이 조절 & 자동 스케일
        fig.update_yaxes(side="right", gridcolor="#333", autorange=True, fixedrange=False, row=1, col=1)

        fig.update_layout(
            height=chart_h,
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            margin=dict(l=5, r=45, t=5, b=5),
            showlegend=False,
            dragmode='pan',
            hovermode='x unified',
            xaxis=dict(range=[-0.5, zoom_val - 0.5]) # 캔들 없는 영역 이탈 방지
        )

        # 자동 맞춤 버튼(Fit)
        fig.update_layout(updatemenus=[dict(
            type="buttons", showactive=False, x=0.01, y=0.99,
            buttons=[dict(label="FIT", method="relayout", args=[{"yaxis.autorange": True}])]
        )])

        st.plotly_chart(fig, use_container_width=True, config={
            'scrollZoom': True, 'displayModeBar': False, 'responsive': True, 'doubleClick': 'reset'
        })
    else:
        st.info("📂 사이드바(>)에서 파일을 업로드하세요.")