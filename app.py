import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="주식 분석 시스템", layout="wide")

# 1. 보안 설정
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 주식 분석 시스템 로그인")
        password = st.text_input("비밀번호를 입력하세요", type="password")
        if st.button("로그인"):
            if password == st.secrets.get("MY_PASSWORD", "1234"):
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
        return False
    return True

if check_password():
    st.title("📈 전용 주식 차트 대시보드")
    
    uploaded_file = st.sidebar.file_uploader("CSV 파일을 업로드하세요", type=['csv'])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        # 컬럼명 매핑 (한글 -> 영문)
        rename_map = {
            '날짜': 'Date', '시가': 'Open', '고가': 'High', 
            '저가': 'Low', '종가': 'Close', '거래량': 'Volume'
        }
        df = df.rename(columns=rename_map)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d') # 날짜 형식 문자열화 (공백 제거를 위함)
        df = df.sort_values('Date')
        
        # [사이드바 설정]
        st.sidebar.header("📊 차트 설정")
        view_count = st.sidebar.slider("표시 데이터 개수", 30, len(df), 200)
        
        # 기술적 지표 설정 (모두 value=False로 시작)
        st.sidebar.subheader("이동평균선 (MA)")
        show_ma20 = st.sidebar.checkbox("MA20", value=False)
        show_ma100 = st.sidebar.checkbox("MA100", value=False)
        show_ma300 = st.sidebar.checkbox("MA300", value=False)
        
        st.sidebar.subheader("일목균형표")
        show_cloud = st.sidebar.checkbox("일목 구름대", value=False)
        show_ichi_lines = st.sidebar.checkbox("전환선/기준선", value=False)
        
        st.sidebar.subheader("볼린저 밴드 & 채널")
        show_bb = st.sidebar.checkbox("Bollinger Upper (26, 52, 129)", value=False)
        show_pc = st.sidebar.checkbox("Price Channel (Mid)", value=False)

        st.sidebar.subheader("기타 지표 (DMI/RSI)")
        show_dmi = st.sidebar.checkbox("DMI (PDI/NDI/ADX)", value=False)

        display_df = df.tail(view_count)

        # 차트 생성
        fig = go.Figure()

        # 1. 캔들스틱 (기본)
        fig.add_trace(go.Candlestick(
            x=display_df['Date'],
            open=display_df['Open'], high=display_df['High'],
            low=display_df['Low'], close=display_df['Close'],
            name="가격",
            increasing_line_color='#ef5350', decreasing_line_color='#2962ff'
        ))

        # 2. 이동평균선 추가
        ma_cfg = [('MA20', show_ma20, 'orange'), ('MA100', show_ma100, 'cyan'), ('MA300', show_ma300, 'purple')]
        for col, show, color in ma_cfg:
            if show and col in display_df.columns:
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[col], name=col, line=dict(color=color, width=1.5)))

        # 3. 일목균형표 (구름대 및 주요 선)
        if show_cloud and 'Ichimoku_SenkouA' in display_df.columns:
            fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['Ichimoku_SenkouA'], line=dict(width=0), showlegend=False))
            fig.add_trace(go.Scatter(
                x=display_df['Date'], y=display_df['Ichimoku_SenkouB'],
                fill='tonexty', fillcolor='rgba(173, 216, 230, 0.2)',
                line=dict(width=0), name="일목구름"
            ))
        if show_ichi_lines:
            if 'Ichimoku_Tenkan' in display_df.columns:
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['Ichimoku_Tenkan'], name="전환선", line=dict(color='pink', width=1)))
            if 'Ichimoku_Kijun' in display_df.columns:
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['Ichimoku_Kijun'], name="기준선", line=dict(color='white', width=1)))

        # 4. 가격 채널
        if show_pc:
            pc_cols = [('PC52_Mid', 'yellow'), ('PC129_Mid', 'lightgreen')]
            for col, color in pc_cols:
                if col in display_df.columns:
                    fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[col], name=col, line=dict(color=color, width=1, dash='dash')))

        # 5. 볼린저 밴드 상단선
        if show_bb:
            bb_cols = [('BB26_Upper1', '#FFEB3B'), ('BB52_Upper1', '#FF9800'), ('BB129_Upper1', '#FF5722')]
            for col, color in bb_cols:
                if col in display_df.columns:
                    fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[col], name=col, line=dict(color=color, width=1, dash='dot')))

        # 6. DMI (보조 지표 성격상 가격 차트에 표시)
        if show_dmi:
            if 'DMI52_ADX' in display_df.columns:
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['DMI52_ADX'], name="ADX52", line=dict(color='white', width=1.5)))

        # [핵심 수정] 주말 등 빈 날짜 없이 채우기 (x축을 카테고리 형식으로 지정)
        fig.update_xaxes(type='category', nticks=10)

        # 레이아웃 설정
        fig.update_layout(
            height=700, 
            template="plotly_dark", 
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("원본 데이터 보기"):
            st.dataframe(display_df.iloc[::-1])
    else:
        st.info("사이드바에서 CSV 파일을 업로드해 주세요.")