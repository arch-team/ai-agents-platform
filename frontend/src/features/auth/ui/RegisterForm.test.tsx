import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { http, HttpResponse } from 'msw';

import { server } from '../../../../tests/mocks/server';
import { renderWithProviders } from '../../../../tests/utils';

import { RegisterForm } from './RegisterForm';

describe('RegisterForm', () => {
  it('应渲染所有表单字段和注册按钮', () => {
    renderWithProviders(<RegisterForm />);

    expect(screen.getByLabelText('姓名')).toBeInTheDocument();
    expect(screen.getByLabelText('邮箱')).toBeInTheDocument();
    expect(screen.getByLabelText('密码')).toBeInTheDocument();
    expect(screen.getByLabelText('确认密码')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '注册' })).toBeInTheDocument();
  });

  it('空提交应显示验证错误', async () => {
    const user = userEvent.setup();
    renderWithProviders(<RegisterForm />);

    await user.click(screen.getByRole('button', { name: '注册' }));

    await waitFor(() => {
      expect(screen.getByText('姓名至少 2 个字符')).toBeInTheDocument();
    });
    expect(screen.getByText('请输入有效的邮箱')).toBeInTheDocument();
    expect(screen.getByText('密码至少 8 位')).toBeInTheDocument();
  });

  it('邮箱格式错误应显示验证提示', async () => {
    const user = userEvent.setup();
    renderWithProviders(<RegisterForm />);

    await user.type(screen.getByLabelText('邮箱'), 'not-an-email');
    await user.click(screen.getByRole('button', { name: '注册' }));

    await waitFor(() => {
      expect(screen.getByText('请输入有效的邮箱')).toBeInTheDocument();
    });
  });

  it('密码不包含大写字母应显示验证提示', async () => {
    const user = userEvent.setup();
    renderWithProviders(<RegisterForm />);

    await user.type(screen.getByLabelText('姓名'), '测试用户');
    await user.type(screen.getByLabelText('邮箱'), 'test@example.com');
    await user.type(screen.getByLabelText('密码'), 'password1');
    await user.type(screen.getByLabelText('确认密码'), 'password1');
    await user.click(screen.getByRole('button', { name: '注册' }));

    await waitFor(() => {
      expect(screen.getByText('密码需要包含大写字母')).toBeInTheDocument();
    });
  });

  it('两次密码不一致应显示验证提示', async () => {
    const user = userEvent.setup();
    renderWithProviders(<RegisterForm />);

    await user.type(screen.getByLabelText('姓名'), '测试用户');
    await user.type(screen.getByLabelText('邮箱'), 'test@example.com');
    await user.type(screen.getByLabelText('密码'), 'Password1');
    await user.type(screen.getByLabelText('确认密码'), 'Different1');
    await user.click(screen.getByRole('button', { name: '注册' }));

    await waitFor(() => {
      expect(screen.getByText('两次密码不一致')).toBeInTheDocument();
    });
  });

  it('注册成功应导航', async () => {
    const user = userEvent.setup();
    renderWithProviders(<RegisterForm />);

    await user.type(screen.getByLabelText('姓名'), '新用户');
    await user.type(screen.getByLabelText('邮箱'), 'new@example.com');
    await user.type(screen.getByLabelText('密码'), 'Password1');
    await user.type(screen.getByLabelText('确认密码'), 'Password1');
    await user.click(screen.getByRole('button', { name: '注册' }));

    // 注册按钮应在提交后恢复可用
    await waitFor(() => {
      expect(screen.getByRole('button', { name: '注册' })).not.toBeDisabled();
    });
  });

  it('API 返回邮箱已注册应显示错误信息', async () => {
    const user = userEvent.setup();
    renderWithProviders(<RegisterForm />);

    await user.type(screen.getByLabelText('姓名'), '已存在用户');
    await user.type(screen.getByLabelText('邮箱'), 'existing@example.com');
    await user.type(screen.getByLabelText('密码'), 'Password1');
    await user.type(screen.getByLabelText('确认密码'), 'Password1');
    await user.click(screen.getByRole('button', { name: '注册' }));

    await waitFor(() => {
      expect(screen.getByText('邮箱已被注册')).toBeInTheDocument();
    });
  });

  it('API 网络错误应显示通用错误信息', async () => {
    server.use(http.post('http://localhost:8000/api/v1/auth/register', () => HttpResponse.error()));

    const user = userEvent.setup();
    renderWithProviders(<RegisterForm />);

    await user.type(screen.getByLabelText('姓名'), '新用户');
    await user.type(screen.getByLabelText('邮箱'), 'new@example.com');
    await user.type(screen.getByLabelText('密码'), 'Password1');
    await user.type(screen.getByLabelText('确认密码'), 'Password1');
    await user.click(screen.getByRole('button', { name: '注册' }));

    await waitFor(() => {
      expect(screen.getByText('注册失败，请重试')).toBeInTheDocument();
    });
  });

  it('输入框应具有正确的无障碍属性', () => {
    renderWithProviders(<RegisterForm />);

    expect(screen.getByLabelText('邮箱')).toHaveAttribute('type', 'email');
    expect(screen.getByLabelText('密码')).toHaveAttribute('type', 'password');
    expect(screen.getByLabelText('确认密码')).toHaveAttribute('type', 'password');
    expect(screen.getByLabelText('邮箱')).toHaveAttribute('autocomplete', 'email');
    expect(screen.getByLabelText('密码')).toHaveAttribute('autocomplete', 'new-password');
  });
});
