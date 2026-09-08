const input = document.querySelector('#question');
const result = document.querySelector('#result');
const ask = document.querySelector('#ask');
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
  } catch { result.className = 'result conflict'; result.innerHTML = '<h2>Could not reach the local service.</h2>'; }
  finally { ask.disabled = false; ask.textContent = 'Ask'; }
}
