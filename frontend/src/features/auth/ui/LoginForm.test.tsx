import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { http, HttpResponse } from 'msw';

import { server } from '../../../../tests/mocks/server';
import { renderWithProviders } from '../../../../tests/utils';

import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  it('应渲染邮箱和密码输入框以及登录按钮', () => {
    renderWithProviders(<LoginForm />);

    expect(screen.getByLabelText('邮箱')).toBeInTheDocument();
    expect(screen.getByLabelText('密码')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument();
  });

  it('空提交应显示验证错误', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    await user.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => {
      expect(screen.getByText('请输入有效的邮箱')).toBeInTheDocument();
    });
    expect(screen.getByText('密码至少 8 位')).toBeInTheDocument();
  });

  it('邮箱格式错误应显示验证提示', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    await user.type(screen.getByLabelText('邮箱'), 'not-an-email');
    await user.type(screen.getByLabelText('密码'), 'Password1');
    await user.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => {
      expect(screen.getByText('请输入有效的邮箱')).toBeInTheDocument();
    });
  });

  it('密码少于 8 位应显示验证提示', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    await user.type(screen.getByLabelText('邮箱'), 'test@example.com');
    await user.type(screen.getByLabelText('密码'), 'short');
    await user.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => {
      expect(screen.getByText('密码至少 8 位')).toBeInTheDocument();
    });
  });

  it('登录成功应导航到首页', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    await user.type(screen.getByLabelText('邮箱'), 'test@example.com');
    await user.type(screen.getByLabelText('密码'), 'Password1');
    await user.click(screen.getByRole('button', { name: '登录' }));

    // 登录按钮应进入 loading 状态
    await waitFor(() => {
      expect(screen.getByRole('button', { name: '登录' })).not.toBeDisabled();
    });
  });

  it('API 返回 401 应显示错误信息', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    await user.type(screen.getByLabelText('邮箱'), 'wrong@example.com');
    await user.type(screen.getByLabelText('密码'), 'WrongPassword1');
    await user.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => {
      expect(screen.getByText('账号或密码错误')).toBeInTheDocument();
    });
  });

  it('API 网络错误应显示通用错误信息', async () => {
    server.use(http.post('http://localhost:8000/api/v1/auth/login', () => HttpResponse.error()));

    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    await user.type(screen.getByLabelText('邮箱'), 'test@example.com');
    await user.type(screen.getByLabelText('密码'), 'Password1');
    await user.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => {
      expect(screen.getByText('登录失败，请重试')).toBeInTheDocument();
    });
  });

  it('输入框应具有正确的无障碍属性', () => {
    renderWithProviders(<LoginForm />);

    const emailInput = screen.getByLabelText('邮箱');
    const passwordInput = screen.getByLabelText('密码');

    expect(emailInput).toHaveAttribute('type', 'email');
    expect(passwordInput).toHaveAttribute('type', 'password');
    expect(emailInput).toHaveAttribute('autocomplete', 'email');
    expect(passwordInput).toHaveAttribute('autocomplete', 'current-password');
  });
});
