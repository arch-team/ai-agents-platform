import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { AgentCoreStack } from '../../lib/stacks/agentcore-stack';
import { createVpcDependency } from '../helpers/test-utils';

describe('AgentCoreStack', () => {
  let template: Template;
  let stack: AgentCoreStack;

  beforeEach(() => {
    const app = new cdk.App();
    const vpc = createVpcDependency(app);

    stack = new AgentCoreStack(app, 'TestAgentCoreStack', {
      vpc,
      envName: 'dev',
    });
    template = Template.fromStack(stack);
  });

  describe('ECR Repository', () => {
    it('应创建 ECR 镜像仓库', () => {
      template.hasResourceProperties('AWS::ECR::Repository', {
        RepositoryName: 'ai-agents-platform-agent-dev',
        ImageScanningConfiguration: {
          ScanOnPush: true,
        },
      });
    });

    it('应配置生命周期规则', () => {
      template.hasResourceProperties('AWS::ECR::Repository', {
        LifecyclePolicy: Match.objectLike({
          LifecyclePolicyText: Match.anyValue(),
        }),
      });
    });

    it('Dev 环境应使用 DESTROY 删除策略', () => {
      const resources = template.findResources('AWS::ECR::Repository');
      const repoKey = Object.keys(resources)[0];
      expect(resources[repoKey].UpdateReplacePolicy).toBe('Delete');
      expect(resources[repoKey].DeletionPolicy).toBe('Delete');
    });
  });

  describe('AgentCore Runtime', () => {
    it('应创建 AgentCore Runtime', () => {
      template.hasResourceProperties('AWS::BedrockAgentCore::Runtime', {
        AgentRuntimeName: 'ai_agents_platform_dev',
        Description: Match.stringLikeRegexp('dev.*Agent Runtime'),
      });
    });

    it('Runtime 应配置 VPC 网络', () => {
      template.hasResourceProperties('AWS::BedrockAgentCore::Runtime', {
        NetworkConfiguration: Match.objectLike({
          NetworkMode: 'VPC',
        }),
      });
    });

    it('Runtime 应配置环境变量', () => {
      template.hasResourceProperties('AWS::BedrockAgentCore::Runtime', {
        EnvironmentVariables: Match.objectLike({
          ENV_NAME: 'dev',
          PROJECT_NAME: 'ai-agents-platform',
        }),
      });
    });

    it('Runtime 执行角色应有 Bedrock InvokeModel 权限', () => {
      template.hasResourceProperties('AWS::IAM::Policy', {
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: Match.arrayWith([
                'bedrock:InvokeModel',
                'bedrock:InvokeModelWithResponseStream',
                'bedrock:ListInferenceProfiles',
              ]),
              Effect: 'Allow',
            }),
          ]),
          Version: '2012-10-17',
        },
      });
    });
  });

  describe('AgentCore Gateway', () => {
    it('应创建 AgentCore Gateway', () => {
      template.hasResourceProperties('AWS::BedrockAgentCore::Gateway', {
        Name: 'ai-agents-platform-gateway-dev',
        Description: Match.stringLikeRegexp('dev.*MCP Gateway'),
      });
    });

    it('Gateway 应使用 MCP 协议', () => {
      template.hasResourceProperties('AWS::BedrockAgentCore::Gateway', {
        ProtocolConfiguration: Match.objectLike({
          Mcp: Match.objectLike({
            SearchType: 'SEMANTIC',
          }),
        }),
      });
    });
  });

  describe('Outputs', () => {
    it('应输出 RuntimeArn', () => {
      template.hasOutput('RuntimeArn', {
        Description: 'AgentCore Runtime ARN',
      });
    });

    it('应输出 GatewayUrl', () => {
      template.hasOutput('GatewayUrl', {
        Description: 'AgentCore Gateway URL',
      });
    });

    it('应输出 EcrRepositoryUri', () => {
      template.hasOutput('EcrRepositoryUri', {
        Description: 'Agent container image repository URI',
      });
    });
  });

  describe('公开属性', () => {
    it('应暴露 runtimeArn, gatewayUrl, ecrRepository', () => {
      expect(stack.runtimeArn).toBeDefined();
      expect(stack.gatewayUrl).toBeDefined();
      expect(stack.ecrRepository).toBeDefined();
      expect(stack.runtime).toBeDefined();
      expect(stack.gateway).toBeDefined();
    });
  });

  describe('Prod 环境配置', () => {
    it('Prod 环境 ECR 应使用 RETAIN 删除策略', () => {
      const app = new cdk.App();
      const vpc = createVpcDependency(app);

      const prodStack = new AgentCoreStack(app, 'ProdAgentCoreStack', {
        vpc,
        envName: 'prod',
      });
      const prodTemplate = Template.fromStack(prodStack);

      const resources = prodTemplate.findResources('AWS::ECR::Repository');
      const repoKey = Object.keys(resources)[0];
      expect(resources[repoKey].UpdateReplacePolicy).toBe('Retain');
      expect(resources[repoKey].DeletionPolicy).toBe('Retain');
    });
  });
});
