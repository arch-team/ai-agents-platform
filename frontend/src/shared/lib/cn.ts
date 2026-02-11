import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

// twMerge 确保 Tailwind 冲突类正确覆盖（如 className="px-4" + "px-2" → "px-2"）
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
