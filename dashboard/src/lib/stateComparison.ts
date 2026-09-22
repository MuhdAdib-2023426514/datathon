/** Unweighted median across observed states, excluding missing/non-finite values. */
export function stateMedian(values: Array<number | null | undefined>): number | null {
  const observed = values.filter((value): value is number => value != null && Number.isFinite(value)).sort((a, b) => a - b);
  if (!observed.length) return null;
  const middle = Math.floor(observed.length / 2);
  return observed.length % 2 ? observed[middle] : (observed[middle - 1] + observed[middle]) / 2;
}
