import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

/** 测试用占位符 AWS 环境 */
export const TEST_ENV: cdk.Environment = { account: '000000000000', region: 'us-east-1' };

/** 测试用默认 VPC CIDR */
export const TEST_VPC_CIDR = '10.0.0.0/16';

/**
 * 创建测试用 VPC (含 Public/Private/Isolated 子网)。
 * @remarks 供所有需要 VPC 依赖的测试复用
 */
export function createTestVpc(stack: cdk.Stack): ec2.Vpc {
  return new ec2.Vpc(stack, 'TestVpc', {
    subnetConfiguration: [
      { name: 'Public', subnetType: ec2.SubnetType.PUBLIC, cidrMask: 24 },
      { name: 'Private', subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS, cidrMask: 24 },
      { name: 'Isolated', subnetType: ec2.SubnetType.PRIVATE_ISOLATED, cidrMask: 24 },
    ],
  });
}

/** 测试依赖集返回类型 */
export interface TestDependencies {
  readonly vpc: ec2.Vpc;
  readonly securityGroup: ec2.SecurityGroup;
  readonly encryptionKey: kms.Key;
}

/**
 * 创建测试用完整依赖集 (VPC + SecurityGroup + KMS Key)。
 * @remarks 供 Aurora Construct 等需要多依赖的测试复用
 */
export function createTestDependencies(stack: cdk.Stack): TestDependencies {
  const vpc = createTestVpc(stack);
  const securityGroup = new ec2.SecurityGroup(stack, 'TestSg', { vpc });
  const encryptionKey = new kms.Key(stack, 'TestKey');
  return { vpc, securityGroup, encryptionKey };
}

/**
 * 创建独立的 VPC Stack + VPC，供跨 Stack 测试使用。
 * @remarks 返回 VPC 对象，供被测 Stack 作为依赖注入。
 *          不设置 env 以避免跨 Stack 引用限制（除非被测 Stack 也设置了 env）。
 */
export function createVpcDependency(app: cdk.App, env?: cdk.Environment): ec2.Vpc {
  const vpcStack = new cdk.Stack(app, 'VpcStack', env ? { env } : undefined);
  return createTestVpc(vpcStack);
}

/** 跨 Stack 数据库依赖集返回类型 */
export interface CrossStackDbDependencies {
  readonly vpc: ec2.Vpc;
  readonly dbSecurityGroup: ec2.SecurityGroup;
  readonly encryptionKey: kms.Key;
}

/**
 * 创建跨 Stack 的数据库依赖集 (VPC + SecurityGroup + KMS Key)。
 * @remarks 所有依赖创建在独立的 VpcStack 中，供 DatabaseStack 等跨 Stack 测试复用
 */
export function createCrossStackDbDependencies(
  app: cdk.App,
  env?: cdk.Environment,
): CrossStackDbDependencies {
  const vpcStack = new cdk.Stack(app, 'VpcStack', env ? { env } : undefined);
  const vpc = createTestVpc(vpcStack);
  const dbSecurityGroup = new ec2.SecurityGroup(vpcStack, 'TestDbSg', { vpc });
  const encryptionKey = new kms.Key(vpcStack, 'TestKey');
  return { vpc, dbSecurityGroup, encryptionKey };
}

/** 跨 Stack Compute 依赖集返回类型 */
export interface CrossStackComputeDependencies {
  readonly vpc: ec2.Vpc;
  readonly dbSecurityGroup: ec2.SecurityGroup;
  /** KMS Key 对象 — 供 DatabaseStack 等需要 IKey 的场景使用 */
  readonly encryptionKey: kms.Key;
  /** KMS Key ARN — 供 ComputeStack 等使用 ARN 避免跨 Stack 循环依赖的场景 */
  readonly encryptionKeyArn: string;
  readonly databaseSecret: secretsmanager.Secret;
  readonly jwtSecretArn: string;
  readonly databaseEndpoint: string;
}

/**
 * 创建跨 Stack 的 Compute 依赖集 (VPC + SecurityGroup + KMS Key + Secrets + DB Endpoint)。
 * @remarks 所有依赖创建在独立的 DepsStack 中，供 ComputeStack 测试复用
 */
export function createCrossStackComputeDependencies(
  app: cdk.App,
  env?: cdk.Environment,
): CrossStackComputeDependencies {
  const depsStack = new cdk.Stack(app, 'DepsStack', env ? { env } : undefined);
  const vpc = createTestVpc(depsStack);
  const dbSecurityGroup = new ec2.SecurityGroup(depsStack, 'TestDbSg', {
    vpc,
    allowAllOutbound: false,
  });
  const encryptionKey = new kms.Key(depsStack, 'TestKey');
  const databaseSecret = new secretsmanager.Secret(depsStack, 'TestDbSecret');
  const jwtSecret = new secretsmanager.Secret(depsStack, 'TestJwtSecret', {
    generateSecretString: {
      secretStringTemplate: JSON.stringify({}),
      generateStringKey: 'secret_key',
      passwordLength: 64,
    },
  });
  const databaseEndpoint = 'test-cluster.cluster-xyz.us-east-1.rds.amazonaws.com';
  return {
    vpc,
    dbSecurityGroup,
    encryptionKey,
    encryptionKeyArn: encryptionKey.keyArn,
    databaseSecret,
    jwtSecretArn: jwtSecret.secretArn,
    databaseEndpoint,
  };
}
