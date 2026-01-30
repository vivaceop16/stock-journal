"""
학습 가이드 페이지
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

from database import init_db
from database.models import AnalysisResult
from services import TradeService, AIAnalyzer, LearningGuide
from styles import apply_toss_style

# 페이지 설정
st.set_page_config(page_title="학습 가이드", page_icon="📚", layout="wide")

# 토스 스타일 적용
apply_toss_style()

# 데이터베이스 초기화
init_db()

# 헤더
st.markdown("""
<div style="padding: 20px 0 10px 0;">
    <h1 style="font-size: 24px; font-weight: 700; color: #191F28; margin: 0;">
        학습 가이드
    </h1>
    <p style="font-size: 14px; color: #8B95A1; margin-top: 6px;">
        나만의 학습 과제를 확인해요
    </p>
</div>
""", unsafe_allow_html=True)

# 서비스 초기화
trade_service = TradeService()
ai_analyzer = AIAnalyzer()
learning_guide = LearningGuide()

# 학습 현황 요약
st.subheader("📊 학습 현황")
summary = learning_guide.get_learning_summary()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("총 과제", f"{summary['total']}개")
with col2:
    st.metric("완료", f"{summary['completed']}개")
with col3:
    st.metric("진행중", f"{summary['in_progress']}개")
with col4:
    st.metric("완료율", f"{summary['completion_rate']:.1f}%")

# 진행률 바
if summary['total'] > 0:
    progress = summary['completed'] / summary['total']
    st.progress(progress)

st.markdown("---")

# 약점 분석
st.subheader("🔍 약점 패턴 분석")

# 최근 분석 결과 가져오기
recent_analyses = ai_analyzer.session.query(AnalysisResult).order_by(
    AnalysisResult.created_at.desc()
).limit(20).all()

if recent_analyses:
    weakness_analysis = learning_guide.analyze_weaknesses(recent_analyses)

    # 약점 요약
    st.info(f"📋 **분석 요약:** {weakness_analysis.get('summary', '데이터 없음')}")

    col1, col2 = st.columns(2)

    with col1:
        # 약점 패턴 차트
        weaknesses = weakness_analysis.get('weaknesses', {})
        if weaknesses:
            fig_weakness = px.pie(
                names=list(weaknesses.keys()),
                values=list(weaknesses.values()),
                title="약점 패턴 분포"
            )
            fig_weakness.update_layout(height=300)
            st.plotly_chart(fig_weakness, use_container_width=True)
        else:
            st.info("발견된 약점 패턴이 없습니다.")

    with col2:
        # 점수 분포
        score_dist = weakness_analysis.get('score_distribution', {})
        if score_dist:
            fig_score = go.Figure(data=[
                go.Bar(
                    x=['논리성 부족', '타이밍 문제', '리스크관리 부족'],
                    y=[score_dist.get('low_logic', 0),
                       score_dist.get('low_timing', 0),
                       score_dist.get('low_risk', 0)],
                    marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1']
                )
            ])
            fig_score.update_layout(
                title="개선 필요 영역",
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig_score, use_container_width=True)

    # 자동 과제 생성 버튼
    st.markdown("---")
    if st.button("🔄 약점 기반 과제 자동 생성", type="primary"):
        with st.spinner("과제 생성 중..."):
            new_tasks = learning_guide.auto_generate_tasks_from_analyses()
            if new_tasks:
                st.success(f"✅ {len(new_tasks)}개의 새 과제가 생성되었습니다!")
                st.rerun()
            else:
                st.info("추가로 생성할 과제가 없습니다.")

else:
    st.warning("분석된 매매 데이터가 없습니다. 먼저 'AI 분석'에서 매매를 분석해주세요.")

# 학습 과제 목록
st.markdown("---")
st.subheader("📝 학습 과제")

# 탭으로 상태별 구분
tab1, tab2, tab3 = st.tabs(["🔥 진행 필요", "⏳ 진행중", "✅ 완료"])

pending_tasks = learning_guide.session.query(
    learning_guide.session.query.__self__.query.__self__.__class__.__mro__[0]
).filter_by(status='pending').order_by().all() if False else []

# 실제 쿼리
from database.models import LearningTask
all_tasks = learning_guide.session.query(LearningTask).all()
pending_tasks = [t for t in all_tasks if t.status == 'pending']
in_progress_tasks = [t for t in all_tasks if t.status == 'in_progress']
completed_tasks = [t for t in all_tasks if t.status == 'completed']

with tab1:
    if pending_tasks:
        for task in sorted(pending_tasks, key=lambda x: x.priority, reverse=True):
            with st.expander(
                f"{'🔴' * min(task.priority, 5)} {task.task_title}",
                expanded=task.priority >= 4
            ):
                st.write(f"**설명:** {task.task_description}")
                st.write(f"**카테고리:** {task.task_category}")
                st.write(f"**우선순위:** {'⭐' * task.priority}")

                if task.related_pattern:
                    st.write(f"**관련 패턴:** {task.related_pattern}")

                # 추천 자료
                resources = learning_guide.get_recommended_resources(task.task_category)
                if resources:
                    st.markdown("**📖 추천 학습 자료:**")
                    for resource in resources:
                        st.write(f"  - {resource}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("▶️ 시작", key=f"start_{task.id}"):
                        learning_guide.update_task_status(task.id, 'in_progress')
                        st.rerun()
                with col2:
                    if st.button("🗑️ 삭제", key=f"del_{task.id}"):
                        learning_guide.session.delete(task)
                        learning_guide.session.commit()
                        st.rerun()
    else:
        st.info("대기 중인 과제가 없습니다.")

with tab2:
    if in_progress_tasks:
        for task in in_progress_tasks:
            with st.expander(f"📝 {task.task_title}", expanded=True):
                st.write(f"**설명:** {task.task_description}")
                st.write(f"**카테고리:** {task.task_category}")

                # 추천 자료
                resources = learning_guide.get_recommended_resources(task.task_category)
                if resources:
                    st.markdown("**📖 추천 학습 자료:**")
                    for resource in resources:
                        st.write(f"  - {resource}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ 완료", key=f"complete_{task.id}"):
                        learning_guide.update_task_status(task.id, 'completed')
                        st.success("과제를 완료했습니다!")
                        st.rerun()
                with col2:
                    if st.button("⏸️ 보류", key=f"pause_{task.id}"):
                        learning_guide.update_task_status(task.id, 'pending')
                        st.rerun()
    else:
        st.info("진행 중인 과제가 없습니다.")

with tab3:
    if completed_tasks:
        for task in sorted(completed_tasks, key=lambda x: x.completion_date or date.min, reverse=True):
            with st.expander(f"✅ {task.task_title}"):
                st.write(f"**설명:** {task.task_description}")
                st.write(f"**완료일:** {task.completion_date}")
                st.write(f"**카테고리:** {task.task_category}")
    else:
        st.info("완료된 과제가 없습니다.")

# 수동 과제 추가
st.markdown("---")
st.subheader("➕ 과제 직접 추가")

with st.form("add_task_form"):
    col1, col2 = st.columns(2)

    with col1:
        new_title = st.text_input("과제 제목")
        new_category = st.selectbox(
            "카테고리",
            options=['기술분석', '심리', '리스크관리', '펀더멘털']
        )

    with col2:
        new_priority = st.slider("우선순위", 1, 5, 3)
        new_description = st.text_area("설명", height=100)

    if st.form_submit_button("➕ 추가"):
        if new_title:
            learning_guide.create_learning_task({
                'task_title': new_title,
                'task_description': new_description,
                'task_category': new_category,
                'priority': new_priority
            })
            st.success("과제가 추가되었습니다!")
            st.rerun()
        else:
            st.error("과제 제목을 입력해주세요.")

# 학습 팁
st.markdown("---")
st.subheader("💡 학습 팁")

tips = {
    '기술분석': [
        "차트를 매일 30분 이상 분석하는 습관을 들이세요",
        "하나의 지표에 집중하여 완전히 이해한 후 다음 지표로 넘어가세요",
        "과거 차트로 백테스트를 진행해보세요"
    ],
    '심리': [
        "매매 전 체크리스트를 만들어 감정적 매매를 방지하세요",
        "손실 후에는 반드시 휴식을 취하세요",
        "매매 일기를 작성하여 감정 변화를 추적하세요"
    ],
    '리스크관리': [
        "한 번의 매매에 전체 자금의 2% 이상 위험을 감수하지 마세요",
        "손절 라인을 진입 전에 반드시 정하세요",
        "포지션 사이즈 계산기를 활용하세요"
    ],
    '펀더멘털': [
        "재무제표의 핵심 지표(매출, 영업이익, ROE)에 집중하세요",
        "산업 동향과 경쟁사 분석을 함께 진행하세요",
        "실적 발표 일정을 미리 파악하세요"
    ]
}

selected_category = st.selectbox(
    "카테고리 선택",
    options=list(tips.keys()),
    key="tip_category"
)

for tip in tips[selected_category]:
    st.write(f"• {tip}")
