import { describe, it, expect } from 'vitest';

import { cn } from './cn';

describe('cn', () => {
  it('应该合并多个类名', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });

  it('应该过滤 falsy 值', () => {
    expect(cn('foo', false, null, undefined, 0, 'bar')).toBe('foo bar');
  });

  it('应该支持条件类名', () => {
    const isActive = true;
    expect(cn('base', isActive && 'active')).toBe('base active');
  });

  it('应该支持对象语法', () => {
    expect(cn({ foo: true, bar: false, baz: true })).toBe('foo baz');
  });

  it('应该支持数组语法', () => {
    expect(cn(['foo', 'bar'])).toBe('foo bar');
  });

  it('应该使用 twMerge 解决 Tailwind 冲突', () => {
    // twMerge 确保后面的类覆盖前面的冲突类
    expect(cn('px-4', 'px-2')).toBe('px-2');
    expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500');
  });

  it('应该在无参数时返回空字符串', () => {
    expect(cn()).toBe('');
  });

  it('应该处理混合参数', () => {
    expect(cn('base', { active: true }, ['extra'])).toBe('base active extra');
  });
});
