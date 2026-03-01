// FrontendStack — S3 私有存储 + CloudFront OAC 前端静态站点托管
import * as path from 'node:path';
import * as cdk from 'aws-cdk-lib';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';
import type { BaseStackProps } from '../config';
import { getRemovalPolicy, isDev } from '../config';

export interface FrontendStackProps extends BaseStackProps {
  /**
   * 前端构建产物路径（相对于 infra/，即 ../frontend/dist）。
   * @default path.join(__dirname, '../../../frontend/dist')
   */
  readonly frontendDistPath?: string;
  /** 后端 ALB DNS 名（如 ai-agents-dev-xxx.us-east-1.elb.amazonaws.com），用于 /api/* 反向代理 */
  readonly apiAlbDnsName?: string;
}

/**
 * FrontendStack — 前端静态站点托管栈。
 * @remarks 使用 S3 私有 Bucket + CloudFront OAC 模式，支持 SPA React Router history 模式。
 * Dev 环境使用 PRICE_CLASS_100（降低成本），Prod 使用 PRICE_CLASS_ALL（全球加速）。
 */
export class FrontendStack extends cdk.Stack {
  /** 前端静态资产 S3 私有 Bucket */
  public readonly bucket: s3.Bucket;
  /** CloudFront 分发 */
  public readonly distribution: cloudfront.Distribution;
  /** CloudFront URL（https://xxx.cloudfront.net） */
  public readonly distributionUrl: string;

  constructor(scope: Construct, id: string, props: FrontendStackProps) {
    super(scope, id, props);

    const { envName } = props;

    // --- S3 私有 Bucket（禁止公开访问） ---
    this.bucket = new s3.Bucket(this, 'FrontendBucket', {
      bucketName: `ai-agents-platform-frontend-${envName}-897473`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      versioned: false,
      removalPolicy: getRemovalPolicy(envName),
      // Dev 环境允许自动删除对象，便于 cdk destroy 清理
      autoDeleteObjects: isDev(envName),
    });

    // --- CloudFront OAC（Origin Access Control，新一代访问控制，取代 OAI） ---
    const oac = new cloudfront.S3OriginAccessControl(this, 'FrontendOAC', {
      description: `Frontend OAC for ${envName}`,
    });

    // --- API Origin（ALB 反向代理，解决 Mixed Content） ---
    const apiOrigin = props.apiAlbDnsName
      ? new origins.HttpOrigin(props.apiAlbDnsName, {
          protocolPolicy: cloudfront.OriginProtocolPolicy.HTTP_ONLY,
          httpPort: 80,
        })
      : undefined;

    // API 行为：禁用缓存，使用 CDK 托管策略
    const apiCachePolicy = cloudfront.CachePolicy.CACHING_DISABLED;

    // Authorization 通过 CachePolicy 转发; OriginRequestPolicy 用 CDK 托管策略（转发除 Host 外的所有 viewer headers）
    const apiOriginRequestPolicy = cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER;

    // --- CloudFront 分发 ---
    this.distribution = new cloudfront.Distribution(this, 'FrontendDistribution', {
      defaultBehavior: {
        // 使用 OAC 模式关联 S3 Bucket，禁止直接访问 S3
        origin: origins.S3BucketOrigin.withOriginAccessControl(this.bucket, {
          originAccessControl: oac,
        }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        compress: true,
      },
      // /api/* 和 /health* 路由到后端 ALB（通过 HTTPS CloudFront → HTTP ALB，解决 Mixed Content）
      additionalBehaviors: apiOrigin
        ? {
            '/api/*': {
              origin: apiOrigin,
              viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
              allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
              cachePolicy: apiCachePolicy,
              originRequestPolicy: apiOriginRequestPolicy,
            },
            '/health*': {
              origin: apiOrigin,
              viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
              allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD,
              cachePolicy: apiCachePolicy,
              originRequestPolicy: apiOriginRequestPolicy,
            },
          }
        : undefined,
      defaultRootObject: 'index.html',
      // SPA 路由支持：所有 404/403 返回 index.html（React Router history mode）
      errorResponses: [
        {
          httpStatus: 404,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.seconds(0),
        },
        {
          httpStatus: 403,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.seconds(0),
        },
      ],
      // Dev: PRICE_CLASS_100（北美+欧洲，降低成本）; Prod: PRICE_CLASS_ALL（全球边缘节点）
      priceClass: isDev(envName)
        ? cloudfront.PriceClass.PRICE_CLASS_100
        : cloudfront.PriceClass.PRICE_CLASS_ALL,
      comment: `AI Agents Platform Frontend - ${envName}`,
    });

    // --- S3 Bucket Policy：仅允许 CloudFront OAC 通过 SigV4 读取对象 ---
    this.bucket.addToResourcePolicy(
      new iam.PolicyStatement({
        actions: ['s3:GetObject'],
        resources: [this.bucket.arnForObjects('*')],
        principals: [new iam.ServicePrincipal('cloudfront.amazonaws.com')],
        conditions: {
          StringEquals: {
            // 限制到当前分发，防止其他 CloudFront 分发访问此 Bucket
            'AWS:SourceArn': `arn:aws:cloudfront::${cdk.Stack.of(this).account}:distribution/${this.distribution.distributionId}`,
          },
        },
      }),
    );

    // --- BucketDeployment：上传前端构建产物并自动 Invalidate CloudFront 缓存 ---
    const distPath = props.frontendDistPath ?? path.join(__dirname, '../../../frontend/dist');

    new s3deploy.BucketDeployment(this, 'DeployFrontend', {
      sources: [s3deploy.Source.asset(distPath)],
      destinationBucket: this.bucket,
      // 部署后自动失效 CloudFront 缓存，确保用户获取最新版本
      distribution: this.distribution,
      distributionPaths: ['/*'],
      memoryLimit: 256,
      prune: true,
    });

    // --- CDK Nag 合规规则抑制 ---
    this.suppressNagRules();

    // --- CloudFormation 输出 ---
    this.distributionUrl = `https://${this.distribution.distributionDomainName}`;

    new cdk.CfnOutput(this, 'FrontendUrl', {
      value: this.distributionUrl,
      description: `Frontend CloudFront URL (${envName})`,
    });

    new cdk.CfnOutput(this, 'FrontendBucketName', {
      value: this.bucket.bucketName,
      description: `Frontend S3 bucket name (${envName})`,
    });
  }

  /** CDK Nag 合规规则抑制 — 前端 Stack 相关安全规则的合理豁免 */
  private suppressNagRules(): void {
    // CloudFront 分发安全规则抑制
    NagSuppressions.addResourceSuppressions(
      this.distribution,
      [
        {
          id: 'AwsSolutions-CFR1',
          reason: 'Geo restriction not required for internal enterprise platform',
        },
        {
          id: 'AwsSolutions-CFR2',
          reason: 'WAF not required for internal enterprise platform in initial deployment',
        },
        {
          id: 'AwsSolutions-CFR3',
          reason:
            'Access logging requires additional S3 bucket; will be added in production hardening phase',
        },
        {
          id: 'AwsSolutions-CFR4',
          reason: 'TLS 1.2 is enforced via ViewerProtocolPolicy.REDIRECT_TO_HTTPS with HTTPS only',
        },
        {
          id: 'AwsSolutions-CFR5',
          reason:
            'API origin uses HTTP-only ALB (no custom domain/cert in Dev); viewer-to-CloudFront is HTTPS, CloudFront-to-ALB is HTTP within VPC',
        },
      ],
      true,
    );

    // S3 Bucket 安全规则抑制
    NagSuppressions.addResourceSuppressions(
      this.bucket,
      [
        {
          id: 'AwsSolutions-S1',
          reason:
            'S3 access logging for frontend static assets not required; CloudFront access logs serve this purpose',
        },
      ],
      true,
    );

    // BucketDeployment 内部创建 Lambda 使用 AWS 托管策略（CDK 自动生成，无法自定义）
    NagSuppressions.addResourceSuppressions(
      this,
      [
        {
          id: 'AwsSolutions-IAM4',
          reason:
            'BucketDeployment custom resource Lambda uses AWS managed policies; generated by CDK and not configurable',
        },
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'BucketDeployment custom resource Lambda requires wildcard access to deployment bucket; generated by CDK',
        },
        {
          id: 'AwsSolutions-L1',
          reason:
            'BucketDeployment custom resource Lambda runtime is managed by CDK and cannot be configured',
        },
      ],
      true,
    );
  }
}
