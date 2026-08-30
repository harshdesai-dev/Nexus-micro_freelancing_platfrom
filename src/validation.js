import { z } from 'zod';

export const uuid = z.string().uuid();
export const verificationPatch = z.object({
  verification_status: z.enum(['VERIFIED', 'REJECTED']),
  admin_action: z.string().trim().min(1).max(2000)
}).strict();
export const casePatch = z.object({
  status: z.enum(['OPEN', 'UNDER_REVIEW', 'RESOLVED', 'DISMISSED']).optional(),
  admin_action: z.string().trim().min(1).max(4000).optional(),
  resolution: z.string().trim().min(1).max(4000).optional()
}).strict().refine(value => Object.keys(value).length > 0, 'Provide at least one field');

export const accountStatusPatch = z.object({ account_status: z.enum(['ACTIVE','SUSPENDED','DISABLED']) }).strict();
export const reportCreate = z.object({
  reported_user: z.string().uuid().optional(),
  reported_job: z.string().uuid().optional(),
  related_job: z.string().uuid().optional(),
  reason: z.string().trim().min(1).max(255),
  details: z.string().trim().min(1),
  involved_users:
 z.array(z.string().uuid()).optional()
}).strict().refine(obj => obj.reported_user || obj.reported_job || obj.related_job, { message: 'Provide at least one target (reported_user, reported_job, related_job)' });
export const disputeCreate = z.object({ job_id: z.string().uuid(), issue: z.string().trim().min(1).max(255), details: z.string().trim().min(1), involved_user_ids: z.array(z.string().uuid()).optional() }).strict();
