"""
AI 분석 페이지
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta

from database import init_db
from database.models import AnalysisResult
from services import TradeService, AIAnalyzer
from styles import apply_toss_style

# 페이지 설정
st.set_page_config(page_title="AI 분석", page_icon="🤖", layout="wide")

# 토스 스타일 적용
apply_toss_style()

# 데이터베이스 초기화
init_db()

# 헤더
st.markdown("""
<div style="padding: 20px 0 10px 0;">
    <h1 style="font-size: 24px; font-weight: 700; color: #191F28; margin: 0;">
        AI 분석
    </h1>
    <p style="font-size: 14px; color: #8B95A1; margin-top: 6px;">
        매매를 분석하고 점수를 확인해요
    </p>
</div>
""", unsafe_allow_html=True)

# 서비스 초기화
trade_service = TradeService()
ai_analyzer = AIAnalyzer()

# API 키 체크 - 안내 메시지 개선
api_key = st.session_state.get('openai_api_key', '')
if api_key:
    st.success("✅ OpenAI API 연결됨 - GPT 기반 상세 분석 제공")
else:
    st.info("💡 규칙 기반 분석을 제공합니다. (OpenAI API 없이도 사용 가능)")

# 최근 매매 목록
recent_trades = trade_service.list_trades(limit=20)

if not recent_trades:
    st.info("분석할 매매 기록이 없습니다. 먼저 '매매 입력'에서 매매를 기록해주세요.")
    st.stop()

# 분석할 매매가 선택되었는지 확인
selected_trade_id = st.session_state.get('analyze_trade_id')
selected_trade = None
existing_analysis = None

if selected_trade_id:
    selected_trade = trade_service.get_trade(selected_trade_id)
    if selected_trade:
        existing_analysis = ai_analyzer.get_analysis_for_trade(selected_trade_id)

# 분석 실행 처리
if st.session_state.get('run_analysis') and selected_trade:
    with st.spinner("분석 중..."):
        try:
            analysis = ai_analyzer.analyze_trade(selected_trade)
            st.success("분석이 완료되었습니다!")
            existing_analysis = analysis
            st.session_state['run_analysis'] = False
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")
            import traceback
            st.code(traceback.format_exc())
            st.session_state['run_analysis'] = False

# 매매 목록 게시판 형태
st.markdown("""
<div style="background: #FFFFFF; border-radius: 12px; overflow: hidden; border: 1px solid #E5E8EB; margin-bottom: 24px;">
""", unsafe_allow_html=True)

# 헤더
col_h1, col_h2, col_h3, col_h4, col_h5, col_h6 = st.columns([0.9, 1.5, 0.7, 1, 1, 0.7])
with col_h1:
    st.markdown('<div style="font-size: 13px; font-weight: 600; color: #6B7684; padding: 8px 0;">날짜</div>', unsafe_allow_html=True)
with col_h2:
    st.markdown('<div style="font-size: 13px; font-weight: 600; color: #6B7684; padding: 8px 0;">종목</div>', unsafe_allow_html=True)
with col_h3:
    st.markdown('<div style="font-size: 13px; font-weight: 600; color: #6B7684; padding: 8px 0;">유형</div>', unsafe_allow_html=True)
with col_h4:
    st.markdown('<div style="font-size: 13px; font-weight: 600; color: #6B7684; padding: 8px 0;">가격</div>', unsafe_allow_html=True)
with col_h5:
    st.markdown('<div style="font-size: 13px; font-weight: 600; color: #6B7684; padding: 8px 0;">손익</div>', unsafe_allow_html=True)
with col_h6:
    st.markdown('<div style="font-size: 13px; font-weight: 600; color: #6B7684; padding: 8px 0; text-align: center;">분석</div>', unsafe_allow_html=True)

st.markdown('<div style="border-bottom: 1px solid #E5E8EB;"></div>', unsafe_allow_html=True)

for trade in recent_trades:
    trade_type_str = "매수" if trade.trade_type == "BUY" else "매도"
    trade_color = "#3182F6" if trade.trade_type == "BUY" else "#F04452"
    trade_bg = "#E8F3FF" if trade.trade_type == "BUY" else "#FFEFEF"

    # 손익 표시
    if trade.profit_rate is not None:
        profit_color = "#F04452" if trade.profit_rate > 0 else "#3182F6"
        profit_str = f"{'+' if trade.profit_rate > 0 else ''}{float(trade.profit_loss):,.0f}원"
    else:
        profit_color = "#8B95A1"
        profit_str = "-"

    # 기존 분석 여부 확인
    has_analysis = ai_analyzer.get_analysis_for_trade(trade.id) is not None

    # 선택된 행 하이라이트
    row_bg = "#F0F6FF" if selected_trade_id == trade.id else "#FFFFFF"

    # 각 행을 컨테이너로
    with st.container():
        col1, col2, col3, col4, col5, col6 = st.columns([0.9, 1.5, 0.7, 1, 1, 0.7])

        with col1:
            st.markdown(f'<div style="color: #6B7684; font-size: 14px; padding: 8px 0;">{trade.trade_date}</div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div style="font-weight: 600; color: #191F28; padding: 8px 0;">{trade.stock_name}</div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div style="padding: 8px 0;"><span style="background: {trade_bg}; color: {trade_color}; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;">{trade_type_str}</span></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div style="color: #191F28; padding: 8px 0;">{float(trade.price):,.0f}원</div>', unsafe_allow_html=True)
        with col5:
            st.markdown(f'<div style="color: {profit_color}; font-weight: 600; padding: 8px 0;">{profit_str}</div>', unsafe_allow_html=True)
        with col6:
            btn_label = "🔄 재분석" if has_analysis else "🔍 분석"
            if st.button(btn_label, key=f"analyze_{trade.id}", use_container_width=True):
                st.session_state['analyze_trade_id'] = trade.id
                st.session_state['run_analysis'] = True
                st.rerun()

    st.markdown('<div style="border-bottom: 1px solid #F2F3F5;"></div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# 선택된 매매 정보 표시
if selected_trade:
    st.markdown("---")
    st.subheader(f"📈 {selected_trade.stock_name} 분석")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("거래일", str(selected_trade.trade_date))
    with col2:
        st.metric("유형", "매수" if selected_trade.trade_type == "BUY" else "매도")
    with col3:
        st.metric("가격", f"{selected_trade.price:,.0f}원 × {selected_trade.quantity}주")
    with col4:
        if selected_trade.profit_rate is not None:
            st.metric("수익률", f"{selected_trade.profit_rate:+.2f}%")
        else:
            st.metric("확신도", f"{selected_trade.confidence_score}/10")

    if selected_trade.trade_reason:
        st.markdown(f"""
        <div style="background: #F7F8FA; border-radius: 8px; padding: 12px 16px; margin: 12px 0;">
            <div style="color: #8B95A1; font-size: 12px; margin-bottom: 4px;">매매 근거</div>
            <div style="color: #191F28; font-size: 14px; line-height: 1.6;">{selected_trade.trade_reason}</div>
        </div>
        """, unsafe_allow_html=True)

# 분석 결과 표시
if existing_analysis:
    st.markdown("---")
    st.subheader("📊 분석 결과")

    # 점수 게이지
    col1, col2 = st.columns([1, 2])

    with col1:
        # 종합 점수 게이지
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=existing_analysis.total_score or 0,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "종합 점수"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 40], 'color': "lightcoral"},
                    {'range': [40, 70], 'color': "lightyellow"},
                    {'range': [70, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 50
                }
            }
        ))
        fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

        # 점수 해석
        score = existing_analysis.total_score or 0
        if score >= 80:
            st.success("🌟 훌륭한 매매입니다!")
        elif score >= 60:
            st.info("👍 양호한 매매입니다")
        elif score >= 40:
            st.warning("⚠️ 개선이 필요합니다")
        else:
            st.error("❌ 매매 전략 재검토 필요")

    with col2:
        # 항목별 점수 레이더 차트
        categories = ['논리성\n(40점)', '타이밍\n(30점)', '리스크관리\n(20점)', '확신도정확성\n(10점)']
        values = [
            (existing_analysis.logic_score or 0) / 40 * 100,
            (existing_analysis.timing_score or 0) / 30 * 100,
            (existing_analysis.risk_management_score or 0) / 20 * 100,
            (existing_analysis.confidence_accuracy_score or 0) / 10 * 100
        ]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values + [values[0]],  # 닫힌 도형을 위해 첫 값 추가
            theta=categories + [categories[0]],
            fill='toself',
            name='점수'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            height=300,
            margin=dict(l=60, r=60, t=30, b=30)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # 상세 점수
    st.markdown("#### 📋 항목별 점수")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "논리성",
            f"{existing_analysis.logic_score or 0}/40",
            help="매매 근거의 구체성, 논리적 일관성"
        )
    with col2:
        st.metric(
            "타이밍",
            f"{existing_analysis.timing_score or 0}/30",
            help="진입/청산 시점의 적절성"
        )
    with col3:
        st.metric(
            "리스크관리",
            f"{existing_analysis.risk_management_score or 0}/20",
            help="손절/익절 계획, 포지션 사이즈"
        )
    with col4:
        st.metric(
            "확신도 정확성",
            f"{existing_analysis.confidence_accuracy_score or 0}/10",
            help="확신도와 실제 결과의 상관관계"
        )

    # 추출된 키워드
    if existing_analysis.extracted_keywords:
        st.markdown("---")
        st.markdown("#### 🏷️ 추출된 키워드")

        keywords = existing_analysis.extracted_keywords
        if isinstance(keywords, dict):
            for category, kw_list in keywords.items():
                if kw_list:
                    st.markdown(f"**{category}:** {', '.join(kw_list)}")
        else:
            st.write("키워드 없음")

    # 패턴 분류
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 매매 패턴")
        if existing_analysis.trade_pattern:
            pattern_colors = {
                '기술분석_기반': '🔵',
                '펀더멘털_기반': '🟢',
                '뉴스_기반': '🟡',
                '심리적_매매': '🟠',
                '충동매매': '🔴',
                '복합_분석': '🟣'
            }
            color = pattern_colors.get(existing_analysis.trade_pattern, '⚪')
            st.info(f"{color} **{existing_analysis.trade_pattern}**")
        else:
            st.info("⚪ **분류 없음**")

    with col2:
        st.markdown("#### ⚠️ 약점 패턴")
        if existing_analysis.weakness_category:
            st.warning(f"**{existing_analysis.weakness_category}**")
        else:
            st.success("**발견된 약점 없음**")

    # AI 피드백
    if existing_analysis.ai_feedback:
        st.markdown("---")
        st.markdown("#### 💬 분석 피드백")
        st.text_area(
            "피드백",
            value=existing_analysis.ai_feedback,
            height=200,
            disabled=True,
            label_visibility="collapsed"
        )

    # 시장 상황 분석
    if existing_analysis.market_context:
        st.markdown("---")
        st.markdown("#### 🌍 시장 상황 분석")
        st.write(existing_analysis.market_context)

elif selected_trade:
    st.info("👆 위 목록에서 🔍 버튼을 클릭하여 분석을 시작하세요.")
else:
    st.info("👆 위 목록에서 분석할 매매의 🔍 버튼을 클릭하세요.")

# 전체 분석 통계
st.markdown("---")
st.subheader("📈 전체 분석 통계")

try:
    # 모든 분석 결과 조회
    all_analyses = ai_analyzer.session.query(AnalysisResult).all()

    if all_analyses:
        # 점수별 분포
        scores = [a.total_score for a in all_analyses if a.total_score is not None]

        if scores:
            col1, col2, col3 = st.columns(3)

            with col1:
                avg_score = sum(scores) / len(scores)
                st.metric("평균 점수", f"{avg_score:.1f}점")

            with col2:
                high_scores = len([s for s in scores if s >= 60])
                st.metric("양호 이상 (60점+)", f"{high_scores}건")

            with col3:
                low_scores = len([s for s in scores if s < 60])
                st.metric("개선 필요 (60점 미만)", f"{low_scores}건")

            # 점수 분포 히스토그램
            if len(scores) >= 3:
                fig_hist = px.histogram(
                    x=scores,
                    nbins=10,
                    title="점수 분포",
                    labels={'x': '점수', 'y': '개수'}
                )
                fig_hist.update_layout(height=300)
                st.plotly_chart(fig_hist, use_container_width=True)

            # 낮은 점수 경고
            if low_scores > 0:
                st.warning(f"⚠️ 60점 미만의 매매가 **{low_scores}건** 있습니다. "
                           "'학습 가이드'에서 개선 방안을 확인하세요.")
        else:
            st.info("점수 데이터가 없습니다.")
    else:
        st.info("아직 분석된 매매가 없습니다. 위에서 매매를 선택하고 분석해보세요.")

except Exception as e:
    st.info("분석 통계를 불러오는 중입니다...")
