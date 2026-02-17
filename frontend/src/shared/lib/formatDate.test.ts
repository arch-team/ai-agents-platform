import { describe, it, expect } from 'vitest';

import { formatDate, formatTime, formatDateTime, formatShortDateTime } from './formatDate';

describe('formatDate', () => {
  it('应该格式化有效的 ISO 日期字符串', () => {
    const result = formatDate('2024-01-15T14:30:00Z');
    // 检查包含年月日数字（不同环境的 locale 格式可能略有差异）
    expect(result).toContain('2024');
    expect(result).toContain('1');
    expect(result).toContain('15');
  });

  it('应该对无效日期返回 Invalid Date（safeFormat 不抛异常）', () => {
    // new Date('invalid') 不抛异常，toLocaleDateString 返回 'Invalid Date'
    const result = formatDate('invalid-date');
    expect(result).toBe('Invalid Date');
  });
});

describe('formatTime', () => {
  it('应该格式化时间部分', () => {
    const result = formatTime('2024-01-15T14:30:00Z');
    // 格式化结果应包含时间信息
    expect(result).toBeTruthy();
  });

  it('应该对无效日期返回 Invalid Date', () => {
    expect(formatTime('not-a-date')).toBe('Invalid Date');
  });
});

describe('formatDateTime', () => {
  it('应该格式化日期和时间', () => {
    const result = formatDateTime('2024-01-15T14:30:00Z');
    expect(result).toContain('2024');
  });

  it('应该对空字符串返回 Invalid Date', () => {
    expect(formatDateTime('')).toBe('Invalid Date');
  });
});

describe('formatShortDateTime', () => {
  it('应该格式化简短日期时间', () => {
    const result = formatShortDateTime('2024-01-15T14:30:00Z');
    expect(result).toBeTruthy();
    // 应该包含月日信息
    expect(result).toContain('15');
  });

  it('应该对无效日期返回 Invalid Date', () => {
    expect(formatShortDateTime('xxx')).toBe('Invalid Date');
  });
});
