import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as iam from 'aws-cdk-lib/aws-iam';
import {
  Runtime,
  AgentRuntimeArtifact,
  RuntimeNetworkConfiguration,
  ProtocolType,
  Gateway,
  GatewayProtocol,
  McpGatewaySearchType,
  MCPProtocolVersion,
} from '@aws-cdk/aws-bedrock-agentcore-alpha';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';
import { PROJECT_NAME, getRemovalPolicy, isProd, type BaseStackProps } from '../config';

export interface AgentCoreStackProps extends BaseStackProps {
  /** Agent Runtime 所在的 VPC */
  readonly vpc: ec2.IVpc;
}

/**
 * AgentCoreStack - Bedrock AgentCore 基础设施栈。
 * @remarks 包含 ECR 镜像仓库、AgentCore Runtime 和 Gateway。
 *          Runtime 部署在 VPC 私有子网中，Gateway 提供 MCP 协议统一工具入口。
 */
export class AgentCoreStack extends cdk.Stack {
  /** AgentCore Runtime ARN */
  public readonly runtimeArn: string;
  /** AgentCore Gateway URL */
  public readonly gatewayUrl: string;
  /** ECR 镜像仓库 */
  public readonly ecrRepository: ecr.Repository;
  /** AgentCore Runtime 实例 */
  public readonly runtime: Runtime;
  /** AgentCore Gateway 实例 */
  public readonly gateway: Gateway;

  constructor(scope: Construct, id: string, props: AgentCoreStackProps) {
    super(scope, id, props);
    const { vpc, envName } = props;

    // 1. ECR Repository — Agent 容器镜像仓库
    this.ecrRepository = new ecr.Repository(this, 'AgentEcrRepo', {
      repositoryName: `${PROJECT_NAME}-agent-${envName}`,
      removalPolicy: getRemovalPolicy(envName),
      emptyOnDelete: !isProd(envName),
      imageScanOnPush: true,
      lifecycleRules: [
        {
          description: 'Keep max 10 images',
          maxImageCount: isProd(envName) ? 20 : 10,
        },
      ],
    });

    // 2. AgentCore Runtime — 部署 Claude Agent SDK Agent 容器
    const runtimeName = `${PROJECT_NAME.replace(/-/g, '_')}_${envName}`;

    this.runtime = new Runtime(this, 'AgentRuntime', {
      runtimeName,
      description: `AI Agents Platform - ${envName} Agent Runtime`,
      agentRuntimeArtifact: AgentRuntimeArtifact.fromEcrRepository(this.ecrRepository, 'latest'),
      networkConfiguration: RuntimeNetworkConfiguration.usingVpc(this, {
        vpc,
        vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      }),
      protocolConfiguration: ProtocolType.HTTP,
      environmentVariables: {
        ENV_NAME: envName,
        PROJECT_NAME: PROJECT_NAME,
      },
    });

    // 为 Runtime 的执行角色添加 Bedrock InvokeModel 权限
    this.runtime.addToRolePolicy(
      new iam.PolicyStatement({
        actions: [
          'bedrock:InvokeModel',
          'bedrock:InvokeModelWithResponseStream',
          'bedrock:ListInferenceProfiles',
        ],
        resources: ['*'],
      }),
    );

    this.runtimeArn = this.runtime.agentRuntimeArn;

    // 3. AgentCore Gateway — MCP 协议统一工具入口
    this.gateway = new Gateway(this, 'AgentGateway', {
      gatewayName: `${PROJECT_NAME}-gateway-${envName}`,
      description: `AI Agents Platform - ${envName} MCP Gateway`,
      protocolConfiguration: GatewayProtocol.mcp({
        supportedVersions: [MCPProtocolVersion.MCP_2025_03_26],
        searchType: McpGatewaySearchType.SEMANTIC,
        instructions: 'AI Agents Platform MCP Gateway - 提供统一工具接入入口',
      }),
    });

    this.gatewayUrl = this.gateway.gatewayUrl ?? '';

    // 4. CDK Nag 抑制
    this.suppressNagRules();

    // 5. Outputs
    new cdk.CfnOutput(this, 'RuntimeArn', {
      value: this.runtimeArn,
      description: 'AgentCore Runtime ARN',
    });
    new cdk.CfnOutput(this, 'GatewayUrl', {
      value: this.gatewayUrl,
      description: 'AgentCore Gateway URL',
    });
    new cdk.CfnOutput(this, 'EcrRepositoryUri', {
      value: this.ecrRepository.repositoryUri,
      description: 'Agent container image repository URI',
    });
  }

  /** CDK Nag 合规规则抑制 — AgentCore L2 Construct 内部资源的豁免 */
  private suppressNagRules(): void {
    NagSuppressions.addResourceSuppressions(
      this.runtime,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Bedrock InvokeModel 需要通配符资源以支持多模型调用; Runtime 执行角色由 L2 Construct 自动创建',
        },
      ],
      true,
    );

    NagSuppressions.addResourceSuppressions(
      this.gateway,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Gateway 服务角色由 L2 Construct 自动创建，通配符权限是 AgentCore 服务所需',
        },
        {
          id: 'AwsSolutions-COG1',
          reason: 'Gateway 默认 Cognito User Pool 密码策略由 L2 Construct 管理',
        },
        {
          id: 'AwsSolutions-COG2',
          reason: 'Gateway 默认 Cognito User Pool 用于 M2M 认证 (Client Credentials)，无需 MFA',
        },
        {
          id: 'AwsSolutions-COG3',
          reason: 'Gateway 默认 Cognito User Pool 用于 M2M 认证，不涉及用户交互',
        },
      ],
      true,
    );

    NagSuppressions.addStackSuppressions(this, [
      {
        id: 'AwsSolutions-IAM4',
        reason: 'AgentCore L2 Construct 内部使用 AWS 托管策略是该服务的最佳实践',
      },
    ]);
  }
}
