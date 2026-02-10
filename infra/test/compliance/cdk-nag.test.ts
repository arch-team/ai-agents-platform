import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import { Aspects } from 'aws-cdk-lib';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';
import {
  NetworkStack,
  SecurityStack,
  DatabaseStack,
  AgentCoreStack,
} from '../../lib/stacks';
import { createTestVpc, createVpcDependency, TEST_ENV, TEST_VPC_CIDR } from '../helpers/test-utils';

/** 提取 CDK Nag 错误断言通用逻辑 */
function expectNoNagErrors(app: cdk.App, stack: cdk.Stack): void {
  const messages = app.synth().getStackArtifact(stack.artifactId).messages;
  const errors = messages.filter((m) => m.level === 'error');
  expect(errors).toHaveLength(0);
}

describe('CDK Nag 合规测试', () => {
  it('NetworkStack 应通过 AWS Solutions checks', () => {
    const app = new cdk.App();
    const stack = new NetworkStack(app, 'TestNetworkStack', {
      env: TEST_ENV,
      vpcCidr: TEST_VPC_CIDR,
      envName: 'dev',
    });

    Aspects.of(stack).add(new AwsSolutionsChecks({ verbose: true }));

    // VPC Flow Log 相关的抑制
    NagSuppressions.addStackSuppressions(stack, [
      {
        id: 'AwsSolutions-IAM5',
        reason: 'VPC Flow Log 使用 CloudWatch Logs 需要通配符日志组权限',
      },
    ]);

    expectNoNagErrors(app, stack);
  });

  it('SecurityStack 应通过 AWS Solutions checks', () => {
    const app = new cdk.App();
    const vpc = createVpcDependency(app, TEST_ENV);

    const stack = new SecurityStack(app, 'TestSecurityStack', {
      env: TEST_ENV,
      vpc,
      envName: 'dev',
    });

    Aspects.of(stack).add(new AwsSolutionsChecks({ verbose: true }));

    expectNoNagErrors(app, stack);
  });

  it('DatabaseStack 应通过 AWS Solutions checks', () => {
    const app = new cdk.App();
    const vpcStack = new cdk.Stack(app, 'VpcStack', { env: TEST_ENV });
    const vpc = createTestVpc(vpcStack);
    const dbSecurityGroup = new ec2.SecurityGroup(vpcStack, 'TestDbSg', { vpc });
    const encryptionKey = new kms.Key(vpcStack, 'TestKey');

    const stack = new DatabaseStack(app, 'TestDatabaseStack', {
      env: TEST_ENV,
      vpc,
      dbSecurityGroup,
      encryptionKey,
      envName: 'dev',
    });

    Aspects.of(stack).add(new AwsSolutionsChecks({ verbose: true }));

    // 注意: RDS10, RDS11, RDS14, RDS16, SMG4 的抑制已在 DatabaseStack 内的资源级别定义
    // 此处仅保留 Stack 内未覆盖的 Nag 规则抑制
    NagSuppressions.addStackSuppressions(stack, [
      {
        id: 'AwsSolutions-RDS6',
        reason: 'IAM 认证已通过 iamAuthentication: true 启用',
      },
    ]);

    expectNoNagErrors(app, stack);
  });

  it('AgentCoreStack 应通过 AWS Solutions checks', () => {
    const app = new cdk.App();
    const vpc = createVpcDependency(app, TEST_ENV);

    const stack = new AgentCoreStack(app, 'TestAgentCoreStack', {
      env: TEST_ENV,
      vpc,
      envName: 'dev',
    });

    Aspects.of(stack).add(new AwsSolutionsChecks({ verbose: true }));

    // 注意: IAM4, IAM5, COG1, COG2, COG3 的抑制已在 AgentCoreStack 内定义
    expectNoNagErrors(app, stack);
  });
});
