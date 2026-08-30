BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE user_role AS ENUM ('STUDENT', 'CLIENT', 'ADMIN');
CREATE TYPE account_status AS ENUM ('ACTIVE', 'SUSPENDED', 'DISABLED');
CREATE TYPE verification_status AS ENUM ('PENDING', 'VERIFIED', 'REJECTED');
CREATE TYPE job_state AS ENUM ('POSTED', 'APPLICATIONS', 'STUDENT_SELECTED', 'IN_PROGRESS', 'WORK_SUBMITTED', 'PAYMENT', 'COMPLETED', 'RATED');
CREATE TYPE application_status AS ENUM ('APPLIED', 'SELECTED');
CREATE TYPE submission_status AS ENUM ('SUBMITTED', 'ACCEPTED', 'REJECTED');
CREATE TYPE transaction_state AS ENUM ('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED');
CREATE TYPE case_status AS ENUM ('OPEN', 'UNDER_REVIEW', 'RESOLVED', 'DISMISSED');

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name VARCHAR(255) NOT NULL,
  email VARCHAR(320) NOT NULL UNIQUE, password_hash TEXT NOT NULL,
  role user_role NOT NULL, account_status account_status NOT NULL DEFAULT 'ACTIVE',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE student_profiles (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  college TEXT, skills JSONB NOT NULL DEFAULT '[]', portfolio TEXT, previous_work TEXT,
  availability TEXT, profile_information JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE client_profiles (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  profile_information JSONB NOT NULL DEFAULT '{}', reputation NUMERIC(3,2) NOT NULL DEFAULT 0 CHECK (reputation BETWEEN 0 AND 5),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE verifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), student_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  college_id_file_reference TEXT NOT NULL, verification_status verification_status NOT NULL DEFAULT 'PENDING',
  admin_action TEXT, reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), reviewed_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX one_pending_verification_per_student ON verifications(student_id) WHERE verification_status = 'PENDING';
CREATE TABLE verification_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), verification_id UUID NOT NULL REFERENCES verifications(id) ON DELETE RESTRICT,
  previous_status verification_status, new_status verification_status NOT NULL, action TEXT NOT NULL,
  actor_id UUID REFERENCES users(id) ON DELETE SET NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), title VARCHAR(255) NOT NULL, description TEXT NOT NULL,
  required_skills JSONB NOT NULL DEFAULT '[]', budget NUMERIC(12,2) NOT NULL CHECK (budget >= 0), deadline TIMESTAMPTZ,
  reference_files JSONB NOT NULL DEFAULT '[]', job_provider UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  selected_student UUID REFERENCES users(id) ON DELETE SET NULL, job_state job_state NOT NULL DEFAULT 'POSTED',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE applications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  student_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT, application_information JSONB NOT NULL DEFAULT '{}',
  application_status application_status NOT NULL DEFAULT 'APPLIED', created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(job_id, student_id)
);
CREATE UNIQUE INDEX one_selected_application_per_job ON applications(job_id) WHERE application_status = 'SELECTED';
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  sender UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT, message TEXT NOT NULL CHECK (length(trim(message)) > 0), timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE submissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  student_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT, submitted_work JSONB NOT NULL DEFAULT '[]',
  submission_information JSONB NOT NULL DEFAULT '{}', submission_status submission_status NOT NULL DEFAULT 'SUBMITTED',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE RESTRICT,
  payer UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT, recipient UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0), platform_commission NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (platform_commission >= 0 AND platform_commission <= amount),
  transaction_state transaction_state NOT NULL DEFAULT 'PENDING', transaction_reference TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), CHECK (payer <> recipient)
);
CREATE TABLE ratings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  reviewer UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT, reviewed_user UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5), review_content TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(job_id, reviewer, reviewed_user), CHECK (reviewer <> reviewed_user)
);
CREATE TABLE reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), reporter UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  reported_user UUID REFERENCES users(id) ON DELETE RESTRICT, reported_job UUID REFERENCES jobs(id) ON DELETE RESTRICT,
  related_job UUID REFERENCES jobs(id) ON DELETE RESTRICT, reason VARCHAR(255) NOT NULL, details TEXT NOT NULL,
  status case_status NOT NULL DEFAULT 'OPEN', admin_action TEXT, reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), CHECK (reported_user IS NOT NULL OR reported_job IS NOT NULL OR related_job IS NOT NULL)
);
CREATE TABLE disputes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE RESTRICT,
  raised_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT, issue VARCHAR(255) NOT NULL, details TEXT NOT NULL,
  admin_handling TEXT, resolution TEXT, status case_status NOT NULL DEFAULT 'OPEN', reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE dispute_users (dispute_id UUID NOT NULL REFERENCES disputes(id) ON DELETE RESTRICT, user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT, PRIMARY KEY(dispute_id, user_id));
CREATE TABLE admin_action_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
  entity_type VARCHAR(32) NOT NULL, entity_id UUID NOT NULL, action TEXT NOT NULL, details JSONB NOT NULL DEFAULT '{}', created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX jobs_provider_idx ON jobs(job_provider); CREATE INDEX applications_student_idx ON applications(student_id);
CREATE INDEX messages_job_idx ON messages(job_id); CREATE INDEX submissions_job_idx ON submissions(job_id);
CREATE INDEX reports_status_idx ON reports(status); CREATE INDEX disputes_status_idx ON disputes(status);
CREATE INDEX verifications_status_idx ON verifications(verification_status); CREATE INDEX admin_action_history_entity_idx ON admin_action_history(entity_type, entity_id);

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN NEW.updated_at = now(); RETURN NEW; END; $$;
CREATE OR REPLACE FUNCTION enforce_verification_transition() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF OLD.verification_status <> 'PENDING' THEN RAISE EXCEPTION 'verification status is final'; END IF;
 IF NEW.verification_status NOT IN ('VERIFIED', 'REJECTED') THEN RAISE EXCEPTION 'invalid verification status transition'; END IF;
 IF NEW.reviewed_by IS NULL THEN RAISE EXCEPTION 'verification requires an admin reviewer'; END IF;
 NEW.reviewed_at = now(); RETURN NEW;
END; $$;
CREATE OR REPLACE FUNCTION enforce_expected_role() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE expected user_role; actual user_role;
BEGIN
 expected := TG_ARGV[0]::user_role;
 EXECUTE format('SELECT role FROM users WHERE id = $1') INTO actual USING NEW.user_id;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION '% profile requires a % user', TG_TABLE_NAME, expected; END IF;
 RETURN NEW;
END; $$;
CREATE OR REPLACE FUNCTION enforce_student_references() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE actual user_role;
BEGIN
 EXECUTE format('SELECT role FROM users WHERE id = $1') INTO actual USING NEW.student_id;
 IF actual IS DISTINCT FROM 'STUDENT' THEN RAISE EXCEPTION '% requires a STUDENT reference', TG_TABLE_NAME; END IF;
 RETURN NEW;
END; $$;
CREATE OR REPLACE FUNCTION enforce_selected_student() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE actual user_role;
BEGIN
 IF NEW.selected_student IS NULL THEN RETURN NEW; END IF;
 SELECT role INTO actual FROM users WHERE id = NEW.selected_student;
 IF actual IS DISTINCT FROM 'STUDENT' THEN RAISE EXCEPTION 'selected_student must be a STUDENT'; END IF;
 RETURN NEW;
END; $$;
CREATE OR REPLACE FUNCTION record_initial_verification() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN INSERT INTO verification_history(verification_id,new_status,action) VALUES(NEW.id,NEW.verification_status,'Verification submitted'); RETURN NEW; END; $$;
CREATE TRIGGER verification_transition BEFORE UPDATE OF verification_status ON verifications FOR EACH ROW WHEN (OLD.verification_status IS DISTINCT FROM NEW.verification_status) EXECUTE FUNCTION enforce_verification_transition();
CREATE TRIGGER student_profile_role BEFORE INSERT OR UPDATE OF user_id ON student_profiles FOR EACH ROW EXECUTE FUNCTION enforce_expected_role('STUDENT');
CREATE TRIGGER client_profile_role BEFORE INSERT OR UPDATE OF user_id ON client_profiles FOR EACH ROW EXECUTE FUNCTION enforce_expected_role('CLIENT');
CREATE TRIGGER verification_student_role BEFORE INSERT OR UPDATE OF student_id ON verifications FOR EACH ROW EXECUTE FUNCTION enforce_student_references();
CREATE TRIGGER application_student_role BEFORE INSERT OR UPDATE OF student_id ON applications FOR EACH ROW EXECUTE FUNCTION enforce_student_references();
CREATE TRIGGER submission_student_role BEFORE INSERT OR UPDATE OF student_id ON submissions FOR EACH ROW EXECUTE FUNCTION enforce_student_references();
CREATE TRIGGER selected_student_role BEFORE INSERT OR UPDATE OF selected_student ON jobs FOR EACH ROW EXECUTE FUNCTION enforce_selected_student();
CREATE TRIGGER verification_initial_history AFTER INSERT ON verifications FOR EACH ROW EXECUTE FUNCTION record_initial_verification();
CREATE TRIGGER users_updated BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER student_profiles_updated BEFORE UPDATE ON student_profiles FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER client_profiles_updated BEFORE UPDATE ON client_profiles FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER verifications_updated BEFORE UPDATE ON verifications FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER jobs_updated BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER applications_updated BEFORE UPDATE ON applications FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER submissions_updated BEFORE UPDATE ON submissions FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER payments_updated BEFORE UPDATE ON payments FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER ratings_updated BEFORE UPDATE ON ratings FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER reports_updated BEFORE UPDATE ON reports FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER disputes_updated BEFORE UPDATE ON disputes FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMIT;
