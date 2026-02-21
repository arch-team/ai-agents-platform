// Evaluation 模块 TypeScript 类型定义

import type { PageResponse } from '@/shared/types';

// -- 测试集 --

export type TestSuiteStatus = 'draft' | 'active' | 'archived';

export interface TestSuite {
  id: number;
  name: string;
  description: string;
  agent_id: number;
  status: TestSuiteStatus;
  owner_id: number;
  created_at: string;
  updated_at: string;
}

export type TestSuiteListResponse = PageResponse<TestSuite>;

export interface CreateTestSuiteRequest {
  name: string;
  description?: string;
  agent_id: number;
}

export interface UpdateTestSuiteRequest {
  name?: string;
  description?: string;
}

// -- 测试用例 --

export interface TestCase {
  id: number;
  suite_id: number;
  input_prompt: string;
  expected_output: string;
  evaluation_criteria: string;
  order_index: number;
  created_at: string;
  updated_at: string;
}

export type TestCaseListResponse = PageResponse<TestCase>;

export interface CreateTestCaseRequest {
  input_prompt: string;
  expected_output?: string;
  evaluation_criteria?: string;
  order_index?: number;
}

export interface UpdateTestCaseRequest {
  input_prompt?: string;
  expected_output?: string;
  evaluation_criteria?: string;
  order_index?: number;
}

// -- 评估运行 --

export type EvaluationRunStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface EvaluationRun {
  id: number;
  suite_id: number;
  agent_id: number;
  user_id: number;
  status: EvaluationRunStatus;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  score: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export type EvaluationRunListResponse = PageResponse<EvaluationRun>;

export interface CreateEvaluationRunRequest {
  suite_id: number;
}

// -- 评估结果 --

export interface EvaluationResult {
  id: number;
  run_id: number;
  case_id: number;
  actual_output: string;
  score: number;
  passed: boolean;
  error_message: string;
  created_at: string;
  updated_at: string;
}

export type EvaluationResultListResponse = PageResponse<EvaluationResult>;

// -- 筛选参数 --

export interface TestSuiteFilters {
  page?: number;
  page_size?: number;
}

export interface EvaluationRunFilters {
  suite_id?: number;
  page?: number;
  page_size?: number;
}

// -- Pipeline --

export type PipelineStatus = 'scheduled' | 'running' | 'completed' | 'failed';

export interface EvalPipeline {
  id: number;
  suite_id: number;
  agent_id: number;
  trigger: string;
  model_ids: string[];
  status: PipelineStatus;
  bedrock_job_id: string | null;
  score_summary: Record<string, number>;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface TriggerPipelineRequest {
  model_ids?: string[];
}
