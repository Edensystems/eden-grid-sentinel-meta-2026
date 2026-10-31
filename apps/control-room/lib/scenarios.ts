export const SCENARIOS = [
  'cloudy_school_day',
  'critical_priority_school',
  'night_reserve',
  'sunny_surplus',
] as const;
export type Scenario = typeof SCENARIOS[number];
export function isScenario(value: unknown): value is Scenario {
  return typeof value === 'string' && (SCENARIOS as readonly string[]).includes(value);
}
export const SCENARIO_TITLES: Record<Scenario,string> = {
  cloudy_school_day: 'Cloudy school day',
  critical_priority_school: 'Critical-load incident',
  night_reserve: 'Night-time reserve',
  sunny_surplus: 'Sunny surplus',
};
