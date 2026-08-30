import { Router } from 'express';
import { query } from './db.js';
import { requireAuth } from './auth.js';
import { reportCreate, disputeCreate } from './validation.js';

const router = Router();

router.post('/reports', requireAuth, async (req,res,next) => {
  const body = reportCreate.safeParse(req.body); if (!body.success) return res.status(400).json({ error: body.error.issues[0].message });
  try {
    const result = await query(`INSERT INTO reports(reporter,reported_user,reported_job,related_job,reason,details) VALUES($1,$2,$3,$4,$5,$6) RETURNING *`, [req.userId, body.data.reported_user || null, body.data.reported_job || null, body.data.related_job || null, body.data.reason, body.data.details]);
    return res.status(201).json(result.rows[0]);
  } catch (e) { next(e); }
});

router.post('/disputes', requireAuth, async (req,res,next) => {
  const body = disputeCreate.safeParse(req.body); if (!body.success) return res.status(400).json({ error: body.error.issues[0].message });
  const client = await query(`INSERT INTO disputes(job_id,raised_by,issue,details) VALUES($1,$2,$3,$4) RETURNING *`, [body.data.job_id, req.userId, body.data.issue, body.data.details]);
  const dispute = client.rows[0];
  if (body.data.involved_user_ids && body.data.involved_user_ids.length) {
    const inserts = body.data.involved_user_ids.map(id => query('INSERT INTO dispute_users(dispute_id,user_id) VALUES($1,$2)', [dispute.id, id]));
    await Promise.all(inserts);
  }
  res.status(201).json(dispute);
});

export default router;
