#!/usr/bin/env python3
"""
Simulador de Backtesting SMC
===========================

Sistema de backtesting para validar la rentabilidad de las estrategias SMC
con análisis completo de performance y métricas de trading.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class TradeResult(Enum):
    WIN = "WIN"
    LOSS = "LOSS"
    BREAKEVEN = "BREAKEVEN"

@dataclass
class BacktestTrade:
    """Estructura de trade de backtesting"""
    entry_time: datetime
    exit_time: Optional[datetime]
    signal_type: str  # LONG/SHORT
    entry_price: float
    exit_price: Optional[float]
    stop_loss: float
    take_profit: float
    result: Optional[TradeResult]
    pnl_points: float = 0.0
    pnl_percent: float = 0.0
    risk_reward_achieved: float = 0.0
    duration_hours: float = 0.0
    max_adverse_excursion: float = 0.0  # MAE
    max_favorable_excursion: float = 0.0  # MFE

@dataclass
class BacktestResults:
    """Resultados completos del backtesting"""
    trades: List[BacktestTrade] = field(default_factory=list)
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    breakeven_trades: int = 0
    win_rate: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    profit_factor: float = 0.0
    total_pnl: float = 0.0
    total_pnl_percent: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    sharpe_ratio: float = 0.0
    calmar_ratio: float = 0.0
    average_trade_duration: float = 0.0
    expectancy: float = 0.0
    final_capital: float = 0.0
    total_return: float = 0.0
    annualized_return: float = 0.0

class SMCBacktester:
    """Simulador de backtesting para estrategias SMC"""

    def __init__(self, initial_capital: float = 10000, risk_per_trade: float = 1.0):
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade  # Porcentaje del capital por trade
        self.results = BacktestResults()

    def run_backtest(self, df: pd.DataFrame, signals: List[Any],
                    max_trade_duration: int = 48) -> BacktestResults:
        """
        Ejecutar backtesting completo

        Args:
            df: DataFrame con datos OHLC
            signals: Lista de señales generadas por el motor de trading
            max_trade_duration: Máximo de horas por trade

        Returns:
            Resultados completos del backtesting
        """
        try:
            print(f"🔍 Iniciando backtesting con {len(signals)} señales...")

            # --- Volatilidad móvil consistente para todo el backtest ---
            volatility_window = 20
            df['volatility'] = df['close'].pct_change().rolling(volatility_window).std()

            # Reset de resultados
            self.results = BacktestResults()

            # Procesar cada señal
            for i, signal in enumerate(signals):
                trade = self._simulate_trade(df, signal, max_trade_duration)
                if trade:
                    self.results.trades.append(trade)

            # Calcular métricas
            self._calculate_metrics()

            print(f"✅ Backtesting completado: {len(self.results.trades)} trades ejecutados")
            return self.results

        except Exception as e:
            print(f"❌ Error en backtesting: {e}")
            return BacktestResults()

    def _simulate_trade(self, df: pd.DataFrame, signal: Any,
                       max_duration: int) -> Optional[BacktestTrade]:
        """Simular ejecución de un trade individual"""
        try:
            # Encontrar índice de entrada
            signal_time = signal.timestamp
            entry_idx = None

            # Buscar la vela correspondiente al timestamp de la señal usando la columna timestamp
            for idx, timestamp in enumerate(df['timestamp']):
                if pd.to_datetime(timestamp) >= pd.to_datetime(signal_time):
                    entry_idx = idx
                    break

            if entry_idx is None or entry_idx >= len(df) - 1:
                return None

            # Validar niveles de SL/TP antes de ejecutar el trade
            validation = validate_sl_tp_levels(
                df, signal.entry_price, signal.stop_loss,
                signal.take_profit, signal.signal_type.value
            )

            if validation.result != LevelValidationResult.VALID:
                print(f"⚠️ Validación SL/TP: {validation.message}")
                for suggestion in validation.suggestions:
                    print(f"   💡 {suggestion}")

                # Opcional: usar niveles recomendados si están disponibles
                if validation.recommended_sl and validation.recommended_tp:
                    print(f"   🔧 Usando niveles recomendados: SL=${validation.recommended_sl:.2f}, TP=${validation.recommended_tp:.2f}")
                    signal.stop_loss = validation.recommended_sl
                    signal.take_profit = validation.recommended_tp

            # Crear trade inicial
            trade = BacktestTrade(
                entry_time=signal_time,
                exit_time=None,
                signal_type=signal.signal_type.value,
                entry_price=signal.entry_price,
                exit_price=None,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                result=None
            )

            # Simular evolución del trade
            max_duration_candles = min(max_duration * 4, len(df) - entry_idx - 1)  # 4 velas por hora para 15m

            for i in range(1, max_duration_candles + 1):
                if entry_idx + i >= len(df):
                    break

                current_candle = df.iloc[entry_idx + i]
                current_time = df['timestamp'].iloc[entry_idx + i]  # Usar columna timestamp

                # Verificar SL/TP según tipo de trade
                if signal.signal_type.value == "LONG":
                    # Trade LONG
                    if current_candle['low'] <= trade.stop_loss:
                        # Hit Stop Loss
                        trade.exit_time = current_time
                        trade.exit_price = trade.stop_loss
                        trade.result = TradeResult.LOSS
                        break
                    elif current_candle['high'] >= trade.take_profit:
                        # Hit Take Profit
                        trade.exit_time = current_time
                        trade.exit_price = trade.take_profit
                        trade.result = TradeResult.WIN
                        break

                elif signal.signal_type.value == "SHORT":
                    # Trade SHORT
                    if current_candle['high'] >= trade.stop_loss:
                        # Hit Stop Loss
                        trade.exit_time = current_time
                        trade.exit_price = trade.stop_loss
                        trade.result = TradeResult.LOSS
                        break
                    elif current_candle['low'] <= trade.take_profit:
                        # Hit Take Profit
                        trade.exit_time = current_time
                        trade.exit_price = trade.take_profit
                        trade.result = TradeResult.WIN
                        break

            # Si no se cerró el trade, cerrarlo al precio de mercado
            if trade.exit_time is None:
                final_idx = min(entry_idx + max_duration_candles, len(df) - 1)
                # Asegurar que final_idx sea al menos 1 vela después del entry
                if final_idx <= entry_idx:
                    final_idx = min(entry_idx + 1, len(df) - 1)

                trade.exit_time = df['timestamp'].iloc[final_idx]
                trade.exit_price = df.iloc[final_idx]['close']

                # Determinar resultado basado en PnL
                if signal.signal_type.value == "LONG":
                    if trade.exit_price > trade.entry_price:
                        trade.result = TradeResult.WIN
                    elif trade.exit_price < trade.entry_price:
                        trade.result = TradeResult.LOSS
                    else:
                        trade.result = TradeResult.BREAKEVEN
                else:  # SHORT
                    if trade.exit_price < trade.entry_price:
                        trade.result = TradeResult.WIN
                    elif trade.exit_price > trade.entry_price:
                        trade.result = TradeResult.LOSS
                    else:
                        trade.result = TradeResult.BREAKEVEN

            # Calcular métricas del trade
            self._calculate_trade_metrics(trade)

            return trade

        except Exception as e:
            print(f"Error simulando trade: {e}")
            return None

    def _calculate_trade_metrics(self, trade: BacktestTrade):
        """Calcular métricas individuales del trade"""
        try:
            if trade.exit_price is None:
                return

            # PnL en puntos
            if trade.signal_type == "LONG":
                trade.pnl_points = trade.exit_price - trade.entry_price
            else:  # SHORT
                trade.pnl_points = trade.entry_price - trade.exit_price

            # PnL en porcentaje
            trade.pnl_percent = (trade.pnl_points / trade.entry_price) * 100

            # Risk/Reward conseguido
            risk_points = abs(trade.entry_price - trade.stop_loss)
            if risk_points > 0:
                trade.risk_reward_achieved = abs(trade.pnl_points) / risk_points

            # Duración del trade
            if trade.exit_time and trade.entry_time:
                try:
                    entry_dt = pd.to_datetime(trade.entry_time)
                    exit_dt = pd.to_datetime(trade.exit_time)
                    duration = exit_dt - entry_dt

                    # Asegurar que la duración sea positiva
                    if duration.total_seconds() > 0:
                        trade.duration_hours = duration.total_seconds() / 3600
                    else:
                        trade.duration_hours = 0.0
                except Exception as e:
                    print(f"Error calculando duración: {e}")
                    trade.duration_hours = 0.0

        except Exception as e:
            print(f"Error calculando métricas de trade: {e}")

    def _calculate_metrics(self):
        """Calcular métricas generales del backtesting"""
        try:
            trades = self.results.trades
            if not trades:
                return

            # Contadores básicos
            self.results.total_trades = len(trades)
            self.results.winning_trades = sum(1 for t in trades if t.result == TradeResult.WIN)
            self.results.losing_trades = sum(1 for t in trades if t.result == TradeResult.LOSS)
            self.results.breakeven_trades = sum(1 for t in trades if t.result == TradeResult.BREAKEVEN)

            # Win rate
            if self.results.total_trades > 0:
                self.results.win_rate = (self.results.winning_trades / self.results.total_trades) * 100

            # PnL total
            total_pnl_points = sum(t.pnl_points for t in trades)
            self.results.total_pnl = total_pnl_points
            self.results.total_pnl_percent = sum(t.pnl_percent for t in trades)

            # Ganancias y pérdidas promedio
            winning_trades = [t for t in trades if t.result == TradeResult.WIN]
            losing_trades = [t for t in trades if t.result == TradeResult.LOSS]

            if winning_trades:
                self.results.average_win = np.mean([t.pnl_points for t in winning_trades])
                self.results.largest_win = max(t.pnl_points for t in winning_trades)

            if losing_trades:
                self.results.average_loss = np.mean([t.pnl_points for t in losing_trades])
                self.results.largest_loss = min(t.pnl_points for t in losing_trades)

            # Profit Factor
            total_wins = sum(t.pnl_points for t in winning_trades) if winning_trades else 0
            total_losses = abs(sum(t.pnl_points for t in losing_trades)) if losing_trades else 0

            if total_losses > 0:
                self.results.profit_factor = total_wins / total_losses

            # Expectancy
            if self.results.total_trades > 0:
                self.results.expectancy = sum(t.pnl_points for t in trades) / self.results.total_trades

            # Duración promedio
            durations = [t.duration_hours for t in trades if t.duration_hours > 0]
            if durations:
                self.results.average_trade_duration = np.mean(durations)

            # Drawdown máximo
            self._calculate_drawdown()

            # Calcular capital final y retornos
            self._calculate_capital_metrics()

        except Exception as e:
            print(f"Error calculando métricas: {e}")

    def _calculate_drawdown(self):
        """Calcular drawdown máximo"""
        try:
            trades = self.results.trades
            if not trades:
                return

            # Crear curva de capital
            capital_curve = [self.initial_capital]
            current_capital = self.initial_capital

            for trade in trades:
                # Calcular tamaño de posición basado en riesgo
                risk_amount = current_capital * (self.risk_per_trade / 100)
                risk_points = abs(trade.entry_price - trade.stop_loss)

                if risk_points > 0:
                    position_size = risk_amount / risk_points
                    trade_pnl = trade.pnl_points * position_size
                    current_capital += trade_pnl

                capital_curve.append(current_capital)

            # Calcular drawdown
            peak = capital_curve[0]
            max_dd = 0
            max_dd_percent = 0

            for capital in capital_curve:
                if capital > peak:
                    peak = capital

                drawdown = peak - capital
                drawdown_percent = (drawdown / peak) * 100 if peak > 0 else 0

                if drawdown > max_dd:
                    max_dd = drawdown

                if drawdown_percent > max_dd_percent:
                    max_dd_percent = drawdown_percent

            self.results.max_drawdown = max_dd
            self.results.max_drawdown_percent = max_dd_percent

        except Exception as e:
            print(f"Error calculando drawdown: {e}")

    def _calculate_capital_metrics(self):
        """Calcular métricas de capital final y retornos"""
        try:
            trades = self.results.trades
            if not trades:
                self.results.final_capital = self.initial_capital
                self.results.total_return = 0.0
                self.results.annualized_return = 0.0
                return

            # Calcular capital final
            current_capital = self.initial_capital

            for trade in trades:
                # Calcular tamaño de posición basado en riesgo
                risk_amount = current_capital * (self.risk_per_trade / 100)
                risk_points = abs(trade.entry_price - trade.stop_loss)

                if risk_points > 0:
                    position_size = risk_amount / risk_points
                    trade_pnl = trade.pnl_points * position_size
                    current_capital += trade_pnl

            self.results.final_capital = current_capital

            # Calcular retorno total
            self.results.total_return = ((current_capital - self.initial_capital) / self.initial_capital) * 100

            # Calcular retorno anualizado
            if trades:
                # Calcular duración total del backtest
                entry_times = []
                exit_times = []

                for trade in trades:
                    # Convertir entry_time
                    if isinstance(trade.entry_time, str):
                        entry_time = pd.to_datetime(trade.entry_time)
                    elif hasattr(trade.entry_time, 'to_pydatetime'):
                        entry_time = trade.entry_time.to_pydatetime()
                    else:
                        entry_time = pd.to_datetime(trade.entry_time)
                    entry_times.append(entry_time)

                    # Convertir exit_time si existe
                    if trade.exit_time:
                        if isinstance(trade.exit_time, str):
                            exit_time = pd.to_datetime(trade.exit_time)
                        elif hasattr(trade.exit_time, 'to_pydatetime'):
                            exit_time = trade.exit_time.to_pydatetime()
                        else:
                            exit_time = pd.to_datetime(trade.exit_time)
                        exit_times.append(exit_time)

                if entry_times and exit_times:
                    start_date = min(entry_times)
                    end_date = max(exit_times)

                    # Asegurar que ambas fechas son datetime
                    if hasattr(start_date, 'to_pydatetime'):
                        start_date = start_date.to_pydatetime()
                    if hasattr(end_date, 'to_pydatetime'):
                        end_date = end_date.to_pydatetime()

                    total_days = (end_date - start_date).days
                    if total_days > 0:
                        years = total_days / 365.25
                        if years > 0:
                            self.results.annualized_return = (((current_capital / self.initial_capital) ** (1/years)) - 1) * 100

        except Exception as e:
            print(f"Error calculando métricas de capital: {e}")
            self.results.final_capital = self.initial_capital
            self.results.total_return = 0.0
            self.results.annualized_return = 0.0

    def create_performance_chart(self) -> go.Figure:
        """Crear gráfico de performance del backtesting"""
        try:
            if not self.results.trades:
                return go.Figure()

            # Preparar datos para el gráfico
            dates = []
            cumulative_pnl = []
            cumulative = 0

            for trade in self.results.trades:
                dates.append(trade.exit_time)
                cumulative += trade.pnl_points
                cumulative_pnl.append(cumulative)

            # Crear subplot con múltiples métricas
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=("Curva de PnL Acumulado", "Distribución de Trades",
                              "Duración vs PnL", "Drawdown"),
                specs=[[{"secondary_y": False}, {"type": "histogram"}],
                       [{"type": "scatter"}, {"secondary_y": False}]]
            )

            # 1. Curva de PnL acumulado
            fig.add_trace(
                go.Scatter(x=dates, y=cumulative_pnl, mode='lines', name='PnL Acumulado',
                          line=dict(color='green', width=2)),
                row=1, col=1
            )

            # 2. Histograma de resultados
            pnl_values = [t.pnl_points for t in self.results.trades]
            fig.add_trace(
                go.Histogram(x=pnl_values, name='Distribución PnL',
                           marker_color='lightblue'),
                row=1, col=2
            )

            # 3. Duración vs PnL
            durations = [t.duration_hours for t in self.results.trades]
            colors = ['green' if p > 0 else 'red' for p in pnl_values]

            fig.add_trace(
                go.Scatter(x=durations, y=pnl_values, mode='markers',
                          marker=dict(color=colors), name='Trades'),
                row=2, col=1
            )

            # 4. Curva de capital (para drawdown)
            capital_curve = [self.initial_capital]
            current_capital = self.initial_capital

            for trade in self.results.trades:
                risk_amount = current_capital * (self.risk_per_trade / 100)
                risk_points = abs(trade.entry_price - trade.stop_loss)

                if risk_points > 0:
                    position_size = risk_amount / risk_points
                    trade_pnl = trade.pnl_points * position_size
                    current_capital += trade_pnl

                capital_curve.append(current_capital)

            fig.add_trace(
                go.Scatter(x=list(range(len(capital_curve))), y=capital_curve,
                          mode='lines', name='Capital', line=dict(color='blue')),
                row=2, col=2
            )

            # Configuración del layout
            fig.update_layout(
                title=f"Análisis de Performance - {self.results.total_trades} Trades",
                showlegend=True,
                height=600
            )

            return fig

        except Exception as e:
            print(f"Error creando gráfico de performance: {e}")
            return go.Figure()

    def generate_report(self) -> str:
        """Generar reporte detallado de backtesting"""
        try:
            results = self.results

            report = f"""
# 📊 REPORTE DE BACKTESTING SMC

## 📈 Resumen General
- **Total de Trades:** {results.total_trades}
- **Trades Ganadores:** {results.winning_trades} ({results.win_rate:.1f}%)
- **Trades Perdedores:** {results.losing_trades}
- **Breakeven:** {results.breakeven_trades}

## 💰 Performance Financiera
- **PnL Total:** {results.total_pnl:.2f} puntos
- **PnL Porcentual:** {results.total_pnl_percent:.2f}%
- **Ganancia Promedio:** {results.average_win:.2f} puntos
- **Pérdida Promedio:** {results.average_loss:.2f} puntos
- **Mayor Ganancia:** {results.largest_win:.2f} puntos
- **Mayor Pérdida:** {results.largest_loss:.2f} puntos

## 📊 Métricas de Riesgo
- **Profit Factor:** {results.profit_factor:.2f}
- **Expectancy:** {results.expectancy:.2f} puntos por trade
- **Drawdown Máximo:** {results.max_drawdown:.2f} ({results.max_drawdown_percent:.1f}%)
- **Duración Promedio:** {results.average_trade_duration:.1f} horas

## 🎯 Evaluación de Estrategia
"""

            # Evaluación cualitativa
            if results.win_rate >= 60:
                report += "✅ **Win Rate Excelente** (≥60%)\n"
            elif results.win_rate >= 50:
                report += "🟡 **Win Rate Bueno** (50-60%)\n"
            else:
                report += "🔴 **Win Rate Bajo** (<50%)\n"

            if results.profit_factor >= 2.0:
                report += "✅ **Profit Factor Excelente** (≥2.0)\n"
            elif results.profit_factor >= 1.5:
                report += "🟡 **Profit Factor Bueno** (1.5-2.0)\n"
            else:
                report += "🔴 **Profit Factor Bajo** (<1.5)\n"

            if results.max_drawdown_percent <= 10:
                report += "✅ **Drawdown Controlado** (≤10%)\n"
            elif results.max_drawdown_percent <= 20:
                report += "🟡 **Drawdown Moderado** (10-20%)\n"
            else:
                report += "🔴 **Drawdown Alto** (>20%)\n"

            return report

        except Exception as e:
            return f"Error generando reporte: {e}"

# Función de utilidad para integración
def run_backtest_analysis(df: pd.DataFrame, signals: List[Any],
                         initial_capital: float = 10000,
                         risk_per_trade: float = 1.0) -> Dict[str, Any]:
    """
    Función principal para ejecutar análisis de backtesting

    Args:
        df: DataFrame con datos OHLC
        signals: Lista de señales del motor de trading
        initial_capital: Capital inicial
        risk_per_trade: Riesgo por trade (%)

    Returns:
        Diccionario con resultados de backtesting
    """
    try:
        backtester = SMCBacktester(initial_capital, risk_per_trade)
        results = backtester.run_backtest(df, signals)
        chart = backtester.create_performance_chart()
        report = backtester.generate_report()

        return {
            'results': results,
            'chart': chart,
            'report': report,
            'backtester': backtester,
            'success': True
        }

    except Exception as e:
        print(f"Error en análisis de backtesting: {e}")
        return {
            'results': BacktestResults(),
            'chart': go.Figure(),
            'report': f"Error: {str(e)}",
            'success': False
        }

# Exportar clases y funciones principales
__all__ = [
    'SMCBacktester',
    'BacktestResults',
    'BacktestTrade',
    'TradeResult',
    'run_backtest_analysis'
]

class LevelValidationResult(Enum):
    """Resultado de validación de niveles SL/TP"""
    VALID = "VALID"
    SL_TOO_TIGHT = "SL_TOO_TIGHT"
    SL_TOO_WIDE = "SL_TOO_WIDE"
    TP_TOO_TIGHT = "TP_TOO_TIGHT"
    TP_TOO_WIDE = "TP_TOO_WIDE"
    OUTSIDE_RANGE = "OUTSIDE_RANGE"
    INVALID_RR = "INVALID_RR"

@dataclass
class ValidationReport:
    """Reporte de validación de niveles"""
    result: LevelValidationResult
    message: str
    suggestions: List[str] = field(default_factory=list)
    recommended_sl: Optional[float] = None
    recommended_tp: Optional[float] = None
    market_volatility: float = 0.0

def validate_sl_tp_levels(df: pd.DataFrame, entry_price: float,
                         stop_loss: float, take_profit: float,
                         signal_type: str = "LONG") -> ValidationReport:
    """
    Validar niveles de SL/TP basados en datos históricos

    Args:
        df: DataFrame con datos OHLC
        entry_price: Precio de entrada
        stop_loss: Precio de stop loss
        take_profit: Precio de take profit
        signal_type: LONG o SHORT

    Returns:
        ValidationReport con resultado y sugerencias
    """
    try:
        # Calcular volatilidad del mercado
        price_min = df['low'].min()
        price_max = df['high'].max()
        price_range = price_max - price_min
        volatility_pct = (price_range / price_min) * 100

        # Calcular ATR (Average True Range) para los últimos 14 períodos
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=14).mean().iloc[-1]
        atr_pct = (atr / entry_price) * 100

        # Calcular porcentajes de SL/TP
        if signal_type == "LONG":
            sl_pct = abs((stop_loss - entry_price) / entry_price) * 100
            tp_pct = abs((take_profit - entry_price) / entry_price) * 100
        else:  # SHORT
            sl_pct = abs((stop_loss - entry_price) / entry_price) * 100
            tp_pct = abs((take_profit - entry_price) / entry_price) * 100

        # Calcular Risk/Reward ratio
        rr_ratio = tp_pct / sl_pct if sl_pct > 0 else 0

        # Criterios de validación
        suggestions = []

        # 1. Verificar que SL/TP estén dentro del rango histórico
        if signal_type == "LONG":
            if stop_loss < price_min or take_profit > price_max:
                return ValidationReport(
                    result=LevelValidationResult.OUTSIDE_RANGE,
                    message=f"Niveles fuera del rango histórico ({price_min:.2f} - {price_max:.2f})",
                    suggestions=["Ajustar SL/TP dentro del rango de precios histórico"],
                    market_volatility=volatility_pct
                )
        else:  # SHORT
            if stop_loss > price_max or take_profit < price_min:
                return ValidationReport(
                    result=LevelValidationResult.OUTSIDE_RANGE,
                    message=f"Niveles fuera del rango histórico ({price_min:.2f} - {price_max:.2f})",
                    suggestions=["Ajustar SL/TP dentro del rango de precios histórico"],
                    market_volatility=volatility_pct
                )

        # 2. Verificar SL basado en ATR
        if sl_pct < atr_pct * 0.3:
            suggestions.append(f"SL muy ajustado ({sl_pct:.1f}%). Considerar usar >={atr_pct * 0.5:.1f}% (0.5x ATR)")
            result = LevelValidationResult.SL_TOO_TIGHT
        elif sl_pct > atr_pct * 3:
            suggestions.append(f"SL muy amplio ({sl_pct:.1f}%). Considerar usar <={atr_pct * 2:.1f}% (2x ATR)")
            result = LevelValidationResult.SL_TOO_WIDE

        # 3. Verificar TP basado en ATR
        if tp_pct < atr_pct * 0.5:
            suggestions.append(f"TP muy ajustado ({tp_pct:.1f}%). Considerar usar >={atr_pct:.1f}% (1x ATR)")
            result = LevelValidationResult.TP_TOO_TIGHT
        elif tp_pct > atr_pct * 5:
            suggestions.append(f"TP muy amplio ({tp_pct:.1f}%). Considerar usar <={atr_pct * 3:.1f}% (3x ATR)")
            result = LevelValidationResult.TP_TOO_WIDE

        # 4. Verificar Risk/Reward ratio
        if rr_ratio < 1.0:
            suggestions.append(f"Risk/Reward bajo ({rr_ratio:.1f}). Considerar RR >= 1.5")
            result = LevelValidationResult.INVALID_RR

        # 5. Generar recomendaciones
        recommended_sl_pct = atr_pct * 1.0  # 1x ATR
        recommended_tp_pct = atr_pct * 2.0  # 2x ATR

        if signal_type == "LONG":
            recommended_sl = entry_price * (1 - recommended_sl_pct / 100)
            recommended_tp = entry_price * (1 + recommended_tp_pct / 100)
        else:  # SHORT
            recommended_sl = entry_price * (1 + recommended_sl_pct / 100)
            recommended_tp = entry_price * (1 - recommended_tp_pct / 100)

        # Si no hay problemas, validar como correcto
        if not suggestions:
            result = LevelValidationResult.VALID
            message = f"Niveles válidos - SL: {sl_pct:.1f}%, TP: {tp_pct:.1f}%, RR: {rr_ratio:.1f}"
        else:
            message = f"Niveles requieren ajustes - SL: {sl_pct:.1f}%, TP: {tp_pct:.1f}%, RR: {rr_ratio:.1f}"

        return ValidationReport(
            result=result,
            message=message,
            suggestions=suggestions,
            recommended_sl=recommended_sl,
            recommended_tp=recommended_tp,
            market_volatility=volatility_pct
        )

    except Exception as e:
        return ValidationReport(
            result=LevelValidationResult.OUTSIDE_RANGE,
            message=f"Error en validación: {e}",
            suggestions=["Verificar datos de entrada"],
            market_volatility=0.0
        )

def calculate_adaptive_levels(df: pd.DataFrame, entry_price: float,
                             signal_type: str = "LONG",
                             risk_multiplier: float = 1.0) -> Tuple[float, float]:
    """
    Calcular niveles adaptativos de SL/TP basados en ATR

    Args:
        df: DataFrame con datos OHLC
        entry_price: Precio de entrada
        signal_type: LONG o SHORT
        risk_multiplier: Multiplicador de riesgo (1.0 = normal, 0.5 = conservador, 2.0 = agresivo)

    Returns:
        Tuple[stop_loss, take_profit]
    """
    try:
        # Calcular ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=14).mean().iloc[-1]

        # Calcular niveles adaptativos
        atr_pct = (atr / entry_price) * 100

        # Ajustar según multiplicador de riesgo
        sl_pct = atr_pct * 1.0 * risk_multiplier  # 1x ATR para SL
        tp_pct = atr_pct * 2.0 * risk_multiplier  # 2x ATR para TP

        if signal_type == "LONG":
            stop_loss = entry_price * (1 - sl_pct / 100)
            take_profit = entry_price * (1 + tp_pct / 100)
        else:  # SHORT
            stop_loss = entry_price * (1 + sl_pct / 100)
            take_profit = entry_price * (1 - tp_pct / 100)

        return stop_loss, take_profit

    except Exception as e:
        print(f"Error calculando niveles adaptativos: {e}")
        # Niveles de fallback
        if signal_type == "LONG":
            return entry_price * 0.99, entry_price * 1.02
        else:
            return entry_price * 1.01, entry_price * 0.98
