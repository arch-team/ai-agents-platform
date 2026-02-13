import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';
import type { BaseStackProps } from '../config';
import { VpcConstruct } from '../constructs/vpc';

export interface NetworkStackProps extends BaseStackProps {
  /** VPC CIDR 地址块 */
  readonly vpcCidr: string;
  /** NAT Gateway 数量 @default 1 */
  readonly natGateways?: number;
}

/**
 * NetworkStack - 网络基础设施 Stack。
 * @remarks Prod 环境自动使用 3 个 NAT Gateway (每 AZ 一个)
 */
export class NetworkStack extends cdk.Stack {
  public readonly vpc: ec2.Vpc;

  constructor(scope: Construct, id: string, props: NetworkStackProps) {
    super(scope, id, props);
    const { vpcCidr, envName, natGateways = 1 } = props;

    // NAT Gateway 数量: Prod 初期使用 1 个 (与 Dev 一致，降低成本)
    // 后续用户量增长后可通过 natGateways 参数提升到每 AZ 一个
    const vpcConstruct = new VpcConstruct(this, 'VpcConstruct', {
      vpcCidr,
      envName,
      natGateways,
    });

    this.vpc = vpcConstruct.vpc;

    // 输出 VPC ID
    new cdk.CfnOutput(this, 'VpcId', {
      value: this.vpc.vpcId,
      description: 'VPC ID',
    });
  }
}
