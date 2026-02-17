import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

import { DateRangePicker } from './DateRangePicker';

describe('DateRangePicker', () => {
  const defaultProps = {
    startDate: '2025-01-01',
    endDate: '2025-01-31',
    onStartDateChange: vi.fn(),
    onEndDateChange: vi.fn(),
  };

  it('应渲染预设按钮', () => {
    render(<DateRangePicker {...defaultProps} />);

    expect(screen.getByText('最近 7 天')).toBeInTheDocument();
    expect(screen.getByText('最近 14 天')).toBeInTheDocument();
    expect(screen.getByText('最近 30 天')).toBeInTheDocument();
    expect(screen.getByText('最近 90 天')).toBeInTheDocument();
  });

  it('应渲染自定义日期输入', () => {
    render(<DateRangePicker {...defaultProps} />);

    expect(screen.getByLabelText('从')).toBeInTheDocument();
    expect(screen.getByLabelText('至')).toBeInTheDocument();
    expect(screen.getByLabelText('从')).toHaveValue('2025-01-01');
    expect(screen.getByLabelText('至')).toHaveValue('2025-01-31');
  });

  it('点击预设按钮应调用日期变更回调', async () => {
    const user = userEvent.setup();
    const handleStartChange = vi.fn();
    const handleEndChange = vi.fn();

    render(
      <DateRangePicker
        {...defaultProps}
        onStartDateChange={handleStartChange}
        onEndDateChange={handleEndChange}
      />,
    );

    await user.click(screen.getByText('最近 7 天'));

    expect(handleStartChange).toHaveBeenCalled();
    expect(handleEndChange).toHaveBeenCalled();
  });

  it('手动修改开始日期应调用 onStartDateChange', async () => {
    const user = userEvent.setup();
    const handleStartChange = vi.fn();

    render(
      <DateRangePicker {...defaultProps} onStartDateChange={handleStartChange} />,
    );

    const startInput = screen.getByLabelText('从');
    await user.clear(startInput);
    await user.type(startInput, '2025-02-01');

    expect(handleStartChange).toHaveBeenCalled();
  });

  it('手动修改结束日期应调用 onEndDateChange', async () => {
    const user = userEvent.setup();
    const handleEndChange = vi.fn();

    render(
      <DateRangePicker {...defaultProps} onEndDateChange={handleEndChange} />,
    );

    const endInput = screen.getByLabelText('至');
    await user.clear(endInput);
    await user.type(endInput, '2025-02-28');

    expect(handleEndChange).toHaveBeenCalled();
  });
});
