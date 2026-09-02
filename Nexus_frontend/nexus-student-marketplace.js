/* Data-backed student marketplace views for the static NEXUS screens. */
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
  const skills = values => (Array.isArray(values) ? values : []).map(skill => `<span class="bg-background border border-border text-text-secondary px-2 py-1 rounded font-label-md text-label-md">${escape(skill)}</span>`).join('') || '<span class="text-text-secondary font-label-md">No skills listed</span>';

  const jobCard = job => `
    <article class="bg-surface border border-border rounded-lg p-6 flex flex-col gap-4 group hover:border-primary/50 transition-colors">
      <div class="flex flex-col gap-2">
        <h3 class="font-headline-md text-headline-md text-text-primary">${escape(job.title)}</h3>
        <p class="font-body-md text-body-md text-text-secondary line-clamp-2">${escape(job.description)}</p>
      </div>
      <div class="flex flex-wrap gap-2 mt-2">${skills(job.required_skills)}</div>
      <div class="flex justify-between items-center mt-auto pt-4 border-t border-border">
        <div class="flex flex-col">
          <span class="text-text-primary font-bold">${money(job.budget)}</span>
          <span class="text-text-secondary font-label-md text-label-md">${escape(date(job.deadline))}</span>
        </div>
        <a class="text-primary font-label-md text-label-md flex items-center gap-1 hover:underline" href="${NexusNavigation.url('jobDetails', { job_id: job.id })}">View Job <span class="material-symbols-outlined text-[16px]">arrow_forward</span></a>
      </div>
    </article>
  `;

  const applicationCard = application => `
    <div class="bg-surface border border-border rounded-lg p-6 hover:border-surface-bright transition-colors group relative overflow-hidden">
      <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div class="flex items-center gap-3 mb-2">
            <h3 class="font-headline-md text-text-primary">${escape(application.job.title)}</h3>
            <span class="px-2.5 py-0.5 rounded text-xs font-label-md ${application.status === 'SELECTED' ? 'bg-primary/20 text-primary border border-primary/30' : 'bg-primary/10 text-primary border border-primary/20'}">${escape(application.status === 'APPLIED' ? 'Under Review' : application.status)}</span>
          </div>
          <div class="flex flex-wrap gap-x-6 gap-y-2 text-sm text-text-secondary font-body-md">
            <span>Client: ${escape(application.job.job_provider.name || application.job.job_provider.username)}</span>
            <span>Budget: ${money(application.job.budget)}</span>
            <span>Applied: ${escape(date(application.created_at))}</span>
            <span>Deadline: ${escape(date(application.job.deadline))}</span>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <a class="text-primary font-label-md text-sm border border-primary/30 px-3 py-1.5 rounded-lg hover:bg-primary/10 transition-colors" href="${NexusNavigation.url('application', { application_id: application.id })}">View Application</a>
          <a class="text-text-secondary hover:text-text-primary font-label-md text-sm border border-border px-3 py-1.5 rounded-lg transition-colors" href="${NexusNavigation.url('jobDetails', { job_id: application.job.id })}">View Job</a>
        </div>
      </div>
    </div>
  `;

  async function jobs() { return (await NexusApi.get('/api/jobs')).jobs || []; }
  async function applications() { return (await NexusApi.get('/api/applications/mine')).applications || []; }

  function renderFind(items) {
    const grids = document.querySelectorAll('main .grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-3.gap-6');
    if (grids.length < 2) return;
    const featured = items.slice(0, 2), remaining = items.slice(2);
    grids[0].innerHTML = featured.map(jobCard).join('') || '<p class="text-text-secondary p-4">No matching open jobs found.</p>';
    grids[1].innerHTML = remaining.map(jobCard).join('') || (featured.length ? '<p class="text-text-secondary p-4">No additional matching jobs found.</p>' : '<p class="text-text-secondary p-4">No matching open jobs found.</p>');
  }

  function setupFindFilters(allItems) {
    const searchInput = document.querySelector('main input[placeholder*="Search jobs"]');
    if (!searchInput) return;
    searchInput.addEventListener('input', () => {
      const q = searchInput.value.trim().toLowerCase();
      if (!q) { renderFind(allItems); return; }
      const filtered = allItems.filter(j => {
        const titleMatch = (j.title || '').toLowerCase().includes(q);
        const descMatch = (j.description || '').toLowerCase().includes(q);
        const skillMatch = Array.isArray(j.required_skills) && j.required_skills.some(s => String(s).toLowerCase().includes(q));
        return titleMatch || descMatch || skillMatch;
      });
      renderFind(filtered);
    });
  }

  function renderDashboard(jobItems, appItems) {
    const grids = document.querySelectorAll('.grid.grid-cols-1.md\\:grid-cols-2.gap-gutter');
    if (grids.length) grids[0].innerHTML = jobItems.slice(0, 2).map(jobCard).join('') || '<p class="text-text-secondary p-4">No open jobs are available yet.</p>';
    const applicationPanel = [...document.querySelectorAll('h2')].find(node => node.textContent.trim() === 'My Applications')?.closest('.bg-surface');
    if (applicationPanel) {
      const body = applicationPanel.querySelector('.p-0');
      if (body) body.innerHTML = appItems.slice(0, 3).map(app => `
        <div class="p-4 border-b border-border flex justify-between items-center">
          <div>
            <h4 class="font-body-lg text-text-primary">${escape(app.job.title)}</h4>
            <p class="text-text-secondary text-label-md">${money(app.job.budget)} • ${escape(date(app.created_at))}</p>
          </div>
          <span class="text-primary text-label-md bg-primary/10 px-2 py-0.5 rounded border border-primary/20">${escape(app.status === 'APPLIED' ? 'Under Review' : app.status)}</span>
        </div>
      `).join('') || '<p class="p-4 text-text-secondary">You have not applied to any jobs yet.</p>';
    }
    const activeWorkPanel = [...document.querySelectorAll('h2')].find(node => node.textContent.trim() === 'Active Work')?.closest('.bg-surface');
    if (activeWorkPanel) {
      const body = activeWorkPanel.querySelector('.p-4');
      const selected = appItems.filter(app => app.status === 'SELECTED');
      if (body) body.innerHTML = selected.map(app => `
        <div class="p-4 bg-surface-container border border-border rounded-lg">
          <h4 class="font-body-lg text-text-primary">${escape(app.job.title)}</h4>
          <p class="text-text-secondary text-label-md">Due: ${escape(date(app.job.deadline))} • ${money(app.job.budget)}</p>
        </div>
      `).join('') || '<p class="text-text-secondary">No active work yet.</p>';
    }
    const values = {
      'Active Apps': appItems.filter(app => app.status === 'APPLIED').length,
      'Active Work': appItems.filter(app => app.status === 'SELECTED').length,
      Completed: '—',
      'Total Earnings': '—'
    };
    document.querySelectorAll('h3').forEach(label => {
      const card = label.closest('.bg-surface');
      const value = values[label.textContent.trim()];
      if (card && value !== undefined) {
        const number = card.querySelector('.font-headline-lg');
        if (number) number.textContent = value;
      }
    });
    const welcome = document.querySelector('h1');
    if (welcome && NexusAuth.getUser()) {
      welcome.textContent = `Welcome back, ${NexusAuth.getUser().name || NexusAuth.getUser().username}`;
    }
  }

  async function loadListing(target) {
    const grids = document.querySelectorAll('main .grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-3.gap-6, .grid.grid-cols-1.md\\:grid-cols-2.gap-gutter');
    grids.forEach(grid => state(grid, 'Loading marketplace data…'));
    if (target === 'dashboard') {
      ['My Applications', 'Active Work'].forEach(heading => {
        const panel = [...document.querySelectorAll('h2')].find(node => node.textContent.trim() === heading)?.closest('.bg-surface');
        const body = panel && panel.querySelector('.p-0, .p-4');
        if (body) state(body, 'Loading…');
      });
    }
    try {
      const data = await jobs();
      if (target === 'find') {
        renderFind(data);
        setupFindFilters(data);
      } else {
        renderDashboard(data, await applications());
      }
    } catch (error) {
      grids.forEach(grid => state(grid, error.message, true));
    }
  }

  async function loadDetail(applyPage = false) {
    const jobId = new URLSearchParams(location.search).get('job_id');
    const root = document.querySelector('main');
    if (!uuid(jobId)) return state(root, 'A valid job ID is required to view this job.', true);
    state(root, 'Loading job details…');
    try {
      const job = (await NexusApi.get(`/api/jobs/${jobId}`)).job;
      if (applyPage) return renderApply(job);
      root.innerHTML = `
        <div class="max-w-5xl">
          <div class="flex flex-col sm:flex-row sm:justify-between gap-4 mb-8">
            <div>
              <div class="text-primary font-label-md mb-3">${escape(job.job_state)}</div>
              <h1 class="font-headline-lg text-text-primary">${escape(job.title)}</h1>
              <p class="font-body-lg text-text-secondary mt-2">Posted by ${escape(job.job_provider.name || job.job_provider.username)}</p>
            </div>
            <a class="border border-border px-4 py-2 rounded-lg inline-flex items-center gap-2 hover:border-primary transition-colors text-text-primary" href="${NexusNavigation.url('jobs')}">
              <span class="material-symbols-outlined text-sm">arrow_back</span> Back to Find Jobs
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
            <aside>
              <a class="w-full bg-primary-container text-white py-3 px-4 rounded-lg font-body-md font-bold flex justify-center hover:opacity-90 transition-opacity" href="${NexusNavigation.url('apply', { job_id: job.id })}">Apply for This Job</a>
            </aside>
          </div>
        </div>
      `;
    } catch (error) {
      state(root, error.status === 404 ? 'This job no longer exists.' : error.message, true);
    }
  }

  function renderApply(job) {
    const root = document.querySelector('main');
    root.innerHTML = `
      <div class="max-w-3xl mx-auto space-y-8">
        <div>
          <a class="text-primary inline-flex items-center gap-1 hover:underline mb-2" href="${NexusNavigation.url('jobDetails', { job_id: job.id })}">
            <span class="material-symbols-outlined text-sm">arrow_back</span> Back to Job Details
          </a>
          <h1 class="font-headline-lg text-text-primary mt-2">Submit Your Application</h1>
        </div>
        <section class="bg-surface border border-border rounded-lg p-6">
          <h2 class="font-headline-md text-text-primary">${escape(job.title)}</h2>
          <p class="text-text-secondary mt-2">${escape(job.job_provider.name || job.job_provider.username)} • ${money(job.budget)} • ${escape(date(job.deadline))}</p>
          <div class="flex flex-wrap gap-2 mt-4">${skills(job.required_skills)}</div>
        </section>
        <form id="application-form" class="space-y-6">
          <div>
            <label class="block text-text-primary font-body-md mb-2" for="cover-letter">Why are you a good fit for this job?</label>
            <textarea required id="cover-letter" class="w-full bg-surface border border-border rounded-lg p-4 text-text-primary focus:border-primary focus:ring-1 focus:ring-primary outline-none" rows="6" placeholder="Describe your experience and why you are the best person for this task..."></textarea>
          </div>
          <div>
            <label class="block text-text-primary font-body-md mb-2" for="completion-date">Expected completion date</label>
            <input required id="completion-date" type="date" class="w-full bg-surface border border-border rounded-lg p-3 text-text-primary focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
          </div>
          <p id="application-feedback" class="font-body-md"></p>
          <button class="bg-primary-container text-white py-3 px-6 rounded-lg font-body-md font-bold hover:opacity-90 transition-opacity" type="submit">Submit Application</button>
        </form>
      </div>
    `;

    root.querySelector('#application-form').addEventListener('submit', async event => {
      event.preventDefault();
      const button = event.currentTarget.querySelector('button');
      const feedback = root.querySelector('#application-feedback');
      button.disabled = true;
      try {
        await NexusApi.post(`/api/jobs/${job.id}/applications`, {
          application_message: root.querySelector('#cover-letter').value.trim(),
          expected_completion: root.querySelector('#completion-date').value,
          application_information: { skills: job.required_skills }
        });
        feedback.textContent = 'Application submitted successfully. Redirecting…';
        feedback.className = 'text-primary font-body-md';
        setTimeout(() => NexusNavigation.go('applications'), 500);
      } catch (error) {
        feedback.textContent = error.message;
        feedback.className = 'text-error font-body-md';
        button.disabled = false;
      }
    });
  }

  async function loadApplications() {
    const root = document.querySelector('main');
    const list = document.querySelector('#marketplace-applications');
    if (list) state(list, 'Loading applications…');
    try {
      const allItems = await applications();
      let currentFilter = 'All';
      let currentQuery = '';

      function updateFilteredList() {
        if (!list) return;
        let filtered = allItems;
        if (currentFilter === 'Under Review') filtered = filtered.filter(a => a.status === 'APPLIED');
        else if (currentFilter === 'Selected') filtered = filtered.filter(a => a.status === 'SELECTED');
        else if (currentFilter === 'Rejected') filtered = [];

        if (currentQuery) {
          filtered = filtered.filter(a => {
            const titleMatch = (a.job && a.job.title || '').toLowerCase().includes(currentQuery);
            const clientMatch = (a.job && a.job.job_provider && a.job.job_provider.name || '').toLowerCase().includes(currentQuery);
            return titleMatch || clientMatch;
          });
        }

        list.innerHTML = filtered.map(applicationCard).join('') || `<p class="text-text-secondary p-6 bg-surface border border-border rounded-lg text-center font-body-md">${currentFilter === 'All' && !currentQuery ? 'You have not applied to any jobs yet.' : 'No applications match your filter.'}</p>`;
      }

      updateFilteredList();

      const summary = document.querySelectorAll('[data-application-count]');
      if (summary.length) {
        summary[0].textContent = allItems.length;
        summary[1].textContent = allItems.filter(item => item.status === 'APPLIED').length;
        summary[2].textContent = allItems.filter(item => item.status === 'SELECTED').length;
        summary[3].textContent = '0';
      }

      // Filter tabs interaction
      const filterButtons = document.querySelectorAll('main .flex.gap-2 button');
      filterButtons.forEach(button => {
        button.addEventListener('click', () => {
          currentFilter = button.textContent.trim();
          filterButtons.forEach(btn => {
            btn.className = 'px-4 py-1.5 rounded-full bg-surface border border-border text-text-secondary text-sm font-label-md whitespace-nowrap hover:bg-surface-bright transition-colors';
          });
          button.className = 'px-4 py-1.5 rounded-full bg-primary/15 border border-primary/30 text-primary text-sm font-label-md whitespace-nowrap hover:bg-primary/25 transition-colors';
          updateFilteredList();
        });
      });

      // Search input interaction
      const searchInput = document.querySelector('main input[placeholder*="Search applications"]');
      if (searchInput) {
        searchInput.addEventListener('input', () => {
          currentQuery = searchInput.value.trim().toLowerCase();
          updateFilteredList();
        });
      }
    } catch (error) {
      if (list) state(list, error.message, true);
    }
  }

  async function loadApplicationDetail() {
    const applicationId = new URLSearchParams(location.search).get('application_id');
    const root = document.querySelector('main');
    if (!uuid(applicationId)) return state(root, 'A valid application ID is required to view this application.', true);
    state(root, 'Loading application details…');
    try {
      const app = (await NexusApi.get(`/api/applications/${applicationId}`)).application;
      root.innerHTML = `
        <div class="p-gutter md:p-margin-desktop flex-1 max-w-max-width mx-auto w-full">
          <div class="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4">
            <div>
              <h2 class="font-headline-lg text-headline-lg text-text-primary mb-2">Application Details</h2>
              <p class="text-text-secondary font-body-md">Track your application and see its current status.</p>
            </div>
            <a class="flex items-center space-x-2 text-text-secondary hover:text-primary transition-colors border border-border px-4 py-2 rounded-lg bg-surface hover:bg-surface-container-high duration-200 font-label-md text-label-md" href="${NexusNavigation.url('applications')}">
              <span class="material-symbols-outlined text-sm">arrow_back</span>
              <span>Back to Applications</span>
            </a>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="lg:col-span-1 space-y-6">
              <div class="bg-surface border border-border rounded-lg p-6 hover:border-primary/50 transition-colors duration-300 relative overflow-hidden">
                <h3 class="font-headline-md text-headline-md text-text-primary mb-4">${escape(app.job.title)}</h3>
                <div class="space-y-3 mb-6">
                  <div class="flex justify-between items-center border-b border-border pb-2">
                    <span class="text-text-secondary font-label-md">Client</span>
                    <span class="text-text-primary font-body-md font-medium">${escape(app.job.job_provider.name || app.job.job_provider.username)}</span>
                  </div>
                  <div class="flex justify-between items-center border-b border-border pb-2">
                    <span class="text-text-secondary font-label-md">Budget</span>
                    <span class="text-primary font-body-md font-bold">${money(app.job.budget)}</span>
                  </div>
                  <div class="flex justify-between items-center border-b border-border pb-2">
                    <span class="text-text-secondary font-label-md">Deadline</span>
                    <span class="text-text-primary font-body-md">${escape(date(app.job.deadline))}</span>
                  </div>
                </div>
                <a class="text-primary hover:underline font-label-md text-label-md flex items-center gap-1" href="${NexusNavigation.url('jobDetails', { job_id: app.job.id })}">
                  View Job Details <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
                </a>
              </div>

              <div class="bg-surface border border-border rounded-lg p-6">
                <h4 class="font-body-lg text-body-lg text-text-primary mb-4 font-semibold">Application Metadata</h4>
                <div class="space-y-4">
                  <div class="flex items-start gap-3">
                    <span class="material-symbols-outlined text-text-secondary">tag</span>
                    <div>
                      <p class="text-text-secondary font-label-md">Application ID</p>
                      <p class="text-text-primary font-body-md text-xs font-mono">${escape(app.id)}</p>
                    </div>
                  </div>
                  <div class="flex items-start gap-3">
                    <span class="material-symbols-outlined text-text-secondary">calendar_today</span>
                    <div>
                      <p class="text-text-secondary font-label-md">Applied On</p>
                      <p class="text-text-primary font-body-md">${escape(date(app.created_at))}</p>
                    </div>
                  </div>
                  <div class="flex items-start gap-3">
                    <span class="material-symbols-outlined text-text-secondary">schedule</span>
                    <div>
                      <p class="text-text-secondary font-label-md">Expected Completion</p>
                      <p class="text-text-primary font-body-md">${app.expected_completion ? escape(date(app.expected_completion)) : 'Not specified'}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="lg:col-span-2 space-y-6">
              <div class="bg-surface border border-border rounded-lg p-6">
                <div class="flex justify-between items-start mb-6">
                  <div>
                    <span class="text-text-secondary font-label-md uppercase tracking-wider block mb-1">Status</span>
                    <div class="flex items-center gap-2">
                      <span class="px-3 py-1 rounded-full font-label-md ${app.status === 'SELECTED' ? 'bg-primary/20 text-primary border border-primary/30' : 'bg-primary/10 text-primary border border-primary/20'}">${escape(app.status === 'APPLIED' ? 'Under Review' : app.status)}</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 class="font-body-lg text-text-primary font-semibold mb-2">Cover Letter & Message</h4>
                  <p class="text-text-secondary font-body-lg whitespace-pre-wrap bg-background p-4 rounded-lg border border-border">${escape(app.application_message || 'No cover letter message provided.')}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    } catch (error) {
      state(root, error.status === 404 ? 'Application not found or you do not have permission to view it.' : error.message, true);
    }
  }

  document.addEventListener('DOMContentLoaded', async () => {
    const user = await NexusAuth.restore();
    if (!user || user.role !== 'STUDENT') return;
    if (page() === 'jobs') loadListing('find');
    if (page() === 'studentDashboard') loadListing('dashboard');
    if (page() === 'jobDetails') loadDetail();
    if (page() === 'apply') loadDetail(true);
    if (page() === 'applications') loadApplications();
    if (page() === 'application') loadApplicationDetail();
  });
})();
