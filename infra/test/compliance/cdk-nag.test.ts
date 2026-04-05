import * as cdk from 'aws-cdk-lib';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';
import {
  NetworkStack,
  SecurityStack,
  DatabaseStack,
  StorageStack,
  AgentCoreStack,
  ComputeStack,
  MonitoringStack,
} from '../../lib/stacks';
import {
  createCrossStackComputeDependencies,
  createCrossStackDbDependencies,
  createMonitoringTestDeps,
  createVpcDependency,
  TEST_ENV,
  TEST_VPC_CIDR,
} from '../helpers/test-utils';

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

    cdk.Aspects.of(stack).add(new AwsSolutionsChecks({ verbose: true }));

    // 资源级抑制: VPC Flow Log 内部创建的 IAM Role 需要通配符日志组权限
    NagSuppressions.addResourceSuppressions(
      stack,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'VPC Flow Log delivery role created by CDK requires wildcard CloudWatch Logs permissions (logs:CreateLogGroup, logs:CreateLogStream, etc.)',
        },
      ],
      true,
    );

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

    cdk.Aspects.of(stack).add(new AwsSolutionsChecks({ verbose: true }));

    expectNoNagErrors(app, stack);
  });

  it('DatabaseStack 应通过 AWS Solutions checks', () => {
    const app = new cdk.App();
    const { vpc, dbSecurityGroup, encryptionKey } = createCrossStackDbDependencies(app, TEST_ENV);

    const stack = new DatabaseStack(app, 'TestDatabaseStack', {
      env: TEST_ENV,
      vpc,
      dbSecurityGroup,
      encryptionKey,
      envName: 'dev',
    });

    cdk.Aspects.of(stack).add(new AwsSolutionsChecks({ verbose: true }));

    // 资源级抑制: CDK Nag RDS6 规则误报 — iamAuthentication: true 已在 AuroraConstruct 中启用
    NagSuppressions.addResourceSuppressions(
      stack,
      [
        {
          id: 'AwsSolutions-RDS6',
          reason:
            'IAM database authentication enabled via iamAuthentication: true in AuroraConstruct; CDK Nag may not detect the synthesized EnableIAMDatabaseAuthentication property',
        },
      ],
      true,
    );

    expectNoNagErrors(app, stack);
  });

  it('StorageStack 应通过 AWS Solutions checks', () => {
    const app = new cdk.App();
    const vpc = createVpcDependency(app, TEST_ENV);

    const stack = new StorageStack(app, 'TestStorageStack', {
      env: TEST_ENV,
      vpc,
      envName: 'dev',
    });

    cdk.Aspects.of(stack).add(new AwsSolutionsChecks({ verbose: true }));

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

    cdk.Aspects.of(stack).add(new AwsSolutionsChecks({ verbose: true }));

    expectNoNagErrors(app, stack);
  });

  it('ComputeStack 应通过 AWS Solutions checks', () => {
    const app = new cdk.App();
    const {
      vpc,
      apiSecurityGroupId,
      encryptionKeyArn,
      databaseSecret,
      jwtSecretArn,
      databaseEndpoint,
    } = createCrossStackComputeDependencies(app, TEST_ENV);

    const stack = new ComputeStack(app, 'TestComputeStack', {
      env: TEST_ENV,
      vpc,
      apiSecurityGroupId,
      databaseSecret,
      databaseEndpoint,
      encryptionKeyArn,
      jwtSecretArn,
      envName: 'dev',
    });

    cdk.Aspects.of(stack).add(new AwsSolutionsChecks({ verbose: true }));

    expectNoNagErrors(app, stack);
  });

  it('MonitoringStack 应通过 AWS Solutions checks', () => {
    const app = new cdk.App();
    const { databaseStack, computeStack, encryptionKey } = createMonitoringTestDeps(app, TEST_ENV);

    const stack = new MonitoringStack(app, 'TestMonitoringStack', {
      env: TEST_ENV,
      cluster: databaseStack.cluster,
      service: computeStack.service,
      loadBalancer: computeStack.loadBalancer,
      targetGroup: computeStack.targetGroup,
      encryptionKey,
      envName: 'dev',
    });

    cdk.Aspects.of(stack).add(new AwsSolutionsChecks({ verbose: true }));

    expectNoNagErrors(app, stack);
  });
});
