const input = document.querySelector('#question');
const result = document.querySelector('#result');
const ask = document.querySelector('#ask');
const history = [];
document.querySelectorAll('.examples button').forEach(b => b.onclick = () => { input.value = b.textContent; run(); });
ask.onclick = run; input.addEventListener('keydown', e => { if (e.key === 'Enter') run(); });
async function run() {
  const question = input.value.trim(); if (!question) return;
  ask.disabled = true; ask.textContent = 'Reading…'; result.className = 'result loading'; result.innerHTML = '<p>Searching the rulebook…</p>';
  try {
    const r = await fetch('/ask', {method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify({question})}); const data = await r.json();
    result.className = `result ${data.status}`;
    const label = data.status === 'answered' ? 'Answered with citations' : data.status === 'conflict' ? 'Conflict detected' : 'Not covered';
    result.innerHTML = `<div class="status">${label}</div><h2>${data.answer}</h2>${data.citations.length ? `<div class="citations">${data.citations.map(c => `<article><div><strong>${c.section}</strong><span>${c.source}</span></div><b>${Math.round(c.similarity*100)}% match</b><p>${c.excerpt}</p></article>`).join('')}</div>` : '<p class="quiet">No citations were returned because the corpus is silent on this.</p>'}`;
    history.unshift({question, status:data.status, answer:data.answer, citations:data.citations, timestamp:new Date().toISOString()});
  } catch { result.className = 'result conflict'; result.innerHTML = '<h2>Could not reach the local service.</h2>'; }
  finally { ask.disabled = false; ask.textContent = 'Ask'; }
}
async function loadAudit() {
  try {
    const audit = await (await fetch('/audit')).json();
    document.querySelector('#metrics').innerHTML = `<div><b>${audit.corpus_words.toLocaleString()}</b><span>words indexed</span></div><div><b>${audit.passages_indexed}</b><span>evidence passages</span></div><div><b>${Object.keys(audit.sources).length}</b><span>source files</span></div><div><b>${audit.planted_conflicts.length}</b><span>conflicts surfaced</span></div>`;
    document.querySelector('#abstentions').textContent = audit.abstention_test_questions;
    document.querySelector('#conflicts').innerHTML = audit.planted_conflicts.map(c => `<button class="conflict-test">${c.question}<small>${c.sections.join(' ↔ ')}</small></button>`).join('');
    document.querySelectorAll('.conflict-test').forEach(b => b.onclick = () => { input.value = b.childNodes[0].textContent.trim(); run(); window.scrollTo({top:0,behavior:'smooth'}); });
  } catch { document.querySelector('#metrics').innerHTML = '<p>Audit data is unavailable. Start the local API to inspect the corpus.</p>'; }
}
document.querySelector('#export').onclick = () => {
  const blob = new Blob([JSON.stringify(history, null, 2)], {type:'application/json'});
  const link = Object.assign(document.createElement('a'), {href:URL.createObjectURL(blob), download:'rulebook-lens-session.json'}); link.click(); URL.revokeObjectURL(link.href);
};
loadAudit();
