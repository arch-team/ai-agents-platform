/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  testEnvironment: 'node',
  roots: ['<rootDir>/test', '<rootDir>/lib'],
  testMatch: ['**/*.test.ts'],
  transform: {
    '^.+\\.tsx?$': 'ts-jest',
  },
  // CDK 合成会产生异步资源（CloudFormation 模板生成），测试结束后可能未完全清理
  // 导致 "worker process has failed to exit gracefully" 警告
  forceExit: true,
  // 限制 worker 内存，防止 CDK 合成导致的内存泄漏积累
  workerIdleMemoryLimit: '512MB',
  collectCoverageFrom: [
    'lib/**/*.ts',
    'bin/**/*.ts',
    '!lib/**/*.d.ts',
    '!lib/**/index.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85,
    },
  },
};
