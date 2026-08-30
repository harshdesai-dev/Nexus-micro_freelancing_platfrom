import pg from 'pg';

if (!process.env.DATABASE_URL) throw new Error('DATABASE_URL must be set');
export const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });
export const query = (text, values) => pool.query(text, values);
