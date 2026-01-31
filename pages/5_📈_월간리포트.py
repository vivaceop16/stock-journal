"""
월간 리포트 페이지
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, datetime
import pandas as pd

from database import init_db
from services import TradeService, ReportService
from styles import apply_toss_style

# 페이지 설정
st.set_page_config(page_title="월간 리포트", page_icon="📈", layout="wide")

# 토스 스타일 적용
apply_toss_style()

# 데이터베이스 초기화
init_db()

# 헤더
st.markdown("""
<div style="padding: 20px 0 10px 0;">
    <h1 style="font-size: 24px; font-weight: 700; color: #191F28; margin: 0;">
        월간 리포트
    </h1>
    <p style="font-size: 14px; color: #8B95A1; margin-top: 6px;">
        이번 달 투자 성과를 확인해요
    </p>
</div>
""", unsafe_allow_html=True)

# 서비스 초기화
trade_service = TradeService()
report_service = ReportService()

# 월 선택
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    selected_year = st.selectbox(
        "연도",
        options=list(range(date.today().year, 2020, -1)),
        index=0
    )

with col2:
    selected_month = st.selectbox(
        "월",
        options=list(range(1, 13)),
        index=date.today().month - 1,
        format_func=lambda x: f"{x}월"
    )

with col3:
    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
    if st.button("📊 리포트 생성", type="primary", use_container_width=True):
        with st.spinner("리포트 생성 중..."):
            try:
                report = report_service.generate_monthly_report(selected_year, selected_month)
                st.success("리포트가 생성되었습니다!")
            except Exception as e:
                st.error(f"리포트 생성 중 오류: {e}")

# 리포트 조회
report = report_service.get_report(selected_year, selected_month)

if not report:
    st.info(f"{selected_year}년 {selected_month}월 리포트가 없습니다. "
            "'리포트 생성' 버튼을 클릭하여 생성하세요.")
    st.stop()

# 대시보드 데이터
dashboard = report_service.get_dashboard_data(report)
summary = dashboard['summary']
breakdown = dashboard['breakdown']

st.markdown("---")

# 핵심 지표 카드
st.subheader(f"📊 {summary['period']} 성과 요약")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "총 거래",
        f"{summary['total_trades']}건"
    )

with col2:
    st.metric(
        "승률",
        f"{summary['win_rate']:.1f}%",
        delta=f"{summary['win_rate'] - 50:.1f}%p" if summary['win_rate'] != 0 else None
    )

with col3:
    st.metric(
        "손익비",
        f"{summary['profit_loss_ratio']:.2f}",
        delta="Good" if summary['profit_loss_ratio'] >= 1.5 else None
    )

with col4:
    profit_color = "normal" if summary['total_profit_loss'] >= 0 else "inverse"
    st.metric(
        "총 손익",
        f"{summary['total_profit_loss']:+,.0f}원"
    )

with col5:
    st.metric(
        "평균 AI점수",
        f"{summary['average_score']:.0f}점"
    )

st.markdown("---")

# 차트 영역
col1, col2 = st.columns(2)

with col1:
    # 승/패 도넛 차트
    st.markdown("#### 🎯 승률 분석")

    fig_win = go.Figure(data=[go.Pie(
        labels=['수익', '손실'],
        values=[breakdown['winning_trades'], breakdown['losing_trades']],
        hole=0.6,
        marker_colors=['#00CC96', '#EF553B']
    )])
    fig_win.update_layout(
        height=300,
        annotations=[dict(text=f"{summary['win_rate']:.0f}%", x=0.5, y=0.5, font_size=24, showarrow=False)]
    )
    st.plotly_chart(fig_win, use_container_width=True)

with col2:
    # 평균 손익 비교
    st.markdown("#### 💰 평균 손익 비교")

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=['평균 수익', '평균 손실'],
        y=[breakdown['average_profit'], abs(breakdown['average_loss'])],
        marker_color=['#00CC96', '#EF553B'],
        text=[f"+{breakdown['average_profit']:,.0f}", f"-{abs(breakdown['average_loss']):,.0f}"],
        textposition='outside'
    ))
    fig_bar.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# 패턴 분석
st.subheader("📊 매매 패턴 분석")

patterns = dashboard['patterns']
pattern_stats = patterns.get('analysis', {}).get('pattern_stats', {})

if pattern_stats:
    col1, col2 = st.columns(2)

    with col1:
        # 패턴별 거래 수
        fig_pattern = px.bar(
            x=list(pattern_stats.keys()),
            y=[p['count'] for p in pattern_stats.values()],
            title="패턴별 거래 수",
            labels={'x': '패턴', 'y': '거래 수'}
        )
        fig_pattern.update_layout(height=300)
        st.plotly_chart(fig_pattern, use_container_width=True)

    with col2:
        # 패턴별 수익
        fig_profit = px.bar(
            x=list(pattern_stats.keys()),
            y=[p['total_profit'] for p in pattern_stats.values()],
            title="패턴별 총 수익",
            labels={'x': '패턴', 'y': '수익 (원)'},
            color=[p['total_profit'] for p in pattern_stats.values()],
            color_continuous_scale=['red', 'yellow', 'green']
        )
        fig_profit.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_profit, use_container_width=True)

    # 최고/최저 패턴 표시
    col1, col2 = st.columns(2)
    with col1:
        if patterns.get('best'):
            st.success(f"🏆 **최고 수익 패턴:** {patterns['best']}")
    with col2:
        if patterns.get('worst'):
            st.error(f"⚠️ **최저 수익 패턴:** {patterns['worst']}")

else:
    st.info("패턴 분석 데이터가 없습니다.")

st.markdown("---")

# 키워드 분석
st.subheader("🏷️ 키워드 분석")

keywords = dashboard['keywords']

if keywords:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📊 전체 키워드**")
        top_keywords = keywords.get('top_keywords', {})
        if top_keywords:
            for kw, count in list(top_keywords.items())[:5]:
                st.write(f"• {kw}: {count}회")
        else:
            st.write("데이터 없음")

    with col2:
        st.markdown("**✅ 수익 매매 키워드**")
        winning_keywords = keywords.get('winning_keywords', {})
        if winning_keywords:
            for kw, count in list(winning_keywords.items())[:5]:
                st.write(f"• {kw}: {count}회")
        else:
            st.write("데이터 없음")

    with col3:
        st.markdown("**❌ 손실 매매 키워드**")
        losing_keywords = keywords.get('losing_keywords', {})
        if losing_keywords:
            for kw, count in list(losing_keywords.items())[:5]:
                st.write(f"• {kw}: {count}회")
        else:
            st.write("데이터 없음")

st.markdown("---")

# 개선 제안
st.subheader("💡 개선 제안")

suggestions = dashboard['suggestions']
if suggestions:
    for i, suggestion in enumerate(suggestions, 1):
        st.write(f"{i}. {suggestion}")
else:
    st.info("개선 제안이 없습니다.")

st.markdown("---")

# 월별 추이
st.subheader("📈 월별 추이")

trend_data = report_service.get_trend_data(months=6)

if trend_data and len(trend_data) > 1:
    df_trend = pd.DataFrame(trend_data)

    # 복합 차트
    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])

    # 승률 라인
    fig_trend.add_trace(
        go.Scatter(
            x=df_trend['month'],
            y=df_trend['win_rate'],
            name='승률 (%)',
            mode='lines+markers',
            line=dict(color='#00CC96')
        ),
        secondary_y=False
    )

    # 손익비 라인
    fig_trend.add_trace(
        go.Scatter(
            x=df_trend['month'],
            y=df_trend['profit_loss_ratio'],
            name='손익비',
            mode='lines+markers',
            line=dict(color='#636EFA')
        ),
        secondary_y=True
    )

    fig_trend.update_layout(
        title='승률 & 손익비 추이',
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig_trend.update_yaxes(title_text="승률 (%)", secondary_y=False)
    fig_trend.update_yaxes(title_text="손익비", secondary_y=True)

    st.plotly_chart(fig_trend, use_container_width=True)

    # 손익 추이
    fig_pnl = px.bar(
        df_trend,
        x='month',
        y='total_profit_loss',
        title='월별 총 손익',
        labels={'month': '월', 'total_profit_loss': '손익 (원)'},
        color='total_profit_loss',
        color_continuous_scale=['red', 'yellow', 'green']
    )
    fig_pnl.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig_pnl, use_container_width=True)

else:
    st.info("추이 분석을 위한 충분한 데이터가 없습니다. (최소 2개월)")

# 상세 데이터
st.markdown("---")
with st.expander("📋 상세 데이터 보기"):
    st.json({
        'summary': summary,
        'breakdown': breakdown,
        'patterns': patterns,
        'keywords': keywords,
        'suggestions': suggestions
    })

# 리포트 다운로드
st.markdown("---")
if st.button("📥 리포트 다운로드 (JSON)"):
    import json
    report_json = json.dumps(dashboard, ensure_ascii=False, indent=2, default=str)
    st.download_button(
        label="다운로드",
        data=report_json,
        file_name=f"trading_report_{selected_year}_{selected_month:02d}.json",
        mime="application/json"
    )
