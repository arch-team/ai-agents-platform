import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { useOperatingItem } from './useOperatingItem';

describe('useOperatingItem', () => {
  it('初始状态 operatingId 为 null', () => {
    const { result } = renderHook(() => useOperatingItem<number>());
    expect(result.current.operatingId).toBeNull();
  });

  it('execute 设置 operatingId 并在 onSettled 后清除', () => {
    const { result } = renderHook(() => useOperatingItem<number>());

    let settledCallback: (() => void) | null = null;
    const mockMutation = {
      mutate: vi.fn((_id: number, opts: { onSettled: () => void }) => {
        settledCallback = opts.onSettled;
      }),
      isPending: false,
    };

    act(() => {
      result.current.execute(mockMutation, 42);
    });

    // execute 后 operatingId 被设置
    expect(result.current.operatingId).toBe(42);
    expect(mockMutation.mutate).toHaveBeenCalledWith(42, expect.any(Object));

    // onSettled 触发后 operatingId 清除
    act(() => {
      settledCallback!();
    });
    expect(result.current.operatingId).toBeNull();
  });

  it('支持 string 类型 ID', () => {
    const { result } = renderHook(() => useOperatingItem<string>());

    let settledCallback: (() => void) | null = null;
    const mockMutation = {
      mutate: vi.fn((_id: string, opts: { onSettled: () => void }) => {
        settledCallback = opts.onSettled;
      }),
      isPending: false,
    };

    act(() => {
      result.current.execute(mockMutation, 'tool-abc');
    });

    expect(result.current.operatingId).toBe('tool-abc');

    act(() => {
      settledCallback!();
    });
    expect(result.current.operatingId).toBeNull();
  });
});
