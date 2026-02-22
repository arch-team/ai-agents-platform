// AdminPage — 系统管理页面（SSO 配置 + 连接测试）

import { useState } from 'react';

import { Button, Card } from '@/shared/ui';
import { useSsoInit } from '@/features/auth';
import { env } from '@/shared/config/env';
import { extractApiError } from '@/shared/lib/extractApiError';

// Metadata URL 固定路径（后端提供）
const SSO_METADATA_URL = `${env.VITE_API_BASE_URL}/api/v1/auth/sso/metadata`;
// SP Entity ID 与 Metadata URL 相同
const SSO_SP_ENTITY_ID = SSO_METADATA_URL;

type TabId = 'sso';

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<TabId>('sso');
  const ssoInit = useSsoInit();

  const handleTestSso = () => {
    ssoInit.mutate({});
  };

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">系统设置</h1>

      {/* 标签页导航 */}
      <div role="tablist" aria-label="系统设置标签页" className="mb-6 border-b border-gray-200">
        <button
          role="tab"
          aria-selected={activeTab === 'sso'}
          aria-controls="tab-panel-sso"
          id="tab-sso"
          onClick={() => setActiveTab('sso')}
          className={[
            'border-b-2 px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500',
            activeTab === 'sso'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700',
          ].join(' ')}
        >
          SSO 配置
        </button>
      </div>

      {/* SSO 配置面板 */}
      <div
        role="tabpanel"
        id="tab-panel-sso"
        aria-labelledby="tab-sso"
        hidden={activeTab !== 'sso'}
      >
        <Card className="space-y-6">
          <h2 className="text-lg font-semibold text-gray-900">SAML 单点登录配置</h2>

          {/* SP 元数据信息 */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">SP Entity ID</label>
              <p className="mt-1 text-xs text-gray-500">
                在 IdP 配置中填写此值作为 Service Provider Entity ID
              </p>
              <div className="mt-2 flex items-center gap-2">
                <code className="flex-1 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-mono text-gray-900 break-all">
                  {SSO_SP_ENTITY_ID}
                </code>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">SP Metadata URL</label>
              <p className="mt-1 text-xs text-gray-500">
                IdP 可通过此 URL 自动获取 SP 元数据（XML 格式）
              </p>
              <div className="mt-2 flex items-center gap-2">
                <code className="flex-1 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-mono text-gray-900 break-all">
                  {SSO_METADATA_URL}
                </code>
                <a
                  href={SSO_METADATA_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 text-sm text-blue-600 hover:text-blue-700"
                  aria-label="在新标签页中打开 SP Metadata XML"
                >
                  查看 XML
                </a>
              </div>
            </div>
          </div>

          {/* 连接测试 */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="mb-2 text-sm font-medium text-gray-700">连接测试</h3>
            <p className="mb-3 text-xs text-gray-500">
              点击"测试 SSO 配置"将跳转至 IdP 登录页，可验证 SAML 配置是否正确
            </p>
            <Button variant="outline" onClick={handleTestSso} loading={ssoInit.isPending}>
              测试 SSO 配置
            </Button>

            {ssoInit.isError && (
              <p role="alert" className="mt-2 text-sm text-red-600">
                {extractApiError(ssoInit.error, 'SSO 配置测试失败，请检查后端 SSO 设置')}
              </p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
