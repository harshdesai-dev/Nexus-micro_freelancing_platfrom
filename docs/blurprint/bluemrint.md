Master Technical Specification
Student Micro-Freelancing Platform
1. Product Definition
The product is a student-first micro-freelancing marketplace connecting verified 
students with people and organizations that need small paid tasks completed.
The platform has three user types:
1. Student / Freelancer
2. Client / Job Provider
3. Admin
A student can also act as a job provider, meaning the same user account can 
participate on both sides of the marketplace.
The platform is intended to become a real deployed revenue-generating product, 
not merely a college demonstration.
2. Core Product Objective
The platform solves two connected problems.
Student problem
Students may have useful skills but lack:
paid opportunities
practical experience
clients
portfolio-building work
a trusted place to find small jobs
Client problem
Students, college clubs, committees, and businesses may need small tasks 
completed but may not know which student is capable and trustworthy.
Platform solution
The platform creates a trusted workflow:
Skill → Job Opportunity → Match → Application → Selection → 
Communication → Work → Payment → Rating → Portfolio/Experience
This is the central business loop of the product.
3. User Types
3.1 Student / Freelancer
A student can:
register
upload college ID
become verified after admin approval
create a profile
add skills
add portfolio items
add previous work
set availability
browse/search jobs
receive AI job recommendations
apply for jobs
communicate after selection
submit work
receive payment
receive ratings
receive AI-based skill suggestions
improve profile using AI
A student can also create/post jobs as a client/job provider.
3.2 Client / Job Provider
A client can:
register
create a profile
post jobs
describe requirements
specify required skills
specify budget
specify deadline
upload reference files
search/browse jobs where applicable
receive suitable student recommendations
review applications
select a student
communicate through the job
review submitted work
make payment through the platform
rate the student
report problems
participate in dispute resolution
Clients can include:
students
college clubs
committees
local businesses
eventually startups
3.3 Admin
Admin responsibilities:
manage students
manage clients
verify students
manage reports
manage disputes
Admin is the platform's trust and control layer.
4. Core Features
The following features are part of the required product scope.
Student-side functionality
1. Student registration
2. College verification
3. Student profile
4. Portfolio
5. Skills
6. Availability
7. Job search
8. AI job recommendations
9. Applications
10. Communication
11. Work submission
12. Payment
13. Ratings
14. Reporting
15. Disputes
16. AI profile improvement
17. AI skill suggestions
Client-side functionality
1. Client registration
2. Client profile
3. Job posting
4. Required skills
5. Budget
6. Deadline
7. Reference files
8. AI-based student matching
9. Application review
10. Student selection
11. Communication
12. Work review
13. Payment
14. Ratings
15. Reporting
16. Disputes
Platform functionality
1. Admin
2. Verification
3. Trust & Safety
4. AI matching
5. AI recommendations
6. AI profile improvement
7. AI review analysis
8. AI skill suggestions
9. Real payment processing
No additional product features should be introduced into the core implementation 
without team approval.
5. Core Marketplace Workflow
This is the most important system workflow.
Step 1 — Registration
User creates an account.
The system identifies the account/user role.
A student account contains student-specific information.
A client account contains client-specific information.
Because students can also post jobs, the platform must support a student acting as a 
job provider without requiring a completely separate identity.
Step 2 — Student Verification
Student uploads:
College ID
Admin reviews the submitted information.
Possible status:
Pending → Verified / Rejected
Only the verification result should determine whether the student's verified status is 
displayed.
Step 3 — Student Profile
Verified student creates/maintains:
profile information
skills
portfolio
previous work
availability
This profile becomes the basis for:
job recommendations
student matching
portfolio presentation
reputation/rating
6. Job Posting Workflow
A job provider creates a job containing:
title
description
required skills
budget
deadline
reference files
The job becomes available for students to discover.
A job may originate from:
another student
club
committee
business
future startup client
7. Job Search
Students can discover jobs through the platform.
The job information shown should allow a student to understand:
what work is required
required skills
budget
deadline
relevant reference material
Search is a discovery mechanism.
AI recommendation is a separate intelligent recommendation mechanism.
8. AI Matching
AI matching connects:
Job requirements ↔ Student profile
Relevant information includes:
required skills
student skills
portfolio/work relevance
job requirements
availability where applicable
The system should produce a compatibility/recommendation result.
Conceptual flow:
Job
↓
Required Skills + Requirements
↓
AI Matching
↓
Suitable Students
↓
Recommended Candidates
For the reverse side:
Student Profile
↓
Skills + Preferences/Profile
↓
AI Matching
↓
Suitable Jobs
↓
Recommended Jobs
AI matching should assist the marketplace; it should not replace the client/student's 
final decision.
9. Application Workflow
Student chooses a job and applies.
The application belongs to the specific job.
The client reviews applications.
Important business rule
The client does not use a reject-selection workflow.
The intended flow is:
Student applies → Client selects student
Once a student is selected, that student becomes the selected worker for the job.
10. Communication Workflow
Communication begins after the student is selected.
Communication happens inside the job context using:
Messages/comments inside the job
The purpose is to:
understand exact requirements
clarify expectations
discuss references
discuss delivery details
coordinate completion
This communication is part of the job's activity history.
11. Work Submission
After communication and understanding the requirements:
Student completes the work → submits the work through the platform.
The submitted work belongs to the specific job.
The client can review the submitted result.
The work-submission stage occurs before final payment completion.
12. Payment Workflow
Payment is real, not simulated.
The core business flow is:
Job selected
↓
Student performs work
↓
Student submits work
↓
Client reviews work
↓
Payment is completed through platform
↓
Platform records transaction
↓
Student receives applicable amount
↓
Platform retains commission
Example business rule:
Job value = ₹500
Platform commission = 10%
Student amount = ₹450
Platform revenue = ₹50
The exact production payment implementation must preserve this business behavior.
13. Ratings
After the job is completed/payment stage is completed:
Both sides can rate each other.
This creates marketplace reputation.
Student reputation can become part of their professional profile/portfolio.
Client reputation can help future students judge opportunities.
Ratings also provide data that can later be analyzed by the AI review-analysis 
system.
14. Reporting
Users can report problems related to jobs/users/interactions.
A report should contain enough information for admin to understand:
who reported
what is being reported
which job is involved
reason/details
relevant status/history
Admin reviews and handles reports.
15. Disputes
A dispute exists when both sides have a disagreement regarding a job or transaction.
Conceptual flow:
Issue occurs
↓
User raises dispute
↓
Dispute linked to job
↓
Admin reviews
↓
Admin resolves/acts
↓
Resolution recorded
The dispute system should remain tied to the specific job and its history.
16. Admin Module
Admin must be able to manage:
Students
view students
view verification status
manage student records
Clients
view/manage client records
Verification
review college ID submissions
approve/reject verification
Reports
review reports
take administrative action
record status
Disputes
view disputes
review related job/user information
resolve/manage disputes
The admin panel is the operational control center for the platform.
17. AI Features
The product requires five AI capabilities.
17.1 AI Matching
Matches suitable students with jobs.
17.2 AI Job Recommendations
Recommends relevant jobs to students.
17.3 AI Profile Improvement
Student provides profile/resume information.
AI suggests improved presentation/content.
The purpose is to help students present their skills more effectively.
17.4 AI Review Analysis
AI analyzes ratings/reviews to identify useful patterns and feedback.
17.5 AI Skill Suggestions
AI analyzes the student's profile/work context and suggests relevant skills that could 
improve future opportunities.
AI principle
AI should produce useful assistance inside the existing marketplace workflow 
rather than becoming a separate standalone product.
18. Data Domains
The system needs to maintain information around the following major domains.
Users
identity
role
account state
Student Profile
student information
college
verification status
skills
availability
portfolio
previous work
ratings
Client Profile
identity/profile information
jobs posted
ratings
Verification
student ID submission
verification status
admin action
verification history
Jobs
title
description
required skills
budget
deadline
reference files
job provider
selected student
job state
Applications
job
student
application information
application state
Communication
job
sender
message/comment
timestamp
Work Submission
job
student
submitted work
submission state
submission information
Payments
job
payer
recipient
amount
platform commission
transaction state
Ratings
job
reviewer
reviewed user
rating
review content
Reports
reporter
reported user/job
reason
status
Disputes
job
involved users
issue/details
admin handling
resolution/status
These are business entities, not yet technology-specific database decisions.
19. Job State
The job lifecycle should be explicitly defined so every module uses the same 
understanding.
Conceptually:
Posted
↓
Applications
↓
Student Selected
↓
Communication / Requirement Discussion
↓
Work in Progress
↓
Work Submitted
↓
Payment
↓
Completed
↓
Ratings
The exact internal state names can be finalized during implementation, but all team 
members must follow the same lifecycle.
20. System Module Ownership
Harsh
Team Lead + System/Backend Architecture
Responsible for:
overall architecture
module coordination
API/interface definitions
integration
system consistency
technical decisions
final integration
Raviraj
Frontend/UI
Responsible for:
student interface
client interface
job interface
profile/interface screens
application screens
communication UI
work submission UI
ratings UI
admin UI where applicable
Arati
Backend + Authentication
Responsible for:
authentication
user management
role handling
core business APIs
job/application workflow
profile-related APIs
communication backend
work-submission backend
Adinath
Database + Admin + Trust & Safety
Responsible for:
business data structure
verification
reports
disputes
admin operations
data consistency
trust/safety records
Dhanashri
AI/ML + Matching/Recommendations
Responsible for:
AI matching
job recommendations
profile improvement
review analysis
skill suggestions
AI-side logic and evaluation
real payment flow
payment-related integration
connecting AI functionality with the application
end-to-end testing
integration testing
regression testing
identifying failures and edge cases
Siya
Payments + AI Integration + QA
Responsible for:
21. How the Modules Connect
The high-level system relationship is:
                 USERS
                   ↓
              Frontend/UI
                   ↓
              Backend/API
          ┌────────┼────────┐
          ↓        ↓        ↓
      Database     AI      Payments
          ↑        ↑        ↑
          └──── Admin / Trust ────┘
More specifically:
Frontend
   ↓
Backend
   ↓
Database
Backend
   ↓
AI Matching / Recommendation
   ↓
UI generation
backend generation
API generation
database code
authentication
payment integration code
AI integration
validation
testing
debugging
documentation
Backend
   ↓
Frontend
Backend
   ↓
Payment System
This establishes the key rule that every module participates in one connected 
product.
22. AI-Assisted Development Model
Because the team has a 10-day development window and will heavily use AI, 
development should follow:
Human defines requirement → AI generates implementation → Run → Test → 
AI fixes → Review → Integrate
AI can be heavily used for:
However:
AI-generated code is not automatically considered correct.
Each module owner is responsible for verifying that the generated implementation 
follows this specification.
23. Cross-Team Contract
Before implementation, all members must use the same definitions for:
user roles
job lifecycle
application lifecycle
payment lifecycle
verification status
database entities
API inputs/outputs
AI request/response
error behavior
The purpose is to prevent six independently generated systems from becoming 
incompatible.
24. Product Scope Rule
The team must follow this rule:
Build the defined marketplace, not a generic freelancing platform.
The required product is specifically:
Verified students + small paid jobs + AI matching/recommendations + 
communication + work delivery + real payment + ratings + trust/admin.
No unnecessary feature should be introduced simply because an AI tool suggests it.
Likewise, none of the required features listed in this specification should be silently 
removed.
25. Production Requirements
Because this is intended as a real-world product, the system should be treated as an 
actual product from the beginning.
The implementation should therefore account for:
authentication/security
user permissions
data validation
payment correctness
protection of user information
reliable job state transitions
safe handling of uploaded files
error handling
admin control
logging/auditing where necessary
AI failure handling
API failure handling
payment failure handling
The first release can be simple, but it must be structured around the real business 
workflow.
26. Ten-Day Development Priority
The highest priority is not individual features. It is the complete working 
marketplace flow.
Priority 1 — Core marketplace
Registration
→ Verification
→ Profile
→ Job posting
→ Job discovery
→ Application
→ Selection
→ Communication
→ Work submission
→ Payment
→ Rating
Priority 2 — Trust & administration
Verification
Reports
Disputes
Admin
Priority 3 — AI
Matching
Job recommendations
Profile improvement
Review analysis
Skill suggestions
Priority 4 — Full integration and testing
Frontend
↕
Backend
↕
Database
↕
AI
↕
Payment
The goal is to get the entire core workflow working end-to-end, rather than having 
many isolated unfinished features.
27. Acceptance Criteria
The product should be considered functionally successful when a realistic scenario 
can be completed:
Example
A student registers.
↓
Student uploads college ID.
↓
Admin verifies student.
↓
Student completes profile with skills and portfolio.
↓
A job provider creates a ₹500 reel-editing job.
↓
The job becomes discoverable.
↓
AI identifies suitable students.
↓
Student applies.
↓
Client selects the student.
↓
Student and client communicate inside the job.
↓
Student completes and submits the work.
↓
Client reviews the submission.
↓
Payment of ₹500 is processed through the platform.
↓
Platform records its commission.
↓
Student receives the applicable payment.
↓
Both sides rate each other.
↓
The student's rating/work contributes to their professional profile.
If this flow works reliably, the fundamental product works.
28. Final Product Definition
One-line definition
A verified student-first micro-freelancing marketplace where students can earn 
from small paid jobs and clients can find suitable student talent, supported by 
AI matching, recommendations, real payments, communication, ratings, and 
trust/safety mechanisms.
Core loop
Student Skills → Job → AI Match → Application → Selection → Communication 
→ Work → Payment → Rating → Experience/Portfolio
Product principle
Keep the marketplace simple, trusted, student-focused, and centered on 
completing real small paid jobs.
29. Technical Integration Contract
This section defines the common technical rules that must be followed by all team 
members during development and integration. The purpose is to ensure that all 
modules remain compatible and that frontend, backend, database, AI, payment, and 
admin systems use the same technical definitions.
29.1 Shared API Contract
All backend APIs must use a common structure and naming convention.
Base API path:
/api
Authentication:
Authorization: Bearer <token>
Success response format:
{
"success": true,
"data": {},
"message": "Operation successful"
}
Error response format:
{
}
"success": false,
"error": {
"code": "ERROR_CODE",
"message": "Human-readable error message"
}
Core API endpoints:
Authentication
POST /api/auth/register
POST /api/auth/login
User
GET /api/users/me
Verification
POST /api/verification
Profile
GET /api/profiles/me
PATCH /api/profiles/me
Jobs
POST /api/jobs
GET /api/jobs
GET /api/jobs/:id
Applications
POST /api/jobs/:id/applications
GET /api/jobs/:id/applications
Selection
POST /api/jobs/:id/select
Communication
POST /api/jobs/:id/messages
GET /api/jobs/:id/messages
Work Submission
POST /api/jobs/:id/submissions
Payment
POST /api/jobs/:id/payment
Ratings
POST /api/jobs/:id/ratings
The backend is the central integration layer.
Frontend
↓
Backend API
├── Database
├── AI Service
└── Payment System
The frontend must not directly access the database or external AI/payment providers.
29.2 Common Database Entities
The following business entities are shared across the system:
User
StudentProfile
ClientProfile
Verification
Job
Application
Message
Submission
Payment
Rating
Report
Dispute
All team members must use the same entity names and definitions across frontend, 
backend, database, AI, and testing.
29.3 Lifecycle and Status Names
All modules must follow the same lifecycle definitions.
Job lifecycle:
POSTED
↓
APPLICATIONS
↓
STUDENT_SELECTED
↓
IN_PROGRESS
↓
WORK_SUBMITTED
↓
PAYMENT
↓
COMPLETED
↓
RATED
Verification status:
PENDING
VERIFIED
REJECTED
Application status:
APPLIED
SELECTED
The client selects a student for the job. The system does not require a separate 
reject-selection workflow.
The same lifecycle and status names must be used consistently across the database, 
backend, frontend, AI logic, and testing.
29.4 Authentication and Authorization Rules
The platform supports three user types:
STUDENT
CLIENT
ADMIN
A student can also act as a job provider and create jobs using the same account.
Student permissions:- Manage own profile- Browse and search jobs- Apply for jobs- Communicate within selected jobs- Submit completed work- Receive applicable payment- Rate users
- Report problems- Raise disputes
Client permissions:- Manage own profile- Create and manage jobs- Review applications- Select a student- Communicate within selected jobs- Review submitted work- Make payment- Rate users- Report problems- Raise disputes
Admin permissions:- Manage students- Manage clients- Review student verification- Approve or reject verification- Review reports- Manage disputes- Take administrative actions- Maintain administrative records
Every protected API request must verify:
1. Authentication
2. User identity
3. User role
4. Resource ownership or permission
29.5 Payment Rules
Payment is a real platform transaction and must not be treated as a simulated 
transaction.
Payment flow:
Student completes work
↓
Student submits work
↓
Client reviews submission
↓
Payment is initiated
↓
Payment gateway processes payment
↓
Backend verifies payment result
↓
Transaction is recorded
↓
Platform commission is calculated
↓
Applicable student amount is recorded
↓
Job is completed
Example business rule:
Job value = ₹500
Platform commission = 10%
Platform revenue = ₹50
Student amount = ₹450
The backend must verify the payment result before recording the transaction as 
successful.
A payment failure must not mark the job as completed.
29.6 Error Handling Rules
All modules must use the common API error response format.
The system must handle at least the following error categories:
Authentication failure
Authorization failure
Invalid input
Missing resource
Validation failure
Database failure
AI failure
API or integration failure
Payment failure
File upload failure
Example:
{
}
"success": false,
"error": {
"code": "PAYMENT_FAILED",
"message": "Payment could not be completed"
}
AI failure must not break the core marketplace workflow.
Payment failure must not mark the job as completed.
Important system failures should be logged for debugging, monitoring, and 
administrative review where necessary.
29.7 Cross-Team Integration Rule
All team members must follow this technical contract when implementing their 
modules.
No team member should independently change the following shared definitions:- API endpoint names- API request and response structure- Database entity names
- Lifecycle and status names- Authentication rules- Authorization rules- Payment rules- Error response format
Any required change to these shared definitions must be discussed and agreed upon 
by the team before integration.
The purpose of this contract is to ensure that all independently developed modules 
can be integrated into one consistent product.
Important project record
Project type: Real-world revenue product
Users: Student/Freelancer + Client/Job Provider + Admin
Students can also post jobs: Yes
Verification: College ID upload + Admin verification
Payment: Real
Communication: Messages/comments inside the job
AI: Real API-based functionality
Deployment: Real deployment
College dependency: None
Provided deadline: 3 September