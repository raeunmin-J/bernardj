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
        
        # 날짜 문자열 변환 (주말 공백 제거용)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df = df.sort_values('Date')
        
        # [사이드바 설정]
        st.sidebar.header("📊 차트 설정")
        view_count = st.sidebar.slider("표시 데이터 개수", 30, len(df), 200)
        
        # 1. 이동평균선 (MA)
        st.sidebar.subheader("이동평균선 (MA)")
        show_ma20 = st.sidebar.checkbox("MA20", value=False)
        show_ma100 = st.sidebar.checkbox("MA100", value=False)
        show_ma300 = st.sidebar.checkbox("MA300", value=False)
        
        # 2. 볼린저 밴드 (BB Upper) - 점선 유지
        st.sidebar.subheader("볼린저 밴드 (상단선)")
        show_bb26 = st.sidebar.checkbox("BB26 Upper", value=False)
        show_bb52 = st.sidebar.checkbox("BB52 Upper", value=False)
        show_bb129 = st.sidebar.checkbox("BB129 Upper", value=False)
        show_bb260 = st.sidebar.checkbox("BB260 Upper", value=False)
        
        # 3. 가격 채널 (Price Channel Mid) - 실선으로 변경
        st.sidebar.subheader("가격 채널 (중심선)")
        show_pc52 = st.sidebar.checkbox("PC52 Mid", value=False)
        show_pc129 = st.sidebar.checkbox("PC129 Mid", value=False)
        show_pc260 = st.sidebar.checkbox("PC260 Mid", value=False)
        show_pc645 = st.sidebar.checkbox("PC645 Mid", value=False)

        display_df = df.tail(view_count)

        # 차트 생성
        fig = go.Figure()

        # [기본] 캔들스틱
        fig.add_trace(go.Candlestick(
            x=display_df['Date'],
            open=display_df['Open'], high=display_df['High'],
            low=display_df['Low'], close=display_df['Close'],
            name="가격",
            increasing_line_color='#ef5350', decreasing_line_color='#2962ff'
        ))

        # [지표 추가] 이동평균선 (실선)
        ma_cfg = [('MA20', show_ma20, 'orange'), ('MA100', show_ma100, 'cyan'), ('MA300', show_ma300, 'purple')]
        for col, show, color in ma_cfg:
            if show and col in display_df.columns:
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[col], name=col, line=dict(color=color, width=1.5)))

        # [지표 추가] 볼린저 밴드 상단선 (점선 유지)
        bb_cfg = [
            ('BB26_Upper1', show_bb26, '#FFEB3B'), 
            ('BB52_Upper1', show_bb52, '#FF9800'), 
            ('BB129_Upper1', show_bb129, '#FF5722'),
            ('BB260_Upper1', show_bb260, '#E91E63')
        ]
        for col, show, color in bb_cfg:
            if show and col in display_df.columns:
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[col], name=col, line=dict(color=color, width=1, dash='dot')))

        # [지표 추가] 가격 채널 중심선 (점선 -> 실선으로 변경됨)
        pc_cfg = [
            ('PC52_Mid', show_pc52, 'yellow'), 
            ('PC129_Mid', show_pc129, 'lightgreen'),
            ('PC260_Mid', show_pc260, 'skyblue'),
            ('PC645_Mid', show_pc645, 'white')
        ]
        for col, show, color in pc_cfg:
            if show and col in display_df.columns:
                # dash='dash' 제거하여 실선으로 출력
                fig.add_trace(go.Scatter(x=display_df['Date'], y=display_df[col], name=col, line=dict(color=color, width=1.2)))

        # 주말 공백 제거 설정
        fig.update_xaxes(type='category', nticks=10)

        # 레이아웃 설정
        fig.update_layout(
            height=750, 
            template="plotly_dark", 
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("데이터 테이블 보기"):
            st.dataframe(display_df.iloc[::-1])
    else:
        st.info("사이드바에서 CSV 파일을 업로드해 주세요.")