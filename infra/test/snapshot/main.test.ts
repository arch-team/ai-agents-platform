import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import {
  NetworkStack,
  SecurityStack,
  DatabaseStack,
  StorageStack,
  ComputeStack,
  AgentCoreStack,
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

/**
 * Docker asset hash 随 backend/ 文件变更而变化，导致 CI/本地快照不一致。
 * 将 container-assets hash 标准化后再做快照比较。
 */
function normalizeDockerHashes(template: Record<string, unknown>): Record<string, unknown> {
  const json = JSON.stringify(template);
  const normalized = json.replace(
    /container-assets-[^:]+:[a-f0-9]{64}/g,
    'container-assets-NORMALIZED:DOCKER_HASH',
  );
  return JSON.parse(normalized) as Record<string, unknown>;
}

describe('Snapshot Tests', () => {
  it('NetworkStack 快照匹配', () => {
    const app = new cdk.App();
    const stack = new NetworkStack(app, 'TestNetworkStack', {
      env: TEST_ENV,
      vpcCidr: TEST_VPC_CIDR,
      envName: 'dev',
    });

    expect(Template.fromStack(stack).toJSON()).toMatchSnapshot();
  });

  it('SecurityStack 快照匹配', () => {
    const app = new cdk.App();
    const vpc = createVpcDependency(app, TEST_ENV);

    const stack = new SecurityStack(app, 'TestSecurityStack', {
      env: TEST_ENV,
      vpc,
      envName: 'dev',
    });

    expect(Template.fromStack(stack).toJSON()).toMatchSnapshot();
  });

  it('DatabaseStack 快照匹配', () => {
    const app = new cdk.App();
    const { vpc, dbSecurityGroup, encryptionKey } = createCrossStackDbDependencies(app, TEST_ENV);

    const stack = new DatabaseStack(app, 'TestDatabaseStack', {
      env: TEST_ENV,
      vpc,
      dbSecurityGroup,
      encryptionKey,
      envName: 'dev',
    });

    expect(Template.fromStack(stack).toJSON()).toMatchSnapshot();
  });

  it('ComputeStack 快照匹配', () => {
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

    // Docker asset hash 标准化，避免 backend/ 文件变更导致快照失败
    expect(normalizeDockerHashes(Template.fromStack(stack).toJSON())).toMatchSnapshot();
  });

  it('StorageStack 快照匹配', () => {
    const app = new cdk.App();
    const vpc = createVpcDependency(app, TEST_ENV);

    const stack = new StorageStack(app, 'TestStorageStack', {
      env: TEST_ENV,
      vpc,
      envName: 'dev',
    });

    expect(Template.fromStack(stack).toJSON()).toMatchSnapshot();
  });

  it('AgentCoreStack 快照匹配', () => {
    const app = new cdk.App();
    const vpc = createVpcDependency(app, TEST_ENV);

    const stack = new AgentCoreStack(app, 'TestAgentCoreStack', {
      env: TEST_ENV,
      vpc,
      envName: 'dev',
    });

    expect(Template.fromStack(stack).toJSON()).toMatchSnapshot();
  });

  it('MonitoringStack 快照匹配', () => {
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

    expect(Template.fromStack(stack).toJSON()).toMatchSnapshot();
  });
});
