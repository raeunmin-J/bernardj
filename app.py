import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정
st.set_page_config(page_title="MTS 주식 분석", layout="wide")

# 2. 세션 상태 초기화 (파일 인덱스 관리)
if 'file_index' not in st.session_state:
    st.session_state.file_index = 0

def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 MTS 시스템 로그인")
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
    # 상단 탭 구성
    tab1, tab2, tab3 = st.tabs(["📊 현재가 차트", "🛠 지표 설정", "📂 파일 관리"])

    with tab3:
        # accept_multiple_files=True를 설정하여 여러 파일을 한 번에 업로드 가능하게 함
        uploaded_files = st.file_uploader(
            "CSV 파일들을 한 번에 선택하세요 (구글 드라이브 가능)", 
            type=['csv'], 
            accept_multiple_files=True
        )
        if uploaded_files:
            st.success(f"{len(uploaded_files)}개의 파일이 로드되었습니다.")
            # 파일 리스트가 바뀌면 인덱스 초기화
            if 'last_upload_count' not in st.session_state or st.session_state.last_upload_count != len(uploaded_files):
                st.session_state.file_index = 0
                st.session_state.last_upload_count = len(uploaded_files)

    if uploaded_files:
        # 현재 선택된 파일 가져오기
        current_file = uploaded_files[st.session_state.file_index]
        df = pd.read_csv(current_file)
        
        # 데이터 정리
        rename_map = {'날짜': 'Date', '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close', '거래량': 'Volume'}
        df = df.rename(columns=rename_map)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df = df.sort_values('Date')

        with tab2:
            st.write("🔧 분석 도구함")
            c1, c2 = st.columns(2)
            with c1:
                st.info("이동평균선")
                show_ma20 = st.toggle("MA20", False)
                show_ma100 = st.toggle("MA100", False)
            with c2:
                st.info("밴드/채널")
                show_bb = st.toggle("Bollinger Upper", False)
                show_pc = st.toggle("Price Channel Mid", False)

        with tab1:
            # [파일 넘기기 컨트롤러]
            col_prev, col_info, col_next = st.columns([1, 3, 1])
            
            with col_prev:
                if st.button("◀ 이전"):
                    # 처음에서 누르면 마지막으로 이동
                    st.session_state.file_index = (st.session_state.file_index - 1) % len(uploaded_files)
                    st.rerun()
            
            with col_info:
                st.markdown(f"<center><b>{current_file.name}</b> ({st.session_state.file_index + 1} / {len(uploaded_files)})</center>", unsafe_allow_html=True)
            
            with col_next:
                if st.button("다음 ▶"):
                    # 마지막에서 누르면 처음으로 이동 (순환)
                    st.session_state.file_index = (st.session_state.file_index + 1) % len(uploaded_files)
                    st.rerun()

            # 줌 슬라이더
            zoom_val = st.select_slider("🔍 차트 범위", options=[30, 60, 100, 200, 300], value=100)
            display_df = df.tail(zoom_val)

            # 차트 구성 (기존 MTS 로직 유지)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])

            # 캔들스틱
            fig.add_trace(go.Candlestick(
                x=display_df['Date'], open=display_df['Open'], high=display_df['High'],
                low=display_df['Low'], close=display_df['Close'], name="가격",
                increasing_line_color='#FF3232', decreasing_line_color='#0066FF'
            ), row=1, col=1)

            # 거래량
            v_colors = ['#FF3232' if r['Close'] >= r['Open'] else '#0066FF' for _, r in display_df.iterrows()]
            fig.add_trace(go.Bar(x=display_df['Date'], y=display_df['Volume'], marker_color=v_colors, opacity=0.8), row=2, col=1)

            # 지표 표시
            if show_ma20: fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA20'], name="MA20", line=dict(color='orange', width=1)), row=1, col=1)
            if show_ma100: fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA100'], name="MA100", line=dict(color='cyan', width=1)), row=1, col=1)
            
            # 레이아웃 설정
            fig.update_xaxes(type='category', nticks=5, showgrid=False, row=2, col=1)
            fig.update_xaxes(type='category', visible=False, row=1, col=1)
            fig.update_yaxes(side="right", gridcolor="#333", row=1, col=1)
            fig.update_yaxes(side="right", showgrid=False, row=2, col=1)

            fig.update_layout(
                height=550, template="plotly_dark", xaxis_rangeslider_visible=False,
                margin=dict(l=5, r=40, t=5, b=5), showlegend=False, dragmode='pan'
            )

            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
    else:
        st.info("📂 '파일 관리' 탭에서 여러 개의 CSV 파일을 한 번에 업로드하세요.")