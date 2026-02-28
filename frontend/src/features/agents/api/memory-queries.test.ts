// Memory Query Key Factory 测试

import { describe, it, expect } from 'vitest';

import { memoryKeys } from './memory-queries';

describe('memoryKeys', () => {
  it('should generate all key for agent', () => {
    expect(memoryKeys.all(42)).toEqual(['agents', 42, 'memories']);
  });

  it('should generate list key for agent', () => {
    expect(memoryKeys.list(42)).toEqual(['agents', 42, 'memories', 'list']);
  });

  it('should generate search key with query', () => {
    expect(memoryKeys.search(42, '会议')).toEqual(['agents', 42, 'memories', 'search', '会议']);
  });

  it('should generate detail key for specific memory', () => {
    expect(memoryKeys.detail(42, 'mem-123')).toEqual([
      'agents',
      42,
      'memories',
      'detail',
      'mem-123',
    ]);
  });

  it('should produce unique keys for different agents', () => {
    const key1 = memoryKeys.list(1);
    const key2 = memoryKeys.list(2);
    expect(key1).not.toEqual(key2);
  });
});
