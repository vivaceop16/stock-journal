"""매매 관리 서비스"""

from datetime import date
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from database.models import Trade
from database.connection import db_manager


class TradeService:
    """매매 기록 관리 서비스"""

    def __init__(self, session: Optional[Session] = None):
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            return db_manager.get_session()
        return self._session

    def create_trade(self, trade_data: Dict[str, Any]) -> Trade:
        """새 매매 기록 생성"""
        # 총 거래금액 계산
        price = Decimal(str(trade_data['price']))
        quantity = trade_data['quantity']
        total_amount = price * quantity

        trade = Trade(
            stock_name=trade_data['stock_name'],
            stock_code=trade_data.get('stock_code'),
            trade_date=trade_data['trade_date'],
            trade_type=trade_data['trade_type'],
            price=price,
            quantity=quantity,
            total_amount=total_amount,
            trade_reason=trade_data['trade_reason'],
            confidence_score=trade_data.get('confidence_score'),
            linked_trade_id=trade_data.get('linked_trade_id'),
        )

        # 매도 거래인 경우 수익 계산
        if trade.trade_type == 'SELL' and trade.linked_trade_id:
            profit_info = self._calculate_profit(trade)
            trade.profit_loss = profit_info['profit_loss']
            trade.profit_rate = profit_info['profit_rate']

        session = self.session
        session.add(trade)
        session.commit()
        session.refresh(trade)
        return trade

    def get_trade(self, trade_id: int) -> Optional[Trade]:
        """ID로 매매 기록 조회"""
        return self.session.query(Trade).filter(Trade.id == trade_id).first()

    def list_trades(
        self,
        stock_name: Optional[str] = None,
        trade_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Trade]:
        """매매 기록 목록 조회"""
        query = self.session.query(Trade)

        if stock_name:
            query = query.filter(Trade.stock_name.like(f'%{stock_name}%'))
        if trade_type:
            query = query.filter(Trade.trade_type == trade_type)
        if start_date:
            query = query.filter(Trade.trade_date >= start_date)
        if end_date:
            query = query.filter(Trade.trade_date <= end_date)

        return query.order_by(desc(Trade.trade_date), desc(Trade.id)).offset(offset).limit(limit).all()

    def get_unlinked_buys(self, stock_name: str) -> List[Trade]:
        """매도와 연결되지 않은 매수 기록 조회"""
        # 이미 매도와 연결된 매수 ID 조회
        linked_buy_ids = self.session.query(Trade.linked_trade_id).filter(
            and_(
                Trade.trade_type == 'SELL',
                Trade.linked_trade_id.isnot(None)
            )
        ).all()
        linked_ids = [id[0] for id in linked_buy_ids]

        # 연결되지 않은 매수 조회
        query = self.session.query(Trade).filter(
            and_(
                Trade.stock_name == stock_name,
                Trade.trade_type == 'BUY'
            )
        )

        if linked_ids:
            query = query.filter(Trade.id.notin_(linked_ids))

        return query.order_by(Trade.trade_date).all()

    def link_sell_to_buy(self, sell_id: int, buy_id: int) -> Trade:
        """매도 거래를 매수 거래와 연결"""
        sell_trade = self.get_trade(sell_id)
        if not sell_trade or sell_trade.trade_type != 'SELL':
            raise ValueError("유효하지 않은 매도 거래입니다.")

        buy_trade = self.get_trade(buy_id)
        if not buy_trade or buy_trade.trade_type != 'BUY':
            raise ValueError("유효하지 않은 매수 거래입니다.")

        sell_trade.linked_trade_id = buy_id
        profit_info = self._calculate_profit(sell_trade)
        sell_trade.profit_loss = profit_info['profit_loss']
        sell_trade.profit_rate = profit_info['profit_rate']

        self.session.commit()
        return sell_trade

    def _calculate_profit(self, sell_trade: Trade) -> Dict[str, Decimal]:
        """수익 계산"""
        if not sell_trade.linked_trade_id:
            return {'profit_loss': Decimal('0'), 'profit_rate': Decimal('0')}

        buy_trade = self.get_trade(sell_trade.linked_trade_id)
        if not buy_trade:
            return {'profit_loss': Decimal('0'), 'profit_rate': Decimal('0')}

        # 수익금 = (매도가 - 매수가) * 수량
        # 실제로는 매도 수량 기준으로 계산 (부분 매도 고려)
        sell_quantity = sell_trade.quantity
        profit_loss = (sell_trade.price - buy_trade.price) * sell_quantity

        # 수익률 = (매도가 - 매수가) / 매수가 * 100
        if buy_trade.price > 0:
            profit_rate = ((sell_trade.price - buy_trade.price) / buy_trade.price) * 100
        else:
            profit_rate = Decimal('0')

        return {
            'profit_loss': profit_loss,
            'profit_rate': profit_rate
        }

    def get_trades_by_month(self, year: int, month: int) -> List[Trade]:
        """특정 월의 매매 기록 조회"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        return self.session.query(Trade).filter(
            and_(
                Trade.trade_date >= start_date,
                Trade.trade_date < end_date
            )
        ).order_by(Trade.trade_date).all()

    def get_completed_trades(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Trade]:
        """완료된 매매 (매도 거래 중 매수와 연결된 것) 조회"""
        query = self.session.query(Trade).filter(
            and_(
                Trade.trade_type == 'SELL',
                Trade.linked_trade_id.isnot(None)
            )
        )

        if start_date:
            query = query.filter(Trade.trade_date >= start_date)
        if end_date:
            query = query.filter(Trade.trade_date <= end_date)

        return query.order_by(desc(Trade.trade_date)).all()

    def delete_trade(self, trade_id: int) -> bool:
        """매매 기록 삭제"""
        session = self.session
        trade = session.query(Trade).filter(Trade.id == trade_id).first()
        if trade:
            session.delete(trade)
            session.commit()
            return True
        return False

    def update_trade(self, trade_id: int, update_data: Dict[str, Any]) -> Optional[Trade]:
        """매매 기록 수정"""
        session = self.session
        trade = session.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            return None

        for key, value in update_data.items():
            if hasattr(trade, key):
                setattr(trade, key, value)

        # 총 거래금액 재계산
        if 'price' in update_data or 'quantity' in update_data:
            trade.total_amount = trade.price * trade.quantity

        # 매도 거래인 경우 수익 재계산
        if trade.trade_type == 'SELL' and trade.linked_trade_id:
            # 연결된 매수 거래 조회 (같은 세션에서)
            buy_trade = session.query(Trade).filter(Trade.id == trade.linked_trade_id).first()
            if buy_trade and buy_trade.price > 0:
                sell_quantity = trade.quantity
                profit_loss = (trade.price - buy_trade.price) * sell_quantity
                profit_rate = ((trade.price - buy_trade.price) / buy_trade.price) * 100
                trade.profit_loss = profit_loss
                trade.profit_rate = profit_rate

        session.commit()
        return trade
