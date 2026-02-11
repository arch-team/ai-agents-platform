import * as cdk from 'aws-cdk-lib';
import { getEnvironmentConfig } from '../../lib/config/environments';

describe('getEnvironmentConfig', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    // 每个测试前清除环境变量覆盖
    delete process.env.CDK_DEFAULT_ACCOUNT;
    delete process.env.CDK_DEFAULT_REGION;
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  it('应正确读取 dev 环境配置', () => {
    const app = new cdk.App({
      context: {
        env: 'dev',
        environments: {
          dev: {
            account: '111111111111',
            region: 'us-east-1',
            vpcCidr: '10.0.0.0/16',
          },
        },
      },
    });

    const config = getEnvironmentConfig(app);

    expect(config).toEqual({
      account: '111111111111',
      region: 'us-east-1',
      vpcCidr: '10.0.0.0/16',
      envName: 'dev',
    });
  });

  it('未指定 env 时应默认为 dev', () => {
    const app = new cdk.App({
      context: {
        environments: {
          dev: {
            account: '111111111111',
            region: 'us-east-1',
            vpcCidr: '10.0.0.0/16',
          },
        },
      },
    });

    const config = getEnvironmentConfig(app);
    expect(config.envName).toBe('dev');
  });

  it('environments 未定义时应抛出错误', () => {
    const app = new cdk.App({ context: {} });

    expect(() => getEnvironmentConfig(app)).toThrow('未找到环境配置: dev');
  });

  it('指定不存在的环境时应抛出错误', () => {
    const app = new cdk.App({
      context: {
        env: 'nonexistent',
        environments: {
          dev: {
            account: '111111111111',
            region: 'us-east-1',
            vpcCidr: '10.0.0.0/16',
          },
        },
      },
    });

    expect(() => getEnvironmentConfig(app)).toThrow('未找到环境配置: nonexistent');
  });

  describe('环境变量覆盖', () => {
    it('CDK_DEFAULT_ACCOUNT 应覆盖 cdk.json 中的 account', () => {
      process.env.CDK_DEFAULT_ACCOUNT = '999999999999';

      const app = new cdk.App({
        context: {
          env: 'dev',
          environments: {
            dev: {
              account: '111111111111',
              region: 'us-east-1',
              vpcCidr: '10.0.0.0/16',
            },
          },
        },
      });

      const config = getEnvironmentConfig(app);
      expect(config.account).toBe('999999999999');
    });

    it('CDK_DEFAULT_REGION 应覆盖 cdk.json 中的 region', () => {
      process.env.CDK_DEFAULT_REGION = 'ap-northeast-1';

      const app = new cdk.App({
        context: {
          env: 'dev',
          environments: {
            dev: {
              account: '111111111111',
              region: 'us-east-1',
              vpcCidr: '10.0.0.0/16',
            },
          },
        },
      });

      const config = getEnvironmentConfig(app);
      expect(config.region).toBe('ap-northeast-1');
    });

    it('未设置环境变量时应 fallback 到 cdk.json 配置', () => {
      const app = new cdk.App({
        context: {
          env: 'dev',
          environments: {
            dev: {
              account: '111111111111',
              region: 'us-east-1',
              vpcCidr: '10.0.0.0/16',
            },
          },
        },
      });

      const config = getEnvironmentConfig(app);
      expect(config.account).toBe('111111111111');
      expect(config.region).toBe('us-east-1');
    });
  });
});
