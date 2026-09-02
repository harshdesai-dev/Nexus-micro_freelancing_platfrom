/* Shared NEXUS workflow handlers: Workspaces, Messaging, Submissions, Review, Payment, Ratings, and Reports */
(() => {
  const page = () => window.NexusNavigation && NexusNavigation.currentPage;
  const escape = value => String(value ?? '').replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
  const money = value => `₹${Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
  const date = value => value ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value)) : 'No deadline';
  const time = value => value ? new Intl.DateTimeFormat(undefined, { timeStyle: 'short', dateStyle: 'short' }).format(new Date(value)) : '';
  const uuid = value => /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value || '');
  const state = (container, text, error = false) => {
    if (!container) return;
    container.innerHTML = `<div class="bg-surface border ${error ? 'border-error text-error' : 'border-border text-text-secondary'} rounded-lg p-6 text-center font-body-md">${escape(text)}</div>`;
  };

  /* ==========================================================================
     1. WORKSPACE (STUDENT & CLIENT VIEWS)
     ========================================================================== */
  async function loadWorkspace(isClient = false) {
    const jobId = new URLSearchParams(location.search).get('job_id');
    const main = document.querySelector('main');
    if (!uuid(jobId)) {
      if (main) state(main, 'A valid job ID is required to access the project workspace.', true);
      return;
    }

    try {
      const res = await NexusApi.get(`/api/jobs/${jobId}`);
      const job = res.job;
      const user = NexusAuth.getUser() || {};
      const otherUser = isClient ? (job.selected_student || {}) : (job.job_provider || {});
      const otherName = otherUser.name || otherUser.username || (isClient ? 'Student' : 'Client');
      const otherRoleLabel = isClient ? 'Student Freelancer' : 'Job Provider';

      const statusBadge = (st) => {
        const map = {
          'STUDENT_SELECTED': { text: 'Student Selected', color: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20' },
          'IN_PROGRESS': { text: 'In Progress', color: 'bg-primary/10 text-primary border-primary/20' },
          'WORK_SUBMITTED': { text: 'Work Submitted', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
          'PAYMENT': { text: 'Payment Pending', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
          'COMPLETED': { text: 'Completed', color: 'bg-primary/10 text-primary border-primary/20' },
          'RATED': { text: 'Completed & Rated', color: 'bg-primary/10 text-primary border-primary/20' }
        };
        const s = map[st] || { text: st, color: 'bg-surface-container text-text-secondary border-border' };
        return `<span class="${s.color} border px-2.5 py-1 rounded text-label-md font-bold uppercase tracking-wider">${escape(s.text)}</span>`;
      };

      if (main) {
        main.innerHTML = `
          <div class="max-w-7xl mx-auto px-4 py-8 space-y-8">
            <!-- Header -->
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-surface border border-border p-6 rounded-xl">
              <div>
                <nav class="flex items-center gap-2 text-text-secondary text-body-md mb-2">
                  <a class="hover:text-primary transition-colors" href="${isClient ? NexusNavigation.url('clientJobs') : NexusNavigation.url('applications')}">${isClient ? 'My Jobs' : 'My Applications'}</a>
                  <span class="material-symbols-outlined text-[16px]">chevron_right</span>
                  <span class="text-text-primary">Workspace</span>
                </nav>
                <div class="flex items-center gap-3 flex-wrap">
                  <h1 class="font-headline-lg text-headline-lg text-text-primary">${escape(job.title)}</h1>
                  ${statusBadge(job.job_state)}
                </div>
                <p class="text-text-secondary font-body-md mt-1">Project with <strong class="text-text-primary">${escape(otherName)}</strong> (${escape(otherRoleLabel)})</p>
              </div>
              <div class="flex flex-wrap gap-3">
                ${!isClient && ['STUDENT_SELECTED', 'IN_PROGRESS', 'WORK_SUBMITTED'].includes(job.job_state) ? `
                  <a class="bg-primary text-background px-4 py-2 rounded-lg font-label-md font-bold hover:bg-surface-tint inline-flex items-center gap-2" href="${NexusNavigation.url('submitWork', { job_id: job.id })}">
                    <span class="material-symbols-outlined text-sm">upload_file</span> Submit Work
                  </a>
                ` : ''}
                ${isClient && job.job_state === 'WORK_SUBMITTED' ? `
                  <a class="bg-primary text-background px-4 py-2 rounded-lg font-label-md font-bold hover:bg-surface-tint inline-flex items-center gap-2" href="${NexusNavigation.url('clientReview', { job_id: job.id })}">
                    <span class="material-symbols-outlined text-sm">rate_review</span> Review Submission
                  </a>
                ` : ''}
                ${isClient && job.job_state === 'PAYMENT' ? `
                  <a class="bg-primary text-background px-4 py-2 rounded-lg font-label-md font-bold hover:bg-surface-tint inline-flex items-center gap-2" href="${NexusNavigation.url('clientPayment', { job_id: job.id })}">
                    <span class="material-symbols-outlined text-sm">payments</span> Release Payment
                  </a>
                ` : ''}
                ${!isClient && (job.job_state === 'PAYMENT' || job.job_state === 'COMPLETED' || job.job_state === 'RATED') ? `
                  <a class="border border-border text-text-primary px-4 py-2 rounded-lg font-label-md hover:border-primary inline-flex items-center gap-2" href="${NexusNavigation.url('studentPayment', { job_id: job.id })}">
                    <span class="material-symbols-outlined text-sm">payments</span> Payment Details
                  </a>
                ` : ''}
                ${['COMPLETED', 'RATED'].includes(job.job_state) ? `
                  <a class="bg-primary/10 text-primary border border-primary/20 px-4 py-2 rounded-lg font-label-md font-bold hover:bg-primary/20 inline-flex items-center gap-2" href="${isClient ? NexusNavigation.url('clientRating', { job_id: job.id }) : NexusNavigation.url('studentRating', { job_id: job.id })}">
                    <span class="material-symbols-outlined text-sm">star</span> Rate & Review
                  </a>
                ` : ''}
                <a class="border border-error/30 text-error px-3 py-2 rounded-lg font-label-md hover:bg-error/10 inline-flex items-center gap-1" href="${NexusNavigation.url('report', { job_id: job.id })}" title="Raise a dispute or report issue">
                  <span class="material-symbols-outlined text-sm">flag</span> Report
                </a>
              </div>
            </div>

            <!-- Bento Content Grid -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <!-- Left 2 Cols: Messages & Collaboration -->
              <div class="lg:col-span-2 space-y-6">
                <!-- Messages Box -->
                <div class="bg-surface border border-border rounded-xl flex flex-col h-[520px] overflow-hidden">
                  <div class="px-6 py-4 border-b border-border bg-surface-container flex items-center justify-between">
                    <div class="flex items-center gap-3">
                      <div class="w-10 h-10 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold">
                        ${escape(otherName.substring(0, 2).toUpperCase())}
                      </div>
                      <div>
                        <h3 class="font-headline-md text-body-lg text-text-primary">${escape(otherName)}</h3>
                        <p class="text-text-secondary text-label-md">${escape(otherRoleLabel)}</p>
                      </div>
                    </div>
                    <span class="text-text-secondary text-label-md flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-primary"></span> Direct Chat</span>
                  </div>

                  <div class="flex-1 p-6 overflow-y-auto space-y-4" id="messages-container">
                    <p class="text-text-secondary font-body-md text-center">Loading conversation…</p>
                  </div>

                  <form class="p-4 border-t border-border bg-surface-container flex gap-3" id="message-form">
                    <input class="flex-1 bg-background border border-border rounded-lg px-4 py-2.5 text-text-primary text-body-md focus:outline-none focus:border-primary" id="message-input" placeholder="Type a message to ${escape(otherName)}…" required autocomplete="off"/>
                    <button class="bg-primary text-background font-label-md font-bold px-5 py-2.5 rounded-lg hover:bg-surface-tint flex items-center gap-1" type="submit">
                      <span>Send</span>
                      <span class="material-symbols-outlined text-sm">send</span>
                    </button>
                  </form>
                </div>
              </div>

              <!-- Right Col: Job Context & Details -->
              <div class="space-y-6">
                <div class="bg-surface border border-border p-6 rounded-xl space-y-4">
                  <h3 class="font-headline-md text-headline-md text-text-primary border-b border-border pb-3">Project Details</h3>
                  <div class="space-y-3 font-body-md">
                    <div>
                      <span class="text-text-secondary block text-label-md uppercase">Agreed Budget</span>
                      <span class="text-primary font-headline-md font-bold">${money(job.budget)}</span>
                    </div>
                    <div>
                      <span class="text-text-secondary block text-label-md uppercase">Deadline</span>
                      <span class="text-text-primary">${escape(date(job.deadline))}</span>
                    </div>
                    <div>
                      <span class="text-text-secondary block text-label-md uppercase">Current Stage</span>
                      <span class="text-text-primary font-semibold">${escape(job.job_state)}</span>
                    </div>
                  </div>
                  <div class="pt-2 border-t border-border">
                    <p class="text-text-secondary text-label-md uppercase mb-2">Description</p>
                    <p class="text-text-secondary text-body-md whitespace-pre-wrap">${escape(job.description)}</p>
                  </div>
                </div>

                <!-- Submissions quick box -->
                <div class="bg-surface border border-border p-6 rounded-xl space-y-3" id="submissions-panel">
                  <h3 class="font-headline-md text-body-lg text-text-primary flex items-center justify-between">
                    <span>Work Submissions</span>
                    <span class="material-symbols-outlined text-text-secondary">folder</span>
                  </h3>
                  <div id="submissions-list" class="space-y-2 text-body-md text-text-secondary">
                    Loading submissions…
                  </div>
                </div>
              </div>
            </div>
          </div>
        `;

        // Setup Messages
        const msgContainer = document.getElementById('messages-container');
        const msgForm = document.getElementById('message-form');
        const msgInput = document.getElementById('message-input');

        async function fetchMessages() {
          try {
            const mRes = await NexusApi.get(`/api/jobs/${job.id}/messages`);
            const msgs = mRes.messages || [];
            if (msgs.length === 0) {
              msgContainer.innerHTML = `<div class="text-center py-12 text-text-secondary font-body-md">No messages yet. Send a greeting to start collaborating!</div>`;
            } else {
              msgContainer.innerHTML = msgs.map(m => {
                const isMe = m.sender && (m.sender.id === user.id || m.sender.username === user.username);
                return `
                  <div class="flex flex-col ${isMe ? 'items-end' : 'items-start'}">
                    <div class="max-w-[80%] rounded-xl px-4 py-2.5 text-body-md ${isMe ? 'bg-primary text-background font-medium' : 'bg-surface-container-high text-text-primary border border-border'}">
                      <p class="whitespace-pre-wrap">${escape(m.message)}</p>
                    </div>
                    <span class="text-[11px] text-text-secondary mt-1 px-1">${escape(m.sender ? (m.sender.name || m.sender.username) : '')} • ${escape(time(m.timestamp))}</span>
                  </div>
                `;
              }).join('');
              msgContainer.scrollTop = msgContainer.scrollHeight;
            }
          } catch (e) {
            msgContainer.innerHTML = `<p class="text-error text-body-md text-center">${escape(e.message)}</p>`;
          }
        }

        fetchMessages();

        msgForm.addEventListener('submit', async (e) => {
          e.preventDefault();
          const text = msgInput.value.trim();
          if (!text) return;
          msgInput.value = '';
          try {
            await NexusApi.post(`/api/jobs/${job.id}/messages`, { message: text });
            await fetchMessages();
          } catch (err) {
            alert(err.message);
          }
        });

        // Setup Submissions List
        const subList = document.getElementById('submissions-list');
        try {
          const sRes = await NexusApi.get(`/api/jobs/${job.id}/submissions`);
          const subs = sRes.submissions || [];
          if (subs.length === 0) {
            subList.innerHTML = `<p class="text-text-secondary text-label-md">No work submitted yet.</p>`;
          } else {
            subList.innerHTML = subs.map(s => {
              const statusColor = s.submission_status === 'ACCEPTED' ? 'text-primary' : s.submission_status === 'REJECTED' ? 'text-error' : 'text-yellow-400';
              const notes = (s.submission_information && s.submission_information.notes) || (s.submitted_work && s.submitted_work[0]) || 'Deliverables submitted';
              return `
                <div class="p-3 bg-background border border-border rounded-lg space-y-1">
                  <div class="flex justify-between items-center">
                    <span class="font-bold text-text-primary text-label-md">${escape(s.student.name || 'Student')}</span>
                    <span class="${statusColor} font-bold text-label-md uppercase">${escape(s.submission_status)}</span>
                  </div>
                  <p class="text-text-secondary text-body-md text-xs truncate">${escape(notes)}</p>
                  <p class="text-[11px] text-text-secondary">${escape(time(s.created_at))}</p>
                </div>
              `;
            }).join('');
          }
        } catch (e) {
          subList.innerHTML = `<p class="text-text-secondary text-label-md">Submissions available when uploaded.</p>`;
        }
      }
    } catch (error) {
      if (main) state(main, error.message, true);
    }
  }

  /* ==========================================================================
     2. SUBMIT WORK (STUDENT) (nexus_submit_work_desktop_2)
     ========================================================================== */
  async function loadSubmitWork() {
    const jobId = new URLSearchParams(location.search).get('job_id');
    const main = document.querySelector('main');
    if (!uuid(jobId)) {
      if (main) state(main, 'A valid job ID is required to submit deliverables.', true);
      return;
    }

    try {
      const res = await NexusApi.get(`/api/jobs/${jobId}`);
      const job = res.job;

      if (main) {
        main.innerHTML = `
          <div class="max-w-3xl mx-auto px-4 py-8 space-y-6">
            <nav class="flex items-center gap-2 text-text-secondary text-body-md mb-2">
              <a class="hover:text-primary transition-colors" href="${NexusNavigation.url('studentWorkspace', { job_id: job.id })}">Workspace</a>
              <span class="material-symbols-outlined text-[16px]">chevron_right</span>
              <span class="text-text-primary">Submit Work</span>
            </nav>

            <div class="bg-surface border border-border p-6 rounded-xl space-y-4">
              <div class="flex items-start justify-between">
                <div>
                  <h1 class="font-headline-lg text-headline-lg text-text-primary">Submit Final Deliverables</h1>
                  <p class="text-text-secondary font-body-md mt-1">Submit your completed work for "${escape(job.title)}" to the client for review and approval.</p>
                </div>
                <span class="bg-primary/10 text-primary border border-primary/20 px-3 py-1 rounded font-bold text-label-md">${money(job.budget)}</span>
              </div>
            </div>

            <form class="bg-surface border border-border p-6 rounded-xl space-y-6" id="submit-work-form">
              <div class="space-y-2">
                <label class="block text-text-primary font-body-md font-semibold" for="submission-notes">Submission Notes & Deliverable Overview *</label>
                <textarea class="w-full bg-background border border-border rounded-lg p-4 text-text-primary font-body-md focus:outline-none focus:border-primary min-h-[140px]" id="submission-notes" placeholder="Describe the work completed, changes made, deliverables included, and how to verify it…" required></textarea>
              </div>

              <div class="space-y-2">
                <label class="block text-text-primary font-body-md font-semibold" for="deliverable-link">Project / Repository / Drive Link (Optional)</label>
                <input class="w-full bg-background border border-border rounded-lg p-3 text-text-primary font-body-md focus:outline-none focus:border-primary" id="deliverable-link" placeholder="https://github.com/... or https://drive.google.com/..." type="url"/>
              </div>

              <div class="flex gap-4 pt-4 border-t border-border">
                <button class="bg-primary text-background font-label-md font-bold px-6 py-3 rounded-lg hover:bg-surface-tint flex-1 flex items-center justify-center gap-2" type="submit" id="submit-btn">
                  <span class="material-symbols-outlined text-sm">send</span>
                  <span>Submit for Client Review</span>
                </button>
                <a class="border border-border text-text-primary font-label-md font-semibold px-6 py-3 rounded-lg hover:bg-surface-container text-center" href="${NexusNavigation.url('studentWorkspace', { job_id: job.id })}">Cancel</a>
              </div>
            </form>
          </div>
        `;

        const form = document.getElementById('submit-work-form');
        const submitBtn = document.getElementById('submit-btn');
        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          const notes = document.getElementById('submission-notes').value.trim();
          const link = document.getElementById('deliverable-link').value.trim();
          if (!notes) return;

          submitBtn.disabled = true;
          submitBtn.textContent = 'Submitting…';

          try {
            await NexusApi.post(`/api/jobs/${job.id}/submissions`, {
              submitted_work: link ? [link] : [notes],
              submission_information: { notes, deliverable_link: link }
            });
            main.innerHTML = `
              <div class="max-w-md mx-auto py-16 text-center bg-surface border border-border rounded-xl p-8 space-y-4">
                <div class="w-16 h-16 rounded-full bg-primary/20 text-primary flex items-center justify-center mx-auto">
                  <span class="material-symbols-outlined text-4xl">check_circle</span>
                </div>
                <h2 class="font-headline-lg text-text-primary">Work Submitted!</h2>
                <p class="text-text-secondary font-body-md">Your work has been submitted to ${escape(job.job_provider.name || 'the client')} for review.</p>
                <div class="pt-4">
                  <a class="bg-primary text-background font-label-md px-6 py-3 rounded-lg font-bold inline-block hover:bg-surface-tint" href="${NexusNavigation.url('studentWorkspace', { job_id: job.id })}">Back to Workspace</a>
                </div>
              </div>
            `;
          } catch (err) {
            alert(err.message);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit for Client Review';
          }
        });
      }
    } catch (error) {
      if (main) state(main, error.message, true);
    }
  }

  /* ==========================================================================
     3. CLIENT REVIEW (nexus_client_review_submitted_work_desktop_2)
     ========================================================================== */
  async function loadClientReview() {
    const jobId = new URLSearchParams(location.search).get('job_id');
    const main = document.querySelector('main');
    if (!uuid(jobId)) {
      if (main) state(main, 'A valid job ID is required to review deliverables.', true);
      return;
    }

    try {
      const jobRes = await NexusApi.get(`/api/jobs/${jobId}`);
      const job = jobRes.job;
      const subRes = await NexusApi.get(`/api/jobs/${jobId}/submissions`);
      const subs = subRes.submissions || [];
      const latestSub = subs[0];

      if (!latestSub) {
        if (main) state(main, 'No submissions found to review for this job.', false);
        return;
      }

      const notes = (latestSub.submission_information && latestSub.submission_information.notes) || (latestSub.submitted_work && latestSub.submitted_work[0]) || 'No submission details provided.';
      const link = latestSub.submission_information && latestSub.submission_information.deliverable_link;
      const studentName = (latestSub.student && latestSub.student.name) || (job.selected_student && job.selected_student.name) || 'Student';

      if (main) {
        main.innerHTML = `
          <div class="max-w-3xl mx-auto px-4 py-8 space-y-6">
            <nav class="flex items-center gap-2 text-text-secondary text-body-md mb-2">
              <a class="hover:text-primary transition-colors" href="${NexusNavigation.url('clientWorkspace', { job_id: job.id })}">Workspace</a>
              <span class="material-symbols-outlined text-[16px]">chevron_right</span>
              <span class="text-text-primary">Review Work</span>
            </nav>

            <div class="bg-surface border border-border p-6 rounded-xl space-y-2">
              <span class="bg-blue-500/10 text-blue-400 border border-blue-500/20 px-3 py-1 rounded text-label-md font-bold uppercase">Pending Review</span>
              <h1 class="font-headline-lg text-headline-lg text-text-primary">Review Submitted Deliverables</h1>
              <p class="text-text-secondary font-body-md">Submitted by <strong class="text-text-primary">${escape(studentName)}</strong> on ${escape(time(latestSub.created_at))}</p>
            </div>

            <div class="bg-surface border border-border p-6 rounded-xl space-y-6">
              <div class="space-y-2">
                <h3 class="font-headline-md text-body-lg text-text-primary font-bold">Deliverable Overview & Notes</h3>
                <div class="bg-background border border-border p-4 rounded-lg text-text-primary font-body-md whitespace-pre-wrap">${escape(notes)}</div>
              </div>

              ${link ? `
                <div class="space-y-2">
                  <h3 class="font-headline-md text-body-lg text-text-primary font-bold">Deliverable Link</h3>
                  <a class="text-primary underline font-body-md flex items-center gap-1.5" href="${escape(link)}" target="_blank" rel="noopener">
                    <span class="material-symbols-outlined text-sm">open_in_new</span>
                    <span>${escape(link)}</span>
                  </a>
                </div>
              ` : ''}

              <div class="grid grid-cols-2 gap-4 bg-surface-container p-4 rounded-lg border border-border font-body-md">
                <div>
                  <span class="text-text-secondary block text-label-md uppercase">Job Budget</span>
                  <span class="text-primary font-bold text-lg">${money(job.budget)}</span>
                </div>
                <div>
                  <span class="text-text-secondary block text-label-md uppercase">Status</span>
                  <span class="text-text-primary font-semibold">${escape(latestSub.submission_status)}</span>
                </div>
              </div>

              <div class="flex flex-col sm:flex-row gap-4 pt-4 border-t border-border">
                <button class="bg-primary text-background font-label-md font-bold py-3 px-6 rounded-lg hover:bg-surface-tint flex-1 flex items-center justify-center gap-2" id="accept-work-btn">
                  <span class="material-symbols-outlined text-sm">check_circle</span>
                  <span>Accept Work & Release Payment</span>
                </button>
                <button class="bg-transparent border border-border text-text-primary font-label-md font-semibold py-3 px-6 rounded-lg hover:bg-surface-container flex-1 flex items-center justify-center gap-2" id="request-changes-btn">
                  <span class="material-symbols-outlined text-sm">replay</span>
                  <span>Request Changes</span>
                </button>
              </div>
            </div>
          </div>
        `;

        const acceptBtn = document.getElementById('accept-work-btn');
        const rejectBtn = document.getElementById('request-changes-btn');

        acceptBtn.addEventListener('click', async () => {
          acceptBtn.disabled = true;
          acceptBtn.textContent = 'Accepting…';
          try {
            await NexusApi.patch(`/api/jobs/${job.id}/submissions/${latestSub.id}`, { status: 'ACCEPTED' });
            NexusNavigation.go('clientPayment', { job_id: job.id });
          } catch (e) {
            alert(e.message);
            acceptBtn.disabled = false;
            acceptBtn.textContent = 'Accept Work & Release Payment';
          }
        });

        rejectBtn.addEventListener('click', async () => {
          rejectBtn.disabled = true;
          rejectBtn.textContent = 'Requesting Changes…';
          try {
            await NexusApi.patch(`/api/jobs/${job.id}/submissions/${latestSub.id}`, { status: 'REJECTED' });
            alert('Requested changes. The job status has been moved back to In Progress.');
            NexusNavigation.go('clientWorkspace', { job_id: job.id });
          } catch (e) {
            alert(e.message);
            rejectBtn.disabled = false;
            rejectBtn.textContent = 'Request Changes';
          }
        });
      }
    } catch (error) {
      if (main) state(main, error.message, true);
    }
  }

  /* ==========================================================================
     4. PAYMENT SCREENS (CLIENT & STUDENT)
     ========================================================================== */
  async function loadPaymentScreen(isClient = false) {
    const jobId = new URLSearchParams(location.search).get('job_id');
    const main = document.querySelector('main');
    if (!uuid(jobId)) {
      if (main) state(main, 'A valid job ID is required to view payment status.', true);
      return;
    }

    try {
      const res = await NexusApi.get(`/api/jobs/${jobId}/payment`);
      const job = res.job;
      const payment = res.payment || { amount: job.budget, transaction_state: 'PENDING' };
      const isCompleted = payment.transaction_state === 'COMPLETED' || job.job_state === 'COMPLETED' || job.job_state === 'RATED';

      if (main) {
        main.innerHTML = `
          <div class="max-w-2xl mx-auto px-4 py-8 space-y-6">
            <nav class="flex items-center gap-2 text-text-secondary text-body-md mb-2">
              <a class="hover:text-primary transition-colors" href="${isClient ? NexusNavigation.url('clientWorkspace', { job_id: job.id }) : NexusNavigation.url('studentWorkspace', { job_id: job.id })}">Workspace</a>
              <span class="material-symbols-outlined text-[16px]">chevron_right</span>
              <span class="text-text-primary">Payment & Completion</span>
            </nav>

            <div class="bg-surface border border-border p-8 rounded-xl text-center space-y-4">
              <div class="w-16 h-16 rounded-full ${isCompleted ? 'bg-primary/20 text-primary' : 'bg-yellow-500/20 text-yellow-500'} flex items-center justify-center mx-auto">
                <span class="material-symbols-outlined text-4xl">${isCompleted ? 'verified' : 'hourglass_top'}</span>
              </div>
              <h1 class="font-headline-lg text-headline-lg text-text-primary">${isCompleted ? 'Payment Completed ✓' : 'Payment Ready for Release'}</h1>
              <p class="text-text-secondary font-body-md">${isCompleted ? 'Funds have been credited to the student freelancer account.' : 'The work has been accepted. Confirm payment release to conclude the contract.'}</p>

              <div class="bg-background border border-border rounded-lg p-6 max-w-md mx-auto my-6 space-y-3 font-body-md">
                <div class="flex justify-between text-text-secondary">
                  <span>Project Budget</span>
                  <span class="text-text-primary font-semibold">${money(job.budget)}</span>
                </div>
                <div class="flex justify-between text-text-secondary">
                  <span>Platform Fee (0%)</span>
                  <span class="text-text-primary">₹0.00</span>
                </div>
                <div class="border-t border-border pt-3 flex justify-between font-bold text-lg">
                  <span class="text-text-primary">Total Amount</span>
                  <span class="text-primary">${money(payment.amount || job.budget)}</span>
                </div>
              </div>

              ${isClient && !isCompleted ? `
                <div class="pt-4">
                  <button class="bg-primary text-background font-label-md font-bold px-8 py-3.5 rounded-lg hover:bg-surface-tint inline-flex items-center gap-2 text-base shadow-[0_0_20px_rgba(78,222,163,0.3)]" id="release-payment-btn">
                    <span class="material-symbols-outlined">payments</span>
                    <span>Confirm & Release Payment</span>
                  </button>
                </div>
              ` : ''}

              ${isCompleted ? `
                <div class="pt-4 flex justify-center gap-4">
                  <a class="bg-primary text-background font-label-md font-bold px-6 py-3 rounded-lg hover:bg-surface-tint inline-flex items-center gap-2" href="${isClient ? NexusNavigation.url('clientRating', { job_id: job.id }) : NexusNavigation.url('studentRating', { job_id: job.id })}">
                    <span class="material-symbols-outlined text-sm">star</span>
                    <span>Rate & Leave Review</span>
                  </a>
                  <a class="border border-border text-text-primary font-label-md px-6 py-3 rounded-lg hover:bg-surface-container" href="${isClient ? NexusNavigation.url('clientJobs') : NexusNavigation.url('studentDashboard')}">
                    Return to Dashboard
                  </a>
                </div>
              ` : ''}
            </div>
          </div>
        `;

        const releaseBtn = document.getElementById('release-payment-btn');
        if (releaseBtn) {
          releaseBtn.addEventListener('click', async () => {
            releaseBtn.disabled = true;
            releaseBtn.textContent = 'Processing Payment…';
            try {
              await NexusApi.post(`/api/jobs/${job.id}/payment`, { action: 'complete' });
              NexusNavigation.go('clientRating', { job_id: job.id });
            } catch (err) {
              alert(err.message);
              releaseBtn.disabled = false;
              releaseBtn.textContent = 'Confirm & Release Payment';
            }
          });
        }
      }
    } catch (error) {
      if (main) state(main, error.message, true);
    }
  }

  /* ==========================================================================
     5. RATING SCREENS (CLIENT & STUDENT)
     ========================================================================== */
  async function loadRatingScreen(isClient = false) {
    const jobId = new URLSearchParams(location.search).get('job_id');
    const main = document.querySelector('main');
    if (!uuid(jobId)) {
      if (main) state(main, 'A valid job ID is required to submit a rating.', true);
      return;
    }

    try {
      const res = await NexusApi.get(`/api/jobs/${jobId}`);
      const job = res.job;
      const otherUser = isClient ? (job.selected_student || {}) : (job.job_provider || {});
      const otherName = otherUser.name || otherUser.username || (isClient ? 'Student' : 'Client');

      if (main) {
        main.innerHTML = `
          <div class="max-w-xl mx-auto px-4 py-8 space-y-6">
            <div class="bg-surface border border-border p-8 rounded-xl text-center space-y-6">
              <div>
                <h1 class="font-headline-lg text-headline-lg text-text-primary">Rate & Review</h1>
                <p class="text-text-secondary font-body-md mt-1">How was your experience working with <strong class="text-text-primary">${escape(otherName)}</strong> on "${escape(job.title)}"?</p>
              </div>

              <form class="space-y-6" id="rating-form">
                <!-- Interactive Star Rating -->
                <div class="flex justify-center items-center gap-2" id="star-container">
                  ${[1, 2, 3, 4, 5].map(val => `
                    <button type="button" class="star-btn text-yellow-400 text-3xl hover:scale-110 transition-transform focus:outline-none" data-value="${val}">
                      <span class="material-symbols-outlined text-4xl" style="font-variation-settings: 'FILL' 1;">star</span>
                    </button>
                  `).join('')}
                </div>
                <input type="hidden" id="rating-score" value="5"/>

                <div class="space-y-2 text-left">
                  <label class="block text-text-primary font-body-md font-semibold" for="review-content">Feedback & Comments (Optional)</label>
                  <textarea class="w-full bg-background border border-border rounded-lg p-4 text-text-primary font-body-md focus:outline-none focus:border-primary min-h-[120px]" id="review-content" placeholder="Share your feedback on communication, quality of work, and timeliness…"></textarea>
                </div>

                <div class="pt-2 flex gap-4">
                  <button class="bg-primary text-background font-label-md font-bold py-3 px-6 rounded-lg hover:bg-surface-tint flex-1" type="submit" id="rating-submit-btn">Submit Rating</button>
                  <a class="border border-border text-text-primary font-label-md font-semibold py-3 px-6 rounded-lg hover:bg-surface-container text-center" href="${isClient ? NexusNavigation.url('clientJobs') : NexusNavigation.url('studentDashboard')}">Skip</a>
                </div>
              </form>
            </div>
          </div>
        `;

        const stars = [...document.querySelectorAll('.star-btn')];
        const ratingInput = document.getElementById('rating-score');
        const updateStars = (val) => {
          ratingInput.value = val;
          stars.forEach((s, idx) => {
            const span = s.querySelector('span');
            span.style.fontVariationSettings = (idx + 1) <= val ? "'FILL' 1" : "'FILL' 0";
            span.className = `material-symbols-outlined text-4xl ${(idx + 1) <= val ? 'text-yellow-400' : 'text-text-secondary'}`;
          });
        };

        stars.forEach(s => s.addEventListener('click', () => updateStars(Number(s.dataset.value))));

        const rForm = document.getElementById('rating-form');
        const submitBtn = document.getElementById('rating-submit-btn');

        rForm.addEventListener('submit', async (e) => {
          e.preventDefault();
          submitBtn.disabled = true;
          submitBtn.textContent = 'Submitting…';
          try {
            await NexusApi.post(`/api/jobs/${job.id}/ratings`, {
              rating: Number(ratingInput.value || 5),
              review_content: document.getElementById('review-content').value.trim()
            });
            main.innerHTML = `
              <div class="max-w-md mx-auto py-16 text-center bg-surface border border-border rounded-xl p-8 space-y-4">
                <div class="w-16 h-16 rounded-full bg-primary/20 text-primary flex items-center justify-center mx-auto">
                  <span class="material-symbols-outlined text-4xl">thumb_up</span>
                </div>
                <h2 class="font-headline-lg text-text-primary">Thank You for Your Feedback!</h2>
                <p class="text-text-secondary font-body-md">Your rating has been saved and helps strengthen the NEXUS community.</p>
                <div class="pt-4">
                  <a class="bg-primary text-background font-label-md px-6 py-3 rounded-lg font-bold inline-block hover:bg-surface-tint" href="${isClient ? NexusNavigation.url('clientJobs') : NexusNavigation.url('studentDashboard')}">Return to Dashboard</a>
                </div>
              </div>
            `;
          } catch (err) {
            alert(err.message);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Rating';
          }
        });
      }
    } catch (error) {
      if (main) state(main, error.message, true);
    }
  }

  /* ==========================================================================
     6. REPORTS & DISPUTES (nexus_report_raise_dispute_desktop)
     ========================================================================== */
  function loadReportDispute() {
    const jobId = new URLSearchParams(location.search).get('job_id');
    const form = document.querySelector('form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const reasonInput = form.querySelector('input[name="reason"], select[name="reason"]') || form.querySelector('input, select');
      const detailsInput = form.querySelector('textarea');
      const reason = reasonInput ? reasonInput.value : 'General Issue';
      const details = detailsInput ? detailsInput.value : 'Dispute filed';

      try {
        if (uuid(jobId)) {
          await NexusApi.post(`/api/jobs/${jobId}/disputes`, { issue: reason, details });
        } else {
          await NexusApi.post('/api/reports', { reason, details, reported_job_id: jobId || undefined });
        }
        alert('Report/Dispute submitted successfully to the administrator.');
        history.back();
      } catch (err) {
        alert(err.message);
      }
    });
  }

  /* ==========================================================================
     7. INITIALIZATION ON DOM READY
     ========================================================================== */
  document.addEventListener('DOMContentLoaded', async () => {
    const user = await NexusAuth.restore();
    if (!user) return;
    const isClient = user.role === 'CLIENT';

    if (page() === 'studentWorkspace') loadWorkspace(false);
    if (page() === 'clientWorkspace') loadWorkspace(true);
    if (page() === 'submitWork') loadSubmitWork();
    if (page() === 'clientReview') loadClientReview();
    if (page() === 'clientPayment') loadPaymentScreen(true);
    if (page() === 'studentPayment') loadPaymentScreen(false);
    if (page() === 'clientRating') loadRatingScreen(true);
    if (page() === 'studentRating') loadRatingScreen(false);
    if (page() === 'report') loadReportDispute();
  });
})();
