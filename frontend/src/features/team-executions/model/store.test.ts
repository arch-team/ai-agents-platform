// team-executions store 单元测试
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';

import {
  useTeamExecStore,
  useStreamLogs,
  useIsTeamStreaming,
  useTeamExecError,
  useTeamExecActions,
} from './store';

import type { StreamLogEntry } from './types';

const mockLogEntry: StreamLogEntry = {
  sequence: 1,
  content: '开始执行任务',
  logType: 'Agent-1',
};

describe('useTeamExecStore', () => {
  beforeEach(() => {
    // 重置 store 到初始状态
    useTeamExecStore.setState({
      selectedExecutionId: null,
      streamLogs: [],
      isStreaming: false,
      error: null,
    });
  });

  it('初始状态应正确', () => {
    const state = useTeamExecStore.getState();
    expect(state.selectedExecutionId).toBeNull();
    expect(state.streamLogs).toEqual([]);
    expect(state.isStreaming).toBe(false);
    expect(state.error).toBeNull();
  });

  describe('setSelectedExecution', () => {
    it('应设置选中的执行 ID', () => {
      const { result } = renderHook(() => useTeamExecActions());

      act(() => {
        result.current.setSelectedExecution(1);
      });

      expect(useTeamExecStore.getState().selectedExecutionId).toBe(1);
    });

    it('应支持设置为 null', () => {
      const { result } = renderHook(() => useTeamExecActions());

      act(() => {
        result.current.setSelectedExecution(1);
      });

      act(() => {
        result.current.setSelectedExecution(null);
      });

      expect(useTeamExecStore.getState().selectedExecutionId).toBeNull();
    });
  });

  describe('appendLog', () => {
    it('应追加日志条目', () => {
      const { result: actionsResult } = renderHook(() => useTeamExecActions());
      const { result: logsResult } = renderHook(() => useStreamLogs());

      act(() => {
        actionsResult.current.appendLog(mockLogEntry);
      });

      expect(logsResult.current).toHaveLength(1);
      expect(logsResult.current[0].content).toBe('开始执行任务');
    });

    it('应支持追加多条日志', () => {
      const { result: actionsResult } = renderHook(() => useTeamExecActions());
      const { result: logsResult } = renderHook(() => useStreamLogs());

      act(() => {
        actionsResult.current.appendLog(mockLogEntry);
      });

      act(() => {
        actionsResult.current.appendLog({
          sequence: 2,
          content: '任务执行中',
          logType: 'Agent-2',
        });
      });

      expect(logsResult.current).toHaveLength(2);
      expect(logsResult.current[1].sequence).toBe(2);
    });
  });

  describe('clearLogs', () => {
    it('应清除日志和流式状态', () => {
      const { result: actionsResult } = renderHook(() => useTeamExecActions());
      const { result: logsResult } = renderHook(() => useStreamLogs());
      const { result: streamingResult } = renderHook(() => useIsTeamStreaming());

      act(() => {
        actionsResult.current.setStreaming(true);
        actionsResult.current.appendLog(mockLogEntry);
      });

      act(() => {
        actionsResult.current.clearLogs();
      });

      expect(logsResult.current).toEqual([]);
      expect(streamingResult.current).toBe(false);
    });
  });

  describe('setStreaming', () => {
    it('应设置流式状态', () => {
      const { result: actionsResult } = renderHook(() => useTeamExecActions());
      const { result: streamingResult } = renderHook(() => useIsTeamStreaming());

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
      const { result: actionsResult } = renderHook(() => useTeamExecActions());
      const { result: errorResult } = renderHook(() => useTeamExecError());

      act(() => {
        actionsResult.current.setError('执行失败');
      });

      expect(errorResult.current).toBe('执行失败');
    });

    it('应清除错误信息', () => {
      const { result: actionsResult } = renderHook(() => useTeamExecActions());
      const { result: errorResult } = renderHook(() => useTeamExecError());

      act(() => {
        actionsResult.current.setError('执行失败');
      });

      act(() => {
        actionsResult.current.clearError();
      });

      expect(errorResult.current).toBeNull();
    });
  });
});
