import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정
st.set_page_config(page_title="MTS 주식 분석", layout="wide")

# 2. 세션 상태 초기화
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
    tab1, tab2, tab3 = st.tabs(["📊 현재가 차트", "🛠 지표 설정", "📂 파일 관리"])

    with tab3:
        uploaded_files = st.file_uploader(
            "CSV 파일들을 선택하세요", 
            type=['csv', 'txt'], 
            accept_multiple_files=True
        )
        if uploaded_files:
            st.success(f"{len(uploaded_files)}개의 파일이 로드되었습니다.")
            if 'last_upload_count' not in st.session_state or st.session_state.last_upload_count != len(uploaded_files):
                st.session_state.file_index = 0
                st.session_state.last_upload_count = len(uploaded_files)

    if uploaded_files:
        current_file = uploaded_files[st.session_state.file_index]
        df = pd.read_csv(current_file, encoding='utf-8-sig')
        
        # 파일명 및 회사명 처리
        file_display_name = current_file.name
        if '종목명' in df.columns and not df['종목명'].empty:
            company_name = df['종목명'].iloc[0]
            file_display_name = f"[{company_name}] {current_file.name}"
        
        # 데이터 정리
        rename_map = {'날짜': 'Date', '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close', '거래량': 'Volume'}
        df = df.rename(columns=rename_map)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df = df.sort_values('Date')

        with tab2:
            st.write("🔧 분석 도구 (세분화)")
            c1, c2 = st.columns(2)
            with c1:
                st.info("볼린저 밴드 (상단)")
                show_bb26 = st.checkbox("BB26 Upper", value=False)
                show_bb52 = st.checkbox("BB52 Upper", value=False)
                show_bb129 = st.checkbox("BB129 Upper", value=False)
                show_bb260 = st.checkbox("BB260 Upper", value=False)
                show_wbb52 = st.checkbox("WBB52 Upper", value=False)
                show_wbb129 = st.checkbox("WBB129 Upper", value=False)
                
                st.info("이동평균선")
                show_ma20 = st.toggle("MA20", False)
                show_ma100 = st.toggle("MA100", False)
            with c2:
                st.info("가격 채널 (중심선)")
                show_pc52 = st.checkbox("PC52 Mid", value=False)
                show_pc129 = st.checkbox("PC129 Mid", value=False)
                show_pc260 = st.checkbox("PC260 Mid", value=False)
                show_pc645 = st.checkbox("PC645 Mid", value=False)

        with tab1:
            # 상단 컨트롤러 (순환 기능 유지)
            col_prev, col_info, col_next = st.columns([1, 4, 1])
            with col_prev:
                if st.button("◀ 이전"):
                    st.session_state.file_index = (st.session_state.file_index - 1) % len(uploaded_files)
                    st.rerun()
            with col_info:
                st.markdown(f"<center><h3 style='margin:0;'>{file_display_name}</h3></center>", unsafe_allow_html=True)
            with col_next:
                if st.button("다음 ▶"):
                    st.session_state.file_index = (st.session_state.file_index + 1) % len(uploaded_files)
                    st.rerun()

            # 차트 범위 슬라이더
            total_len = len(df)
            zoom_val = st.slider(
                "🔍 보기 범위", 
                min_value=10, 
                max_value=total_len, 
                value=min(100, total_len),
                step=10
            )
            
            display_df = df.tail(zoom_val)

            # 차트 구성 (2단 구성 유지)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])

            # 캔들스틱 (뭉개짐 완화 설정 유지)
            fig.add_trace(go.Candlestick(
                x=display_df['Date'], open=display_df['Open'], high=display_df['High'],
                low=display_df['Low'], close=display_df['Close'], name="가격",
                increasing_line_color='#FF3232', decreasing_line_color='#0066FF',
                line=dict(width=1.5)
            ), row=1, col=1)

            # 거래량
            v_colors = ['#FF3232' if r['Close'] >= r['Open'] else '#0066FF' for _, r in display_df.iterrows()]
            fig.add_trace(go.Bar(x=display_df['Date'], y=display_df['Volume'], name="거래량", marker_color=v_colors, opacity=0.8), row=2, col=1)

            # [세분화된 지표 레이어]
            # 1. 이동평균선 (실선)
            if show_ma20: fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA20'], name="MA20", line=dict(color='orange', width=1.5)), row=1, col=1)
            if show_ma100: fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA100'], name="MA100", line=dict(color='cyan', width=1.5)), row=1, col=1)
            
            # 2. 볼린저 밴드 (점선 -> 실선으로 변경)
            bb_map = [
                ('BB26_Upper1', show_bb26, '#FFFF00'), ('BB52_Upper1', show_bb52, '#FF8C00'), 
                ('BB129_Upper1', show_bb129, '#FF5722'), ('BB260_Upper1', show_bb260, '#E91E63'),
                ('WBB52_Upper1', show_wbb52, '#DDA0DD'), ('WBB129_Upper1', show_wbb129, '#EE82EE')
            ]
            for col, show, color in bb_map:
                if show and col in display_df.columns:
                    # dash='dot' 제거하여 실선으로 출력
                    fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[col], name=col, line=dict(color=color, width=1)), row=1, col=1)

            # 3. 가격 채널 (실선 유지)
            pc_map = [
                ('PC52_Mid', show_pc52, '#ADFF2F'), ('PC129_Mid', show_pc129, '#00FF7F'),
                ('PC260_Mid', show_pc260, '#00BFFF'), ('PC645_Mid', show_pc645, '#FFFFFF')
            ]
            for col, show, color in pc_map:
                if show and col in display_df.columns:
                    fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[col], name=col, line=dict(color=color, width=1.2)), row=1, col=1)

            # 레이아웃 (오른쪽 가격축, 핀치 줌 유지)
            fig.update_xaxes(type='category', nticks=6, row=2, col=1)
            fig.update_yaxes(side="right", gridcolor="#333", row=1, col=1)
            
            fig.update_layout(
                height=650, template="plotly_dark",
                xaxis_rangeslider_visible=True,
                xaxis_rangeslider_thickness=0.04,
                margin=dict(l=5, r=45, t=10, b=10),
                showlegend=False,
                dragmode='zoom', 
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True, config={
                'scrollZoom': True,
                'displayModeBar': False,
                'responsive': True,
                'doubleClick': 'reset'
            })
            
    else:
        st.info("📂 '파일 관리' 탭에서 CSV 파일을 업로드하세요.")