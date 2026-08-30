import fs from 'node:fs/promises'; import path from 'node:path'; import { pool } from '../src/db.js';
const dir = path.resolve('migrations');
await pool.query('CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())');
for (const name of (await fs.readdir(dir)).filter(x => x.endsWith('.sql')).sort()) { if (!(await pool.query('SELECT 1 FROM schema_migrations WHERE name=$1',[name])).rowCount) { await pool.query(await fs.readFile(path.join(dir,name),'utf8')); await pool.query('INSERT INTO schema_migrations(name) VALUES($1)',[name]); console.log(`Applied ${name}`); } }
await pool.end();
