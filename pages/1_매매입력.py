"""
매매 입력 페이지
"""

import streamlit as st
from datetime import date, datetime
from decimal import Decimal
import base64
import json
import re

from database import init_db
from services import TradeService

# 데이터베이스 초기화
init_db()

st.title("📝 매매 입력")
st.markdown("새로운 매매 기록을 입력하세요.")
st.markdown("---")

# 서비스 초기화
trade_service = TradeService()

# 세션 상태 초기화
if 'confidence_level' not in st.session_state:
    st.session_state.confidence_level = 3  # 기본값: 보통

if 'extracted_trades' not in st.session_state:
    st.session_state.extracted_trades = []

# 이미지에서 매매 내역 추출 함수
def extract_trades_from_image(image_bytes, api_key):
    """OpenAI Vision API로 이미지에서 매매 내역 추출"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """이 이미지는 주식 매매 내역 캡처입니다. 각 거래 정보를 추출해서 JSON 배열로 반환해주세요.

반환 형식:
[
  {
    "date": "2024-01-30",
    "stock_name": "종목명",
    "trade_type": "BUY" 또는 "SELL",
    "quantity": 수량(정수),
    "price": 1주당가격(정수),
    "total_amount": 총금액(정수)
  }
]

참고:
- "구매"는 "BUY", "판매"/"매도"는 "SELL"
- 날짜가 "1.30" 형식이면 올해 날짜로 변환 (예: "2024-01-30")
- 금액에서 쉼표, "원" 등 제거하고 숫자만
- 1주당 가격을 알 수 없으면 총금액/수량으로 계산
- 손익 금액(빨간색/파란색)이 아닌 실제 거래 금액 사용

JSON만 반환하세요. 다른 텍스트 없이."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        result_text = response.choices[0].message.content.strip()
        # JSON 부분만 추출
        json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(result_text)
    except Exception as e:
        st.error(f"이미지 분석 오류: {e}")
        return []

# 📸 이미지 업로드 섹션
st.subheader("📸 스크린샷으로 자동 입력")

api_key = st.session_state.get('openai_api_key', '')

if not api_key:
    st.warning("⚠️ 이미지 인식을 사용하려면 메인 페이지에서 OpenAI API Key를 입력하세요.")
else:
    uploaded_file = st.file_uploader(
        "매매 내역 스크린샷을 업로드하세요",
        type=['png', 'jpg', 'jpeg'],
        help="증권사 앱의 매매 내역 캡처 이미지를 올리면 자동으로 인식합니다"
    )

    if uploaded_file is not None:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.image(uploaded_file, caption="업로드된 이미지", use_container_width=True)

        with col2:
            if st.button("🔍 이미지 분석", use_container_width=True):
                with st.spinner("이미지 분석 중..."):
                    image_bytes = uploaded_file.getvalue()
                    extracted = extract_trades_from_image(image_bytes, api_key)

                    if extracted:
                        st.session_state.extracted_trades = extracted
                        st.success(f"✅ {len(extracted)}건의 거래를 인식했습니다!")
                    else:
                        st.error("거래 내역을 인식하지 못했습니다.")

    # 추출된 거래 표시 및 저장
    if st.session_state.extracted_trades:
        st.markdown("### 📋 인식된 거래 내역")

        for idx, trade in enumerate(st.session_state.extracted_trades):
            trade_type_kr = "매수" if trade.get('trade_type') == 'BUY' else "매도"
            emoji = "🟢" if trade.get('trade_type') == 'BUY' else "🔴"

            with st.expander(f"{emoji} {trade.get('stock_name', '?')} - {trade_type_kr} {trade.get('quantity', '?')}주", expanded=True):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**날짜:** {trade.get('date', '-')}")
                    st.write(f"**종목:** {trade.get('stock_name', '-')}")
                    st.write(f"**유형:** {trade_type_kr}")

                with col2:
                    st.write(f"**수량:** {trade.get('quantity', 0)}주")
                    st.write(f"**단가:** {trade.get('price', 0):,}원")
                    st.write(f"**총액:** {trade.get('total_amount', 0):,}원")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ 전체 저장", use_container_width=True, type="primary"):
                saved_count = 0
                for trade in st.session_state.extracted_trades:
                    try:
                        trade_data = {
                            'stock_name': trade.get('stock_name', ''),
                            'stock_code': None,
                            'trade_date': datetime.strptime(trade.get('date', ''), '%Y-%m-%d').date() if trade.get('date') else date.today(),
                            'trade_type': trade.get('trade_type', 'BUY'),
                            'price': trade.get('price', 0),
                            'quantity': trade.get('quantity', 0),
                            'trade_reason': '스크린샷에서 자동 입력',
                            'confidence_score': 5,
                            'linked_trade_id': None
                        }
                        trade_service.create_trade(trade_data)
                        saved_count += 1
                    except Exception as e:
                        st.error(f"저장 오류 ({trade.get('stock_name')}): {e}")

                if saved_count > 0:
                    st.success(f"✅ {saved_count}건 저장 완료!")
                    st.session_state.extracted_trades = []
                    st.rerun()

        with col2:
            if st.button("🗑️ 취소", use_container_width=True):
                st.session_state.extracted_trades = []
                st.rerun()

st.markdown("---")
st.subheader("✏️ 직접 입력")

# 입력 폼
with st.form("trade_form"):
    col1, col2 = st.columns(2)

    with col1:
        stock_name = st.text_input(
            "종목명 *",
            placeholder="예: 삼성전자",
            help="매매한 종목의 이름을 입력하세요"
        )

        stock_code = st.text_input(
            "종목코드 (선택)",
            placeholder="예: 005930",
            help="종목 코드를 알고 있다면 입력하세요"
        )

        trade_date = st.date_input(
            "거래일 *",
            value=date.today(),
            help="매매가 이루어진 날짜"
        )

    with col2:
        trade_type = st.radio(
            "거래 유형 *",
            options=["BUY", "SELL"],
            format_func=lambda x: "매수" if x == "BUY" else "매도",
            horizontal=True
        )

        price = st.number_input(
            "거래가격 (원) *",
            min_value=0,
            step=100,
            help="1주당 거래 가격"
        )

        quantity = st.number_input(
            "수량 (주) *",
            min_value=1,
            step=1,
            help="거래한 주식 수"
        )

    # 총 거래금액 표시
    if price > 0 and quantity > 0:
        total = price * quantity
        st.info(f"💰 총 거래금액: **{total:,.0f}원**")

    # 매도인 경우 연결할 매수 건 선택
    linked_trade_id = None
    if trade_type == "SELL" and stock_name:
        st.markdown("---")
        st.subheader("📎 매수 건 연결")

        unlinked_buys = trade_service.get_unlinked_buys(stock_name)

        if unlinked_buys:
            buy_options = {
                f"{b.trade_date} | {b.price:,.0f}원 x {b.quantity}주": b.id
                for b in unlinked_buys
            }
            selected_buy = st.selectbox(
                "연결할 매수 건 선택",
                options=["선택 안함"] + list(buy_options.keys()),
                help="이 매도와 연결할 기존 매수 기록을 선택하세요"
            )

            if selected_buy != "선택 안함":
                linked_trade_id = buy_options[selected_buy]
                buy_trade = next(b for b in unlinked_buys if b.id == linked_trade_id)
                profit_rate = ((price - float(buy_trade.price)) / float(buy_trade.price)) * 100
                profit_loss = (price - float(buy_trade.price)) * quantity

                if profit_rate >= 0:
                    st.success(f"📈 예상 수익률: **+{profit_rate:.2f}%** ({profit_loss:+,.0f}원)")
                else:
                    st.error(f"📉 예상 수익률: **{profit_rate:.2f}%** ({profit_loss:+,.0f}원)")
        else:
            st.warning("연결 가능한 매수 기록이 없습니다. 먼저 매수 기록을 입력하세요.")

    st.markdown("---")
    st.subheader("📋 매매 근거")

    trade_reason = st.text_area(
        "매매 근거 *",
        height=150,
        placeholder="이 매매를 결정한 이유를 상세히 작성해주세요.\n\n"
                    "예시:\n"
                    "- 기술적 분석: 20일 이평선 돌파, RSI 과매도 구간 탈출\n"
                    "- 펀더멘털: 분기 실적 서프라이즈, 신사업 진출 발표\n"
                    "- 시장 상황: 섹터 순환매 시작, 외국인 순매수 전환",
        help="최소 30자 이상 작성을 권장합니다. 상세할수록 AI 분석이 정확해집니다."
    )

    # 근거 길이 표시
    reason_length = len(trade_reason)
    if reason_length > 0:
        if reason_length < 30:
            st.warning(f"⚠️ 현재 {reason_length}자 - 30자 이상 작성을 권장합니다")
        elif reason_length < 100:
            st.info(f"📝 현재 {reason_length}자 - 좋습니다!")
        else:
            st.success(f"✅ 현재 {reason_length}자 - 상세한 기록입니다!")

    # 확신도 5단계 선택
    st.markdown("#### 🎯 매매 확신도")
    st.caption("이 매매에 대한 본인의 확신 정도를 선택하세요")

    confidence_options = {
        1: ("😰", "매우 낮음", "확신이 거의 없음, 시험 삼아"),
        2: ("😟", "낮음", "불안하지만 해볼만함"),
        3: ("😐", "보통", "반반의 확률"),
        4: ("😊", "높음", "꽤 확신있음"),
        5: ("🔥", "매우 높음", "강한 확신, 자신있음")
    }

    confidence_score = st.radio(
        "확신도 선택",
        options=[1, 2, 3, 4, 5],
        format_func=lambda x: f"{confidence_options[x][0]} {confidence_options[x][1]}",
        horizontal=True,
        index=2,  # 기본값: 보통 (인덱스 2 = 값 3)
        label_visibility="collapsed"
    )

    # 선택된 확신도 설명 표시
    selected_conf = confidence_options[confidence_score]
    st.info(f"{selected_conf[0]} **{selected_conf[1]}** - {selected_conf[2]}")

    st.markdown("---")
    submitted = st.form_submit_button("💾 저장", use_container_width=True)

    if submitted:
        # 유효성 검사
        errors = []
        if not stock_name:
            errors.append("종목명을 입력해주세요")
        if price <= 0:
            errors.append("거래가격을 입력해주세요")
        if quantity <= 0:
            errors.append("수량을 입력해주세요")
        if not trade_reason:
            errors.append("매매 근거를 입력해주세요")

        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            try:
                # 5단계를 10점 만점으로 변환 (1->2, 2->4, 3->5, 4->7, 5->9)
                score_mapping = {1: 2, 2: 4, 3: 5, 4: 7, 5: 9}
                mapped_score = score_mapping[confidence_score]

                trade_data = {
                    'stock_name': stock_name,
                    'stock_code': stock_code if stock_code else None,
                    'trade_date': trade_date,
                    'trade_type': trade_type,
                    'price': price,
                    'quantity': quantity,
                    'trade_reason': trade_reason,
                    'confidence_score': mapped_score,
                    'linked_trade_id': linked_trade_id
                }

                trade = trade_service.create_trade(trade_data)
                st.success(f"✅ 매매 기록이 저장되었습니다! (ID: {trade.id})")

                # 저장 후 정보 표시
                st.markdown("### 저장된 내용")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("종목", stock_name)
                with col2:
                    st.metric("유형", "매수" if trade_type == "BUY" else "매도")
                with col3:
                    st.metric("총 금액", f"{trade.total_amount:,.0f}원")

                if trade.profit_rate is not None:
                    st.metric("수익률", f"{trade.profit_rate:.2f}%")

                st.info("💡 'AI 분석' 페이지에서 이 매매에 대한 분석을 받아보세요!")

            except Exception as e:
                st.error(f"❌ 저장 중 오류가 발생했습니다: {e}")

# 최근 입력 내역
st.markdown("---")
st.subheader("📜 최근 입력 내역")

recent_trades = trade_service.list_trades(limit=5)

# 확신도 점수를 레이블로 변환하는 함수
def get_confidence_label(score):
    if score is None:
        return "-"
    if score <= 2:
        return "😰 매우 낮음"
    elif score <= 4:
        return "😟 낮음"
    elif score <= 6:
        return "😐 보통"
    elif score <= 8:
        return "😊 높음"
    else:
        return "🔥 매우 높음"

if recent_trades:
    for trade in recent_trades:
        with st.expander(
            f"{'🟢' if trade.trade_type == 'BUY' else '🔴'} "
            f"{trade.trade_date} | {trade.stock_name} | "
            f"{'매수' if trade.trade_type == 'BUY' else '매도'} | "
            f"{trade.price:,.0f}원 x {trade.quantity}주"
        ):
            st.write(f"**매매 근거:** {trade.trade_reason[:200]}{'...' if len(trade.trade_reason) > 200 else ''}")
            st.write(f"**확신도:** {get_confidence_label(trade.confidence_score)}")
            if trade.profit_rate is not None:
                color = "green" if trade.profit_rate >= 0 else "red"
                st.markdown(f"**수익률:** :{color}[{trade.profit_rate:.2f}%]")
else:
    st.info("아직 매매 기록이 없습니다.")
