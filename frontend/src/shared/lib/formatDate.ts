// 日期格式化工具函数

/** 格式化为日期字符串（如 "2024/1/15"） */
export function formatDate(isoString: string): string {
  try {
    return new Date(isoString).toLocaleDateString('zh-CN');
  } catch {
    return '';
  }
}

/** 格式化为时间字符串（如 "14:30"） */
export function formatTime(isoString: string): string {
  try {
    return new Date(isoString).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '';
  }
}

/** 格式化为日期时间字符串（如 "2024/1/15 14:30"） */
export function formatDateTime(isoString: string): string {
  try {
    return new Date(isoString).toLocaleString('zh-CN');
  } catch {
    return '';
  }
}

/** 格式化为简短日期时间（如 "1月15日 14:30"） */
export function formatShortDateTime(isoString: string): string {
  try {
    return new Date(isoString).toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '';
  }
}
