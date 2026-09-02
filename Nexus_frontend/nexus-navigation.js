/* Shared routing, page protection, and UI navigation for the static NEXUS export. */
(() => {
  const pages = {
    landing: 'nexus_landing_page_updated_hero', role: 'nexus_choose_your_role', login: 'nexus_login_desktop', studentRegistration: 'nexus_student_registration_with_verification_desktop', clientRegistration: 'nexus_client_registration_desktop', verification: 'nexus_student_verification_status_desktop_2', verificationLegacy: 'nexus_student_verification_status_desktop_1', studentDashboard: 'nexus_student_dashboard_desktop', profile: 'nexus_student_profile_setup_desktop', jobs: 'nexus_find_jobs_desktop_2', jobDetails: 'nexus_job_details_desktop', apply: 'nexus_submit_job_application_desktop_2', applications: 'nexus_my_applications_desktop_2', application: 'nexus_application_details_desktop_2', studentWorkspace: 'nexus_job_workspace_desktop_student_view', submitWork: 'nexus_submit_work_desktop_2', studentPayment: 'nexus_payment_job_completion_desktop_student_view', studentRating: 'nexus_rating_reputation_desktop_student_view', earnings: 'nexus_student_earnings_history_desktop', aiProfile: 'nexus_ai_profile_improvement_desktop', aiJobs: 'nexus_ai_job_recommendations_desktop', aiReview: 'nexus_ai_review_analysis_desktop', aiSkills: 'nexus_ai_skill_suggestions_desktop', clientDashboard: 'nexus_client_my_jobs_desktop', clientJobs: 'nexus_client_my_jobs_desktop', postJob: 'nexus_post_job_desktop', clientApplications: 'nexus_client_application_review_desktop_2', selection: 'nexus_selection_confirmation_desktop_2', clientWorkspace: 'nexus_job_workspace_desktop_client_view_dark_mode_2', clientReview: 'nexus_client_review_submitted_work_desktop_2', clientPayment: 'nexus_payment_job_completion_desktop_client_view_2', clientRating: 'nexus_rating_reputation_desktop_client_view_2', report: 'nexus_report_raise_dispute_desktop', adminDashboard: 'nexus_admin_student_verification_queue_desktop', verificationQueue: 'nexus_admin_student_verification_queue_desktop', adminReport: 'nexus_admin_review_report_desktop', adminManagement: 'nexus_admin_user_job_management_desktop'
  };
  const roles = {
    STUDENT: ['verification', 'verificationLegacy', 'studentDashboard', 'profile', 'jobs', 'jobDetails', 'apply', 'applications', 'application', 'studentWorkspace', 'submitWork', 'studentPayment', 'studentRating', 'earnings', 'aiProfile', 'aiJobs', 'aiReview', 'aiSkills', 'report'],
    CLIENT: ['clientDashboard', 'clientJobs', 'postJob', 'jobDetails', 'clientApplications', 'selection', 'clientWorkspace', 'clientReview', 'clientPayment', 'clientRating', 'report'],
    ADMIN: ['adminDashboard', 'verificationQueue', 'adminReport', 'adminManagement']
  };
  const byDirectory = Object.fromEntries(Object.entries(pages).map(([key, directory]) => [directory, key]));
  const currentDirectory = location.pathname.split('/').filter(Boolean).slice(-2, -1)[0] || '';
  const currentPage = byDirectory[currentDirectory] || 'landing';
  const allowedRoles = key => Object.entries(roles).filter(([, values]) => values.includes(key)).map(([role]) => role);
  const homeForRole = role => role === 'ADMIN' ? 'adminDashboard' : role === 'CLIENT' ? 'clientDashboard' : 'studentDashboard';
  const url = (key, params = {}) => {
    const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== '')).toString();
    return `../${pages[key] || pages.landing}/code.html${query ? `?${query}` : ''}`;
  };
  const go = (key, params) => location.assign(url(key, params));
  const isClient = () => (NexusAuth.getUser() || {}).role === 'CLIENT';

  async function guardCurrentPage() {
    const required = allowedRoles(currentPage);
    if (!required.length) return true;
    const user = await NexusAuth.restore();
    if (!user) { go('login', { next: currentPage }); return false; }
    if (!required.includes(user.role)) { go(homeForRole(user.role)); return false; }
    return true;
  }
  async function logout() { await NexusAuth.logout(); go('landing'); }
  function destination(text) {
    const t = text.toLowerCase().replace(/\s+/g, ' ').trim();
    if (/^logout$/.test(t)) return '__logout__';
    if (/^(back|cancel|arrow_back|choose your role)$/.test(t)) return 'landing';
    if (/back to find jobs/.test(t)) return 'jobs'; if (/back to applications|back to review/.test(t)) return isClient() ? 'clientApplications' : 'applications'; if (/back to workspace/.test(t)) return isClient() ? 'clientWorkspace' : 'studentWorkspace'; if (/back to profile/.test(t)) return 'profile'; if (/back to reputation/.test(t)) return 'studentRating'; if (/back to completed jobs|skip for now/.test(t)) return isClient() ? 'clientJobs' : 'earnings'; if (/save & continue|let'?s start/.test(t)) return 'studentDashboard';
    if (/^(nexus|freelanceflow|student portal)$/.test(t)) return 'landing'; if (/continue as student|i'?m a student/.test(t)) return 'studentRegistration'; if (/continue as client|i'?m a client/.test(t)) return 'clientRegistration'; if (/get started|join nexus|create an account/.test(t)) return 'role'; if (/sign in|log in|login/.test(t)) return currentPage === 'login' ? null : 'login';
    if (/create student account|submit.*verification|verify.*student/.test(t)) return 'verification'; if (/create client account/.test(t)) return 'clientDashboard'; if (/find opportunities|find jobs|explore matching jobs|search|view all/.test(t)) return 'jobs'; if (/recommended.*job|ai job|matching jobs/.test(t)) return 'aiJobs'; if (/improve profile/.test(t)) return 'aiProfile'; if (/skill suggestions|update profile skills/.test(t)) return 'aiSkills'; if (/review analysis/.test(t)) return 'aiReview'; if (/profile/.test(t)) return isClient() ? 'clientDashboard' : 'profile'; if (/earnings|withdraw funds/.test(t)) return 'earnings'; if (/dashboard/.test(t)) return homeForRole((NexusAuth.getUser() || {}).role); if (/my jobs/.test(t)) return 'clientJobs'; if (/post a job/.test(t)) return isClient() ? 'postJob' : 'clientRegistration'; if (/view applications|applications/.test(t)) return isClient() ? 'clientApplications' : 'applications'; if (/view application|application details/.test(t)) return 'application'; if (/apply now|apply for this job/.test(t)) return 'apply'; if (/view job details|view details/.test(t)) return 'jobDetails'; if (/view job/.test(t)) return isClient() ? 'clientWorkspace' : 'apply'; if (/open workspace|workspace|my work/.test(t)) return isClient() ? 'clientWorkspace' : 'studentWorkspace'; if (/submit work/.test(t)) return 'submitWork'; if (/review submitted work|review work/.test(t)) return 'clientReview'; if (/release payment.*complete job/.test(t)) return 'clientRating'; if (/approve work|release payment|complete job|payment/.test(t)) return isClient() ? 'clientPayment' : 'studentPayment'; if (/rate student|rate client|rating|reputation|leave.*review/.test(t)) return isClient() ? 'clientRating' : 'studentRating'; if (/report|raise dispute/.test(t)) return currentDirectory.startsWith('nexus_admin') ? 'adminReport' : 'report'; if (/verification/.test(t)) return 'verificationQueue'; if (/review|approve|resubmission/.test(t) && currentDirectory.startsWith('nexus_admin')) return 'adminReport'; if (/users|jobs|management/.test(t) && currentDirectory.startsWith('nexus_admin')) return 'adminManagement'; return null;
  }
  function connect(element) {
    if (element.closest('form') && element.type === 'submit') return;
    const target = destination((element.textContent || element.getAttribute('aria-label') || '').toLowerCase().replace(/\s+/g, ' ').trim());
    if (target === '__logout__') { element.addEventListener('click', event => { event.preventDefault(); logout(); }); return; }
    if (target) { if (element.tagName === 'A') element.href = url(target); element.addEventListener('click', event => { event.preventDefault(); go(target); }); }
  }
  function showLoginError(form, message) {
    let node = form.querySelector('[data-auth-error]');
    if (!node) { node = document.createElement('p'); node.dataset.authError = 'true'; node.className = 'text-sm text-red-400 text-center'; form.append(node); }
    node.textContent = message;
  }
  function connectLogin(form) {
    form.addEventListener('submit', async event => {
      event.preventDefault(); if (!form.checkValidity()) return form.reportValidity();
      const submit = form.querySelector('[type="submit"]'); submit.disabled = true; submit.setAttribute('aria-busy', 'true');
      try {
        const user = await NexusAuth.login({ email: form.querySelector('#email').value.trim(), password: form.querySelector('#password').value });
        const next = new URLSearchParams(location.search).get('next');
        go(next && allowedRoles(next).includes(user.role) ? next : homeForRole(user.role));
      } catch (error) { showLoginError(form, error.message); } finally { submit.disabled = false; submit.removeAttribute('aria-busy'); }
    });
  }
  function connectRegistration(form, role, next) {
    form.addEventListener('submit', async event => {
      event.preventDefault(); if (!form.checkValidity()) return form.reportValidity();
      const password = form.querySelector('#password').value;
      if (password !== form.querySelector('#confirmPassword').value) return showLoginError(form, 'Passwords do not match.');
      const email = form.querySelector('#email').value.trim(); const submit = form.querySelector('[type="submit"]');
      submit.disabled = true; submit.setAttribute('aria-busy', 'true');
      try { await NexusAuth.register({ username: email, email, password, name: form.querySelector('#fullName').value.trim(), role }); go(next); }
      catch (error) { showLoginError(form, error.message); } finally { submit.disabled = false; submit.removeAttribute('aria-busy'); }
    });
  }
  function connectStaticForm(form) {
    form.addEventListener('submit', event => {
      if (!form.checkValidity()) { event.preventDefault(); form.reportValidity(); return; }
      const next = currentDirectory.includes('student_registration') ? 'verification' : currentDirectory.includes('client_registration') ? 'clientDashboard' : currentDirectory.includes('submit_job_application') ? 'applications' : currentDirectory.includes('submit_work') ? 'studentWorkspace' : currentDirectory.includes('report_raise_dispute') ? (isClient() ? 'clientWorkspace' : 'studentWorkspace') : currentDirectory.includes('rating_reputation') ? (isClient() ? 'clientJobs' : 'earnings') : null;
      if (next) { event.preventDefault(); go(next); }
    });
  }
  document.addEventListener('DOMContentLoaded', async () => {
    if (!await guardCurrentPage()) return;
    const form = document.querySelector('form'); const login = currentPage === 'login' && form;
    if (login) connectLogin(login);
    else if (currentPage === 'studentRegistration' && form) connectRegistration(form, 'STUDENT', 'verification');
    else if (currentPage === 'clientRegistration' && form) connectRegistration(form, 'CLIENT', 'clientDashboard');
    else document.querySelectorAll('form').forEach(connectStaticForm);
    document.querySelectorAll('a, button, [role="button"]').forEach(connect);
  });
  window.NexusNavigation = Object.freeze({ go, url, currentPage, pages, allowedRoles, homeForRole, logout });
})();
