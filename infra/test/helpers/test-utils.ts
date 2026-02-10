import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';

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

/**
 * 创建测试用完整依赖集 (VPC + SecurityGroup + KMS Key)。
 * @remarks 供 Aurora Construct 等需要多依赖的测试复用
 */
export function createTestDependencies(stack: cdk.Stack) {
  const vpc = createTestVpc(stack);
  const securityGroup = new ec2.SecurityGroup(stack, 'TestSg', { vpc });
  const encryptionKey = new kms.Key(stack, 'TestKey');
  return { vpc, securityGroup, encryptionKey };
}
