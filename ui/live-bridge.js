/**
 * Live backend bridge — must load AFTER the main page script.
 */
(function () {
  if (!window.AGENTTHREE_LIVE) return;
  const API = window.AGENTTHREE_API || '';

  function $(id) {
    return document.getElementById(id);
  }

  function status(msg, color) {
    const el = $('live-status');
    if (el) {
      el.textContent = msg;
      el.style.color = color || 'var(--soft)';
    }
  }

  function mountChrome() {
    const run = document.querySelector('#run .banner');
    if (!run || $('mode-live')) return;

    const modeRow = document.createElement('div');
    modeRow.className = 'ctrl';
    modeRow.style.margin = '10px 0 0';
    modeRow.innerHTML =
      '<button type="button" class="btn primary" id="mode-live">Live</button>' +
      '<button type="button" class="btn" id="mode-sim">Simulation</button>' +
      '<span class="label" id="live-status" style="margin-left:8px">checking…</span>';

    const banner = document.createElement('div');
    banner.className = 'banner';
    banner.id = 'live-banner';
    banner.style.margin = '12px 0 0';
    banner.innerHTML =
      '<b>Live backend.</b> Talking to ADK/Gemini + MCP at <span class="mono">' +
      (API || location.origin) +
      '</span>. Use <b>Simulation</b> for the in-browser-only demo.';

    run.parentNode.insertBefore(modeRow, run);
    run.parentNode.insertBefore(banner, run);

    $('mode-live').addEventListener('click', () => setMode(true));
    $('mode-sim').addEventListener('click', () => setMode(false));
  }

  let live = true;
  let currentCaseId = null;

  function setMode(isLive) {
    live = isLive;
    const a = $('mode-live');
    const b = $('mode-sim');
    if (a && b) {
      a.classList.toggle('primary', live);
      b.classList.toggle('primary', !live);
    }
    const banner = $('live-banner');
    if (banner) banner.querySelector('b').textContent = live ? 'Live backend.' : 'Simulation.';
  }

  async function refreshHealth() {
    try {
      const j = await fetch(API + '/api/health').then((r) => r.json());
      status(
        (j.demoMode ? 'fixtures' : 'Gemini · ' + j.model) + ' · ' + j.project,
        j.hasApiKey && !j.demoMode ? 'var(--lime)' : 'var(--amber)'
      );
    } catch (e) {
      status('backend offline', 'var(--red)');
    }
  }

  function applyAgentState(st) {
    if (typeof S === 'undefined' || !S) return;
    S.agent = Object.assign(S.agent || {}, st || {});
    if (typeof renderPipeline === 'function') renderPipeline();
  }

  function handleLiveMsg(msg) {
    if (typeof S === 'undefined' || !S) return;
    if (msg.contextId) {
      S.ctx = msg.contextId;
      if ($('ctxid')) $('ctxid').textContent = 'contextId · ' + S.ctx;
    }
    if (msg.traceId) S.traceId = msg.traceId;
    if (msg.agentState) applyAgentState(msg.agentState);
    if (msg.type === 'event' && msg.event) {
      S.events.push(msg.event);
      S.steps = msg.steps || S.events.length;
      if (msg.tokens != null) S.tokens = msg.tokens;
      if (msg.audit) S.audit.push(msg.audit);
      if (typeof renderProgress === 'function') renderProgress();
      if (typeof renderInspector === 'function') renderInspector();
    }
    if (msg.type === 'tool' && msg.tool) {
      S.tools.push(msg.tool);
      if (typeof renderInspector === 'function') renderInspector();
    }
    if (msg.type === 'a2a' && msg.a2a) {
      S.a2a.push(msg.a2a);
      if (typeof renderInspector === 'function') renderInspector();
    }
    if (msg.intake) S.x = msg.intake;
    if (msg.pol) S.pol = msg.pol;
    if (msg.cds) S.cds = msg.cds;
    if (msg.faults) S.faults = msg.faults;
    if (msg.result) hydrateFromCase(msg.result);
    if (typeof renderPipeline === 'function') renderPipeline();
    if (typeof renderInspector === 'function') renderInspector();
  }

  function hydrateFromCase(c) {
    if (!c || typeof S === 'undefined' || !S) return;
    S.ctx = c.contextId || S.ctx;
    S.traceId = c.traceId || S.traceId;
    if (c.events) S.events = c.events;
    if (c.tools) S.tools = c.tools;
    if (c.a2a) S.a2a = c.a2a;
    if (c.spans) S.spans = c.spans;
    if (c.audit) S.audit = c.audit;
    if (c.agent) S.agent = c.agent;
    if (c.intake) S.x = c.intake;
    if (c.pol) S.pol = c.pol;
    if (c.cds) S.cds = c.cds;
    if (c.faults) S.faults = c.faults;
    if (c.fault) S.fault = c.fault;
    if (c.tokens != null) S.tokens = c.tokens;
    S.steps = (S.events && S.events.length) || S.steps;
    if (S.ctx && $('ctxid')) $('ctxid').textContent = 'contextId · ' + S.ctx;
    if (typeof renderPipeline === 'function') renderPipeline();
    if (typeof renderProgress === 'function') renderProgress();
    if (typeof renderInspector === 'function') renderInspector();
  }

  async function waitForCase(caseId, timeoutMs) {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      const r = await fetch(API + '/api/cases/' + caseId);
      if (r.ok) return r.json();
      await new Promise((res) => setTimeout(res, 400));
    }
    throw new Error('Timed out waiting for case result');
  }

  async function humanGateLive(my) {
    if (typeof setAgent === 'function') setAgent('human', 'waiting');
    itab = 'review';
    document.querySelectorAll('#itabs button').forEach((x) =>
      x.setAttribute('aria-selected', x.dataset.i === 'review')
    );
    if (typeof renderInspector === 'function') renderInspector();

    const dec = await new Promise((r) => {
      gateResolve = r;
    });
    if (my !== runId) return;

    const sealed = await fetch(API + '/api/cases/' + currentCaseId + '/decision', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: dec.action || 'info',
        reviewer: dec.reviewer || ($('rv-name') && $('rv-name').value) || 'Reviewer',
        note: dec.note || ($('rv-note') && $('rv-note').value) || '',
      }),
    }).then((r) => r.json());

    S.decision = sealed.decision || dec;
    S.audit = sealed.audit || S.audit;
    if (typeof setAgent === 'function') setAgent('human', 'done');
    running = false;
    const btn = $('b-run');
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Run again';
    }
    itab = 'audit';
    document.querySelectorAll('#itabs button').forEach((x) =>
      x.setAttribute('aria-selected', x.dataset.i === 'audit')
    );
    if (typeof renderInspector === 'function') renderInspector();
  }

  async function runLive() {
    if (typeof running === 'undefined') {
      status('page script not ready — hard refresh', 'var(--red)');
      return;
    }
    if (running) return;

    try {
      resetRun();
      running = true;
      const my = runId;
      S = freshState();
      S.fault = ($('f-fault') && $('f-fault').value) || 'none';

      const btn = $('b-run');
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Running (live)…';
      }
      if ($('ctxid')) $('ctxid').textContent = 'contextId · starting…';
      status('submitting case…', 'var(--cyan)');
      if (typeof renderPipeline === 'function') renderPipeline();

      const body = {
        patient: $('f-name').value,
        dob: $('f-dob').value,
        member: $('f-member').value,
        payer: $('f-payer').value,
        cpt: $('f-cpt').value,
        icd: $('f-icd').value,
        note: $('f-note').value,
        fault: ($('f-fault') && $('f-fault').value) || 'none',
      };

      const createdRes = await fetch(API + '/api/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const created = await createdRes.json();
      if (!createdRes.ok || !created.caseId) {
        throw new Error(created.detail ? JSON.stringify(created.detail) : 'failed to create case');
      }
      currentCaseId = created.caseId;
      status('streaming · ' + currentCaseId.slice(0, 8) + '…', 'var(--cyan)');

      await new Promise((resolve, reject) => {
        const es = new EventSource(API + created.streamUrl);
        let settled = false;
        const finish = (fn, arg) => {
          if (settled) return;
          settled = true;
          es.close();
          fn(arg);
        };
        es.onmessage = (ev) => {
          if (my !== runId) return finish(resolve);
          try {
            const msg = JSON.parse(ev.data);
            handleLiveMsg(msg);
            if (msg.type === 'done') finish(resolve);
            if (msg.type === 'error') finish(reject, new Error(msg.message || 'run failed'));
          } catch (err) {
            finish(reject, err);
          }
        };
        es.onerror = () => finish(resolve);
      });

      const finalCase = await waitForCase(currentCaseId, 120000);
      hydrateFromCase(finalCase);
      status('awaiting human review', 'var(--amber)');
      await humanGateLive(my);
      status('complete', 'var(--lime)');
    } catch (e) {
      console.error(e);
      status('error: ' + (e && e.message ? e.message : e), 'var(--red)');
      alert('Live run failed: ' + (e && e.message ? e.message : e));
      running = false;
      const btn = $('b-run');
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Submit request';
      }
    }
  }

  function patchRunButton() {
    const btn = $('b-run');
    if (!btn) {
      status('Submit button not found', 'var(--red)');
      return;
    }
    // Replace node to drop the original runSim listener, then bind ours.
    const next = btn.cloneNode(true);
    btn.parentNode.replaceChild(next, btn);
    next.addEventListener('click', function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      if (live) {
        runLive();
      } else if (typeof runSim === 'function') {
        runSim();
      }
    });
    status('ready — press Submit request', 'var(--lime)');
  }

  function boot() {
    mountChrome();
    setMode(true);
    patchRunButton();
    refreshHealth();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    // Main page script is above us; give it a tick to finish.
    setTimeout(boot, 0);
  }
})();
