"""
Bollinger Squeeze Strategy
Volatility-based strategy that identifies low-volatility squeezes before breakouts.

Entry: Buy when bands expand after a squeeze (breakout above upper band)
Exit: Sell when price crosses back below the middle band or stop loss hit

Author: Agentic Trading
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Trade:
    entry_date: datetime
    exit_date: Optional[datetime]
    symbol: str
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    pnl: float = 0.0
    pnl_pct: float = 0.0
    duration_days: int = 0
    exit_reason: str = ""


class BollingerSqueezeStrategy:
    """
    Bollinger Squeeze Strategy

    Detects periods of low volatility (squeeze) when Bollinger Bands contract.
    Enters a long position on a bullish breakout after the squeeze resolves.

    Parameters:
    -----------
    bb_period : int
        Bollinger Bands lookback period (default: 20)
    bb_std : float
        Number of standard deviations for bands (default: 2.0)
    kc_period : int
        Keltner Channel period (default: 20)
    kc_mult : float
        Keltner Channel multiplier (default: 1.5)
    squeeze_periods : int
        Consecutive periods bands must be inside KC to confirm squeeze (default: 3)
    stop_loss_pct : float
        Stop loss percentage (default: 0.06)
    position_size_pct : float
        Position size as % of equity (default: 0.20)

    Example:
    --------
    >>> strategy = BollingerSqueezeStrategy(bb_period=20, bb_std=2.0)
    >>> results = strategy.backtest(df, initial_capital=100_000)
    >>> print(f"Total Return: {results['total_return']:.2%}")
    """

    def __init__(
        self,
        bb_period: int = 20,
        bb_std: float = 2.0,
        kc_period: int = 20,
        kc_mult: float = 1.5,
        squeeze_periods: int = 3,
        stop_loss_pct: float = 0.06,
        take_profit_pct: float = 0.18,
        position_size_pct: float = 0.20,
    ):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.kc_period = kc_period
        self.kc_mult = kc_mult
        self.squeeze_periods = squeeze_periods
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.position_size_pct = position_size_pct

    def calculate_bollinger_bands(self, close: pd.Series):
        sma = close.rolling(self.bb_period).mean()
        std = close.rolling(self.bb_period).std()
        upper = sma + self.bb_std * std
        lower = sma - self.bb_std * std
        return upper, sma, lower

    def calculate_keltner_channels(self, high: pd.Series, low: pd.Series, close: pd.Series):
        typical = (high + low + close) / 3
        ema = typical.ewm(span=self.kc_period, adjust=False).mean()
        atr = (high - low).rolling(self.kc_period).mean()
        upper = ema + self.kc_mult * atr
        lower = ema - self.kc_mult * atr
        return upper, ema, lower

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['bb_upper'], df['bb_mid'], df['bb_lower'] = self.calculate_bollinger_bands(df['close'])
        df['kc_upper'], df['kc_mid'], df['kc_lower'] = self.calculate_keltner_channels(
            df['high'], df['low'], df['close']
        )

        # Squeeze: BB upper < KC upper AND BB lower > KC lower
        in_squeeze = (df['bb_upper'] < df['kc_upper']) & (df['bb_lower'] > df['kc_lower'])
        df['squeeze'] = in_squeeze.rolling(self.squeeze_periods).sum() == self.squeeze_periods

        # Breakout: price closes above upper BB after a squeeze
        prev_squeeze = df['squeeze'].shift(1)
        breakout_up = prev_squeeze & (df['close'] > df['bb_upper'])
        cross_below_mid = df['close'] < df['bb_mid']

        df['signal'] = 0
        df.loc[breakout_up, 'signal'] = 1
        df.loc[cross_below_mid, 'signal'] = -1

        return df

    def backtest(
        self,
        data: pd.DataFrame,
        initial_capital: float = 100_000.0,
        commission: float = 0.001,
        slippage: float = 0.001,
    ) -> Dict:
        df = self.generate_signals(data)
        capital = initial_capital
        equity_curve = []
        trades = []
        position = None

        for timestamp, row in df.iterrows():
            if pd.isna(row['bb_mid']):
                equity_curve.append({'date': timestamp, 'equity': capital, 'drawdown': 0})
                continue

            if row['signal'] == 1 and position is None:
                pos_value = capital * self.position_size_pct
                entry_price = row['close'] * (1 + slippage)
                shares = pos_value / entry_price
                capital -= pos_value * commission
                position = {
                    'entry_date': timestamp,
                    'entry_price': entry_price,
                    'shares': shares,
                    'stop_loss': entry_price * (1 - self.stop_loss_pct),
                    'take_profit': entry_price * (1 + self.take_profit_pct),
                }

            elif position is not None:
                price = row['close']
                exit_reason = None
                exit_price = price

                if price <= position['stop_loss']:
                    exit_reason, exit_price = 'stop_loss', position['stop_loss']
                elif price >= position['take_profit']:
                    exit_reason, exit_price = 'take_profit', position['take_profit']
                elif row['signal'] == -1:
                    exit_reason = 'below_midband'
                    exit_price = price * (1 - slippage)

                if exit_reason:
                    gross_pnl = position['shares'] * (exit_price - position['entry_price'])
                    net_pnl = gross_pnl - (position['shares'] * exit_price * commission)
                    trades.append(Trade(
                        entry_date=position['entry_date'],
                        exit_date=timestamp,
                        symbol='UNKNOWN',
                        entry_price=position['entry_price'],
                        exit_price=exit_price,
                        quantity=position['shares'],
                        pnl=net_pnl,
                        pnl_pct=(exit_price - position['entry_price']) / position['entry_price'],
                        duration_days=(timestamp - position['entry_date']).days,
                        exit_reason=exit_reason,
                    ))
                    capital += net_pnl
                    position = None

            current_equity = capital + (position['shares'] * row['close'] if position else 0)
            peak = max((e['equity'] for e in equity_curve), default=current_equity)
            drawdown = (peak - current_equity) / peak if peak > 0 else 0
            equity_curve.append({'date': timestamp, 'equity': current_equity, 'drawdown': drawdown})

        equity_df = pd.DataFrame(equity_curve)
        total_return = (equity_df['equity'].iloc[-1] - initial_capital) / initial_capital
        daily_returns = equity_df['equity'].pct_change().dropna()
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0
        winners = [t for t in trades if t.pnl > 0]

        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': equity_df['drawdown'].max(),
            'win_rate': len(winners) / len(trades) if trades else 0,
            'total_trades': len(trades),
            'equity_curve': equity_curve,
            'trades': trades,
        }


if __name__ == "__main__":
    print("Bollinger Squeeze Strategy")
    print("Entry: Price breaks above upper Bollinger Band after a squeeze")
    print("Exit:  Price crosses below middle band, stop loss, or take profit")
