// Reporting content and the admin moderation queue.
import type { ReportInput, ReportResponse } from '../../types/community';
import { request } from './client';

/**
 * Report content
 */
export async function reportContent(input: ReportInput): Promise<ReportResponse> {
  return request<ReportResponse>('/reports', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export interface Report {
  id: string;
  reporter_id: string;
  reported_user_id?: string;
  post_id?: string;
  comment_id?: string;
  reason: string;
  description?: string;
  status: 'pending' | 'resolved' | 'dismissed';
  created_at: string;
  reviewed_at?: string;
  reviewed_by?: string;
  admin_notes?: string;
  action_taken?: string;
  reporter?: { id: string; username: string; avatar_url?: string };
  reported_user?: { id: string; username: string; avatar_url?: string };
  post?: { id: string; content: string; user_id: string };
  comment?: { id: string; content: string; user_id: string };
}

export interface ReportsResponse {
  success: boolean;
  reports: Report[];
  count: number;
  error?: string;
}

export interface ModerationStats {
  reports: {
    pending: number;
    resolved: number;
    dismissed: number;
    total: number;
  };
  users: {
    total: number;
    banned: number;
  };
  posts: {
    total: number;
  };
}

export interface ModerationStatsResponse {
  success: boolean;
  stats: ModerationStats;
  error?: string;
}

export interface ActionResponse {
  success: boolean;
  message?: string;
  error?: string;
}

/**
 * Get all reports (admin only)
 */
export async function getReports(status: string = 'pending', limit?: number): Promise<ReportsResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set('status', status);
  if (limit) searchParams.set('limit', limit.toString());
  return request<ReportsResponse>(`/admin/reports?${searchParams.toString()}`);
}

/**
 * Take action on a report (admin only)
 */
export async function handleReport(
  reportId: string,
  action: 'dismiss' | 'delete_content' | 'warn_user' | 'ban_user',
  notes?: string
): Promise<ActionResponse> {
  return request<ActionResponse>(`/admin/reports/${reportId}/action`, {
    method: 'POST',
    body: JSON.stringify({ action, notes }),
  });
}

/**
 * Get moderation statistics (admin only)
 */
export async function getModerationStats(): Promise<ModerationStatsResponse> {
  return request<ModerationStatsResponse>('/admin/stats');
}
