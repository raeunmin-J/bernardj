import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정: 레이아웃 꽉 차게, 사이드바 기본 열림
st.set_page_config(page_title="MTS Pro Final", layout="wide", initial_sidebar_state="expanded")

# [핵심] 스크롤 완전 박멸 및 UI 고정 CSS
st.markdown("""
    <style>
    /* 1. 전체 브라우저 스크롤 차단 및 헤더/푸터 제거 */
    header[data-testid="stHeader"] { visibility: hidden; height: 0; }
    footer { visibility: hidden; }
    html, body, [data-testid="stAppViewContainer"] { 
        overflow: hidden !important; 
        height: 100vh !important; 
        margin: 0; padding: 0;
        background-color: #0E1117;
    }
    
    /* 2. 메인 컨테이너 여백 제로화 (한 화면 고정의 핵심) */
    .main .block-container { 
        padding: 0px 5px !important; 
        max-width: 100% !important; 
        height: 100vh !important;
        display: flex;
        flex-direction: column;
    }
    
    /* 3. 상단 컨트롤러바 고정 스타일 */
    .fixed-top-bar {
        background-color: #1E2329;
        padding: 5px;
        border-radius: 0 0 10px 10px;
        margin-bottom: 5px;
    }
    
    /* 4. 슬라이더 및 버튼 압축 */
    div[data-testid="stHorizontalBlock"] { align-items: center !important; gap: 0.5rem !important; }
    .stSlider { margin-top: -15px; }
    .stButton button { height: 40px; border-radius: 8px; font-weight: bold; background-color: #2B3139; color: white; border: none; }
    
    /* 5. 사이드바 내부만 스크롤 허용 (설정용) */
    [data-testid="stSidebar"] { overflow-y: auto !important; }
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
    # 사이드바: 지표 및 파일 관리 (사용하지 않을 땐 접어서 차트 극대화)
    with st.sidebar:
        st.title("🛠 MTS TOOLBAR")
        uploaded_files = st.file_uploader("CSV Data", type=['csv', 'txt'], accept_multiple_files=True)
        if uploaded_files:
            st.divider()
            st.subheader("Indicators (Solid)")
            show_ma = st.toggle("MA 20/100", True)
            show_bb = st.toggle("Bollinger Detail", False)
            show_pc = st.toggle("Price Channel Detail", False)
            st.divider()
            # 핸드폰 기종에 맞춰 스크롤이 생기기 직전까지 높이를 조절하세요
            chart_h = st.slider("Chart height", 300, 800, 520)

    if uploaded_files:
        current_file = uploaded_files[st.session_state.file_index]
        df = pd.read_csv(current_file, encoding='utf-8-sig')
        
        # 데이터 클리닝 및 전처리
        rename_map = {'날짜': 'Date', '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close', '거래량': 'Volume'}
        df = df.rename(columns=rename_map)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df = df.sort_values('Date')
        comp_name = df['종목명'].iloc[0] if '종목명' in df.columns else current_file.name

        # [항상 고정된 최상단 툴바: < 회사명 슬라이더 >]
        t_col1, t_col2, t_col3, t_col4 = st.columns([0.6, 2.5, 3.5, 0.6])
        with t_col1:
            if st.button("◀"):
                st.session_state.file_index = (st.session_state.file_index - 1) % len(uploaded_files)
                st.rerun()
        with t_col2:
            st.markdown(f"<div style='text-align:center; line-height:40px; font-size:16px; color:#F0B90B;'><b>{comp_name}</b></div>", unsafe_allow_html=True)
        with t_col3:
            zoom_val = st.slider("R", 10, len(df), min(120, len(df)), step=10, label_visibility="collapsed")
        with t_col4:
            if st.button("▶"):
                st.session_state.file_index = (st.session_state.file_index + 1) % len(uploaded_files)
                st.rerun()

        # 데이터 슬라이싱
        display_df = df.tail(zoom_val)

        # 차트 생성 (Row 1: 가격, Row 2: 거래량)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.75, 0.25])

        # 캔들스틱
        fig.add_trace(go.Candlestick(
            x=display_df['Date'], open=display_df['Open'], high=display_df['High'],
            low=display_df['Low'], close=display_df['Close'], name="Price",
            increasing_line_color='#FF3232', decreasing_line_color='#0066FF'
        ), row=1, col=1)

        # 거래량 (캔들 색상 연동)
        v_cols = ['#FF3232' if r['Close'] >= r['Open'] else '#0066FF' for _, r in display_df.iterrows()]
        fig.add_trace(go.Bar(x=display_df['Date'], y=display_df['Volume'], marker_color=v_cols), row=2, col=1)

        # [지표 레이어 - 모두 실선]
        if show_ma:
            fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA20'], name="MA20", line=dict(color='orange', width=1.5)), row=1, col=1)
            fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA100'], name="MA100", line=dict(color='cyan', width=1.5)), row=1, col=1)
        
        if show_bb:
            for c, clr in [('BB26_Upper1', '#FFFF00'), ('BB52_Upper1', '#FF8C00'), ('WBB52_Upper1', '#DDA0DD')]:
                if c in display_df.columns:
                    fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[c], name=c, line=dict(color=clr, width=1.2)), row=1, col=1)
        
        if show_pc:
            for c, clr in [('PC52_Mid', '#ADFF2F'), ('PC129_Mid', '#00FF7F'), ('PC645_Mid', '#FFFFFF')]:
                if c in display_df.columns:
                    fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[c], name=c, line=dict(color=clr, width=1.5)), row=1, col=1)

        # [MTS 핵심 조작 설정]
        # 1. 휴장일 공백 제거
        fig.update_xaxes(type='category', row=1, col=1)
        fig.update_xaxes(type='category', nticks=5, row=2, col=1)
        
        # 2. 우측 가격축 & Y축 높낮이 조절(드래그) 활성화 & 자동 스케일
        fig.update_yaxes(side="right", gridcolor="#333", autorange=True, fixedrange=False, row=1, col=1)
        fig.update_yaxes(side="right", showgrid=False, autorange=True, fixedrange=False, row=2, col=1)

        fig.update_layout(
            height=chart_h,
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            margin=dict(l=5, r=45, t=5, b=5),
            showlegend=False,
            dragmode='pan', # 차트 이동 기본
            hovermode='x unified',
            # 캔들 없는 영역으로 나가지 않도록 고정
            xaxis=dict(range=[-0.5, zoom_val - 0.5])
        )

        # 자동 맞춤 버튼(Fit)
        fig.update_layout(updatemenus=[dict(
            type="buttons", showactive=False, x=0.01, y=0.99,
            buttons=[dict(label="FIT", method="relayout", args=[{"yaxis.autorange": True, "yaxis2.autorange": True}])]
        )])

        st.plotly_chart(fig, use_container_width=True, config={
            'scrollZoom': True,      # 핀치 줌 활성화
            'displayModeBar': False, # 상단 툴바 제거
            'responsive': True,
            'doubleClick': 'reset'
        })
    else:
        st.info("📂 왼쪽 사이드바(>)를 열어 데이터를 업로드하세요.")