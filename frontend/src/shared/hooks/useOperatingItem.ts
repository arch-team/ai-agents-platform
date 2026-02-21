// 列表项操作状态管理 hook — 统一管理 operatingId + mutation 执行
// 消除各列表组件中重复的 setOperatingId → mutate → onSettled 模式

import { useCallback, useState } from 'react';

type MutateFn<TId> = {
  mutate: (id: TId, opts: { onSettled: () => void }) => void;
  isPending: boolean;
};

/**
 * 管理列表中"正在操作的条目"状态
 *
 * 使用场景: 列表组件中多个 mutation（激活/归档/删除等）共享同一个 operatingId，
 * 每个 mutation 的 loading 状态需要精确到具体条目。
 *
 * @returns operatingId — 当前操作中的条目 ID（用于 loading 指示器判断）
 * @returns execute — 执行 mutation 并自动管理 operatingId 生命周期
 */
export function useOperatingItem<TId extends string | number>() {
  const [operatingId, setOperatingId] = useState<TId | null>(null);

  const execute = useCallback((mutation: MutateFn<TId>, id: TId) => {
    setOperatingId(id);
    mutation.mutate(id, { onSettled: () => setOperatingId(null) });
  }, []);

  return { operatingId, execute } as const;
}
