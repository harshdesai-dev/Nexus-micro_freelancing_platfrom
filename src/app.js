import express from 'express';
import adminRoutes from './admin-routes.js';
import publicRoutes from './public-routes.js';
const app = express(); app.use(express.json({ limit: '100kb' })); app.use('/api', publicRoutes); app.use('/api/admin', adminRoutes);
app.use((error, req, res, next) => { console.error(error); res.status(error.code === '23505' ? 409 : 500).json({ error: error.code === '23503' ? 'Related resource does not exist' : 'Database operation failed' }); });
export default app;
