// ErrorBoundary 单元测试

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { ErrorBoundary } from './ErrorBoundary';

// 抛出渲染错误的测试组件
function ThrowError({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error('测试渲染错误');
  }
  return <div>正常内容</div>;
}

describe('ErrorBoundary', () => {
  // 抑制 React 和 jsdom 的错误日志（ErrorBoundary 触发时会打印错误）
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('正常渲染子组件', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>,
    );
    expect(screen.getByText('正常内容')).toBeInTheDocument();
  });

  it('捕获渲染错误后显示默认 fallback UI', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('页面出现异常')).toBeInTheDocument();
    expect(screen.getByText('测试渲染错误')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '重试' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '返回首页' })).toBeInTheDocument();
  });

  it('点击重试按钮后重新渲染子组件', async () => {
    const user = userEvent.setup();

    // 首先 key 为 1，触发错误
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText('页面出现异常')).toBeInTheDocument();

    // 重新渲染为不抛错的组件（模拟问题已修复）
    // 先点击重试清除错误状态
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>,
    );

    await user.click(screen.getByRole('button', { name: '重试' }));
    expect(screen.getByText('正常内容')).toBeInTheDocument();
  });

  it('点击返回首页按钮导航到首页', async () => {
    const user = userEvent.setup();

    // mock window.location.href
    const hrefSetter = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { href: '/' },
      writable: true,
    });
    Object.defineProperty(window.location, 'href', {
      set: hrefSetter,
      get: () => '/',
    });

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    await user.click(screen.getByRole('button', { name: '返回首页' }));
    expect(hrefSetter).toHaveBeenCalledWith('/');
  });

  it('使用自定义 fallback UI', () => {
    render(
      <ErrorBoundary fallback={<div>自定义错误页面</div>}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText('自定义错误页面')).toBeInTheDocument();
    expect(screen.queryByText('页面出现异常')).not.toBeInTheDocument();
  });
});
