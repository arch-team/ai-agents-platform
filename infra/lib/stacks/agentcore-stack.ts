import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as s3 from 'aws-cdk-lib/aws-s3';
import {
  Runtime,
  AgentRuntimeArtifact,
  RuntimeNetworkConfiguration,
  ProtocolType,
  Gateway,
  GatewayProtocol,
  McpGatewaySearchType,
  MCPProtocolVersion,
  Memory,
  MemoryStrategyType,
  ManagedMemoryStrategy,
} from '@aws-cdk/aws-bedrock-agentcore-alpha';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';
import {
  PROJECT_NAME,
  PROJECT_NAME_UNDERSCORE,
  getRemovalPolicy,
  isProd,
  createBedrockInvokePolicy,
  type BaseStackProps,
} from '../config';

export interface AgentCoreStackProps extends BaseStackProps {
  /** Agent Runtime 所在的 VPC */
  readonly vpc: ec2.IVpc;
  /** S3 Workspace 存储桶 — Runtime 启动时下载 Agent 工作目录 (M17) @default undefined */
  readonly workspaceBucket?: s3.IBucket;
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
  /** AgentCore Memory 实例 */
  public readonly memory: Memory;
  /** AgentCore Memory ID (注入 ECS 环境变量) */
  public readonly memoryId: string;
  /** Gateway Cognito Token Endpoint URL (OAuth2 Client Credentials) */
  public readonly gatewayTokenEndpoint: string;
  /** Gateway Cognito User Pool Client ID */
  public readonly gatewayCognitoClientId: string;

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
    const runtimeName = `${PROJECT_NAME_UNDERSCORE}_${envName}`;

    // AgentCore Runtime 仅支持部分 AZ (us-east-1 不支持 use1-az6)
    // 限制为前 2 个 AZ 的私有子网，避免部署失败
    const runtimeSubnets = vpc.selectSubnets({
      subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      availabilityZones: vpc.availabilityZones.slice(0, 2),
    });

    this.runtime = new Runtime(this, 'AgentRuntime', {
      runtimeName,
      description: `AI Agents Platform - ${envName} Agent Runtime`,
      agentRuntimeArtifact: AgentRuntimeArtifact.fromEcrRepository(this.ecrRepository, 'latest'),
      networkConfiguration: RuntimeNetworkConfiguration.usingVpc(this, {
        vpc,
        vpcSubnets: { subnets: runtimeSubnets.subnets },
      }),
      protocolConfiguration: ProtocolType.HTTP,
      environmentVariables: {
        ENV_NAME: envName,
        PROJECT_NAME: PROJECT_NAME,
      },
    });

    // 为 Runtime 的执行角色添加 Bedrock InvokeModel 权限
    // 限制到 foundation-model 和 inference-profile 资源 (与 ComputeStack 共享工厂函数)
    const accountId = cdk.Stack.of(this).account;
    this.runtime.addToRolePolicy(createBedrockInvokePolicy(accountId));

    this.runtimeArn = this.runtime.agentRuntimeArn;

    // M17: 授权 Runtime 读取 S3 Workspace 存储桶 (容器启动时下载 Agent 工作目录)
    if (props.workspaceBucket) {
      props.workspaceBucket.grantRead(this.runtime.role!);
    }

    // 3. AgentCore Gateway — MCP 协议统一工具入口
    this.gateway = new Gateway(this, 'AgentGateway', {
      gatewayName: `${PROJECT_NAME}-gateway-${envName}`,
      description: `AI Agents Platform - ${envName} MCP Gateway`,
      protocolConfiguration: GatewayProtocol.mcp({
        supportedVersions: [MCPProtocolVersion.MCP_2025_03_26],
        searchType: McpGatewaySearchType.SEMANTIC,
        instructions: 'AI Agents Platform MCP Gateway - Unified tool access entry point',
      }),
    });

    this.gatewayUrl = this.gateway.gatewayUrl ?? '';

    // Gateway Cognito 认证参数 (L2 Construct 自动创建的 Cognito User Pool)
    this.gatewayTokenEndpoint = this.gateway.tokenEndpointUrl ?? '';
    this.gatewayCognitoClientId = this.gateway.userPoolClient?.userPoolClientId ?? '';

    // 4. AgentCore Memory — Agent 跨会话长期记忆存储
    const memoryName = `${PROJECT_NAME_UNDERSCORE}_memory_${envName}`;
    this.memory = new Memory(this, 'AgentMemory', {
      memoryName,
      description: `AI Agents Platform - ${envName} Agent Memory`,
      expirationDuration: cdk.Duration.days(isProd(envName) ? 365 : 90),
      memoryStrategies: [
        new ManagedMemoryStrategy(MemoryStrategyType.SEMANTIC, {
          name: 'semantic',
          description: '提取语义记忆 — 事实、偏好和概念',
          namespaces: ['/strategies/{memoryStrategyId}/actors/{actorId}/sessions/{sessionId}'],
        }),
        new ManagedMemoryStrategy(MemoryStrategyType.USER_PREFERENCE, {
          name: 'user_preference',
          description: '提取用户偏好 — 行为模式和习惯',
          namespaces: ['/strategies/{memoryStrategyId}/actors/{actorId}/sessions/{sessionId}'],
        }),
        new ManagedMemoryStrategy(MemoryStrategyType.SUMMARIZATION, {
          name: 'summarization',
          description: '提取对话摘要 — 关键上下文压缩',
          namespaces: ['/strategies/{memoryStrategyId}/actors/{actorId}/sessions/{sessionId}'],
        }),
      ],
    });
    this.memoryId = this.memory.memoryId;

    // 6. CDK Nag 抑制
    this.suppressNagRules();

    // 7. Outputs
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
    new cdk.CfnOutput(this, 'GatewayTokenEndpoint', {
      value: this.gatewayTokenEndpoint,
      description: 'AgentCore Gateway Cognito Token Endpoint (OAuth2 Client Credentials)',
    });
    new cdk.CfnOutput(this, 'GatewayCognitoClientId', {
      value: this.gatewayCognitoClientId,
      description: 'AgentCore Gateway Cognito User Pool Client ID',
    });
    new cdk.CfnOutput(this, 'MemoryId', {
      value: this.memoryId,
      description: 'AgentCore Memory ID',
    });
  }

  /** CDK Nag 合规规则抑制 — AgentCore L2 Construct 内部资源的豁免 */
  private suppressNagRules(): void {
    NagSuppressions.addResourceSuppressions(
      this.runtime,
      [
        {
          id: 'AwsSolutions-IAM4',
          reason:
            'AgentCore Runtime L2 Construct internally creates IAM roles with AWS managed policies as best practice for this service',
        },
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Bedrock InvokeModel uses scoped wildcards (foundation-model/*, inference-profile/*); Runtime execution role is auto-created by L2 Construct',
        },
      ],
      true,
    );

    NagSuppressions.addResourceSuppressions(
      this.memory,
      [
        {
          id: 'AwsSolutions-IAM4',
          reason:
            'AgentCore Memory L2 Construct internally creates IAM execution role with AWS managed policies for memory strategy processing',
        },
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Memory execution role requires wildcard permissions for Bedrock model invocation used by memory extraction strategies',
        },
      ],
      true,
    );

    NagSuppressions.addResourceSuppressions(
      this.gateway,
      [
        {
          id: 'AwsSolutions-IAM4',
          reason:
            'AgentCore Gateway L2 Construct internally creates IAM roles with AWS managed policies as best practice for this service',
        },
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Gateway service role is auto-created by L2 Construct; wildcard permissions are required by AgentCore service',
        },
        {
          id: 'AwsSolutions-COG1',
          reason: 'Gateway default Cognito User Pool password policy is managed by L2 Construct',
        },
        {
          id: 'AwsSolutions-COG2',
          reason:
            'Gateway default Cognito User Pool is for M2M auth (Client Credentials); MFA not required',
        },
        {
          id: 'AwsSolutions-COG3',
          reason: 'Gateway default Cognito User Pool is for M2M auth; no user interaction involved',
        },
      ],
      true,
    );
  }
}
