// Zustand store: Team Execution 选中状态 + 流式日志缓冲

import { create } from 'zustand';
import { useShallow } from 'zustand/shallow';

import type { StreamLogEntry, TeamExecState } from './types';

export const useTeamExecStore = create<TeamExecState>()((set) => ({
  selectedExecutionId: null,
  streamLogs: [],
  isStreaming: false,
  error: null,
  setSelectedExecution: (id) => set({ selectedExecutionId: id }),
  appendLog: (entry: StreamLogEntry) =>
    set((state) => ({ streamLogs: [...state.streamLogs, entry] })),
  clearLogs: () => set({ streamLogs: [], isStreaming: false }),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));

// 细粒度 selector hooks
export const useStreamLogs = () => useTeamExecStore((state) => state.streamLogs);
export const useIsTeamStreaming = () => useTeamExecStore((state) => state.isStreaming);
export const useTeamExecError = () => useTeamExecStore((state) => state.error);
export const useTeamExecActions = () =>
  useTeamExecStore(
    useShallow((state) => ({
      setSelectedExecution: state.setSelectedExecution,
      appendLog: state.appendLog,
      clearLogs: state.clearLogs,
      setStreaming: state.setStreaming,
      setError: state.setError,
      clearError: state.clearError,
    })),
  );
