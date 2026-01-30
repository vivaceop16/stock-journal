"""
주식 매매일지 웹 앱 - 메인 애플리케이션
"""

import streamlit as st
from database import init_db, db_manager

# 페이지 설정
st.set_page_config(
    page_title="주식 매매일지",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 데이터베이스 초기화
@st.cache_resource
def initialize_database():
    init_db()
    return True

initialize_database()

# 메인 페이지
st.title("📈 주식 매매일지")
st.markdown("---")

# 간단한 소개
st.markdown("""
### 환영합니다!

이 앱은 여러분의 주식 매매를 기록하고 분석하여 **투자 실력을 향상**시키는 데 도움을 드립니다.

#### 주요 기능

| 기능 | 설명 |
|------|------|
| 📝 **매매 입력** | 매수/매도 기록과 매매 근거를 상세히 기록 |
| 📊 **매매 목록** | 전체 매매 기록 조회 및 관리 |
| 🤖 **AI 분석** | 매매 근거의 논리성과 타이밍을 AI가 분석하여 점수 산출 |
| 📚 **학습 가이드** | 약점 패턴을 분석하여 개인화된 학습 과제 제공 |
| 📈 **월간 리포트** | 승률, 손익비, 매매 패턴 등 월간 성과 대시보드 |

#### 시작하기

왼쪽 사이드바에서 원하는 메뉴를 선택하세요.

1. **매매 입력**에서 첫 번째 거래를 기록해보세요
2. 매도 시에는 해당 매수 건과 연결하여 수익률을 자동 계산
3. **AI 분석**에서 매매 점수와 피드백을 확인
4. **월간 리포트**에서 전체 성과를 파악

""")

# 사이드바
with st.sidebar:
    st.markdown("### ⚙️ 설정")

    # API 키 입력 (세션에 저장)
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ''

    api_key = st.text_input(
        "OpenAI API Key (선택)",
        value=st.session_state.openai_api_key,
        type="password",
        help="AI 분석 기능을 사용하려면 OpenAI API 키가 필요합니다."
    )

    if api_key != st.session_state.openai_api_key:
        st.session_state.openai_api_key = api_key
        import os
        os.environ['OPENAI_API_KEY'] = api_key

# 최근 매매 요약 (있는 경우)
st.markdown("---")
st.subheader("📊 최근 매매 요약")

try:
    from services import TradeService
    trade_service = TradeService()
    recent_trades = trade_service.list_trades(limit=5)

    if recent_trades:
        import pandas as pd

        df_data = []
        for trade in recent_trades:
            df_data.append({
                '날짜': trade.trade_date,
                '종목': trade.stock_name,
                '유형': '매수' if trade.trade_type == 'BUY' else '매도',
                '가격': f"{trade.price:,.0f}원",
                '수량': trade.quantity,
                '수익률': f"{trade.profit_rate:.2f}%" if trade.profit_rate else "-"
            })

        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("아직 매매 기록이 없습니다. '매매 입력'에서 첫 거래를 기록해보세요!")

except Exception as e:
    st.warning(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")

# 푸터
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "📈 주식 매매일지 v1.0 | 꾸준한 기록이 실력이 됩니다"
    "</div>",
    unsafe_allow_html=True
)
