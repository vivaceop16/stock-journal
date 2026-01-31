"""
매매 목록 페이지
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from collections import defaultdict

from database import init_db
from services import TradeService
from styles import apply_toss_style, data_table_header, data_table_row

# 페이지 설정
st.set_page_config(page_title="매매 목록", page_icon="📋", layout="wide")

# 토스 스타일 적용
apply_toss_style()

# 데이터베이스 초기화
init_db()

# 서비스 초기화
trade_service = TradeService()

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
        # 대시보드 스타일 테이블
        st.markdown('<div class="data-table">', unsafe_allow_html=True)
        data_table_header()

        for trade in trades:
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
                trade_date=str(trade.trade_date),
                price=f"{float(trade.price):,.0f}원",
                quantity=f"{trade.quantity}주",
                profit=profit_str,
                trade_type=trade_type,
                profit_type=profit_type
            )

        st.markdown('</div>', unsafe_allow_html=True)

        # 상세 보기 (접을 수 있게)
        with st.expander("🔎 상세 보기 / 삭제"):
            selected_id = st.selectbox(
                "매매 선택",
                options=[t.id for t in trades],
                format_func=lambda x: f"#{x} - {next(t.stock_name for t in trades if t.id == x)} ({next(t.trade_date for t in trades if t.id == x)})"
            )

            if selected_id:
                selected_trade = next(t for t in trades if t.id == selected_id)

                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**종목:** {selected_trade.stock_name}")
                    st.write(f"**거래일:** {selected_trade.trade_date}")
                    st.write(f"**유형:** {'매수' if selected_trade.trade_type == 'BUY' else '매도'}")
                    st.write(f"**가격:** {selected_trade.price:,.0f}원 × {selected_trade.quantity}주")

                with col2:
                    st.write(f"**확신도:** {selected_trade.confidence_score}/10")
                    if selected_trade.profit_rate is not None:
                        st.write(f"**수익률:** {selected_trade.profit_rate:.2f}%")
                        st.write(f"**손익:** {selected_trade.profit_loss:+,.0f}원")

                st.text_area("매매 근거", value=selected_trade.trade_reason, height=100, disabled=True)

                if st.button("🗑️ 삭제", type="secondary"):
                    if trade_service.delete_trade(selected_id):
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
