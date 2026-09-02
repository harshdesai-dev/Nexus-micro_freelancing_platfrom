/* Data-backed client marketplace views for NEXUS client screens. */
(() => {
  const page = () => window.NexusNavigation && NexusNavigation.currentPage;
  const escape = value => String(value ?? '').replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
  const money = value => `₹${Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
  const date = value => value ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value)) : 'No deadline';
  const uuid = value => /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value || '');
  const state = (container, text, error = false) => {
    if (!container) return;
    container.innerHTML = `<div class="bg-surface border ${error ? 'border-error text-error' : 'border-border text-text-secondary'} rounded-lg p-6 text-center font-body-md">${escape(text)}</div>`;
  };
  const skills = values => (Array.isArray(values) ? values : []).map(skill => `<span class="bg-primary/10 text-primary border border-primary/20 px-2 py-1 rounded text-label-md">${escape(skill)}</span>`).join('') || '<span class="text-text-secondary text-label-md">No skills listed</span>';

  /* ==========================================================================
     1. CLIENT DASHBOARD & MY JOBS (nexus_client_my_jobs_desktop)
     ========================================================================== */
  function jobCard(job) {
    const isOpen = job.job_state === 'POSTED' || job.job_state === 'APPLICATIONS';
    const isInProgress = ['STUDENT_SELECTED', 'IN_PROGRESS', 'WORK_SUBMITTED'].includes(job.job_state);
    const isCompleted = ['COMPLETED', 'PAYMENT', 'RATED'].includes(job.job_state);
    const statusLabel = isOpen ? 'Open' : isInProgress ? 'In Progress' : isCompleted ? 'Completed' : job.job_state;
    const appCount = Number(job.applications_count || 0);

    return `
      <div class="bg-surface border border-border rounded-xl p-6 flex flex-col md:flex-row gap-6 justify-between items-start md:items-center group hover:border-primary/50 transition-colors relative overflow-hidden">
        <div class="absolute left-0 top-0 bottom-0 w-1 ${isOpen ? 'bg-primary' : isInProgress ? 'bg-yellow-500' : 'bg-surface-variant'}"></div>
        <div class="flex flex-col gap-3 flex-1 pl-2">
          <div class="flex items-center gap-3 flex-wrap">
            <span class="${isOpen ? 'bg-primary/10 text-primary border-primary/20' : 'bg-surface-container text-text-secondary border-border'} border px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider">${escape(statusLabel)}</span>
            <h3 class="font-headline-md text-headline-md text-text-primary">${escape(job.title)}</h3>
          </div>
          <div class="flex flex-wrap items-center gap-x-6 gap-y-2 font-body-md text-body-md text-text-secondary">
            <div class="flex items-center gap-1.5"><span class="material-symbols-outlined text-[16px]">group</span> ${appCount} Applicant${appCount === 1 ? '' : 's'}</div>
            <div class="flex items-center gap-1.5"><span class="material-symbols-outlined text-[16px]">payments</span> Budget: ${money(job.budget)}</div>
            <div class="flex items-center gap-1.5"><span class="material-symbols-outlined text-[16px]">event</span> Deadline: ${escape(date(job.deadline))}</div>
          </div>
          <div class="flex flex-wrap gap-2 mt-1">${skills(job.required_skills)}</div>
        </div>
        <div class="flex flex-row md:flex-col gap-3 w-full md:w-auto mt-4 md:mt-0">
          <a class="flex-1 md:flex-none border border-border text-text-primary bg-background hover:bg-surface-variant font-body-md text-body-md px-4 py-2 rounded-lg transition-colors text-center inline-flex items-center justify-center gap-1" href="${NexusNavigation.url('jobDetails', { job_id: job.id })}">View Job</a>
          <a class="flex-1 md:flex-none border border-primary text-primary bg-primary/5 hover:bg-primary/10 font-body-md text-body-md px-4 py-2 rounded-lg transition-colors text-center inline-flex items-center justify-center gap-1 font-semibold" href="${NexusNavigation.url('clientApplications', { job_id: job.id })}">View Applications (${appCount})</a>
        </div>
      </div>
    `;
  }

  async function loadMyJobs() {
    const list = document.querySelector('.flex.flex-col.gap-4');
    if (list) state(list, 'Loading your posted jobs…');
    try {
      const response = await NexusApi.get('/api/jobs/mine');
      const allJobs = response.jobs || [];

      // Summary counts
      const allCount = allJobs.length;
      const openCount = allJobs.filter(j => j.job_state === 'POSTED' || j.job_state === 'APPLICATIONS').length;
      const progressCount = allJobs.filter(j => ['STUDENT_SELECTED', 'IN_PROGRESS', 'WORK_SUBMITTED'].includes(j.job_state)).length;
      const completedCount = allJobs.filter(j => ['COMPLETED', 'PAYMENT', 'RATED'].includes(j.job_state)).length;

      const countCards = document.querySelectorAll('.grid.grid-cols-2.md\\:grid-cols-4 span.font-headline-lg-mobile');
      if (countCards.length >= 4) {
        countCards[0].textContent = allCount;
        countCards[1].textContent = openCount;
        countCards[2].textContent = progressCount;
        countCards[3].textContent = completedCount;
      }

      let currentQuery = '';
      let currentFilter = 'all';

      function renderJobs() {
        if (!list) return;
        let filtered = allJobs;
        if (currentFilter === 'open') filtered = filtered.filter(j => j.job_state === 'POSTED' || j.job_state === 'APPLICATIONS');
        else if (currentFilter === 'progress') filtered = filtered.filter(j => ['STUDENT_SELECTED', 'IN_PROGRESS', 'WORK_SUBMITTED'].includes(j.job_state));
        else if (currentFilter === 'completed') filtered = filtered.filter(j => ['COMPLETED', 'PAYMENT', 'RATED'].includes(j.job_state));

        if (currentQuery) {
          filtered = filtered.filter(j => {
            const titleMatch = (j.title || '').toLowerCase().includes(currentQuery);
            const descMatch = (j.description || '').toLowerCase().includes(currentQuery);
            const skillMatch = Array.isArray(j.required_skills) && j.required_skills.some(s => String(s).toLowerCase().includes(currentQuery));
            return titleMatch || descMatch || skillMatch;
          });
        }

        list.innerHTML = filtered.map(jobCard).join('') || `<div class="bg-surface border border-border rounded-xl p-8 text-center"><p class="text-text-secondary font-body-md">${currentQuery || currentFilter !== 'all' ? 'No jobs match your search/filter.' : 'You have not posted any jobs yet.'}</p><a class="mt-4 inline-flex items-center gap-2 bg-primary text-background font-label-md px-4 py-2 rounded-lg font-semibold hover:bg-surface-tint transition-colors" href="${NexusNavigation.url('postJob')}"><span class="material-symbols-outlined text-sm">add</span> Post Your First Job</a></div>`;
      }

      renderJobs();

      const searchInput = document.querySelector('input[placeholder*="Search jobs"]');
      if (searchInput) {
        searchInput.addEventListener('input', () => {
          currentQuery = searchInput.value.trim().toLowerCase();
          renderJobs();
        });
      }

      const selectFilter = document.querySelector('select');
      if (selectFilter) {
        selectFilter.addEventListener('change', () => {
          currentFilter = selectFilter.value;
          renderJobs();
        });
      }
    } catch (error) {
      if (list) state(list, error.message, true);
    }
  }

  /* ==========================================================================
     2. POST A JOB (nexus_post_job_desktop)
     ========================================================================== */
  function setupPostJob() {
    const form = document.getElementById('post-job-form');
    const panel = document.getElementById('post-form-panel');
    const result = document.getElementById('result-panel');
    if (!form || !panel || !result) return;

    const title = document.getElementById('job-title');
    const description = document.getElementById('job-description');
    const budget = document.getElementById('budget');
    const deadline = document.getElementById('deadline');
    const chips = [...document.querySelectorAll('.skill-chip')];
    const submitBtn = form.querySelector('button[type="submit"]');

    const formatDate = value => value ? new Intl.DateTimeFormat('en-IN', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value + 'T00:00:00')) : 'Not set';
    const selectedSkills = () => chips.filter(chip => chip.getAttribute('aria-pressed') === 'true').map(chip => chip.dataset.skill);

    const syncPreview = () => {
      const pTitle = document.getElementById('preview-title');
      const pDesc = document.getElementById('preview-description');
      const pBudget = document.getElementById('preview-budget');
      const pDeadline = document.getElementById('preview-deadline');
      const pSkills = document.getElementById('preview-skills');
      if (pTitle) pTitle.textContent = title.value || 'Untitled job';
      if (pDesc) pDesc.textContent = description.value || 'No description added yet.';
      if (pBudget) pBudget.textContent = budget.value ? `₹${budget.value}` : 'Not set';
      if (pDeadline) pDeadline.textContent = formatDate(deadline.value);
      if (pSkills) {
        pSkills.innerHTML = selectedSkills().map(skill => `<span class="bg-primary/10 text-primary border border-primary/20 px-2 py-1 rounded-full text-label-md">${escape(skill)}</span>`).join('') || '<span class="text-text-secondary text-label-md">No skills selected</span>';
      }
    };

    const showError = (name, invalid) => {
      const el = document.querySelector(`[data-error="${name}"]`);
      if (el) el.classList.toggle('hidden', !invalid);
    };

    chips.forEach(chip => chip.addEventListener('click', () => {
      const active = chip.getAttribute('aria-pressed') === 'true';
      chip.setAttribute('aria-pressed', String(!active));
      chip.classList.toggle('bg-primary/10', !active);
      chip.classList.toggle('border-primary', !active);
      chip.classList.toggle('text-primary', !active);
      chip.classList.toggle('bg-surface-container', active);
      chip.classList.toggle('border-border', active);
      chip.classList.toggle('text-text-primary', active);
      syncPreview();
    }));

    [title, description, budget, deadline].forEach(input => {
      if (input) input.addEventListener('input', syncPreview);
    });

    syncPreview();

    form.addEventListener('submit', async event => {
      event.preventDefault();
      const currentSkills = selectedSkills();
      const invalid = {
        title: !title.value.trim(),
        description: !description.value.trim(),
        skills: currentSkills.length === 0,
        budget: !budget.value || Number(budget.value) <= 0,
        deadline: !deadline.value
      };
      Object.entries(invalid).forEach(([name, val]) => showError(name, val));
      if (Object.values(invalid).some(Boolean)) return;

      submitBtn.disabled = true;
      submitBtn.textContent = 'Posting Job…';

      try {
        const payload = {
          title: title.value.trim(),
          description: description.value.trim(),
          required_skills: currentSkills,
          budget: String(budget.value),
          deadline: deadline.value ? `${deadline.value}T23:59:59Z` : null
        };
        const res = await NexusApi.post('/api/jobs', payload);
        const createdJob = res.job;

        panel.classList.add('hidden');
        result.classList.remove('hidden');
        document.getElementById('result-title').textContent = 'Job Posted ✓';
        document.getElementById('result-message').textContent = 'Your job has been posted and is now available for student applications.';
        document.getElementById('result-job').textContent = createdJob.title;
        document.getElementById('result-budget').textContent = money(createdJob.budget);
        document.getElementById('result-deadline').textContent = formatDate(deadline.value);
        document.getElementById('result-status').textContent = 'Open';

        const viewJobsBtn = result.querySelector('a');
        if (viewJobsBtn) viewJobsBtn.href = NexusNavigation.url('clientJobs');

        window.scrollTo({ top: 0, behavior: 'smooth' });
      } catch (error) {
        alert(error.message);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Post Job';
      }
    });

    const postAnother = document.getElementById('post-another');
    if (postAnother) {
      postAnother.addEventListener('click', () => {
        form.reset();
        chips.forEach(chip => {
          chip.setAttribute('aria-pressed', 'false');
          chip.className = 'skill-chip bg-surface-container border border-border text-text-primary px-3 py-2 rounded-full text-label-md hover:border-primary transition-colors';
        });
        panel.classList.remove('hidden');
        result.classList.add('hidden');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Post Job';
        syncPreview();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }
  }

  /* ==========================================================================
     3. CLIENT APPLICATION REVIEW (nexus_client_application_review_desktop_2)
     ========================================================================== */
  function applicantCard(app, job) {
    const student = app.student || {};
    const profile = app.student_profile || {};
    const isSelected = app.status === 'SELECTED';
    const studentName = student.name || student.username || 'Student Applicant';
    const education = [profile.course, profile.year_of_study].filter(Boolean).join(', ') || 'Student Freelancer';
    const appSkills = (app.application_information && app.application_information.skills) || profile.skills || job.required_skills || [];

    return `
      <article class="bg-surface border ${isSelected ? 'border-primary' : 'border-border'} rounded-lg p-6 relative overflow-hidden group hover:border-primary/50 transition-colors duration-300">
        ${isSelected ? '<div class="absolute top-0 right-0 bg-primary/20 border-b border-l border-primary/40 px-4 py-1.5 rounded-bl-lg text-primary text-label-md font-bold uppercase tracking-wider">Selected Student</div>' : ''}
        <div class="flex items-start gap-4 mb-4">
          <div class="w-14 h-14 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-headline-md font-bold text-lg">
            ${escape(studentName.substring(0, 2).toUpperCase())}
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h3 class="text-headline-md font-headline-md text-text-primary">${escape(studentName)}</h3>
              <span class="material-symbols-outlined text-primary text-[18px]" style="font-variation-settings: 'FILL' 1;" title="Verified Student">verified</span>
            </div>
            <p class="text-text-secondary text-body-md font-body-md">${escape(education)}</p>
            <div class="flex items-center gap-3 mt-1 text-text-secondary text-label-md">
              <span>Applied: ${escape(date(app.created_at))}</span>
              ${app.expected_completion ? `<span>• Expected: ${escape(date(app.expected_completion))}</span>` : ''}
            </div>
          </div>
        </div>
        <div class="space-y-4">
          <div>
            <p class="text-text-secondary text-label-md font-label-md mb-2">Skills</p>
            <div class="flex flex-wrap gap-2">${skills(appSkills)}</div>
          </div>
          <div class="bg-surface-container-high rounded p-4 border border-border">
            <p class="text-text-secondary font-label-md uppercase mb-1">Cover Letter & Application Message</p>
            <p class="text-on-surface text-body-md font-body-md whitespace-pre-wrap">${escape(app.application_message || 'No application cover letter provided.')}</p>
          </div>
        </div>
        <div class="mt-6 flex justify-end gap-3">
          ${isSelected ? `
            <span class="px-6 py-2 bg-primary/20 text-primary border border-primary/30 text-label-md font-bold rounded inline-block">Selected</span>
          ` : `
            <a class="px-6 py-2 bg-primary text-background text-label-md font-label-md rounded font-bold hover:bg-surface-tint transition-colors shadow-[0_0_15px_rgba(78,222,163,0.3)] inline-block" href="${NexusNavigation.url('selection', { job_id: job.id, application_id: app.id })}">Select Student</a>
          `}
        </div>
      </article>
    `;
  }

  async function loadClientApplications() {
    const jobId = new URLSearchParams(location.search).get('job_id');
    const main = document.querySelector('main');
    if (!uuid(jobId)) return state(main, 'A valid job ID is required to review applications.', true);

    state(main, 'Loading applications…');
    try {
      const res = await NexusApi.get(`/api/jobs/${jobId}/applications`);
      const allApps = res.applications || [];
      const job = res.job || {};

      main.innerHTML = `
        <div class="flex-grow w-full px-margin-desktop max-w-max-width mx-auto py-8">
          <nav aria-label="Breadcrumb" class="flex items-center gap-2 text-text-secondary text-body-md font-body-md mb-6">
            <a class="hover:text-primary transition-colors" href="${NexusNavigation.url('clientJobs')}">My Jobs</a>
            <span class="material-symbols-outlined text-[16px]">chevron_right</span>
            <span class="text-on-surface">Applications (${allApps.length})</span>
          </nav>
          <div class="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 mb-8">
            <div>
              <h1 class="text-headline-lg font-headline-lg text-text-primary mb-2">Review Applications</h1>
              <p class="text-body-lg font-body-lg text-text-secondary">Review student applications for "${escape(job.title)}" and select the best student.</p>
            </div>
            <a class="border border-border text-text-primary px-4 py-2 rounded-lg font-label-md hover:border-primary inline-flex items-center gap-2" href="${NexusNavigation.url('clientJobs')}">
              <span class="material-symbols-outlined text-sm">arrow_back</span> Back to My Jobs
            </a>
          </div>
          <div class="bento-grid">
            <div class="flex flex-col gap-6 order-2 lg:order-1" id="applicant-list-container">
            </div>
            <div class="order-1 lg:order-2">
              <div class="bg-surface border border-border rounded-lg p-6 sticky top-24 shadow-lg shadow-black/50">
                <h2 class="text-label-md font-label-md text-text-secondary uppercase tracking-wider mb-4 border-b border-border pb-2">Job Context</h2>
                <h3 class="text-headline-md font-headline-md text-text-primary mb-2">${escape(job.title)}</h3>
                <div class="grid grid-cols-2 gap-4 my-6">
                  <div class="bg-background rounded p-3 border border-border/50">
                    <span class="material-symbols-outlined text-primary mb-1 text-[20px]">payments</span>
                    <p class="text-label-md font-label-md text-text-secondary">Budget</p>
                    <p class="text-body-lg font-body-lg text-text-primary font-semibold">${money(job.budget)}</p>
                  </div>
                  <div class="bg-background rounded p-3 border border-border/50">
                    <span class="material-symbols-outlined text-primary mb-1 text-[20px]">schedule</span>
                    <p class="text-label-md font-label-md text-text-secondary">Deadline</p>
                    <p class="text-body-lg font-body-lg text-text-primary font-semibold">${escape(date(job.deadline))}</p>
                  </div>
                </div>
                <div class="mb-4">
                  <p class="text-label-md font-label-md text-text-secondary mb-2">Required Skills</p>
                  <div class="flex flex-wrap gap-2">${skills(job.required_skills)}</div>
                </div>
                <div class="flex items-center justify-between border-t border-border pt-4 mt-6">
                  <span class="text-body-md font-body-md text-text-secondary">Total Applicants</span>
                  <span class="bg-primary/10 text-primary px-3 py-1 rounded-full text-label-md font-label-md font-bold">${allApps.length}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;

      const listContainer = document.getElementById('applicant-list-container');
      if (allApps.length === 0) {
        listContainer.innerHTML = `<div class="bg-surface border border-border rounded-lg p-8 text-center"><p class="text-text-secondary font-body-md">No student applications received yet for this job.</p></div>`;
      } else {
        listContainer.innerHTML = allApps.map(a => applicantCard(a, job)).join('');
      }
    } catch (error) {
      state(main, error.status === 404 ? 'Job not found.' : error.message, true);
    }
  }

  /* ==========================================================================
     4. SELECTION CONFIRMATION (nexus_selection_confirmation_desktop_2)
     ========================================================================== */
  async function loadSelectionConfirmation() {
    const params = new URLSearchParams(location.search);
    const jobId = params.get('job_id');
    const appId = params.get('application_id');
    const main = document.querySelector('main');

    if (!uuid(jobId) || !uuid(appId)) {
      return state(main, 'A valid job ID and application ID are required to confirm student selection.', true);
    }

    state(main, 'Loading candidate selection details…');
    try {
      const res = await NexusApi.get(`/api/jobs/${jobId}/applications`);
      const allApps = res.applications || [];
      const job = res.job || {};
      const targetApp = allApps.find(a => a.id === appId);

      if (!targetApp) {
        return state(main, 'The specified application was not found for this job.', true);
      }

      const student = targetApp.student || {};
      const profile = targetApp.student_profile || {};
      const studentName = student.name || student.username || 'Student Applicant';
      const education = [profile.course, profile.year_of_study].filter(Boolean).join(' · ') || 'Student Freelancer';
      const studentSkills = (targetApp.application_information && targetApp.application_information.skills) || profile.skills || job.required_skills || [];

      main.innerHTML = `
        <div class="max-w-[720px] w-full flex flex-col gap-6 py-8">
          <div>
            <nav class="flex items-center text-text-secondary font-label-md text-label-md mb-4 gap-2">
              <a class="hover:text-primary transition-colors" href="${NexusNavigation.url('clientJobs')}">My Jobs</a>
              <span class="material-symbols-outlined text-[16px]">chevron_right</span>
              <a class="hover:text-primary transition-colors" href="${NexusNavigation.url('clientApplications', { job_id: job.id })}">Applications</a>
              <span class="material-symbols-outlined text-[16px]">chevron_right</span>
              <span class="text-text-primary">Select Student</span>
            </nav>
            <h1 class="font-headline-lg text-headline-lg mb-2">Confirm Student Selection</h1>
            <p class="font-body-lg text-body-lg text-text-secondary">Review the details below before confirming your selection.</p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-surface border border-border p-6 rounded-lg flex flex-col gap-4 relative overflow-hidden">
              <div class="flex items-start gap-4">
                <div class="w-14 h-14 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-headline-md font-bold text-lg">
                  ${escape(studentName.substring(0, 2).toUpperCase())}
                </div>
                <div>
                  <h3 class="font-headline-md text-headline-md text-text-primary">${escape(studentName)}</h3>
                  <p class="font-label-md text-label-md text-text-secondary mt-1">${escape(education)}</p>
                  <div class="flex items-center gap-1 mt-2 text-primary font-label-md text-label-md">
                    <span class="material-symbols-outlined text-[16px]">verified</span> Verified Student
                  </div>
                </div>
              </div>
              <div class="flex flex-col gap-2 mt-2">
                <div class="flex flex-wrap gap-2">${skills(studentSkills)}</div>
              </div>
            </div>

            <div class="bg-surface border border-border p-6 rounded-lg flex flex-col justify-between">
              <div>
                <h3 class="font-label-md text-label-md text-text-secondary uppercase tracking-wider mb-2">Job Summary</h3>
                <h4 class="font-headline-md text-headline-md text-text-primary mb-4">${escape(job.title)}</h4>
                <div class="grid grid-cols-2 gap-y-4 font-body-md text-body-md text-text-secondary">
                  <div><span class="block text-text-primary font-medium mb-1">Budget</span> ${money(job.budget)}</div>
                  <div><span class="block text-text-primary font-medium mb-1">Deadline</span> ${escape(date(job.deadline))}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="bg-surface-container border border-primary/30 p-6 rounded-lg flex flex-col gap-6">
            <div>
              <h3 class="font-headline-md text-headline-md text-primary mb-2 flex items-center gap-2">
                <span class="material-symbols-outlined">info</span>
                You are about to select ${escape(studentName)}
              </h3>
              <p class="font-body-md text-body-md text-text-secondary">Selecting this student will assign them to the project and move the job into the active work stage.</p>
            </div>
            <label class="flex items-center gap-3 cursor-pointer group">
              <input class="w-5 h-5 rounded bg-surface border-border text-primary focus:ring-primary transition-colors cursor-pointer" id="confirm-checkbox" type="checkbox"/>
              <span class="font-body-md text-body-md text-text-primary group-hover:text-primary transition-colors">I confirm that I want to select this student for this job.</span>
            </label>
            <p id="selection-error" class="hidden text-error font-body-md"></p>
            <div class="flex flex-col sm:flex-row gap-4 mt-2">
              <button class="bg-primary text-background font-label-md text-label-md py-3 px-6 rounded-lg hover:bg-surface-tint transition-colors font-semibold flex items-center justify-center gap-2 flex-1 sm:order-2 opacity-50 cursor-not-allowed" disabled id="confirm-btn">
                Confirm Selection
                <span class="material-symbols-outlined text-[18px]">arrow_forward</span>
              </button>
              <a class="bg-transparent border border-border text-text-primary font-label-md text-label-md py-3 px-6 rounded-lg hover:bg-surface-container-high transition-colors font-semibold flex items-center justify-center flex-1 sm:order-1 text-center" href="${NexusNavigation.url('clientApplications', { job_id: job.id })}">
                Back to Review
              </a>
            </div>
          </div>
        </div>
      `;

      const checkbox = document.getElementById('confirm-checkbox');
      const confirmBtn = document.getElementById('confirm-btn');
      const errorMsg = document.getElementById('selection-error');

      checkbox.addEventListener('change', () => {
        if (checkbox.checked) {
          confirmBtn.classList.remove('opacity-50', 'cursor-not-allowed');
          confirmBtn.removeAttribute('disabled');
        } else {
          confirmBtn.classList.add('opacity-50', 'cursor-not-allowed');
          confirmBtn.setAttribute('disabled', 'true');
        }
      });

      confirmBtn.addEventListener('click', async () => {
        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Confirming Selection…';
        try {
          await NexusApi.post(`/api/jobs/${job.id}/select`, { application_id: targetApp.id });
          main.innerHTML = `
            <div class="max-w-md mx-auto py-12 text-center bg-surface border border-border rounded-xl p-8 space-y-4">
              <div class="w-16 h-16 rounded-full bg-primary/20 text-primary flex items-center justify-center mx-auto">
                <span class="material-symbols-outlined text-4xl">check_circle</span>
              </div>
              <h2 class="font-headline-lg text-text-primary">Student Selected!</h2>
              <p class="text-text-secondary font-body-md">${escape(studentName)} has been assigned to "${escape(job.title)}".</p>
              <div class="pt-4">
                <a class="bg-primary text-background font-label-md px-6 py-3 rounded-lg font-bold inline-block hover:bg-surface-tint" href="${NexusNavigation.url('clientJobs')}">Return to My Jobs</a>
              </div>
            </div>
          `;
        } catch (error) {
          errorMsg.textContent = error.message;
          errorMsg.classList.remove('hidden');
          confirmBtn.disabled = false;
          confirmBtn.textContent = 'Confirm Selection';
        }
      });
    } catch (error) {
      state(main, error.message, true);
    }
  }

  /* ==========================================================================
     5. JOB DETAILS FOR CLIENT (nexus_job_details_desktop)
     ========================================================================== */
  async function loadJobDetailsForClient() {
    const jobId = new URLSearchParams(location.search).get('job_id');
    const root = document.querySelector('main');
    if (!uuid(jobId)) return state(root, 'A valid job ID is required to view this job.', true);
    state(root, 'Loading job details…');
    try {
      const job = (await NexusApi.get(`/api/jobs/${jobId}`)).job;
      const user = NexusAuth.getUser();
      const isOwner = user && job.job_provider && (user.id === job.job_provider.id || user.username === job.job_provider.username);
      root.innerHTML = `
        <div class="max-w-5xl">
          <div class="flex flex-col sm:flex-row sm:justify-between gap-4 mb-8">
            <div>
              <div class="text-primary font-label-md mb-3">${escape(job.job_state)}</div>
              <h1 class="font-headline-lg text-text-primary">${escape(job.title)}</h1>
              <p class="font-body-lg text-text-secondary mt-2">Posted by ${escape(job.job_provider.name || job.job_provider.username)}</p>
            </div>
            <a class="border border-border px-4 py-2 rounded-lg inline-flex items-center gap-2 hover:border-primary transition-colors text-text-primary" href="${NexusNavigation.url('clientJobs')}">
              <span class="material-symbols-outlined text-sm">arrow_back</span> Back to My Jobs
            </a>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_320px] gap-8">
            <div class="space-y-6">
              <section class="bg-surface border border-border rounded-xl p-6">
                <div class="grid grid-cols-2 gap-5">
                  <div>
                    <div class="text-text-secondary font-label-md uppercase mb-1">BUDGET</div>
                    <div class="text-primary font-headline-md">${money(job.budget)}</div>
                  </div>
                  <div>
                    <div class="text-text-secondary font-label-md uppercase mb-1">DEADLINE</div>
                    <div class="text-text-primary">${escape(date(job.deadline))}</div>
                  </div>
                  <div class="col-span-2">
                    <div class="text-text-secondary font-label-md mb-2">REQUIRED SKILLS</div>
                    <div class="flex flex-wrap gap-2">${skills(job.required_skills)}</div>
                  </div>
                </div>
              </section>
              <section class="bg-surface border border-border rounded-xl p-6">
                <h2 class="font-headline-md text-text-primary mb-3">About This Job</h2>
                <p class="text-text-secondary font-body-lg whitespace-pre-wrap">${escape(job.description)}</p>
              </section>
            </div>
            <aside class="space-y-4">
              ${isOwner ? `
                <a class="w-full bg-primary text-background py-3 px-4 rounded-lg font-body-md font-bold flex justify-center hover:bg-surface-tint transition-colors text-center" href="${NexusNavigation.url('clientApplications', { job_id: job.id })}">View Applications (${job.applications_count || 0})</a>
              ` : ''}
              <a class="w-full border border-border text-text-primary py-3 px-4 rounded-lg font-body-md font-medium flex justify-center hover:bg-surface transition-colors text-center" href="${NexusNavigation.url('clientJobs')}">My Jobs</a>
            </aside>
          </div>
        </div>
      `;
    } catch (error) {
      state(root, error.status === 404 ? 'This job no longer exists.' : error.message, true);
    }
  }

  /* ==========================================================================
     6. INITIALIZATION ON DOM READY
     ========================================================================== */
  document.addEventListener('DOMContentLoaded', async () => {
    const user = await NexusAuth.restore();
    if (!user || user.role !== 'CLIENT') return;
    if (page() === 'clientDashboard' || page() === 'clientJobs') loadMyJobs();
    if (page() === 'postJob') setupPostJob();
    if (page() === 'clientApplications') loadClientApplications();
    if (page() === 'selection') loadSelectionConfirmation();
    if (page() === 'jobDetails') loadJobDetailsForClient();
  });
})();
