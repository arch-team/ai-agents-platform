/**
 * 安全解析 URL 路由参数为正整数
 * 返回合法的正整数 或 undefined（参数为空、NaN、负数、小数时）
 */
export function parseNumericParam(value: string | undefined): number | undefined {
  if (!value) return undefined;
  const num = Number(value);
  if (!Number.isFinite(num) || num <= 0 || !Number.isInteger(num)) return undefined;
  return num;
}
