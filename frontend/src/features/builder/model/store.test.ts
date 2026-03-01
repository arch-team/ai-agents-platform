// builder store 单元测试
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';

import {
  useBuilderStore,
  useBuilderSessionId,
  useBuilderStreamContent,
  useBuilderGeneratedConfig,
  useBuilderIsGenerating,
  useBuilderIsConfirming,
  useBuilderError,
  useBuilderActions,
} from './store';

import type { AgentConfig } from '../api/types';

const mockConfig: AgentConfig = {
  name: '客服助手',
  description: '智能客服 Agent',
  system_prompt: '你是一个客服助手',
  model_id: 'claude-3-5-sonnet',
  temperature: 0.7,
  max_tokens: 4096,
};

describe('useBuilderStore', () => {
  beforeEach(() => {
    // 通过 reset action 重置 store
    const { result } = renderHook(() => useBuilderActions());
    act(() => {
      result.current.reset();
    });
  });

  it('初始状态应正确', () => {
    const state = useBuilderStore.getState();
    expect(state.sessionId).toBeNull();
    expect(state.streamContent).toBe('');
    expect(state.generatedConfig).toBeNull();
    expect(state.isGenerating).toBe(false);
    expect(state.isConfirming).toBe(false);
    expect(state.error).toBeNull();
  });

  describe('setSessionId', () => {
    it('应设置会话 ID', () => {
      const { result: actionsResult } = renderHook(() => useBuilderActions());
      const { result: sessionResult } = renderHook(() => useBuilderSessionId());

      act(() => {
        actionsResult.current.setSessionId(42);
      });

      expect(sessionResult.current).toBe(42);
    });

    it('应支持设置为 null', () => {
      const { result: actionsResult } = renderHook(() => useBuilderActions());
      const { result: sessionResult } = renderHook(() => useBuilderSessionId());

      act(() => {
        actionsResult.current.setSessionId(42);
      });

      act(() => {
        actionsResult.current.setSessionId(null);
      });

      expect(sessionResult.current).toBeNull();
    });
  });

  describe('appendStreamContent', () => {
    it('应追加流式内容', () => {
      const { result: actionsResult } = renderHook(() => useBuilderActions());
      const { result: contentResult } = renderHook(() => useBuilderStreamContent());

      act(() => {
        actionsResult.current.appendStreamContent('你好');
      });

      act(() => {
        actionsResult.current.appendStreamContent('世界');
      });

      expect(contentResult.current).toBe('你好世界');
    });
  });

  describe('setGeneratedConfig', () => {
    it('应设置生成的配置', () => {
      const { result: actionsResult } = renderHook(() => useBuilderActions());
      const { result: configResult } = renderHook(() => useBuilderGeneratedConfig());

      act(() => {
        actionsResult.current.setGeneratedConfig(mockConfig);
      });

      expect(configResult.current).toEqual(mockConfig);
      expect(configResult.current?.name).toBe('客服助手');
    });

    it('应支持设置为 null', () => {
      const { result: actionsResult } = renderHook(() => useBuilderActions());
      const { result: configResult } = renderHook(() => useBuilderGeneratedConfig());

      act(() => {
        actionsResult.current.setGeneratedConfig(mockConfig);
      });

      act(() => {
        actionsResult.current.setGeneratedConfig(null);
      });

      expect(configResult.current).toBeNull();
    });
  });

  describe('setGenerating', () => {
    it('应设置生成状态', () => {
      const { result: actionsResult } = renderHook(() => useBuilderActions());
      const { result: generatingResult } = renderHook(() => useBuilderIsGenerating());

      act(() => {
        actionsResult.current.setGenerating(true);
      });

      expect(generatingResult.current).toBe(true);

      act(() => {
        actionsResult.current.setGenerating(false);
      });

      expect(generatingResult.current).toBe(false);
    });
  });

  describe('setConfirming', () => {
    it('应设置确认状态', () => {
      const { result: actionsResult } = renderHook(() => useBuilderActions());
      const { result: confirmingResult } = renderHook(() => useBuilderIsConfirming());

      act(() => {
        actionsResult.current.setConfirming(true);
      });

      expect(confirmingResult.current).toBe(true);

      act(() => {
        actionsResult.current.setConfirming(false);
      });

      expect(confirmingResult.current).toBe(false);
    });
  });

  describe('setError', () => {
    it('应设置错误信息', () => {
      const { result: actionsResult } = renderHook(() => useBuilderActions());
      const { result: errorResult } = renderHook(() => useBuilderError());

      act(() => {
        actionsResult.current.setError('生成失败');
      });

      expect(errorResult.current).toBe('生成失败');
    });

    it('应支持设置为 null 以清除错误', () => {
      const { result: actionsResult } = renderHook(() => useBuilderActions());
      const { result: errorResult } = renderHook(() => useBuilderError());

      act(() => {
        actionsResult.current.setError('生成失败');
      });

      act(() => {
        actionsResult.current.setError(null);
      });

      expect(errorResult.current).toBeNull();
    });
  });

  describe('reset', () => {
    it('应将所有状态重置为初始值', () => {
      const { result: actionsResult } = renderHook(() => useBuilderActions());

      // 修改所有状态
      act(() => {
        actionsResult.current.setSessionId(1);
        actionsResult.current.appendStreamContent('一些内容');
        actionsResult.current.setGeneratedConfig(mockConfig);
        actionsResult.current.setGenerating(true);
        actionsResult.current.setConfirming(true);
        actionsResult.current.setError('错误');
      });

      // 重置
      act(() => {
        actionsResult.current.reset();
      });

      const state = useBuilderStore.getState();
      expect(state.sessionId).toBeNull();
      expect(state.streamContent).toBe('');
      expect(state.generatedConfig).toBeNull();
      expect(state.isGenerating).toBe(false);
      expect(state.isConfirming).toBe(false);
      expect(state.error).toBeNull();
    });
  });
});
