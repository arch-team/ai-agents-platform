import * as cdk from 'aws-cdk-lib';
import { getEnvironmentConfig } from '../../lib/config/environments';

describe('getEnvironmentConfig', () => {
  const originalEnv = process.env;

  beforeEach(() => {
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

    expect(() => getEnvironmentConfig(app)).toThrow('无效的环境名称: nonexistent');
  });

  describe('cdk.json 优先，环境变量 fallback', () => {
    it('cdk.json 有值时不被 CDK_DEFAULT_ACCOUNT 覆盖', () => {
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
      expect(config.account).toBe('111111111111');
    });

    it('cdk.json 有值时不被 CDK_DEFAULT_REGION 覆盖', () => {
      process.env.CDK_DEFAULT_REGION = 'us-west-2';

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
      expect(config.region).toBe('us-east-1');
    });

    it('未设置环境变量时应使用 cdk.json 配置', () => {
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
