// 文档上传组件
import { useRef, useState } from 'react';

import { ErrorMessage } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';
import { formatFileSize } from '@/shared/lib/formatFileSize';

import { useUploadDocument } from '../api/queries';

// 文件大小上限 10MB
const MAX_FILE_SIZE = 10 * 1024 * 1024;

// 允许的 MIME 类型白名单
const ALLOWED_MIME_TYPES = new Set([
  'application/pdf',
  'text/plain',
  'text/markdown',
  'text/csv',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
]);

// 允许的文件扩展名（用于 MIME 为空时的兜底检测）
const ALLOWED_EXTENSIONS = new Set(['.pdf', '.txt', '.md', '.docx', '.csv']);

/**
 * 校验文件是否符合上传要求
 * @returns 错误信息，无错误时返回 null
 */
function validateFile(file: File): string | null {
  // 文件大小校验
  if (file.size > MAX_FILE_SIZE) {
    return `文件大小 ${formatFileSize(file.size)} 超过限制（最大 ${formatFileSize(MAX_FILE_SIZE)}）`;
  }

  // MIME 类型校验（部分浏览器可能返回空 MIME，此时降级为扩展名检测）
  if (file.type && !ALLOWED_MIME_TYPES.has(file.type)) {
    return `不支持的文件类型: ${file.type}`;
  }

  // 扩展名兜底校验
  const extension = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
  if (!ALLOWED_EXTENSIONS.has(extension)) {
    return `不支持的文件格式: ${extension}`;
  }

  return null;
}

interface DocumentUploadProps {
  knowledgeBaseId: number;
}

export function DocumentUpload({ knowledgeBaseId }: DocumentUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadDocument();
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setValidationError(null);

    const error = validateFile(file);
    if (error) {
      setValidationError(error);
      // 清空文件输入，允许重新选择
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      return;
    }

    uploadMutation.mutate(
      { kbId: knowledgeBaseId, file },
      {
        onSuccess: () => {
          // 清空文件输入，允许重复上传同名文件
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
        },
      },
    );
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileChange}
          accept=".pdf,.txt,.md,.docx,.csv"
          className="text-sm text-gray-600 file:mr-3 file:rounded-md file:border-0 file:bg-blue-50 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-blue-700 hover:file:bg-blue-100"
          aria-label="选择文档文件"
        />
        {uploadMutation.isPending && (
          <span className="text-sm text-blue-600">上传中...</span>
        )}
        {uploadMutation.isSuccess && (
          <span className="text-sm text-green-600">上传成功</span>
        )}
      </div>
      {validationError && (
        <div role="alert" className="text-sm text-red-600">
          {validationError}
        </div>
      )}
      {uploadMutation.isError && (
        <ErrorMessage error={extractApiError(uploadMutation.error, '上传文档失败')} />
      )}
      <p className="text-xs text-gray-500">
        支持格式: PDF、TXT、Markdown、DOCX、CSV（最大 10MB）
      </p>
    </div>
  );
}
