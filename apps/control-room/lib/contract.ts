/* Structural normalization for the exact M3Evaluation contract. Never substitute fake values. */
export type DataPoint = {
  timestamp: string;
  solarKw: number;
  demandKw: number;
  forecastKw: number;
  batteryPct: number;
  scheduledBatteryPct: number;
};
export type Move = { from: number; to: number; energyKwh: number };
export type DashboardData = {
  mode: 'simulation';
  scenario: string;
  method: 'previous_day_analogue';
  schedulingStatus: string;
  generatedSolarKwh: number;
  essentialBaselineKwh: number;
  essentialScheduledKwh: number;
  flexibleBaselineKwh: number;
  flexibleScheduledKwh: number;
  batteryPct: number;
  shiftedKwh: number;
  solarMaeKw: number;
  reserveViolations: number;
  balanceResidualKwh: number;
  points: DataPoint[];
  moves: Move[];
};

function obj(x: unknown, name: string): Record<string, unknown> {
  if (typeof x !== 'object' || x === null || Array.isArray(x)) throw new Error(`Invalid ${name}`);
  return x as Record<string, unknown>;
}
function num(x: unknown, name: string): number {
  if (typeof x !== 'number' || !Number.isFinite(x)) throw new Error(`Invalid ${name}`);
  return x;
}
function str(x: unknown, name: string): string {
  if (typeof x !== 'string' || x.length < 1) throw new Error(`Invalid ${name}`);
  return x;
}
function list(x: unknown, name: string): unknown[] {
  if (!Array.isArray(x) || x.length === 0 || x.length > 24) throw new Error(`Invalid ${name}`);
  return x;
}
export function normalizeEvaluation(raw: unknown): DashboardData {
  const root = obj(raw, 'evaluation');
  if (root.mode !== 'simulation') throw new Error('Data is not explicitly simulated');
  const forecast = obj(root.forecast, 'forecast');
  if (forecast.method !== 'previous_day_analogue') throw new Error('Unsupported forecast method');
  const metrics = obj(forecast.metrics, 'forecast metrics');
  const planned = obj(root.scheduling, 'scheduling');
  const plannedSummary = obj(planned.summary, 'scheduling summary');
  const realized = obj(root.realized, 'realized');
  const baseline = obj(realized.baseline, 'baseline');
  const scheduled = obj(realized.scheduled, 'scheduled');
  const baseSummary = obj(baseline.summary, 'baseline summary');
  const schedSummary = obj(scheduled.summary, 'scheduled summary');
  if (baseline.mode !== 'simulation' || scheduled.mode !== 'simulation') throw new Error('Invalid simulation mode');
  const baselineIntervals = list(baseline.intervals, 'baseline intervals');
  const scheduledIntervals = list(scheduled.intervals, 'scheduled intervals');
  const forecasts = list(forecast.forecasts, 'forecast points');
  if (baselineIntervals.length !== forecasts.length || scheduledIntervals.length !== forecasts.length)
    throw new Error('Mismatched interval counts');
  const points = baselineIntervals.map((value, i) => {
    const interval = obj(value, 'interval');
    const scheduledInterval = obj(scheduledIntervals[i], 'scheduled interval');
    const predicted = obj(forecasts[i], 'forecast interval');
    const timestamp = str(interval.timestamp, 'timestamp');
    if (!Number.isFinite(Date.parse(timestamp)) || timestamp !== scheduledInterval.timestamp || timestamp !== predicted.timestamp)
      throw new Error('Mismatched timestamps');
    const minutes = num(interval.duration_minutes, 'duration_minutes');
    if (minutes <= 0) throw new Error('Invalid duration');
    const multiplier = 60 / minutes;
    return {
      timestamp,
      solarKw: num(interval.solar_generation_kwh, 'solar generation') * multiplier,
      demandKw: (num(interval.essential_demand_kwh, 'essential demand') + num(interval.flexible_demand_kwh, 'flexible demand')) * multiplier,
      forecastKw: num(predicted.solar_kw, 'forecast solar'),
      batteryPct: num(interval.soc_end_fraction, 'SOC') * 100,
      scheduledBatteryPct: num(scheduledInterval.soc_end_fraction, 'scheduled SOC') * 100,
    };
  });
  const moves = Array.isArray(planned.moves) ? planned.moves.map(value => {
    const move = obj(value, 'move');
    return {from: num(move.from_index, 'from_index'), to: num(move.to_index, 'to_index'), energyKwh: num(move.energy_kwh, 'movement energy')};
  }) : [];
  const reserveViolations = num(realized.battery_reserve_violations, 'reserve violations');
  const residual = num(realized.max_abs_bus_residual_kwh, 'energy residual');
  if (reserveViolations !== 0 || residual > 1e-8 || points.some(p=>p.batteryPct < -1e-5 || p.batteryPct > 100.00001 || p.scheduledBatteryPct < -1e-5 || p.scheduledBatteryPct > 100.00001))
    throw new Error('Unsafe or inconsistent simulation result');
  const solar = num(baseSummary.generated_solar_kwh, 'solar yield');
  return {
    mode: 'simulation', scenario: str(root.scenario,'scenario'),
    method: 'previous_day_analogue',
    schedulingStatus: str(planned.status, 'schedule status'),
    generatedSolarKwh: solar,
    essentialBaselineKwh: num(baseSummary.unserved_essential_kwh, 'baseline essential unserved'),
    essentialScheduledKwh: num(schedSummary.unserved_essential_kwh, 'scheduled essential unserved'),
    flexibleBaselineKwh: num(baseSummary.unserved_flexible_kwh, 'baseline flexible unserved'),
    flexibleScheduledKwh: num(schedSummary.unserved_flexible_kwh, 'scheduled flexible unserved'),
    batteryPct: num(schedSummary.final_soc_fraction, 'final SOC')*100,
    shiftedKwh: num(plannedSummary.energy_shifted_kwh,'shifted energy'),
    solarMaeKw: num(metrics.solar_mae_kw, 'solar MAE'),
    reserveViolations,
    balanceResidualKwh: residual,
    points, moves,
  };
}
