// SSO 企业登录按钮组件

import { Button } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';

import { useSsoInit } from '../api/ssoQueries';

export function SsoLoginButton() {
  const ssoInit = useSsoInit();

  const handleClick = () => {
    ssoInit.mutate({});
  };

  return (
    <div>
      <Button
        variant="outline"
        className="w-full"
        onClick={handleClick}
        loading={ssoInit.isPending}
        aria-label="通过企业 SSO 登录"
      >
        企业 SSO 登录
      </Button>

      {/* SSO 初始化失败时显示错误信息 */}
      {ssoInit.isError && (
        <p role="alert" className="mt-2 text-center text-sm text-red-600">
          {extractApiError(ssoInit.error, 'SSO 登录失败，请稍后重试')}
        </p>
      )}
    </div>
  );
}
