export interface BollingerConfig {
  period: number;
  stdDev: number;
  stopLossPct: number;
  takeProfitPct: number;
}

export const defaultConfig: BollingerConfig = {
  period: 20,
  stdDev: 2.0,
  stopLossPct: 0.06,
  takeProfitPct: 0.18,
};

export function calculateBollingerBands(
  closes: number[],
  config: BollingerConfig = defaultConfig
): { upper: number[]; middle: number[]; lower: number[]; bandwidth: number[] } {
  const { period, stdDev } = config;

  return closes.reduce<{ upper: number[]; middle: number[]; lower: number[]; bandwidth: number[] }>(
    (acc, _, i) => {
      if (i < period - 1) {
        acc.upper.push(NaN); acc.middle.push(NaN);
        acc.lower.push(NaN); acc.bandwidth.push(NaN);
        return acc;
      }
      const slice = closes.slice(i - period + 1, i + 1);
      const mean = slice.reduce((a, b) => a + b, 0) / period;
      const variance = slice.reduce((sum, v) => sum + (v - mean) ** 2, 0) / period;
      const std = Math.sqrt(variance);
      const upper = mean + stdDev * std;
      const lower = mean - stdDev * std;
      acc.upper.push(upper);
      acc.middle.push(mean);
      acc.lower.push(lower);
      acc.bandwidth.push((upper - lower) / mean);
      return acc;
    },
    { upper: [], middle: [], lower: [], bandwidth: [] }
  );
}

export function generateSignals(
  closes: number[],
  config: BollingerConfig = defaultConfig
): Array<{ index: number; signal: 1 | -1 | 0; upper: number; middle: number; lower: number }> {
  const bands = calculateBollingerBands(closes, config);

  return closes.map((price, i) => {
    const upper = bands.upper[i];
    const middle = bands.middle[i];
    const lower = bands.lower[i];
    if (isNaN(upper)) return { index: i, signal: 0 as const, upper, middle, lower };

    const prevBw = bands.bandwidth[i - 1] ?? NaN;
    const squeeze = !isNaN(prevBw) && bands.bandwidth[i] > prevBw;
    const breakoutUp = squeeze && price > upper;
    const exitSignal = price < middle;

    const signal = breakoutUp ? 1 : exitSignal ? -1 : 0;
    return { index: i, signal: signal as 1 | -1 | 0, upper, middle, lower };
  });
}
