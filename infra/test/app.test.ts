import * as cdk from 'aws-cdk-lib';
import {
  NetworkStack,
  SecurityStack,
  DatabaseStack,
  ComputeStack,
  AgentCoreStack,
  MonitoringStack,
} from '../lib/stacks';
import { TEST_ENV, TEST_VPC_CIDR } from './helpers/test-utils';

/** 完整 6 层 Stack 组合的返回类型 */
interface StackGroup {
  readonly networkStack: NetworkStack;
  readonly securityStack: SecurityStack;
  readonly databaseStack: DatabaseStack;
  readonly computeStack: ComputeStack;
  readonly agentCoreStack: AgentCoreStack;
  readonly monitoringStack: MonitoringStack;
}

/**
 * 创建完整的 6 层 Stack 组合并设置依赖关系。
 * @remarks 依赖链: Network → Security → Database → Compute → Monitoring，Network → AgentCore
 */
function createStackGroup(app: cdk.App): StackGroup {
  const networkStack = new NetworkStack(app, 'TestNetworkStack', {
    env: TEST_ENV,
    vpcCidr: TEST_VPC_CIDR,
    envName: 'dev',
  });

  const securityStack = new SecurityStack(app, 'TestSecurityStack', {
    env: TEST_ENV,
    vpc: networkStack.vpc,
    envName: 'dev',
  });
  securityStack.addDependency(networkStack);

  const databaseStack = new DatabaseStack(app, 'TestDatabaseStack', {
    env: TEST_ENV,
    vpc: networkStack.vpc,
    dbSecurityGroup: securityStack.dbSecurityGroup,
    encryptionKey: securityStack.encryptionKey,
    envName: 'dev',
  });
  databaseStack.addDependency(networkStack);
  databaseStack.addDependency(securityStack);

  const computeStack = new ComputeStack(app, 'TestComputeStack', {
    env: TEST_ENV,
    vpc: networkStack.vpc,
    apiSecurityGroupId: securityStack.apiSecurityGroup.securityGroupId,
    databaseSecret: databaseStack.dbSecret,
    databaseEndpoint: databaseStack.cluster.clusterEndpoint.hostname,
    encryptionKeyArn: securityStack.encryptionKey.keyArn,
    jwtSecretArn: securityStack.jwtSecret.secretArn,
    envName: 'dev',
  });
  computeStack.addDependency(networkStack);
  computeStack.addDependency(securityStack);
  computeStack.addDependency(databaseStack);

  const agentCoreStack = new AgentCoreStack(app, 'TestAgentCoreStack', {
    env: TEST_ENV,
    vpc: networkStack.vpc,
    envName: 'dev',
  });
  agentCoreStack.addDependency(networkStack);

  const monitoringStack = new MonitoringStack(app, 'TestMonitoringStack', {
    env: TEST_ENV,
    cluster: databaseStack.cluster,
    service: computeStack.service,
    loadBalancer: computeStack.loadBalancer,
    targetGroup: computeStack.targetGroup,
    encryptionKey: securityStack.encryptionKey,
    envName: 'dev',
  });
  monitoringStack.addDependency(databaseStack);
  monitoringStack.addDependency(computeStack);
  monitoringStack.addDependency(securityStack);

  return {
    networkStack,
    securityStack,
    databaseStack,
    computeStack,
    agentCoreStack,
    monitoringStack,
  };
}

describe('CDK App 集成测试', () => {
  it('应能创建完整的 6 个 Stack', () => {
    const app = new cdk.App();
    const stacks = createStackGroup(app);

    expect(stacks.networkStack).toBeDefined();
    expect(stacks.securityStack).toBeDefined();
    expect(stacks.databaseStack).toBeDefined();
    expect(stacks.computeStack).toBeDefined();
    expect(stacks.agentCoreStack).toBeDefined();
    expect(stacks.monitoringStack).toBeDefined();
  });

  it('Stack 依赖关系应正确', () => {
    const app = new cdk.App();
    const {
      networkStack,
      securityStack,
      databaseStack,
      computeStack,
      agentCoreStack,
      monitoringStack,
    } = createStackGroup(app);

    // SecurityStack 依赖 NetworkStack
    expect(securityStack.dependencies).toContain(networkStack);

    // DatabaseStack 依赖 NetworkStack + SecurityStack
    expect(databaseStack.dependencies).toContain(networkStack);
    expect(databaseStack.dependencies).toContain(securityStack);

    // ComputeStack 依赖 NetworkStack + SecurityStack + DatabaseStack
    expect(computeStack.dependencies).toContain(networkStack);
    expect(computeStack.dependencies).toContain(securityStack);
    expect(computeStack.dependencies).toContain(databaseStack);

    // AgentCoreStack 依赖 NetworkStack
    expect(agentCoreStack.dependencies).toContain(networkStack);

    // MonitoringStack 依赖 DatabaseStack + ComputeStack + SecurityStack
    expect(monitoringStack.dependencies).toContain(databaseStack);
    expect(monitoringStack.dependencies).toContain(computeStack);
    expect(monitoringStack.dependencies).toContain(securityStack);
  });

  it('ComputeStack 应暴露 ALB 和 ECS 服务属性', () => {
    const app = new cdk.App();
    const { computeStack } = createStackGroup(app);

    expect(computeStack.albDnsName).toBeDefined();
    expect(computeStack.service).toBeDefined();
    expect(computeStack.loadBalancer).toBeDefined();
    expect(computeStack.targetGroup).toBeDefined();
  });

  it('DatabaseStack 应暴露集群和 Secret 属性', () => {
    const app = new cdk.App();
    const { databaseStack } = createStackGroup(app);

    expect(databaseStack.cluster).toBeDefined();
    expect(databaseStack.dbSecret).toBeDefined();
  });
});
