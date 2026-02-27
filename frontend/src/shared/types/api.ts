export interface PageResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/** 日期范围查询参数（billing / insights 等模块通用） */
export interface DateRangeParams {
  start_date: string;
  end_date: string;
}
