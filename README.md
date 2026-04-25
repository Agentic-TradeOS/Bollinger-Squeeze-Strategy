# Bollinger Squeeze Breakout Strategy

A quantitative volatility breakout system that identifies periods of market consolidation ("coiling") and signals high-probability entries when volatility expands.

## 📈 Strategy Overview
The **Bollinger Squeeze** is based on the premise that prices typically alternate between periods of low volatility (consolidation) and high volatility (trending). By identifying these cycles, we can anticipate explosive moves before they happen.

## 🛠 How It Works
The strategy monitors the relationship between **Bollinger Bands** and **Keltner Channels**:

1.  **The Squeeze:** Occurs when Bollinger Bands (20, 2) move *inside* the Keltner Channels (20, 1.5). This indicates that volatility has dropped to historically low levels.
2.  **The Build-up:** During the squeeze, the momentum oscillator (usually a histogram based on Linear Regression) tracks the underlying pressure.
3.  **The Fire:** A signal is generated when the Bollinger Bands expand back *outside* the Keltner Channels.

### Entry Rules
- **Long:** The Squeeze "fires" (Bands expand) and the momentum histogram is positive and increasing.
- **Short:** The Squeeze "fires" (Bands expand) and the momentum histogram is negative and decreasing.

## ⚙️ Core Components
| Indicator | Purpose | Configuration |
| :--- | :--- | :--- |
| **Bollinger Bands** | Measures Volatility | 20 SMA, 2.0 StdDev |
| **Keltner Channels** | Measures ATR Range | 20 EMA, 1.5 ATR |
| **Momentum Oscillator**| Directional Filter | Linear Regression / MACD |

## 📊 Mathematical Logic
The squeeze is active when:
`Bollinger Band Width < Keltner Channel Width`

The exit is typically signaled when the momentum histogram changes color (showing a slowing of the trend) or the price touches the opposite Bollinger Band.

## 🚀 Usage
This strategy is highly effective on **1H, 4H, and Daily** timeframes. It is best used on liquid assets such as Major FX Pairs, Blue Chip Stocks, or High-Cap Crypto.

---
*Disclaimer: Trading involves significant risk. This strategy documentation is for educational purposes only.*
