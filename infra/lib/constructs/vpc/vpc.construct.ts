import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export interface VpcConstructProps {
  /** VPC CIDR 地址块 */
  readonly vpcCidr: string;
  /** 最大可用区数量 @default 3 */
  readonly maxAzs?: number;
  /** NAT Gateway 数量 @default 1 (Dev 节省成本) */
  readonly natGateways?: number;
  /** 是否启用 VPC Flow Log @default true */
  readonly enableFlowLog?: boolean;
}

/**
 * VPC Construct - 创建分层 VPC (Public/Private/Isolated)。
 * @remarks 默认 3 AZ，1 个 NAT Gateway (Dev 节省成本)。
 */
export class VpcConstruct extends Construct {
  public readonly vpc: ec2.Vpc;

  constructor(scope: Construct, id: string, props: VpcConstructProps) {
    super(scope, id);
    const { vpcCidr, maxAzs = 3, natGateways = 1, enableFlowLog = true } = props;

    this.vpc = new ec2.Vpc(this, 'Vpc', {
      ipAddresses: ec2.IpAddresses.cidr(vpcCidr),
      maxAzs,
      natGateways,
      subnetConfiguration: [
        { name: 'Public', subnetType: ec2.SubnetType.PUBLIC, cidrMask: 24 },
        {
          name: 'Private',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          cidrMask: 24,
        },
        {
          name: 'Isolated',
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
          cidrMask: 24,
        },
      ],
      enableDnsHostnames: true,
      enableDnsSupport: true,
    });

    // VPC Flow Log (安全审计)
    if (enableFlowLog) {
      this.vpc.addFlowLog('FlowLog', {
        destination: ec2.FlowLogDestination.toCloudWatchLogs(),
        trafficType: ec2.FlowLogTrafficType.ALL,
      });
    }

    // S3 Gateway Endpoint (免费，减少 NAT 流量)
    this.vpc.addGatewayEndpoint('S3Endpoint', {
      service: ec2.GatewayVpcEndpointAwsService.S3,
    });
  }
}
