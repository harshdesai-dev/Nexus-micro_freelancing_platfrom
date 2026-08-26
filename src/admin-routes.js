import { Router } from 'express';
import { pool, query } from './db.js';
import { casePatch, uuid, verificationPatch } from './validation.js';

const router = Router();
const parseId = (value) => uuid.safeParse(value);
const bad = (res, message) => res.status(400).json({ error: message });
const one = async (res, sql, values) => {
  const result = await query(sql, values);
  return result.rows[0] ? res.json(result.rows[0]) : res.status(404).json({ error: 'Resource not found' });
};
const many = async (res, sql, values = []) => res.json((await query(sql, values)).rows);

// Authentication remains outside this module. A trusted middleware may set req.adminId;
// for standalone use, an upstream gateway can provide x-admin-id.
router.use(async (req, res, next) => {
  const adminId = req.adminId || req.get('x-admin-id');
  if (!adminId || !parseId(adminId).success) return res.status(403).json({ error: 'Admin context is required' });
  const result = await query("SELECT id FROM users WHERE id = $1 AND role = 'ADMIN' AND account_status = 'ACTIVE'", [adminId]);
  if (!result.rowCount) return res.status(403).json({ error: 'Active administrator required' });
  req.adminId = adminId;
  next();
});

router.get('/students', (req, res, next) => many(res, `SELECT u.id,u.name,u.email,u.account_status,u.created_at,sp.college,sp.skills,sp.availability,
  (SELECT v.verification_status FROM verifications v WHERE v.student_id=u.id ORDER BY v.created_at DESC LIMIT 1) AS verification_status
  FROM users u JOIN student_profiles sp ON sp.user_id=u.id WHERE u.role='STUDENT' ORDER BY u.created_at DESC`, []).catch(next));
router.get('/students/:id', (req, res, next) => !parseId(req.params.id).success ? bad(res, 'Invalid student id') : one(res, `SELECT u.id,u.name,u.email,u.account_status,u.created_at,sp.college,sp.skills,sp.portfolio,sp.previous_work,sp.availability,sp.profile_information,
  (SELECT v.verification_status FROM verifications v WHERE v.student_id=u.id ORDER BY v.created_at DESC LIMIT 1) AS verification_status
  FROM users u JOIN student_profiles sp ON sp.user_id=u.id WHERE u.id=$1 AND u.role='STUDENT'`, [req.params.id]).catch(next));
router.get('/clients', (req, res, next) => many(res, `SELECT u.id,u.name,u.email,u.account_status,u.created_at,cp.profile_information,cp.reputation FROM users u JOIN client_profiles cp ON cp.user_id=u.id WHERE u.role='CLIENT' ORDER BY u.created_at DESC`).catch(next));
router.get('/clients/:id', (req, res, next) => !parseId(req.params.id).success ? bad(res, 'Invalid client id') : one(res, `SELECT u.id,u.name,u.email,u.account_status,u.created_at,cp.profile_information,cp.reputation FROM users u JOIN client_profiles cp ON cp.user_id=u.id WHERE u.id=$1 AND u.role='CLIENT'`, [req.params.id]).catch(next));

router.get('/verifications', (req, res, next) => many(res, `SELECT v.id,v.student_id,v.verification_status,v.admin_action,v.created_at,v.updated_at,v.reviewed_at,u.name,u.email FROM verifications v JOIN users u ON u.id=v.student_id ORDER BY v.created_at DESC`).catch(next));
router.get('/verifications/:id', (req, res, next) => !parseId(req.params.id).success ? bad(res, 'Invalid verification id') : one(res, `SELECT v.id,v.student_id,v.college_id_file_reference,v.verification_status,v.admin_action,v.created_at,v.updated_at,v.reviewed_at,u.name,u.email FROM verifications v JOIN users u ON u.id=v.student_id WHERE v.id=$1`, [req.params.id]).catch(next));
router.patch('/verifications/:id', async (req, res, next) => {
  const body = verificationPatch.safeParse(req.body); if (!parseId(req.params.id).success || !body.success) return bad(res, body.error?.issues?.[0]?.message || 'Invalid verification update');
  const client = await pool.connect();
  try { await client.query('BEGIN');
    const current = await client.query('SELECT verification_status FROM verifications WHERE id=$1 FOR UPDATE', [req.params.id]);
    if (!current.rowCount) { await client.query('ROLLBACK'); return res.status(404).json({ error: 'Resource not found' }); }
    if (current.rows[0].verification_status !== 'PENDING') { await client.query('ROLLBACK'); return bad(res, 'Only PENDING verifications can be reviewed'); }
    const updated = await client.query('UPDATE verifications SET verification_status=$1,admin_action=$2,reviewed_by=$3 WHERE id=$4 RETURNING *', [body.data.verification_status, body.data.admin_action, req.adminId, req.params.id]);
    await client.query('INSERT INTO verification_history(verification_id,previous_status,new_status,action,actor_id) VALUES($1,$2,$3,$4,$5)', [req.params.id, 'PENDING', body.data.verification_status, body.data.admin_action, req.adminId]);
    await client.query("INSERT INTO admin_action_history(actor_id,entity_type,entity_id,action) VALUES($1,'Verification',$2,$3)", [req.adminId, req.params.id, `Verification ${body.data.verification_status.toLowerCase()}`]);
    await client.query('COMMIT'); res.json(updated.rows[0]);
  } catch (error) { await client.query('ROLLBACK'); next(error); } finally { client.release(); }
});

const caseRoutes = (name, table, listSql, detailSql, includesResolution) => {
  router.get(`/${name}`, (req,res,next) => many(res, listSql).catch(next));
  router.get(`/${name}/:id`, (req,res,next) => !parseId(req.params.id).success ? bad(res, `Invalid ${name.slice(0,-1)} id`) : one(res, detailSql, [req.params.id]).catch(next));
  router.patch(`/${name}/:id`, async (req,res,next) => {
    const body=casePatch.safeParse(req.body); if (!parseId(req.params.id).success || !body.success) return bad(res, body.error?.issues?.[0]?.message || 'Invalid update');
    if (!includesResolution && body.data.resolution) return bad(res, 'Reports do not accept a resolution');
    const sets=[], values=[]; for (const key of ['status','admin_action','resolution']) if (body.data[key] !== undefined) { values.push(body.data[key]); sets.push(`${key}=$${values.length}`); }
    values.push(req.adminId, req.params.id); const client=await pool.connect();
    try { await client.query('BEGIN'); const updated=await client.query(`UPDATE ${table} SET ${sets.join(',')},reviewed_by=$${values.length-1} WHERE id=$${values.length} RETURNING *`, values);
      if (!updated.rowCount) { await client.query('ROLLBACK'); return res.status(404).json({error:'Resource not found'}); }
      await client.query("INSERT INTO admin_action_history(actor_id,entity_type,entity_id,action,details) VALUES($1,$2,$3,$4,$5)", [req.adminId, name === 'reports' ? 'Report':'Dispute', req.params.id, 'Administrative case update', JSON.stringify(body.data)]);
      await client.query('COMMIT'); res.json(updated.rows[0]);
    } catch(error) { await client.query('ROLLBACK'); next(error); } finally { client.release(); }
  });
};
caseRoutes('reports','reports',`SELECT d.*,reporter.name AS reporter_name,reported.name AS reported_user_name,j.title AS reported_job_title FROM reports d JOIN users reporter ON reporter.id=d.reporter LEFT JOIN users reported ON reported.id=d.reported_user LEFT JOIN jobs j ON j.id=d.reported_job ORDER BY d.created_at DESC`,`SELECT d.*,reporter.name AS reporter_name,reported.name AS reported_user_name,j.title AS reported_job_title FROM reports d JOIN users reporter ON reporter.id=d.reporter LEFT JOIN users reported ON reported.id=d.reported_user LEFT JOIN jobs j ON j.id=d.reported_job WHERE d.id=$1`,false);
caseRoutes('disputes','disputes',`SELECT d.*,j.title AS job_title,COALESCE(json_agg(json_build_object('id',u.id,'name',u.name)) FILTER (WHERE u.id IS NOT NULL),'[]') AS involved_users FROM disputes d JOIN jobs j ON j.id=d.job_id LEFT JOIN dispute_users du ON du.dispute_id=d.id LEFT JOIN users u ON u.id=du.user_id GROUP BY d.id,j.title ORDER BY max(d.created_at) DESC`,`SELECT d.*,j.title AS job_title,COALESCE(json_agg(json_build_object('id',u.id,'name',u.name)) FILTER (WHERE u.id IS NOT NULL),'[]') AS involved_users FROM disputes d JOIN jobs j ON j.id=d.job_id LEFT JOIN dispute_users du ON du.dispute_id=d.id LEFT JOIN users u ON u.id=du.user_id WHERE d.id=$1 GROUP BY d.id,j.title`,true);
export default router;
