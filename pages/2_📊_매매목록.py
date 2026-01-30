"""
매매 목록 페이지
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from collections import defaultdict

from database import init_db
from services import TradeService

# 데이터베이스 초기화
init_db()

st.title("📊 매매 목록")
st.markdown("모든 매매 기록을 조회하고 관리합니다.")
st.markdown("---")

# 서비스 초기화
trade_service = TradeService()

# 보기 모드 선택
view_mode = st.radio(
    "보기 모드",
    options=["전체 목록", "종목별 묶어보기"],
    horizontal=True
)

st.markdown("---")

# 필터 옵션
st.subheader("🔍 검색 필터")
col1, col2, col3, col4 = st.columns(4)

with col1:
    stock_filter = st.text_input("종목명", placeholder="종목명 검색")

with col2:
    type_filter = st.selectbox(
        "거래 유형",
        options=["전체", "매수", "매도"]
    )

with col3:
    start_date = st.date_input(
        "시작일",
        value=date.today() - timedelta(days=90)
    )

with col4:
    end_date = st.date_input(
        "종료일",
        value=date.today()
    )

# 필터 적용
type_map = {"전체": None, "매수": "BUY", "매도": "SELL"}
trades = trade_service.list_trades(
    stock_name=stock_filter if stock_filter else None,
    trade_type=type_map[type_filter],
    start_date=start_date,
    end_date=end_date,
    limit=200
)

st.markdown("---")

# 요약 통계
if trades:
    total_trades = len(trades)
    buy_trades = len([t for t in trades if t.trade_type == 'BUY'])
    sell_trades = len([t for t in trades if t.trade_type == 'SELL'])

    completed_sells = [t for t in trades if t.trade_type == 'SELL' and t.profit_rate is not None]
    if completed_sells:
        total_profit = sum(float(t.profit_loss or 0) for t in completed_sells)
        avg_profit_rate = sum(float(t.profit_rate or 0) for t in completed_sells) / len(completed_sells)
        winning = len([t for t in completed_sells if t.profit_loss and t.profit_loss > 0])
        win_rate = (winning / len(completed_sells)) * 100 if completed_sells else 0
    else:
        total_profit = 0
        avg_profit_rate = 0
        win_rate = 0

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("총 거래", f"{total_trades}건")
    with col2:
        st.metric("매수", f"{buy_trades}건", delta=None)
    with col3:
        st.metric("매도", f"{sell_trades}건", delta=None)
    with col4:
        st.metric("승률", f"{win_rate:.1f}%")
    with col5:
        st.metric("총 손익", f"{total_profit:+,.0f}원")

    st.markdown("---")

# ========== 종목별 묶어보기 모드 ==========
if view_mode == "종목별 묶어보기":
    st.subheader("📦 종목별 매매 현황")

    if trades:
        # 종목별로 그룹화
        stock_groups = defaultdict(lambda: {'buys': [], 'sells': [], 'total_profit': 0, 'total_invested': 0})

        for trade in trades:
            if trade.trade_type == 'BUY':
                stock_groups[trade.stock_name]['buys'].append(trade)
                stock_groups[trade.stock_name]['total_invested'] += float(trade.total_amount or 0)
            else:
                stock_groups[trade.stock_name]['sells'].append(trade)
                if trade.profit_loss:
                    stock_groups[trade.stock_name]['total_profit'] += float(trade.profit_loss)

        # 종목별 요약 카드
        for stock_name, data in sorted(stock_groups.items()):
            buys = data['buys']
            sells = data['sells']
            total_profit = data['total_profit']

            # 보유 상태 계산
            total_buy_qty = sum(b.quantity for b in buys)
            total_sell_qty = sum(s.quantity for s in sells)
            holding_qty = total_buy_qty - total_sell_qty

            # 상태 표시
            if holding_qty > 0:
                status_icon = "🟢"
                status_text = f"보유중 ({holding_qty}주)"
            elif total_profit > 0:
                status_icon = "✅"
                status_text = "익절 완료"
            elif total_profit < 0:
                status_icon = "❌"
                status_text = "손절 완료"
            else:
                status_icon = "⚪"
                status_text = "청산 완료"

            # 평균 매수가 계산
            if buys:
                avg_buy_price = sum(float(b.price) * b.quantity for b in buys) / total_buy_qty
            else:
                avg_buy_price = 0

            with st.expander(
                f"{status_icon} **{stock_name}** | {status_text} | "
                f"매수 {len(buys)}건 / 매도 {len(sells)}건 | "
                f"손익: {total_profit:+,.0f}원",
                expanded=holding_qty > 0
            ):
                # 요약 정보
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("평균 매수가", f"{avg_buy_price:,.0f}원")
                with col2:
                    st.metric("총 매수량", f"{total_buy_qty}주")
                with col3:
                    st.metric("총 매도량", f"{total_sell_qty}주")
                with col4:
                    if total_profit >= 0:
                        st.metric("총 손익", f"+{total_profit:,.0f}원")
                    else:
                        st.metric("총 손익", f"{total_profit:,.0f}원")

                # 매수 기록
                if buys:
                    st.markdown("##### 🟢 매수 기록")
                    buy_data = []
                    for b in sorted(buys, key=lambda x: x.trade_date):
                        buy_data.append({
                            '날짜': b.trade_date,
                            '가격': f"{b.price:,.0f}원",
                            '수량': f"{b.quantity}주",
                            '금액': f"{b.total_amount:,.0f}원",
                            '확신도': f"{b.confidence_score}/10" if b.confidence_score else "-",
                            '근거': b.trade_reason[:50] + "..." if len(b.trade_reason) > 50 else b.trade_reason
                        })
                    st.dataframe(pd.DataFrame(buy_data), use_container_width=True, hide_index=True)

                # 매도 기록
                if sells:
                    st.markdown("##### 🔴 매도 기록")
                    sell_data = []
                    for s in sorted(sells, key=lambda x: x.trade_date):
                        sell_data.append({
                            '날짜': s.trade_date,
                            '가격': f"{s.price:,.0f}원",
                            '수량': f"{s.quantity}주",
                            '금액': f"{s.total_amount:,.0f}원",
                            '수익률': f"{s.profit_rate:.2f}%" if s.profit_rate else "-",
                            '손익': f"{s.profit_loss:+,.0f}원" if s.profit_loss else "-",
                            '근거': s.trade_reason[:50] + "..." if len(s.trade_reason) > 50 else s.trade_reason
                        })
                    st.dataframe(pd.DataFrame(sell_data), use_container_width=True, hide_index=True)

                # 수익률 계산 (완료된 경우)
                if sells and total_profit != 0:
                    total_invested = data['total_invested']
                    if total_invested > 0:
                        total_return = (total_profit / total_invested) * 100
                        st.info(f"📊 **총 수익률:** {total_return:+.2f}% (투자금 대비)")

    else:
        st.info("조건에 맞는 매매 기록이 없습니다.")

# ========== 전체 목록 모드 ==========
else:
    st.subheader(f"📋 매매 기록 ({len(trades)}건)")

    if trades:
        # DataFrame 생성
        df_data = []
        for trade in trades:
            df_data.append({
                'ID': trade.id,
                '날짜': trade.trade_date,
                '종목': trade.stock_name,
                '유형': '매수' if trade.trade_type == 'BUY' else '매도',
                '가격': trade.price,
                '수량': trade.quantity,
                '금액': trade.total_amount,
                '확신도': f"{trade.confidence_score}/10" if trade.confidence_score else "-",
                '수익률': f"{trade.profit_rate:.2f}%" if trade.profit_rate else "-",
                '손익': f"{trade.profit_loss:+,.0f}" if trade.profit_loss else "-"
            })

        df = pd.DataFrame(df_data)

        # 테이블 표시
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'ID': st.column_config.NumberColumn('ID', width='small'),
                '날짜': st.column_config.DateColumn('날짜'),
                '가격': st.column_config.NumberColumn('가격', format='%,.0f원'),
                '금액': st.column_config.NumberColumn('금액', format='%,.0f원'),
            }
        )

        # 상세 보기
        st.markdown("---")
        st.subheader("🔎 상세 보기")

        selected_id = st.selectbox(
            "매매 선택",
            options=[t.id for t in trades],
            format_func=lambda x: f"#{x} - {next(t.stock_name for t in trades if t.id == x)} ({next(t.trade_date for t in trades if t.id == x)})"
        )

        if selected_id:
            selected_trade = next(t for t in trades if t.id == selected_id)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 기본 정보")
                st.write(f"**종목명:** {selected_trade.stock_name}")
                if selected_trade.stock_code:
                    st.write(f"**종목코드:** {selected_trade.stock_code}")
                st.write(f"**거래일:** {selected_trade.trade_date}")
                st.write(f"**거래유형:** {'매수' if selected_trade.trade_type == 'BUY' else '매도'}")
                st.write(f"**가격:** {selected_trade.price:,.0f}원")
                st.write(f"**수량:** {selected_trade.quantity}주")
                st.write(f"**총금액:** {selected_trade.total_amount:,.0f}원")

            with col2:
                st.markdown("#### 분석 정보")
                st.write(f"**확신도:** {selected_trade.confidence_score}/10")

                if selected_trade.profit_rate is not None:
                    profit_color = "green" if selected_trade.profit_rate >= 0 else "red"
                    st.markdown(f"**수익률:** :{profit_color}[{selected_trade.profit_rate:.2f}%]")
                    st.write(f"**손익금액:** {selected_trade.profit_loss:+,.0f}원")

                if selected_trade.linked_trade_id:
                    linked = trade_service.get_trade(selected_trade.linked_trade_id)
                    if linked:
                        st.write(f"**연결된 매수:** #{linked.id} ({linked.trade_date})")

            st.markdown("#### 매매 근거")
            st.text_area(
                "근거",
                value=selected_trade.trade_reason,
                height=150,
                disabled=True,
                label_visibility="collapsed"
            )

            # 삭제 버튼
            st.markdown("---")
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("🗑️ 삭제", type="secondary", use_container_width=True):
                    if trade_service.delete_trade(selected_id):
                        st.success("삭제되었습니다.")
                        st.rerun()
                    else:
                        st.error("삭제에 실패했습니다.")

    else:
        st.info("조건에 맞는 매매 기록이 없습니다.")

# 내보내기 기능
if trades:
    st.markdown("---")
    st.subheader("📥 데이터 내보내기")

    export_data = []
    for trade in trades:
        export_data.append({
            'ID': trade.id,
            '날짜': trade.trade_date.isoformat(),
            '종목명': trade.stock_name,
            '종목코드': trade.stock_code or '',
            '거래유형': trade.trade_type,
            '가격': float(trade.price),
            '수량': trade.quantity,
            '총금액': float(trade.total_amount or 0),
            '매매근거': trade.trade_reason,
            '확신도': trade.confidence_score,
            '수익률': float(trade.profit_rate) if trade.profit_rate else None,
            '손익': float(trade.profit_loss) if trade.profit_loss else None
        })

    export_df = pd.DataFrame(export_data)
    csv = export_df.to_csv(index=False, encoding='utf-8-sig')

    st.download_button(
        label="📄 CSV 다운로드",
        data=csv,
        file_name=f"매매기록_{start_date}_{end_date}.csv",
        mime="text/csv"
    )
