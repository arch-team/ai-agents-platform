// execution (chat) store 单元测试
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';

import {
  useChatStore,
  useStreamingContent,
  useIsStreaming,
  useChatError,
  useChatActions,
} from './store';

describe('useChatStore', () => {
  beforeEach(() => {
    // 重置 store 到初始状态
    useChatStore.setState({
      currentConversationId: null,
      streamingContent: '',
      isStreaming: false,
      error: null,
    });
  });

  it('初始状态应正确', () => {
    const state = useChatStore.getState();
    expect(state.currentConversationId).toBeNull();
    expect(state.streamingContent).toBe('');
    expect(state.isStreaming).toBe(false);
    expect(state.error).toBeNull();
  });

  describe('setCurrentConversation', () => {
    it('应设置当前对话 ID', () => {
      const { result } = renderHook(() => useChatActions());

      act(() => {
        result.current.setCurrentConversation(1);
      });

      expect(useChatStore.getState().currentConversationId).toBe(1);
    });

    it('应支持设置为 null', () => {
      const { result } = renderHook(() => useChatActions());

      act(() => {
        result.current.setCurrentConversation(1);
      });

      act(() => {
        result.current.setCurrentConversation(null);
      });

      expect(useChatStore.getState().currentConversationId).toBeNull();
    });
  });

  describe('appendStreamContent', () => {
    it('应追加流式内容', () => {
      const { result: actionsResult } = renderHook(() => useChatActions());
      const { result: contentResult } = renderHook(() => useStreamingContent());

      act(() => {
        actionsResult.current.setCurrentConversation(1);
      });

      act(() => {
        actionsResult.current.appendStreamContent(1, '你好');
      });

      act(() => {
        actionsResult.current.appendStreamContent(1, '世界');
      });

      expect(contentResult.current).toBe('你好世界');
    });

    it('应忽略非当前对话的流式内容', () => {
      const { result: actionsResult } = renderHook(() => useChatActions());
      const { result: contentResult } = renderHook(() => useStreamingContent());

      // 设置当前对话为 1
      act(() => {
        actionsResult.current.setCurrentConversation(1);
      });

      act(() => {
        actionsResult.current.appendStreamContent(1, '对话1');
      });

      // 尝试追加对话 2 的内容（应被忽略）
      act(() => {
        actionsResult.current.appendStreamContent(2, '对话2');
      });

      expect(contentResult.current).toBe('对话1');
    });

    it('currentConversationId 为 null 时应追加内容', () => {
      const { result: actionsResult } = renderHook(() => useChatActions());
      const { result: contentResult } = renderHook(() => useStreamingContent());

      // 不设置 currentConversationId（保持 null）
      act(() => {
        actionsResult.current.appendStreamContent(1, '内容');
      });

      expect(contentResult.current).toBe('内容');
    });
  });

  describe('clearStream', () => {
    it('应清除流式内容和流式状态', () => {
      const { result: actionsResult } = renderHook(() => useChatActions());
      const { result: contentResult } = renderHook(() => useStreamingContent());
      const { result: streamingResult } = renderHook(() => useIsStreaming());

      act(() => {
        actionsResult.current.setStreaming(true);
        actionsResult.current.appendStreamContent(1, '一些内容');
      });

      act(() => {
        actionsResult.current.clearStream();
      });

      expect(contentResult.current).toBe('');
      expect(streamingResult.current).toBe(false);
    });
  });

  describe('setStreaming', () => {
    it('应设置流式状态', () => {
      const { result: actionsResult } = renderHook(() => useChatActions());
      const { result: streamingResult } = renderHook(() => useIsStreaming());

      act(() => {
        actionsResult.current.setStreaming(true);
      });

      expect(streamingResult.current).toBe(true);

      act(() => {
        actionsResult.current.setStreaming(false);
      });

      expect(streamingResult.current).toBe(false);
    });
  });

  describe('setError / clearError', () => {
    it('应设置错误信息', () => {
      const { result: actionsResult } = renderHook(() => useChatActions());
      const { result: errorResult } = renderHook(() => useChatError());

      act(() => {
        actionsResult.current.setError('连接失败');
      });

      expect(errorResult.current).toBe('连接失败');
    });

    it('应清除错误信息', () => {
      const { result: actionsResult } = renderHook(() => useChatActions());
      const { result: errorResult } = renderHook(() => useChatError());

      act(() => {
        actionsResult.current.setError('连接失败');
      });

      act(() => {
        actionsResult.current.clearError();
      });

      expect(errorResult.current).toBeNull();
    });
  });
});
