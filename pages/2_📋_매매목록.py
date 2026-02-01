"""
매매 목록 페이지
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from collections import defaultdict

from database import init_db
from services import TradeService
from styles import apply_toss_style

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
@st.dialog("매매 수정", width="large")
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

        # 매도인 경우 매수 건 연결 (수익 계산용)
        new_linked_trade_id = trade.linked_trade_id
        if new_trade_type == "SELL":
            # 해당 종목의 매수 거래 목록 가져오기
            all_buys = trade_service.list_trades(
                stock_name=new_stock_name,
                trade_type="BUY",
                limit=100
            )
            if all_buys:
                buy_options = {"선택 안함": None}
                for b in all_buys:
                    label = f"{b.trade_date} | {float(b.price):,.0f}원 × {b.quantity}주"
                    buy_options[label] = b.id

                # 현재 연결된 매수 찾기
                current_selection = "선택 안함"
                if trade.linked_trade_id:
                    for label, bid in buy_options.items():
                        if bid == trade.linked_trade_id:
                            current_selection = label
                            break

                selected_buy = st.selectbox(
                    "연결할 매수 건 (수익 계산)",
                    options=list(buy_options.keys()),
                    index=list(buy_options.keys()).index(current_selection) if current_selection in buy_options else 0
                )
                new_linked_trade_id = buy_options[selected_buy]

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
                'confidence_score': score_mapping[new_confidence],
                'linked_trade_id': new_linked_trade_id
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

# 정렬/보기 모드 + 필터를 한 줄에
col_view, col_filter1, col_filter2, col_filter3 = st.columns([1.5, 1, 1, 1])

with col_view:
    view_mode = st.selectbox(
        "보기",
        options=["종목별", "전체 목록", "날짜별"],
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

# 삭제할 항목 저장 (모든 뷰에서 공통 사용)
if 'delete_ids' not in st.session_state:
    st.session_state.delete_ids = set()

# 체크박스 콜백 함수 (모든 뷰에서 공통 사용)
def on_checkbox_change(trade_id):
    if st.session_state.get(f"check_{trade_id}") or st.session_state.get(f"check_stock_{trade_id}"):
        st.session_state.delete_ids.add(trade_id)
    else:
        st.session_state.delete_ids.discard(trade_id)

# ========== 날짜별 보기 ==========
if view_mode == "날짜별":
    if trades:
        # 날짜별로 그룹화
        date_groups = defaultdict(list)
        for trade in trades:
            date_groups[trade.trade_date].append(trade)

        for trade_date, day_trades in sorted(date_groups.items(), reverse=True):
            day_profit = sum(float(t.profit_loss or 0) for t in day_trades if t.profit_loss)
            profit_str = ""
            if day_profit != 0:
                profit_color = "#F04452" if day_profit > 0 else "#3182F6"
                profit_sign = "+" if day_profit > 0 else ""
                profit_str = f'<span style="color: {profit_color}; font-weight: 600;">{profit_sign}{day_profit:,.0f}원</span>'

            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center;
                        padding: 10px 0; margin-top: 8px;">
                <span style="font-weight: 600; color: #191F28; font-size: 14px;">{trade_date}</span>
                {profit_str}
            </div>
            """, unsafe_allow_html=True)

            for trade in day_trades:
                trade_type_str = "매수" if trade.trade_type == "BUY" else "매도"
                trade_color = "#3182F6" if trade.trade_type == "BUY" else "#F04452"
                trade_bg = "#E8F3FF" if trade.trade_type == "BUY" else "#FFEFEF"

                profit_info = ""
                if trade.profit_rate is not None:
                    rate = float(trade.profit_rate)
                    p_color = "#F04452" if rate > 0 else "#3182F6"
                    p_sign = "+" if rate > 0 else ""
                    profit_info = f'<span style="color: {p_color}; font-weight: 600;">{p_sign}{float(trade.profit_loss):,.0f}원</span>'

                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center;
                            padding: 12px 16px; background: #FFFFFF; border-radius: 8px;
                            margin: 6px 0; border: 1px solid #F2F3F5;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="background: {trade_bg}; color: {trade_color}; padding: 4px 8px;
                                    border-radius: 4px; font-size: 12px; font-weight: 600;">{trade_type_str}</span>
                        <span style="font-weight: 600; color: #191F28;">{trade.stock_name}</span>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #191F28; font-size: 14px;">{float(trade.price):,.0f}원 × {trade.quantity}주</div>
                        <div style="font-size: 13px;">{profit_info if profit_info else '<span style="color: #8B95A1;">-</span>'}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    else:
        st.info("조건에 맞는 매매 기록이 없습니다.")

# ========== 종목별 보기 ==========
elif view_mode == "종목별":
    if trades:
        stock_groups = defaultdict(lambda: {
            'buys': [], 'sells': [], 'total_profit': 0,
            'total_invested': 0, 'latest_date': None, 'trade_reasons': [],
            'display_name': None  # 실제 표시될 종목명
        })

        for trade in trades:
            # 대소문자 무시하고 같은 종목으로 그룹화
            stock_key = trade.stock_name.upper()
            stock_data = stock_groups[stock_key]

            # 표시 이름 설정 (첫 번째 거래의 종목명 사용)
            if stock_data['display_name'] is None:
                stock_data['display_name'] = trade.stock_name

            # 최근 거래일 업데이트
            if stock_data['latest_date'] is None or trade.trade_date > stock_data['latest_date']:
                stock_data['latest_date'] = trade.trade_date

            # 매매 근거 수집
            if trade.trade_reason:
                stock_data['trade_reasons'].append({
                    'date': trade.trade_date,
                    'type': trade.trade_type,
                    'reason': trade.trade_reason
                })

            if trade.trade_type == 'BUY':
                stock_data['buys'].append(trade)
                stock_data['total_invested'] += float(trade.total_amount or 0)
            else:
                stock_data['sells'].append(trade)
                if trade.profit_loss:
                    stock_data['total_profit'] += float(trade.profit_loss)

        # 최신 거래일 기준 정렬
        sorted_stocks = sorted(stock_groups.items(), key=lambda x: x[1]['latest_date'] or date.min, reverse=True)

        for stock_key, data in sorted_stocks:
            stock_name = data['display_name']
            buys = data['buys']
            sells = data['sells']
            total_profit = data['total_profit']
            latest_date = data['latest_date']

            total_buy_qty = sum(b.quantity for b in buys)
            total_sell_qty = sum(s.quantity for s in sells)

            # 평단가 계산 (총 매수금액 / 총 매수수량)
            avg_price = data['total_invested'] / total_buy_qty if total_buy_qty > 0 else 0

            # 종목 요약 카드 (전체 목록 스타일)
            profit_info = ""
            if total_profit != 0:
                p_color = "#F04452" if total_profit > 0 else "#3182F6"
                p_sign = "+" if total_profit > 0 else ""
                profit_info = f'<span style="color: {p_color}; font-weight: 600;">{p_sign}{total_profit:,.0f}원</span>'

            with st.expander(f"📊 {stock_name}", expanded=False):
                # 종목 요약 정보
                st.markdown(f"""
                <div style="display: flex; gap: 16px; padding: 8px 0 12px 0; font-size: 13px; color: #6B7684; border-bottom: 1px solid #F2F3F5; margin-bottom: 8px;">
                    <span>최근 거래 <strong style="color: #191F28;">{latest_date}</strong></span>
                    <span>매수 <strong style="color: #3182F6;">{len(buys)}회</strong></span>
                    <span>매도 <strong style="color: #F04452;">{len(sells)}회</strong></span>
                    <span>평단가 <strong style="color: #191F28;">{avg_price:,.0f}원</strong></span>
                </div>
                """, unsafe_allow_html=True)

                # 거래 내역 - 날짜별 그룹화
                all_stock_trades = buys + sells
                date_grouped = defaultdict(list)
                for t in all_stock_trades:
                    date_grouped[t.trade_date].append(t)

                for t_date, day_trades in sorted(date_grouped.items(), reverse=True):
                    # 날짜 헤더
                    st.markdown(f"""
                    <div style="font-size: 13px; font-weight: 600; color: #6B7684; padding: 12px 0 6px 0; border-bottom: 1px solid #F2F3F5;">
                        {t_date}
                    </div>
                    """, unsafe_allow_html=True)

                    # 해당 날짜 거래들
                    for t in sorted(day_trades, key=lambda x: x.id):
                        t_type = "매수" if t.trade_type == "BUY" else "매도"
                        t_bg = "#E8F3FF" if t.trade_type == "BUY" else "#FFEFEF"
                        t_color = "#3182F6" if t.trade_type == "BUY" else "#F04452"

                        t_profit_info = ""
                        if t.profit_loss:
                            tp_color = "#F04452" if t.profit_loss > 0 else "#3182F6"
                            t_profit_info = f'<span style="color: {tp_color}; font-weight: 600; margin-left: 8px;">{t.profit_loss:+,.0f}원</span>'

                        # 거래 정보 표시
                        trade_radius = "6px 6px 0 0" if t.trade_reason else "6px"
                        st.markdown(f'<div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; background: #FAFBFC; border-radius: {trade_radius}; margin-top: 4px;"><div style="display: flex; align-items: center; gap: 10px;"><span style="background: {t_bg}; color: {t_color}; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;">{t_type}</span><span style="color: #191F28; font-size: 14px;">{float(t.price):,.0f}원 × {t.quantity}주</span></div><div><span style="color: #6B7684; font-size: 13px;">{float(t.total_amount or 0):,.0f}원</span>{t_profit_info}</div></div>', unsafe_allow_html=True)

                        # 매매 근거 표시 (별도 마크다운)
                        if t.trade_reason:
                            st.markdown(f'<div style="padding: 8px 12px; margin: 0 0 8px 0; background: #F7F8FA; border-radius: 0 0 6px 6px; border-top: 1px dashed #E5E8EB;"><span style="color: #8B95A1; font-size: 11px;">📝 </span><span style="color: #6B7684; font-size: 13px; line-height: 1.5;">{t.trade_reason}</span></div>', unsafe_allow_html=True)

                # 손익 요약
                if total_profit != 0:
                    profit_color = "#F04452" if total_profit > 0 else "#3182F6"
                    profit_sign = "+" if total_profit > 0 else ""
                    st.markdown(f"""
                    <div style="margin-top: 12px; padding: 12px 16px; background: {'#FFF5F5' if total_profit > 0 else '#F0F6FF'};
                                border-radius: 8px; text-align: right;">
                        <span style="color: #6B7684; font-size: 13px;">총 손익</span>
                        <span style="color: {profit_color}; font-weight: 700; font-size: 16px; margin-left: 12px;">
                            {profit_sign}{total_profit:,.0f}원
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                # 수정 버튼 안내
                st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)
                st.info("💡 개별 거래를 수정하려면 '전체 목록' 보기에서 수정할 수 있어요.")

    else:
        st.info("조건에 맞는 매매 기록이 없습니다.")

# ========== 전체 목록 ==========
else:
    if trades:

        # 날짜별로 그룹화
        date_groups = defaultdict(list)
        for trade in trades:
            date_groups[trade.trade_date].append(trade)

        # 날짜별로 정렬하여 표시
        for trade_date, day_trades in sorted(date_groups.items(), reverse=True):
            # 해당 날짜의 손익 합계
            day_profit = sum(float(t.profit_loss or 0) for t in day_trades if t.profit_loss)
            profit_str = ""
            if day_profit != 0:
                profit_color = "#F04452" if day_profit > 0 else "#3182F6"
                profit_sign = "+" if day_profit > 0 else ""
                profit_str = f'<span style="color: {profit_color}; font-weight: 600;">{profit_sign}{day_profit:,.0f}원</span>'

            # 날짜 헤더
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center;
                        padding: 10px 0; margin-top: 8px;">
                <span style="font-weight: 600; color: #191F28; font-size: 14px;">{trade_date}</span>
                {profit_str}
            </div>
            """, unsafe_allow_html=True)

            # 해당 날짜의 거래들
            for trade in day_trades:
                trade_type_str = "매수" if trade.trade_type == "BUY" else "매도"
                trade_color = "#3182F6" if trade.trade_type == "BUY" else "#F04452"
                trade_bg = "#E8F3FF" if trade.trade_type == "BUY" else "#FFEFEF"

                profit_info = ""
                if trade.profit_rate is not None:
                    rate = float(trade.profit_rate)
                    p_color = "#F04452" if rate > 0 else "#3182F6"
                    p_sign = "+" if rate > 0 else ""
                    profit_info = f'<span style="color: {p_color}; font-weight: 600;">{p_sign}{float(trade.profit_loss):,.0f}원</span>'

                # 카드 + 수정버튼
                col_card, col_edit = st.columns([0.88, 0.12])

                with col_card:
                    # 체크박스를 카드 왼쪽에 포함
                    check_col, card_col = st.columns([0.05, 0.95])
                    with check_col:
                        st.checkbox(
                            "선택",
                            key=f"check_{trade.id}",
                            value=trade.id in st.session_state.delete_ids,
                            label_visibility="collapsed",
                            on_change=on_checkbox_change,
                            args=(trade.id,)
                        )
                    with card_col:
                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; align-items: center;
                                    padding: 12px 16px; background: #FFFFFF; border-radius: 8px;
                                    margin: 6px 0; border: 1px solid #F2F3F5;">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <span style="background: {trade_bg}; color: {trade_color}; padding: 4px 8px;
                                            border-radius: 4px; font-size: 12px; font-weight: 600;">{trade_type_str}</span>
                                <span style="font-weight: 600; color: #191F28;">{trade.stock_name}</span>
                            </div>
                            <div style="text-align: right;">
                                <div style="color: #191F28; font-size: 14px;">{float(trade.price):,.0f}원 × {trade.quantity}주</div>
                                <div style="font-size: 13px;">{profit_info if profit_info else '<span style="color: #8B95A1;">-</span>'}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                with col_edit:
                    st.markdown("<div style='height: 6px'></div>", unsafe_allow_html=True)
                    if st.button("수정", key=f"edit_{trade.id}", use_container_width=True):
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
