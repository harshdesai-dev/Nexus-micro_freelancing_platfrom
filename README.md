# Database, Admin, and Trust & Safety API

This is a PostgreSQL/Express implementation containing only the requested modules. Entity names map to tables as follows: `User` → `users`, `StudentProfile` → `student_profiles`, `ClientProfile` → `client_profiles`, with the remaining entities using their plural snake-case names.

## Run

1. Copy `.env.example` to `.env` and set `DATABASE_URL` (PostgreSQL 13+).
2. Load that environment variable, run `npm install`, then `npm run migrate` and `npm test`.
3. Start with `npm start`.

The admin routes are under `/api/admin`. They expect trusted upstream identity middleware to set `req.adminId`; for standalone operation send an active ADMIN user's UUID as `x-admin-id`. This is authorization context only; authentication is deliberately not implemented.

Verification ID file references are returned only by `GET /api/admin/verifications/:id`, not the list endpoint. Verification records, case history, and administrative action history are retained; the schema uses restrictive foreign keys for those audit records.
