import * as cdk from 'aws-cdk-lib';
import * as logs from 'aws-cdk-lib/aws-logs';
import {
  PROJECT_NAME,
  getRequiredTags,
  getRemovalPolicy,
  getLogRetention,
  isDev,
  isProd,
  BEDROCK_EVAL_ACTIONS,
  getBedrockEvalResourceArns,
} from '../../lib/config/constants';
import type { EnvironmentName } from '../../lib/config/types';

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
    });
  });

  describe('getRemovalPolicy', () => {
    it('Dev 环境应返回 DESTROY', () => {
      expect(getRemovalPolicy('dev')).toBe(cdk.RemovalPolicy.DESTROY);
    });

    it('Prod 环境应返回 RETAIN', () => {
      expect(getRemovalPolicy('prod')).toBe(cdk.RemovalPolicy.RETAIN);
    });
  });

  describe('isDev', () => {
    it.each<[EnvironmentName, boolean]>([
      ['dev', true],
      ['prod', false],
    ])('环境 "%s" 应返回 %s', (envName, expected) => {
      expect(isDev(envName)).toBe(expected);
    });
  });

  describe('isProd', () => {
    it.each<[EnvironmentName, boolean]>([
      ['prod', true],
      ['dev', false],
    ])('环境 "%s" 应返回 %s', (envName, expected) => {
      expect(isProd(envName)).toBe(expected);
    });
  });

  describe('getLogRetention', () => {
    it('Dev 环境应返回 ONE_WEEK', () => {
      expect(getLogRetention('dev')).toBe(logs.RetentionDays.ONE_WEEK);
    });

    it('Prod 环境应返回 THREE_MONTHS', () => {
      expect(getLogRetention('prod')).toBe(logs.RetentionDays.THREE_MONTHS);
    });
  });

  describe('BEDROCK_EVAL_ACTIONS', () => {
    it('应包含 4 个评估相关 IAM actions', () => {
      expect(BEDROCK_EVAL_ACTIONS).toHaveLength(4);
      expect(BEDROCK_EVAL_ACTIONS).toContain('bedrock:CreateModelEvaluationJob');
      expect(BEDROCK_EVAL_ACTIONS).toContain('bedrock:GetModelEvaluationJob');
      expect(BEDROCK_EVAL_ACTIONS).toContain('bedrock:ListModelEvaluationJobs');
      expect(BEDROCK_EVAL_ACTIONS).toContain('bedrock:StopModelEvaluationJob');
    });
  });

  describe('getBedrockEvalResourceArns', () => {
    it('应返回 evaluation-job 资源 ARN', () => {
      const arns = getBedrockEvalResourceArns('123456789012');
      expect(arns).toHaveLength(1);
      expect(arns[0]).toBe('arn:aws:bedrock:*:123456789012:evaluation-job/*');
    });
  });
});
