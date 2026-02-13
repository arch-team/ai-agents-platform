// UI 组件
export { KnowledgeList } from './ui/KnowledgeList';
export { KnowledgeDetail } from './ui/KnowledgeDetail';
export { KnowledgeCreateDialog } from './ui/KnowledgeCreateDialog';
export { KnowledgeStatusBadge } from './ui/KnowledgeStatusBadge';
export { DocumentUpload } from './ui/DocumentUpload';

// Hooks
export {
  useKnowledgeBases,
  useKnowledgeBase,
  useKnowledgeDocuments,
  useCreateKnowledgeBase,
  useUpdateKnowledgeBase,
  useDeleteKnowledgeBase,
  useUploadDocument,
  useDeleteDocument,
  useSyncKnowledgeBase,
  useQueryKnowledgeBase,
} from './api/queries';

// 类型
export type {
  KnowledgeBase,
  KnowledgeBaseStatus,
  KnowledgeDocument,
  KnowledgeBaseFilters,
  CreateKnowledgeBaseRequest,
  UpdateKnowledgeBaseRequest,
} from './api/types';
