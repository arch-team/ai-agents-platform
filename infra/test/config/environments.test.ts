import * as cdk from 'aws-cdk-lib';
import { getEnvironmentConfig } from '../../lib/config/environments';

describe('getEnvironmentConfig', () => {
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
});
