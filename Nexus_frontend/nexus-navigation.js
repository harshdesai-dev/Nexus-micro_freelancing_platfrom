/* Shared local navigation for the static NEXUS Stitch export. */
(() => {
  const pages = {
    landing: 'nexus_landing_page_updated_hero', role: 'nexus_choose_your_role', login: 'nexus_login_desktop',
    studentRegistration: 'nexus_student_registration_with_verification_desktop', clientRegistration: 'nexus_client_registration_desktop',
    verification: 'nexus_student_verification_status_desktop_2', studentDashboard: 'nexus_student_dashboard_desktop',
    profile: 'nexus_student_profile_setup_desktop', jobs: 'nexus_find_jobs_desktop_2', jobDetails: 'nexus_job_details_desktop', apply: 'nexus_submit_job_application_desktop_2',
    applications: 'nexus_my_applications_desktop_2', application: 'nexus_application_details_desktop_2',
    studentWorkspace: 'nexus_job_workspace_desktop_student_view', submitWork: 'nexus_submit_work_desktop_2',
    studentPayment: 'nexus_payment_job_completion_desktop_student_view', studentRating: 'nexus_rating_reputation_desktop_student_view',
    earnings: 'nexus_student_earnings_history_desktop', aiProfile: 'nexus_ai_profile_improvement_desktop',
    aiJobs: 'nexus_ai_job_recommendations_desktop', aiReview: 'nexus_ai_review_analysis_desktop', aiSkills: 'nexus_ai_skill_suggestions_desktop',
    clientDashboard: 'nexus_client_my_jobs_desktop', clientJobs: 'nexus_client_my_jobs_desktop', postJob: 'nexus_post_job_desktop',
    clientApplications: 'nexus_client_application_review_desktop_2', selection: 'nexus_selection_confirmation_desktop_2',
    clientWorkspace: 'nexus_job_workspace_desktop_client_view_dark_mode_2', clientReview: 'nexus_client_review_submitted_work_desktop_2',
    clientPayment: 'nexus_payment_job_completion_desktop_client_view_2', clientRating: 'nexus_rating_reputation_desktop_client_view_2',
    report: 'nexus_report_raise_dispute_desktop', adminDashboard: 'nexus_admin_student_verification_queue_desktop',
    verificationQueue: 'nexus_admin_student_verification_queue_desktop', adminReport: 'nexus_admin_review_report_desktop',
    adminManagement: 'nexus_admin_user_job_management_desktop'
  };
  const current = location.pathname.split('/').slice(-2, -1)[0] || '';
  const url = key => `../${pages[key]}/code.html`;
  const go = key => { location.href = url(key); };
  const isClient = /client_|client_my_jobs|post_job|job_workspace_desktop_client|selection_confirmation|payment_job_completion_desktop_client|rating_reputation_desktop_client/.test(current);
  const back = {
    nexus_choose_your_role: 'landing', nexus_login_desktop: 'landing', nexus_student_registration_with_verification_desktop: 'role',
    nexus_client_registration_desktop: 'role', nexus_post_job_desktop: 'clientJobs', nexus_student_verification_status_desktop_1: 'studentRegistration', nexus_student_verification_status_desktop_2: 'studentRegistration',
    nexus_find_jobs_desktop_2: 'studentDashboard', nexus_job_details_desktop: 'jobs', nexus_submit_job_application_desktop_2: 'jobDetails',
    nexus_my_applications_desktop_2: 'studentDashboard', nexus_application_details_desktop_2: 'applications',
    nexus_job_workspace_desktop_student_view: 'studentDashboard', nexus_submit_work_desktop_2: 'studentWorkspace',
    nexus_client_application_review_desktop_2: 'clientJobs', nexus_selection_confirmation_desktop_2: 'clientApplications',
    nexus_job_workspace_desktop_client_view_dark_mode_2: 'clientJobs',
    nexus_client_review_submitted_work_desktop_2: 'clientWorkspace',
    nexus_payment_job_completion_desktop_client_view_2: 'clientWorkspace',
    nexus_payment_job_completion_desktop_student_view: 'studentWorkspace', nexus_rating_reputation_desktop_student_view: 'studentPayment',
    nexus_rating_reputation_desktop_client_view_2: 'clientPayment',
    nexus_admin_review_report_desktop: 'adminDashboard', nexus_admin_student_verification_queue_desktop: 'adminDashboard', nexus_admin_user_job_management_desktop: 'adminDashboard',
    nexus_report_raise_dispute_desktop: isClient ? 'clientWorkspace' : 'studentWorkspace'
  };
  function destination(text) {
    const t = text.toLowerCase().replace(/\s+/g, ' ').trim();
    if (current === 'nexus_admin_student_verification_queue_desktop' && /^(review|view|details)/.test(t)) return null;
    if (current === 'nexus_admin_user_job_management_desktop' && /^view/.test(t)) return null;
    if (/^(back|cancel|arrow_back|choose your role)$/.test(t)) return back[current] || 'landing';
    if (/back to find jobs/.test(t)) return 'jobs';
    if (/back to applications|back to review/.test(t)) return current.includes('selection_confirmation') ? 'clientApplications' : 'applications';
    if (/back to workspace/.test(t)) return isClient ? 'clientWorkspace' : 'studentWorkspace';
    if (/back to profile/.test(t)) return 'profile';
    if (/back to reputation/.test(t)) return 'studentRating';
    if (/back to completed jobs|skip for now/.test(t)) return isClient ? 'clientJobs' : 'earnings';
    if (/save & continue/.test(t)) return 'studentDashboard';
    if (/let'?s start/.test(t)) return 'studentDashboard';
    if (/^(nexus|freelanceflow|student portal)$/.test(t)) return 'landing';
    if (/continue as student|i'?m a student/.test(t)) return 'studentRegistration';
    if (/continue as client|i'?m a client/.test(t)) return 'clientRegistration';
    if (/get started|join nexus|create an account/.test(t)) return 'role';
    if (/sign in|log in|login/.test(t)) return current === pages.login ? null : 'login';
    if (/create student account|submit.*verification|verify.*student/.test(t)) return 'verification';
    if (/create client account/.test(t)) return 'clientDashboard';
    if (/find opportunities|find jobs|explore matching jobs|search|view all/.test(t)) return 'jobs';
    if (/recommended.*job|ai job|matching jobs/.test(t)) return 'aiJobs';
    if (/improve profile/.test(t)) return 'aiProfile';
    if (/skill suggestions|update profile skills/.test(t)) return 'aiSkills';
    if (/review analysis/.test(t)) return 'aiReview';
    if (/profile/.test(t)) return isClient ? 'clientDashboard' : 'profile';
    if (/earnings|withdraw funds/.test(t)) return 'earnings';
    if (/dashboard/.test(t)) return current.startsWith('nexus_admin') ? 'adminDashboard' : (isClient ? 'clientDashboard' : 'studentDashboard');
    if (/my jobs/.test(t)) return 'clientJobs';
    if (/post a job/.test(t)) return current === pages.landing || current === pages.role ? 'clientRegistration' : (isClient ? 'postJob' : 'clientJobs');
    if (/view applications|applications/.test(t)) return isClient ? 'clientApplications' : 'applications';
    if (/view application|application details/.test(t)) return 'application';
    if (/apply now/.test(t)) return 'apply';
    if (/view job details|view details/.test(t)) return 'jobDetails';
    if (/view job/.test(t)) return current.includes('find_jobs') || current.includes('ai_job') || current.includes('student_dashboard') ? 'jobDetails' : (isClient ? 'clientWorkspace' : 'apply');
    if (/apply for this job/.test(t)) return 'apply';
    if (/submit application/.test(t)) return 'applications';
    if (/confirm selection/.test(t)) return 'clientWorkspace';
    if (/select student/.test(t)) return 'selection';
    if (/open workspace|workspace|my work/.test(t)) return isClient ? 'clientWorkspace' : 'studentWorkspace';
    if (/submit work/.test(t)) return 'submitWork';
    if (/review submitted work|review work/.test(t)) return 'clientReview';
    if (/release payment.*complete job/.test(t)) return 'clientRating';
    if (/approve work|release payment|complete job|payment/.test(t)) return isClient ? 'clientPayment' : 'studentPayment';
    if (/rate student|rate client|rating|reputation|leave.*review/.test(t)) return isClient ? 'clientRating' : 'studentRating';
    if (/report|raise dispute/.test(t)) return current.startsWith('nexus_admin') ? 'adminReport' : 'report';
    if (/verification/.test(t)) return 'verificationQueue';
    if (/review|approve|resubmission/.test(t) && current.startsWith('nexus_admin')) return current === pages.adminReport ? 'adminDashboard' : 'adminReport';
    if (/users|jobs|management/.test(t) && current.startsWith('nexus_admin')) return 'adminManagement';
    if (/reports/.test(t) && current.startsWith('nexus_admin')) return 'adminReport';
    return null;
  }
  function connect(el) {
    const label = (el.textContent || el.getAttribute('aria-label') || '').toLowerCase().replace(/\s+/g, ' ').trim();
    if (current === 'nexus_admin_student_verification_queue_desktop' && /^(review|view|details)/.test(label)) {
      el.addEventListener('click', event => {
        event.preventDefault();
        const row = el.closest('tr');
        const status = row && [...row.querySelectorAll('span')].find(node => /pending review|needs resubmission|approved/.test(node.textContent.toLowerCase()));
        if (status && /^review/.test(label)) {
          const approved = window.confirm('Approve this student verification? Choose Cancel to request resubmission.');
          status.textContent = approved ? 'Approved' : 'Needs Resubmission';
        } else {
          window.alert('Verification details are available in this queue.');
        }
      });
      return;
    }
    if (current === 'nexus_admin_user_job_management_desktop' && /^view/.test(label)) {
      el.addEventListener('click', event => { event.preventDefault(); window.alert('User and job details are available in this management view.'); });
      return;
    }
    const target = destination(label);
    const href = el.getAttribute('href');
    if (target) {
      if (el.tagName === 'A') el.href = url(target);
      el.addEventListener('click', event => { event.preventDefault(); go(target); });
    } else if (el.tagName === 'A' && (!href || href === '#' || href.includes('{{DATA:SCREEN:'))) {
      el.href = url(back[current] || 'landing');
    }
  }
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('a, button, [role="button"]').forEach(connect);
    document.querySelectorAll('form').forEach(form => form.addEventListener('submit', event => {
      if (!form.checkValidity()) {
        event.preventDefault();
        form.reportValidity();
        return;
      }
      event.preventDefault();
      const email = form.querySelector('input[type="email"]');
      const next = current.includes('student_registration') ? 'verification' : current.includes('client_registration') ? 'clientDashboard' : current.includes('submit_job_application') ? 'applications' : current.includes('submit_work') ? 'studentWorkspace' : current.includes('report_raise_dispute') ? (isClient ? 'clientWorkspace' : 'studentWorkspace') : current.includes('rating_reputation') ? (isClient ? 'clientJobs' : 'earnings') : current.includes('login') ? (email && /admin/i.test(email.value) ? 'adminDashboard' : 'studentDashboard') : null;
      if (next) go(next);
    }));
  });
})();
