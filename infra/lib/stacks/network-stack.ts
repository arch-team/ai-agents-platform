import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';
import { isProd, type BaseStackProps } from '../config';
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

    const vpcConstruct = new VpcConstruct(this, 'VpcConstruct', {
      vpcCidr,
      envName,
      natGateways: isProd(envName) ? 3 : natGateways,
    });

    this.vpc = vpcConstruct.vpc;

    // 输出 VPC ID
    new cdk.CfnOutput(this, 'VpcId', {
      value: this.vpc.vpcId,
      description: 'VPC ID',
    });
  }
}
