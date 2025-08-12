async function postJSON(url, data){
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if(!r.ok){
    const t = await r.text();
    throw new Error(`Request failed: ${r.status} ${t}`);
  }
  return await r.json();
}

const form = document.getElementById('ask-form');
const result = document.getElementById('result');
const answer = document.getElementById('answer');
const confidence = document.getElementById('confidence');
const reasons = document.getElementById('reasons');
const citations = document.getElementById('citations');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = {
    question: document.getElementById('question').value,
    district: document.getElementById('district').value || null,
    crop: document.getElementById('crop').value || null,
    lang: document.getElementById('lang').value || 'en'
  };
  try{
    const res = await postJSON('/ask', data);
    result.classList.remove('hidden');
    answer.textContent = res.answer || '';
    confidence.textContent = (res.confidence != null ? res.confidence.toFixed(2): '');
    reasons.innerHTML = '';
    (res.reasons || []).forEach(r => {
      const li = document.createElement('li'); li.textContent = r; reasons.appendChild(li);
    });
    citations.innerHTML = '';
    (res.citations || []).forEach(c => {
      const li = document.createElement('li');
      const src = c.source || 'source';
      const ds = c.dataset || 'dataset';
      if(c.url){
        const a = document.createElement('a'); a.href = c.url; a.target = '_blank'; a.rel = 'noopener'; a.textContent = `${ds} (${src})`;
        li.appendChild(a);
      } else {
        li.textContent = `${ds} (${src})`;
      }
      citations.appendChild(li);
    });
  }catch(err){
    result.classList.remove('hidden');
    answer.textContent = `Error: ${err.message}`;
    confidence.textContent = '';
    reasons.innerHTML = '';
    citations.innerHTML = '';
  }
});