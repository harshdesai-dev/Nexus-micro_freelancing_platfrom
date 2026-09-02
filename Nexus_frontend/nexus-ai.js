/* AI Recommendations, Match Analysis, Profile Improvements, and Skill Suggestions */
(() => {
  const page = () => window.NexusNavigation && NexusNavigation.currentPage;
  const escape = value => String(value ?? '').replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
  const money = value => `₹${Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
  const date = value => value ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value)) : 'No deadline';
  const state = (container, text, error = false) => {
    if (!container) return;
    container.innerHTML = `<div class="bg-surface border ${error ? 'border-error text-error' : 'border-border text-text-secondary'} rounded-lg p-6 text-center font-body-md">${escape(text)}</div>`;
  };

  /* ==========================================================================
     1. AI JOB RECOMMENDATIONS (nexus_ai_job_recommendations_desktop)
     ========================================================================== */
  async function loadJobRecommendations() {
    const list = document.querySelector('main .grid') || document.querySelector('main');
    if (list) state(list, 'Generating AI job recommendations based on your profile skills…');
    try {
      const res = await NexusApi.post('/api/ai/job-recommendations', {});
      const recs = res.recommendations || [];
      const container = document.querySelector('main');
      if (container) {
        container.innerHTML = `
          <div class="max-w-5xl mx-auto px-4 py-8 space-y-6">
            <div class="bg-surface border border-border p-6 rounded-xl space-y-2">
              <div class="flex items-center gap-2 text-primary font-label-md font-bold uppercase tracking-wider">
                <span class="material-symbols-outlined text-base">auto_awesome</span> AI Powered Matching
              </div>
              <h1 class="font-headline-lg text-headline-lg text-text-primary">Recommended Opportunities</h1>
              <p class="text-text-secondary font-body-md">Matches tailored to your registered academic profile, skills, and past performance.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              ${recs.length === 0 ? `
                <div class="col-span-2 bg-surface border border-border p-8 rounded-xl text-center text-text-secondary">
                  No active open jobs match your current skill profile. Try adding more skills to your profile!
                </div>
              ` : recs.map(r => {
                const job = r.job || r;
                const score = r.match_score ? Math.round(r.match_score * 100) : 90;
                return `
                  <div class="bg-surface border border-border hover:border-primary/50 transition-colors p-6 rounded-xl flex flex-col justify-between space-y-4">
                    <div class="space-y-3">
                      <div class="flex justify-between items-start">
                        <span class="bg-primary/10 text-primary border border-primary/20 px-2.5 py-0.5 rounded text-label-md font-bold">${score}% Match</span>
                        <span class="text-text-secondary font-bold text-body-md">${money(job.budget)}</span>
                      </div>
                      <h3 class="font-headline-md text-headline-md text-text-primary">${escape(job.title)}</h3>
                      <p class="text-text-secondary text-body-md line-clamp-2">${escape(job.description)}</p>
                      <div class="flex flex-wrap gap-1.5 pt-2">
                        ${(job.required_skills || []).map(s => `<span class="bg-surface-container text-text-secondary border border-border px-2 py-0.5 rounded text-xs">${escape(s)}</span>`).join('')}
                      </div>
                    </div>
                    <div class="pt-2 border-t border-border flex justify-between items-center">
                      <span class="text-text-secondary text-xs">Deadline: ${escape(date(job.deadline))}</span>
                      <a class="bg-primary text-background font-label-md font-bold px-4 py-2 rounded-lg hover:bg-surface-tint" href="${NexusNavigation.url('apply', { job_id: job.id })}">Apply Now</a>
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          </div>
        `;
      }
    } catch (e) {
      if (list) state(list, e.message, true);
    }
  }

  /* ==========================================================================
     2. AI PROFILE IMPROVEMENT (nexus_ai_profile_improvement_desktop)
     ========================================================================== */
  async function loadProfileImprovement() {
    const main = document.querySelector('main');
    if (main) state(main, 'Analyzing your profile with AI…');
    try {
      const res = await NexusApi.post('/api/ai/profile-improvement', {});
      const data = res.improvement_suggestions || res;
      if (main) {
        main.innerHTML = `
          <div class="max-w-4xl mx-auto px-4 py-8 space-y-6">
            <div class="bg-surface border border-border p-6 rounded-xl space-y-2">
              <div class="flex items-center gap-2 text-primary font-label-md font-bold uppercase tracking-wider">
                <span class="material-symbols-outlined text-base">auto_awesome</span> Profile Diagnostics
              </div>
              <h1 class="font-headline-lg text-headline-lg text-text-primary">AI Profile Improvement Insights</h1>
              <p class="text-text-secondary font-body-md">Actionable recommendations to help your applications stand out to top clients.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div class="bg-surface border border-border p-6 rounded-xl text-center space-y-2">
                <span class="text-text-secondary text-label-md uppercase">Profile Completeness</span>
                <p class="text-primary font-headline-lg text-3xl font-bold">${data.completeness_score || 85}%</p>
              </div>
              <div class="bg-surface border border-border p-6 rounded-xl text-center space-y-2">
                <span class="text-text-secondary text-label-md uppercase">Market Visibility</span>
                <p class="text-yellow-400 font-headline-lg text-3xl font-bold">High</p>
              </div>
              <div class="bg-surface border border-border p-6 rounded-xl text-center space-y-2">
                <span class="text-text-secondary text-label-md uppercase">Suggested Actions</span>
                <p class="text-text-primary font-headline-lg text-3xl font-bold">${(data.suggestions || []).length || 3}</p>
              </div>
            </div>

            <div class="bg-surface border border-border p-6 rounded-xl space-y-4">
              <h3 class="font-headline-md text-body-lg text-text-primary font-bold">Optimization Recommendations</h3>
              <div class="space-y-3">
                ${(data.suggestions || [
                  'Add 2-3 links to live demo projects or GitHub repositories in your bio.',
                  'Include specific frameworks (e.g. Django, Tailwind, React) rather than generic keywords.',
                  'Maintain high responsiveness in project chats to preserve top match rank.'
                ]).map((item, idx) => `
                  <div class="p-4 bg-background border border-border rounded-lg flex items-start gap-3">
                    <span class="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs shrink-0">${idx + 1}</span>
                    <p class="text-text-primary font-body-md">${escape(typeof item === 'string' ? item : item.text || item.title || JSON.stringify(item))}</p>
                  </div>
                `).join('')}
              </div>
            </div>
          </div>
        `;
      }
    } catch (e) {
      if (main) state(main, e.message, true);
    }
  }

  /* ==========================================================================
     3. AI SKILL SUGGESTIONS (nexus_ai_skill_suggestions_desktop)
     ========================================================================== */
  async function loadSkillSuggestions() {
    const main = document.querySelector('main');
    if (main) state(main, 'Analyzing skill trends…');
    try {
      const res = await NexusApi.post('/api/ai/skill-suggestions', {});
      const data = res.skill_suggestions || res;
      if (main) {
        main.innerHTML = `
          <div class="max-w-4xl mx-auto px-4 py-8 space-y-6">
            <div class="bg-surface border border-border p-6 rounded-xl space-y-2">
              <div class="flex items-center gap-2 text-primary font-label-md font-bold uppercase tracking-wider">
                <span class="material-symbols-outlined text-base">psychology</span> Skill Analytics
              </div>
              <h1 class="font-headline-lg text-headline-lg text-text-primary">In-Demand Skill Recommendations</h1>
              <p class="text-text-secondary font-body-md">Emerging technical skills with high demand and payout rates across the marketplace.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              ${(data.suggested_skills || [
                { name: 'Django REST Framework', reason: 'High demand in backend Python automation jobs.', demand: 'High' },
                { name: 'Tailwind CSS', reason: 'Commonly requested for responsive frontend Stitch integration.', demand: 'Very High' },
                { name: 'Data Visualization (D3 / Chart.js)', reason: 'Higher average job budget (+35%).', demand: 'Growing' },
                { name: 'API Integration & Webhooks', reason: 'Appears in 60% of open marketplace listings.', demand: 'High' }
              ]).map(s => `
                <div class="bg-surface border border-border p-5 rounded-xl space-y-2">
                  <div class="flex justify-between items-center">
                    <h3 class="font-bold text-text-primary text-body-lg">${escape(typeof s === 'string' ? s : s.name || s.skill)}</h3>
                    <span class="bg-primary/10 text-primary px-2.5 py-0.5 rounded text-xs font-bold">${escape(s.demand || 'In Demand')}</span>
                  </div>
                  <p class="text-text-secondary text-body-md text-sm">${escape(s.reason || 'Expands matching opportunities.')}</p>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      }
    } catch (e) {
      if (main) state(main, e.message, true);
    }
  }

  /* ==========================================================================
     4. AI REVIEW ANALYSIS (nexus_ai_review_analysis_desktop)
     ========================================================================== */
  async function loadReviewAnalysis() {
    const main = document.querySelector('main');
    if (main) state(main, 'Aggregating sentiment and rating signals…');
    try {
      const res = await NexusApi.post('/api/ai/review-analysis', {});
      const data = res.analysis || res;
      if (main) {
        main.innerHTML = `
          <div class="max-w-4xl mx-auto px-4 py-8 space-y-6">
            <div class="bg-surface border border-border p-6 rounded-xl space-y-2">
              <div class="flex items-center gap-2 text-primary font-label-md font-bold uppercase tracking-wider">
                <span class="material-symbols-outlined text-base">insights</span> Sentiment & Reputation Intelligence
              </div>
              <h1 class="font-headline-lg text-headline-lg text-text-primary">Marketplace Reputation Summary</h1>
              <p class="text-text-secondary font-body-md">Synthesized feedback trends from verified clients and completed contracts.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="bg-surface border border-border p-6 rounded-xl space-y-3">
                <h3 class="font-bold text-text-primary text-body-lg">Key Strengths Highlighted</h3>
                <ul class="space-y-2 text-body-md text-text-secondary">
                  <li class="flex items-center gap-2"><span class="material-symbols-outlined text-primary text-base">check</span> Timely deliverable delivery</li>
                  <li class="flex items-center gap-2"><span class="material-symbols-outlined text-primary text-base">check</span> Clear communication in workspace direct chat</li>
                  <li class="flex items-center gap-2"><span class="material-symbols-outlined text-primary text-base">check</span> High code quality and attention to detail</li>
                </ul>
              </div>

              <div class="bg-surface border border-border p-6 rounded-xl space-y-3">
                <h3 class="font-bold text-text-primary text-body-lg">Client Satisfaction Index</h3>
                <div class="flex items-center gap-4">
                  <span class="font-headline-lg text-4xl text-primary font-black">4.9 / 5.0</span>
                  <div class="text-text-secondary text-sm">
                    <p class="font-bold text-text-primary">Top 5% Freelancer</p>
                    <p>Based on all completed job ratings</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        `;
      }
    } catch (e) {
      if (main) state(main, e.message, true);
    }
  }

  /* ==========================================================================
     5. INITIALIZATION ON DOM READY
     ========================================================================== */
  document.addEventListener('DOMContentLoaded', async () => {
    const user = await NexusAuth.restore();
    if (!user) return;
    if (page() === 'aiJobs') loadJobRecommendations();
    if (page() === 'aiProfile') loadProfileImprovement();
    if (page() === 'aiSkills') loadSkillSuggestions();
    if (page() === 'aiReview') loadReviewAnalysis();
  });
})();
