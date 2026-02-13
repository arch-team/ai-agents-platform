// 文档上传组件
import { useRef } from 'react';

import { Button, ErrorMessage } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';

import { useUploadDocument } from '../api/queries';

interface DocumentUploadProps {
  knowledgeBaseId: number;
}

export function DocumentUpload({ knowledgeBaseId }: DocumentUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadDocument();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

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
      {uploadMutation.isError && (
        <ErrorMessage error={extractApiError(uploadMutation.error, '上传文档失败')} />
      )}
      <p className="text-xs text-gray-500">
        支持格式: PDF、TXT、Markdown、DOCX、CSV
      </p>
    </div>
  );
}
