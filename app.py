import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="주식 분석 앱", layout="wide")

# 1. 보안 설정 (Secrets에서 MY_PASSWORD를 설정해야 함)
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 주식 분석 시스템 로그인")
        password = st.text_input("비밀번호를 입력하세요", type="password")
        if st.button("로그인"):
            if password == st.secrets.get("MY_PASSWORD", "1234"): # 설정 안했을 시 기본값 1234
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
        return False
    return True

# 2. 메인 로직
if check_password():
    st.title("📈 전용 주식 차트 대시보드")
    
    uploaded_file = st.sidebar.file_uploader("CSV 파일을 업로드하세요 (002350.csv 형식 지원)", type=['csv'])

    if uploaded_file:
        # 데이터 로드
        df = pd.read_csv(uploaded_file)
        
        # 컬럼명 매핑 (업로드하신 파일의 한글 이름을 영문으로 변환)
        rename_map = {
            '날짜': 'Date', '시가': 'Open', '고가': 'High', 
            '저가': 'Low', '종가': 'Close', '거래량': 'Volume'
        }
        df = df.rename(columns=rename_map)
        
        # 날짜 변환 및 정렬
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
            
            # 사이드바 옵션
            st.sidebar.header("차트 설정")
            view_count = st.sidebar.slider("표시할 데이터 개수", 30, len(df), 200)
            show_ma = st.sidebar.toggle("이동평균선 표시 (CSV 데이터)", value=True)
            show_cloud = st.sidebar.toggle("일목균형표 구름대 표시", value=True)
            
            display_df = df.tail(view_count)

            # 차트 생성
            fig = go.Figure()

            # 캔들스틱 (봉차트)
            fig.add_trace(go.Candlestick(
                x=display_df['Date'],
                open=display_df['Open'], high=display_df['High'],
                low=display_df['Low'], close=display_df['Close'],
                name="가격",
                increasing_line_color='#ef5350', # 상승 빨강
                decreasing_line_color='#2962ff'  # 하락 파랑
            ))

            # CSV에 포함된 MA20, MA100 그리기
            if show_ma:
                if 'MA20' in display_df.columns:
                    fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA20'], name="MA20", line=dict(color='orange', width=1.5)))
                if 'MA100' in display_df.columns:
                    fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['MA100'], name="MA100", line=dict(color='cyan', width=1.5)))

            # CSV에 포함된 일목균형표 선행스팬 데이터로 구름대 그리기
            if show_cloud and 'Ichimoku_SenkouA' in display_df.columns and 'Ichimoku_SenkouB' in display_df.columns:
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df['Ichimoku_SenkouA'], line=dict(width=0), showlegend=False))
                fig.add_trace(go.Scatter(
                    x=display_df['Date'], y=display_df['Ichimoku_SenkouB'],
                    fill='tonexty', fillcolor='rgba(173, 216, 230, 0.2)',
                    line=dict(width=0), name="일목구름"
                ))

            # 레이아웃 최적화 (모바일 터치 대응)
            fig.update_layout(
                height=700,
                template="plotly_dark",
                xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig, use_container_width=True)
            
            # 하단 데이터 테이블
            with st.expander("원본 데이터 확인"):
                st.dataframe(display_df.iloc[::-1]) # 최근 데이터가 위로 오게 표시
        else:
            st.error("파일에 '날짜' 컬럼이 없습니다. 확인해 주세요.")
    else:
        st.info("좌측 사이드바에서 002350.csv 파일을 업로드해 주세요.")