import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import {
  NetworkStack,
  SecurityStack,
  DatabaseStack,
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
      dbSecurityGroup,
      encryptionKeyArn,
      databaseSecret,
      jwtSecretArn,
      databaseEndpoint,
    } = createCrossStackComputeDependencies(app, TEST_ENV);

    const stack = new ComputeStack(app, 'TestComputeStack', {
      env: TEST_ENV,
      vpc,
      dbSecurityGroup,
      databaseSecret,
      databaseEndpoint,
      encryptionKeyArn,
      jwtSecretArn,
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
