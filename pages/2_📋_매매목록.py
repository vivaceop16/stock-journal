"""
매매 목록 페이지
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from collections import defaultdict

from database import init_db
from services import TradeService
from styles import apply_toss_style, data_table_row

# 페이지 설정
st.set_page_config(page_title="매매 목록", page_icon="📋", layout="wide")

# 토스 스타일 적용
apply_toss_style()

# 데이터베이스 초기화
init_db()

# 서비스 초기화
trade_service = TradeService()

# 수정 완료 메시지
if st.session_state.get('trade_updated'):
    st.success("✅ 매매가 수정되었습니다!")
    del st.session_state['trade_updated']

# 수정 모달 (다이얼로그)
@st.dialog("매매 수정")
def edit_trade_dialog(trade_id):
    trade = trade_service.get_trade(trade_id)
    if not trade:
        st.error("거래를 찾을 수 없습니다.")
        return

    with st.form("edit_form"):
        st.markdown(f"**{trade.stock_name}** 수정", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            new_stock_name = st.text_input("종목명", value=trade.stock_name)
        with col2:
            new_trade_date = st.date_input("거래일", value=trade.trade_date)

        new_trade_type = st.radio(
            "거래유형",
            options=["BUY", "SELL"],
            format_func=lambda x: "🔵 매수" if x == "BUY" else "🔴 매도",
            horizontal=True,
            index=0 if trade.trade_type == "BUY" else 1
        )

        col1, col2 = st.columns(2)
        with col1:
            new_price = st.number_input("거래가격 (원)", value=int(trade.price), min_value=0, step=100)
        with col2:
            new_quantity = st.number_input("수량 (주)", value=trade.quantity, min_value=1, step=1)

        new_trade_reason = st.text_area("매매 근거", value=trade.trade_reason or "", height=100)

        # 확신도 (1-5를 score로 변환: 2,4,5,7,9)
        score_to_level = {2: 1, 4: 2, 5: 3, 7: 4, 9: 5}
        current_level = score_to_level.get(trade.confidence_score, 3)
        new_confidence = st.radio(
            "확신도",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: ["⚪ 매우 낮음", "🔵 낮음", "🟢 보통", "🟡 높음", "🔴 매우 높음"][x-1],
            horizontal=True,
            index=current_level - 1
        )

        col1, col2 = st.columns(2)
        with col1:
            cancel = st.form_submit_button("취소", use_container_width=True)
        with col2:
            submit = st.form_submit_button("저장", type="primary", use_container_width=True)

        if submit:
            score_mapping = {1: 2, 2: 4, 3: 5, 4: 7, 5: 9}
            update_data = {
                'stock_name': new_stock_name,
                'trade_date': new_trade_date,
                'trade_type': new_trade_type,
                'price': new_price,
                'quantity': new_quantity,
                'trade_reason': new_trade_reason,
                'confidence_score': score_mapping[new_confidence]
            }
            trade_service.update_trade(trade_id, update_data)
            st.session_state['trade_updated'] = True
            st.rerun()

        if cancel:
            st.rerun()

# 수정 버튼 클릭 처리
if 'edit_trade_id' in st.session_state and st.session_state.edit_trade_id:
    edit_trade_dialog(st.session_state.edit_trade_id)
    st.session_state.edit_trade_id = None

# 헤더
st.markdown("""
<div style="padding: 20px 0 16px 0;">
    <h1 style="font-size: 24px; font-weight: 700; color: #191F28; margin: 0;">
        매매 목록
    </h1>
    <p style="font-size: 14px; color: #8B95A1; margin-top: 6px;">
        전체 거래 기록을 확인해요
    </p>
</div>
""", unsafe_allow_html=True)

# 상단 컨트롤 영역 (보기모드 + 필터)
st.markdown("""
<div style="background: #FFFFFF; border-radius: 12px; padding: 16px 20px; margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid #E5E8EB;">
""", unsafe_allow_html=True)

# 정렬/보기 모드 + 필터를 한 줄에
col_view, col_filter1, col_filter2, col_filter3 = st.columns([1.5, 1, 1, 1])

with col_view:
    view_mode = st.selectbox(
        "보기",
        options=["전체 목록", "종목별", "날짜별"],
        label_visibility="collapsed"
    )

with col_filter1:
    stock_filter = st.text_input("종목", placeholder="종목 검색", label_visibility="collapsed")

with col_filter2:
    type_filter = st.selectbox(
        "유형",
        options=["전체", "매수", "매도"],
        label_visibility="collapsed"
    )

with col_filter3:
    date_range = st.selectbox(
        "기간",
        options=["최근 1개월", "최근 3개월", "최근 6개월", "전체"],
        index=1,
        label_visibility="collapsed"
    )

st.markdown("</div>", unsafe_allow_html=True)

# 기간 계산
date_map = {
    "최근 1개월": 30,
    "최근 3개월": 90,
    "최근 6개월": 180,
    "전체": 3650
}
start_date = date.today() - timedelta(days=date_map[date_range])
end_date = date.today()

# 필터 적용
type_map = {"전체": None, "매수": "BUY", "매도": "SELL"}
trades = trade_service.list_trades(
    stock_name=stock_filter if stock_filter else None,
    trade_type=type_map[type_filter],
    start_date=start_date,
    end_date=end_date,
    limit=500
)

# 요약 통계 (간소화)
if trades:
    total_trades = len(trades)
    buy_count = len([t for t in trades if t.trade_type == 'BUY'])
    sell_count = len([t for t in trades if t.trade_type == 'SELL'])
    completed_sells = [t for t in trades if t.trade_type == 'SELL' and t.profit_rate is not None]
    total_profit = sum(float(t.profit_loss or 0) for t in completed_sells)

    profit_color = "#F04452" if total_profit > 0 else "#3182F6" if total_profit < 0 else "#6B7684"
    profit_sign = "+" if total_profit > 0 else ""

    st.markdown(f"""
    <div style="display: flex; gap: 24px; padding: 8px 0 16px 0; font-size: 14px; color: #6B7684;">
        <span>전체 <strong style="color: #191F28;">{total_trades}건</strong></span>
        <span>매수 <strong style="color: #3182F6;">{buy_count}건</strong></span>
        <span>매도 <strong style="color: #F04452;">{sell_count}건</strong></span>
        <span>손익 <strong style="color: {profit_color};">{profit_sign}{total_profit:,.0f}원</strong></span>
    </div>
    """, unsafe_allow_html=True)

# ========== 날짜별 보기 ==========
if view_mode == "날짜별":
    if trades:
        # 날짜별로 그룹화
        date_groups = defaultdict(list)
        for trade in trades:
            date_groups[trade.trade_date].append(trade)

        for trade_date, day_trades in sorted(date_groups.items(), reverse=True):
            day_profit = sum(float(t.profit_loss or 0) for t in day_trades if t.profit_loss)
            profit_str = f"+{day_profit:,.0f}원" if day_profit > 0 else f"{day_profit:,.0f}원" if day_profit < 0 else ""
            profit_color = "#F04452" if day_profit > 0 else "#3182F6" if day_profit < 0 else ""

            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center;
                        padding: 12px 0; border-bottom: 1px solid #F2F3F5; margin-top: 8px;">
                <span style="font-weight: 600; color: #191F28;">{trade_date}</span>
                <span style="font-size: 14px; color: {profit_color}; font-weight: 600;">{profit_str}</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="data-table" style="margin-bottom: 16px;">', unsafe_allow_html=True)

            for trade in day_trades:
                trade_type = "buy" if trade.trade_type == "BUY" else "sell"
                if trade.profit_rate is not None:
                    rate = float(trade.profit_rate)
                    profit_loss = float(trade.profit_loss or 0)
                    profit_str = f"{'+' if rate > 0 else ''}{profit_loss:,.0f}원"
                    profit_type = "positive" if rate > 0 else "negative"
                else:
                    profit_str = "-"
                    profit_type = "neutral"

                data_table_row(
                    stock_name=trade.stock_name,
                    trade_date="",
                    price=f"{float(trade.price):,.0f}원",
                    quantity=f"{trade.quantity}주",
                    profit=profit_str,
                    trade_type=trade_type,
                    profit_type=profit_type
                )

            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("조건에 맞는 매매 기록이 없습니다.")

# ========== 종목별 보기 ==========
elif view_mode == "종목별":
    if trades:
        stock_groups = defaultdict(lambda: {'buys': [], 'sells': [], 'total_profit': 0, 'total_invested': 0})

        for trade in trades:
            if trade.trade_type == 'BUY':
                stock_groups[trade.stock_name]['buys'].append(trade)
                stock_groups[trade.stock_name]['total_invested'] += float(trade.total_amount or 0)
            else:
                stock_groups[trade.stock_name]['sells'].append(trade)
                if trade.profit_loss:
                    stock_groups[trade.stock_name]['total_profit'] += float(trade.profit_loss)

        for stock_name, data in sorted(stock_groups.items()):
            buys = data['buys']
            sells = data['sells']
            total_profit = data['total_profit']

            total_buy_qty = sum(b.quantity for b in buys)
            total_sell_qty = sum(s.quantity for s in sells)
            holding_qty = total_buy_qty - total_sell_qty

            # 상태
            if holding_qty > 0:
                status = "🟢 보유중"
                status_detail = f"{holding_qty}주"
            elif total_profit > 0:
                status = "✅ 익절"
                status_detail = f"+{total_profit:,.0f}원"
            elif total_profit < 0:
                status = "❌ 손절"
                status_detail = f"{total_profit:,.0f}원"
            else:
                status = "⚪ 청산"
                status_detail = ""

            with st.expander(f"{status} **{stock_name}** — {status_detail}", expanded=holding_qty > 0):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("매수", f"{len(buys)}건 / {total_buy_qty}주")
                with col2:
                    st.metric("매도", f"{len(sells)}건 / {total_sell_qty}주")
                with col3:
                    profit_delta = f"{'+' if total_profit > 0 else ''}{total_profit:,.0f}원" if total_profit != 0 else None
                    st.metric("손익", f"{total_profit:,.0f}원", delta=profit_delta)

                # 거래 목록
                all_stock_trades = sorted(buys + sells, key=lambda x: x.trade_date, reverse=True)
                for t in all_stock_trades[:5]:
                    t_type = "매수" if t.trade_type == "BUY" else "매도"
                    t_color = "#3182F6" if t.trade_type == "BUY" else "#F04452"
                    profit_info = f" → {t.profit_loss:+,.0f}원" if t.profit_loss else ""
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 8px 0;
                                border-bottom: 1px solid #F5F6F7; font-size: 14px;">
                        <span><span style="color: {t_color}; font-weight: 500;">{t_type}</span> · {t.trade_date}</span>
                        <span style="color: #191F28;">{float(t.price):,.0f}원 × {t.quantity}주{profit_info}</span>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("조건에 맞는 매매 기록이 없습니다.")

# ========== 전체 목록 ==========
else:
    if trades:
        # 삭제할 항목 저장
        if 'delete_ids' not in st.session_state:
            st.session_state.delete_ids = set()

        # 체크박스 콜백 함수
        def on_checkbox_change(trade_id):
            if st.session_state.get(f"check_{trade_id}"):
                st.session_state.delete_ids.add(trade_id)
            else:
                st.session_state.delete_ids.discard(trade_id)

        # 거래 목록 (체크박스 + 펼침 상세)
        for trade in trades:
            trade_type_str = "매수" if trade.trade_type == "BUY" else "매도"
            trade_color = "#3182F6" if trade.trade_type == "BUY" else "#F04452"

            if trade.profit_rate is not None:
                rate = float(trade.profit_rate)
                profit_loss = float(trade.profit_loss or 0)
                profit_str = f"{'+' if rate > 0 else ''}{profit_loss:,.0f}원"
                profit_color = "#F04452" if rate > 0 else "#3182F6"
            else:
                profit_str = "-"
                profit_color = "#8B95A1"

            # 카드 스타일 컨테이너
            with st.container():
                col_check, col_content = st.columns([0.08, 0.92])

                with col_check:
                    st.checkbox(
                        "선택",
                        key=f"check_{trade.id}",
                        value=trade.id in st.session_state.delete_ids,
                        label_visibility="collapsed",
                        on_change=on_checkbox_change,
                        args=(trade.id,)
                    )

                with col_content:
                    # 펼침 가능한 상세 정보
                    with st.expander(
                        f"**{trade.stock_name}** · {trade.trade_date} · "
                        f":{'blue' if trade.trade_type == 'BUY' else 'red'}[{trade_type_str}] · "
                        f"{float(trade.price):,.0f}원 × {trade.quantity}주 · "
                        f":{('red' if trade.profit_rate and trade.profit_rate > 0 else 'blue') if trade.profit_rate else 'gray'}[{profit_str}]"
                    ):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"""
                            <div style="font-size: 14px; line-height: 2;">
                                <div><span style="color: #8B95A1;">종목</span> <strong>{trade.stock_name}</strong></div>
                                <div><span style="color: #8B95A1;">거래일</span> <strong>{trade.trade_date}</strong></div>
                                <div><span style="color: #8B95A1;">유형</span> <strong style="color: {trade_color};">{trade_type_str}</strong></div>
                                <div><span style="color: #8B95A1;">가격</span> <strong>{float(trade.price):,.0f}원 × {trade.quantity}주</strong></div>
                                <div><span style="color: #8B95A1;">총액</span> <strong>{float(trade.total_amount or 0):,.0f}원</strong></div>
                            </div>
                            """, unsafe_allow_html=True)

                        with col2:
                            profit_info = ""
                            if trade.profit_rate is not None:
                                profit_info = f"""
                                <div><span style="color: #8B95A1;">수익률</span> <strong style="color: {profit_color};">{'+' if trade.profit_rate > 0 else ''}{trade.profit_rate:.2f}%</strong></div>
                                <div><span style="color: #8B95A1;">손익</span> <strong style="color: {profit_color};">{'+' if trade.profit_loss > 0 else ''}{trade.profit_loss:,.0f}원</strong></div>
                                """
                            st.markdown(f"""
                            <div style="font-size: 14px; line-height: 2;">
                                <div><span style="color: #8B95A1;">확신도</span> <strong>{trade.confidence_score}/5</strong></div>
                                {profit_info}
                            </div>
                            """, unsafe_allow_html=True)

                        if trade.trade_reason:
                            st.markdown(f"""
                            <div style="margin-top: 12px; padding: 12px; background: #F7F8FA; border-radius: 8px; font-size: 14px;">
                                <div style="color: #8B95A1; margin-bottom: 4px;">매매 근거</div>
                                <div style="color: #191F28;">{trade.trade_reason}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        # 수정 버튼
                        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
                        if st.button("✏️ 수정", key=f"edit_{trade.id}", use_container_width=True):
                            st.session_state.edit_trade_id = trade.id
                            st.rerun()

        # 삭제 버튼 (선택된 항목이 있을 때만 - 리스트 하단에 표시)
        if st.session_state.delete_ids:
            st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)
            col_del1, col_del2, col_del3 = st.columns([1, 1, 1])
            with col_del2:
                if st.button(f"🗑️ {len(st.session_state.delete_ids)}건 삭제", type="primary", use_container_width=True):
                    for del_id in list(st.session_state.delete_ids):
                        trade_service.delete_trade(del_id)
                    st.session_state.delete_ids = set()
                    st.success("삭제되었습니다.")
                    st.rerun()

    else:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: #FFFFFF;
                    border-radius: 12px; border: 1px solid #E5E8EB;">
            <div style="font-size: 48px; margin-bottom: 16px;">📋</div>
            <div style="font-size: 16px; color: #191F28; font-weight: 600;">매매 기록이 없어요</div>
            <div style="font-size: 14px; color: #8B95A1; margin-top: 8px;">검색 조건을 변경하거나 새 거래를 입력해보세요</div>
        </div>
        """, unsafe_allow_html=True)

# 내보내기 (하단에 작게)
if trades:
    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        export_data = []
        for trade in trades:
            export_data.append({
                'ID': trade.id,
                '날짜': trade.trade_date.isoformat(),
                '종목명': trade.stock_name,
                '거래유형': trade.trade_type,
                '가격': float(trade.price),
                '수량': trade.quantity,
                '총금액': float(trade.total_amount or 0),
                '수익률': float(trade.profit_rate) if trade.profit_rate else None,
                '손익': float(trade.profit_loss) if trade.profit_loss else None
            })

        export_df = pd.DataFrame(export_data)
        csv = export_df.to_csv(index=False, encoding='utf-8-sig')

        st.download_button(
            label="📥 CSV 내보내기",
            data=csv,
            file_name=f"매매기록_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )
