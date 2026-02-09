import { PROJECT_NAME, getRequiredTags } from '../../lib/config/constants';

describe('constants', () => {
  describe('PROJECT_NAME', () => {
    it('应为 ai-agents-platform', () => {
      expect(PROJECT_NAME).toBe('ai-agents-platform');
    });
  });

  describe('getRequiredTags', () => {
    it('应返回包含必须标签的对象', () => {
      const tags = getRequiredTags('dev');

      expect(tags).toEqual({
        Project: 'ai-agents-platform',
        Environment: 'dev',
        CostCenter: 'ai-platform',
        ManagedBy: 'cdk',
      });
    });

    it('应根据环境名称设置 Environment 标签', () => {
      const prodTags = getRequiredTags('prod');
      expect(prodTags.Environment).toBe('prod');

      const stagingTags = getRequiredTags('staging');
      expect(stagingTags.Environment).toBe('staging');
    });
  });
});
