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
