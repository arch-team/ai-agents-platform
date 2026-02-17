import { describe, it, expect } from 'vitest';

import { parseNumericParam } from './parseNumericParam';

describe('parseNumericParam', () => {
  it('应该解析有效的正整数字符串', () => {
    expect(parseNumericParam('1')).toBe(1);
    expect(parseNumericParam('42')).toBe(42);
    expect(parseNumericParam('100')).toBe(100);
  });

  it('应该对 undefined 返回 undefined', () => {
    expect(parseNumericParam(undefined)).toBeUndefined();
  });

  it('应该对空字符串返回 undefined', () => {
    expect(parseNumericParam('')).toBeUndefined();
  });

  it('应该对非数字字符串返回 undefined', () => {
    expect(parseNumericParam('abc')).toBeUndefined();
    expect(parseNumericParam('12abc')).toBeUndefined();
  });

  it('应该对零返回 undefined', () => {
    expect(parseNumericParam('0')).toBeUndefined();
  });

  it('应该对负数返回 undefined', () => {
    expect(parseNumericParam('-1')).toBeUndefined();
    expect(parseNumericParam('-100')).toBeUndefined();
  });

  it('应该对小数返回 undefined', () => {
    expect(parseNumericParam('1.5')).toBeUndefined();
    expect(parseNumericParam('3.14')).toBeUndefined();
  });

  it('应该对 Infinity 返回 undefined', () => {
    expect(parseNumericParam('Infinity')).toBeUndefined();
  });

  it('应该对 NaN 返回 undefined', () => {
    expect(parseNumericParam('NaN')).toBeUndefined();
  });
});
