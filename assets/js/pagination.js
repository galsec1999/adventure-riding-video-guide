export const INITIAL_VISIBLE_LIMIT = 48;
export const LOAD_MORE_BATCH_SIZE = 48;


function nonNegativeInteger(value, fallback = 0) {
  return Number.isInteger(value) && value >= 0 ? value : fallback;
}


export function clampVisibleLimit(totalCount, requestedLimit = INITIAL_VISIBLE_LIMIT) {
  const total = nonNegativeInteger(totalCount);
  const requested = nonNegativeInteger(requestedLimit, INITIAL_VISIBLE_LIMIT);
  return Math.min(total, requested);
}


export function getVisibleItems(items, requestedLimit = INITIAL_VISIBLE_LIMIT) {
  if (!Array.isArray(items)) throw new TypeError("items must be an array");
  return items.slice(0, clampVisibleLimit(items.length, requestedLimit));
}


export function nextVisibleLimit(
  currentLimit,
  totalCount,
  batchSize = LOAD_MORE_BATCH_SIZE,
) {
  const total = nonNegativeInteger(totalCount);
  const current = nonNegativeInteger(currentLimit, INITIAL_VISIBLE_LIMIT);
  const batch = Number.isInteger(batchSize) && batchSize > 0
    ? batchSize
    : LOAD_MORE_BATCH_SIZE;
  return Math.min(total, current + batch);
}
