// 日期格式化工具函数

/** 安全格式化 — 统一处理无效日期字符串 */
function safeFormat(isoString: string, formatter: (date: Date) => string): string {
  try {
    return formatter(new Date(isoString));
  } catch {
    return '';
  }
}

/** 格式化为日期字符串（如 "2024/1/15"） */
export function formatDate(isoString: string): string {
  return safeFormat(isoString, (d) => d.toLocaleDateString('zh-CN'));
}

/** 格式化为时间字符串（如 "14:30"） */
export function formatTime(isoString: string): string {
  return safeFormat(isoString, (d) =>
    d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
  );
}

/** 格式化为日期时间字符串（如 "2024/1/15 14:30"） */
export function formatDateTime(isoString: string): string {
  return safeFormat(isoString, (d) => d.toLocaleString('zh-CN'));
}

/** 格式化为简短日期时间（如 "1月15日 14:30"） */
export function formatShortDateTime(isoString: string): string {
  return safeFormat(isoString, (d) =>
    d.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
  );
}
