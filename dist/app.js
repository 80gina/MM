const screens = [...document.querySelectorAll('.screen')];
const navButtons = [...document.querySelectorAll('.bottom-nav [data-go]')];
const backButton = document.querySelector('.back-button');
const miniBrand = document.querySelector('.mini-brand');
const screenTitle = document.querySelector('.screen-title');
const titles = { home: '', diary: '감정 일기', analysis: 'AI 감정 분석', coach: '맞춤형 힐링 코치', chat: '마음 친구', records: '나의 마음 기록' };
let currentScreen = 'home';
let historyStack = ['home'];
let selectedTags = [];
let selectedMood = { name: '걱정되는', color: '#ec846f' };
let lastAnalysis = null;
let missionTimer = null;
let breathTimer = null;
let memoryToken = null;
try { memoryToken = localStorage.getItem('mindily-memory-token'); } catch (_) {}

const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));

function showScreen(name, push = true) {
  if (!titles.hasOwnProperty(name)) return;
  screens.forEach((screen) => screen.classList.toggle('active', screen.dataset.screen === name));
  navButtons.forEach((button) => button.classList.toggle('active', button.dataset.go === (name === 'analysis' || name === 'chat' ? (name === 'analysis' ? 'diary' : 'coach') : name)));
  currentScreen = name;
  if (push && historyStack.at(-1) !== name) historyStack.push(name);
  const isHome = name === 'home';
  miniBrand.hidden = !isHome;
  screenTitle.hidden = isHome;
  screenTitle.textContent = titles[name];
  backButton.hidden = isHome || ['diary', 'coach', 'records'].includes(name);
  document.querySelector(`[data-screen="${name}"]`).scrollTop = 0;
}

document.addEventListener('click', (event) => {
  const go = event.target.closest('[data-go]');
  if (go) showScreen(go.dataset.go);
  const opener = event.target.closest('[data-open-dialog]');
  if (opener) document.getElementById(opener.dataset.openDialog)?.showModal();
  const toastTarget = event.target.closest('[data-toast]');
  if (toastTarget) toast(toastTarget.dataset.toast);
  if (event.target.closest('[data-start-breath]')) startBreathing();
});

document.getElementById('feedback-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const satisfaction = document.querySelector('input[name="satisfaction"]:checked')?.value;
  const consent = document.getElementById('feedback-consent').checked;
  if (!satisfaction || !consent) { toast('만족도와 익명 제출 동의를 확인해주세요.'); return; }
  const button = event.currentTarget.querySelector('[type="submit"]');
  if (button.disabled) return;
  button.disabled = true;
  const payload = { card_id: 'session-exit', satisfaction: Number(satisfaction),
    comment: document.getElementById('feedback-comment').value.trim() || null, consent: true };
  try {
    const response = await fetch('/api/feedback', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
    if (!response.ok) throw new Error('feedback');
    const result = await response.json();
    if (!result.saved) throw new Error('not saved');
    document.getElementById('feedback-dialog').close();
    document.getElementById('feedback-form').reset();
    toast('만족도를 저장했어요. 고마워요.');
  } catch (error) { toast('저장하지 못했어요. 입력을 보관 중이니 다시 시도해주세요.'); }
  finally { button.disabled = false; }
});

backButton.addEventListener('click', () => {
  historyStack.pop();
  showScreen(historyStack.at(-1) || 'home', false);
});

const now = new Date();
document.getElementById('today-date').textContent = new Intl.DateTimeFormat('ko-KR', { month: 'long', day: 'numeric', weekday: 'long' }).format(now);

const diaryText = document.getElementById('diary-text');
diaryText.addEventListener('input', () => document.getElementById('char-count').textContent = diaryText.value.length);

document.getElementById('emotion-tags').addEventListener('click', (event) => {
  const button = event.target.closest('[data-tag]');
  if (!button) return;
  button.classList.toggle('selected');
  selectedTags = [...document.querySelectorAll('[data-tag].selected')].map((item) => item.dataset.tag);
});

const emotionMeta = {
  불안: ['😰', '걱정되는'], 슬픔: ['😔', '지친'], 분노: ['😣', '답답한'], 기쁨: ['🙂', '기분 좋은'], 상처: ['🥺', '외로운'], 당황: ['😯', '초조한']
};

async function analyzeDiary(text, stress) {
  const response = await fetch('/api/emotions/analyze', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text, self_reported_stress: stress}),
    signal: AbortSignal.timeout(60000)
  });
  if (!response.ok) throw new Error('지금은 분석할 수 없어요. 잠시 후 다시 시도해주세요.');
  const data = await response.json();
  return {id: crypto.randomUUID(), ranked: data.labels.map(x => ({name:x.name, score:x.score})),
    model: data.model, revision: data.revision, chunks: data.chunks,
    stress, text, tags: [...selectedTags], date: new Date().toISOString(),
    detailedMood: null, confirmedMood: null};
}

document.getElementById('diary-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const text = diaryText.value.trim();
  if (!text) return toast('마음을 한 문장으로 들려주세요.');
  const stress = Number(new FormData(event.currentTarget).get('stress'));
  const button = event.currentTarget.querySelector('[type="submit"]');
  if (button.disabled) return;
  button.disabled = true; button.textContent = '마음을 읽고 있어요…';
  try {
    lastAnalysis = await analyzeDiary(text, stress);
    selectedMood = {name:'직접 골라주세요', color:'#b7bfce'};
    document.querySelectorAll('[data-mood]').forEach(x => x.classList.remove('selected'));
    renderAnalysis(); saveEntry(lastAnalysis); showScreen('analysis');
  } catch (error) {
    toast(error.name === 'TimeoutError' ? '분석 시간이 길어졌어요. 글은 그대로 있으니 다시 시도해주세요.' : '분석 서버에 연결하지 못했어요. 글은 그대로 보관 중이에요.');
  } finally { button.disabled = false; button.textContent = 'AI에게 마음 맡기기 ✨'; }
});

function renderAnalysis() {
  const top = lastAnalysis.ranked.slice(0, 3);
  document.getElementById('emotion-result').innerHTML = top.map((item) => `<div class="emotion-pill"><span aria-hidden="true">${emotionMeta[item.name][0]}</span><strong>${item.name}</strong><small>분류 점수 ${item.score.toFixed(3)}</small></div>`).join('');
  const level = lastAnalysis.stress >= 4 ? '높은' : lastAnalysis.stress === 3 ? '조금 높은' : '낮은';
  document.getElementById('analysis-summary').textContent = `직접 기록한 스트레스 ${lastAnalysis.stress}/5`;
  document.getElementById('analysis-meter').style.width = `${lastAnalysis.stress * 20}%`;
  const lead = top[0].name;
  const messages = {
    불안: '앞으로 일어날 일을 계속 대비하느라 마음이 쉬지 못한 것 같아요. 지금 당장 정답을 찾지 않아도 괜찮아요.',
    슬픔: '오늘은 에너지가 많이 소모된 날이었나 봐요. 감정을 서둘러 바꾸기보다 잠시 곁에 있어볼게요.',
    분노: '중요하게 여기는 것이 지켜지지 않아 답답함이 커진 것 같아요. 그 마음에는 이유가 있어요.',
    기쁨: '마음이 환해지는 순간이 있었군요. 그 장면을 천천히 기억해두어도 좋겠어요.',
    상처: '관계 속에서 마음이 다친 흔적이 보여요. 그 서운함을 사소하게 여기지 않아도 괜찮아요.',
    당황: '예상하지 못한 일이 마음의 리듬을 흔든 것 같아요. 천천히 상황을 다시 정리해봐요.'
  };
  document.getElementById('analysis-message').textContent = messages[lead];
  updateMoodUI();
  updateRecordUI(lastAnalysis);
  loadHealingRecommendations();
}

async function loadHealingRecommendations() {
  if (!lastAnalysis) return;
  try {
    const response = await fetch('/api/healing/recommend', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({emotion: lastAnalysis.ranked[0].name, stress: lastAnalysis.stress, minutes: 20,
        allow_location: false, memory_token: memoryToken})
    });
    if (!response.ok) throw new Error('recommendation');
    const data = await response.json();
    const list = document.querySelector('.recommend-list');
    list.innerHTML = data.cards.slice(0, 4).map((card, index) => `<article class="card recommendation ${index === 0 ? 'featured' : ''}">
      <div class="rec-icon ${index % 2 ? 'blue' : 'mint'}" aria-hidden="true">${card.kind === '음악' ? '♫' : card.kind === '감각활동' ? '◌' : '🌱'}</div>
      <div><span class="soft-chip">${index === 0 ? '1순위 추천' : escapeHtml(card.kind)}</span><h3>${escapeHtml(card.title)}</h3><p>${escapeHtml(card.description)}</p></div>
      ${card.id === 'breathing-1m' ? '<button class="secondary-button" type="button" data-start-breath>1분 시작하기</button>' : ''}
      ${card.source_url?.startsWith('https://') ? `<a class="secondary-button" href="${escapeHtml(card.source_url)}" target="_blank" rel="noopener noreferrer" aria-label="${escapeHtml(card.source_title)} 자료 새 창에서 보기">${escapeHtml(card.source_title)} ↗</a>` : ''}
    </article>`).join('');
  } catch (_) {
    // 기본 정적 추천 카드는 API 오류에도 그대로 사용할 수 있다.
  }
}

document.getElementById('save-memory').addEventListener('click', async () => {
  if (!document.getElementById('memory-consent').checked) return toast('기억 저장 동의를 먼저 확인해주세요.');
  const token = memoryToken || [...crypto.getRandomValues(new Uint8Array(32))].map(x => x.toString(16).padStart(2, '0')).join('');
  const preferred_kind = document.getElementById('preferred-kind').value;
  try {
    const response = await fetch('/api/memory', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({token, preferred_kind, consent: true})});
    if (!response.ok) throw new Error('memory');
    localStorage.setItem('mindily-memory-token', token);
    memoryToken = token;
    document.getElementById('memory-status').textContent = `${preferred_kind} 활동을 기억했어요.`;
    loadHealingRecommendations();
  } catch (_) { toast('선호를 저장하지 못했어요. 다시 시도해주세요.'); }
});

document.getElementById('delete-memory').addEventListener('click', async () => {
  if (!memoryToken) return toast('저장된 선호가 없어요.');
  try {
    const response = await fetch('/api/memory/delete', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({token: memoryToken})});
    if (!response.ok) throw new Error('delete');
    localStorage.removeItem('mindily-memory-token');
    memoryToken = null;
    document.getElementById('memory-consent').checked = false;
    document.getElementById('memory-status').textContent = '저장된 선호를 삭제했어요.';
    loadHealingRecommendations();
  } catch (_) { toast('삭제하지 못했어요. 다시 시도해주세요.'); }
});

if (memoryToken) {
  fetch('/api/memory/read', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({token: memoryToken})})
    .then(response => response.json())
    .then(data => { if (data.preferred_kind) {
      document.getElementById('preferred-kind').value = data.preferred_kind;
      document.getElementById('memory-status').textContent = `${data.preferred_kind} 활동을 기억하고 있어요.`;
    } }).catch(() => {});
}

function saveEntry(entry) {
  try {
    const records = JSON.parse(localStorage.getItem('mindily-records') || '[]');
    const existing = records.findIndex(x => x.id && x.id === entry.id);
    if (existing >= 0) records.splice(existing, 1);
    records.unshift(entry);
    localStorage.setItem('mindily-records', JSON.stringify(records.slice(0, 30)));
    return true;
  } catch (_) { toast('이 브라우저에서는 기록 저장이 안 돼요. 저장 설정을 확인해주세요.'); return false; }
}

function updateRecordUI(entry) {
  const lead = entry.ranked[0].name;
  document.getElementById('record-date').textContent = '오늘';
  document.getElementById('record-emoji').textContent = emotionMeta[lead][0];
  document.getElementById('record-mood').textContent = selectedMood.name;
  document.getElementById('record-stress').textContent = `스트레스 ${entry.stress}/5`;
  document.getElementById('record-copy').textContent = entry.text;
  document.getElementById('latest-mood').textContent = selectedMood.name;
  document.getElementById('home-coach-message').textContent = '기록한 마음을 확인했어요. 어떤 휴식이 필요한지 천천히 골라보세요.';
  const dots = document.querySelector('.stress-dots');
  dots.setAttribute('aria-label', `직접 기록한 스트레스 ${entry.stress}/5`);
  [...dots.children].forEach((dot,i) => dot.classList.toggle('off', i >= entry.stress));
}

function updateMoodUI() {
  document.getElementById('selected-detailed-mood').textContent = selectedMood.name;
  document.getElementById('mood-dot').style.background = selectedMood.color;
}

document.getElementById('mood-meter').addEventListener('click', (event) => {
  const button = event.target.closest('[data-mood]');
  if (!button) return;
  document.querySelectorAll('[data-mood]').forEach((item) => item.classList.remove('selected'));
  button.classList.add('selected');
  selectedMood = { name: button.dataset.mood, color: button.dataset.color };
});

document.getElementById('confirm-mood').addEventListener('click', () => {
  updateMoodUI();
  if (!lastAnalysis || selectedMood.name === '직접 골라주세요') return toast('먼저 마음을 선택해주세요.');
  lastAnalysis.confirmedMood = {...selectedMood};
  lastAnalysis.detailedMood = selectedMood.name;
  if (saveEntry(lastAnalysis)) { updateRecordUI(lastAnalysis); toast(`‘${selectedMood.name}’ 마음으로 기록했어요.`); }
});

const missionButton = document.getElementById('mission-button');
missionButton.addEventListener('click', () => {
  if (missionTimer) return;
  let value = 0;
  missionButton.textContent = '잠시 창밖을 바라봐요…';
  missionTimer = setInterval(() => {
    value += 10;
    document.getElementById('mission-progress').style.width = `${value}%`;
    if (value >= 100) {
      clearInterval(missionTimer); missionTimer = null;
      missionButton.textContent = '오늘의 미션 완료 ✓';
      missionButton.disabled = true;
      toast('잘했어요. 오늘 당신을 위해 잠시 시간을 내주었네요.');
      document.getElementById('feedback-dialog').showModal();
    }
  }, 450);
});

function startBreathing() {
  const dialog = document.getElementById('breath-dialog');
  dialog.showModal();
  let remaining = 60;
  let phase = true;
  clearInterval(breathTimer);
  breathTimer = setInterval(() => {
    remaining -= 1;
    const label = document.getElementById('breath-label');
    if (remaining % 4 === 0) { phase = !phase; label.textContent = phase ? '들이쉬어요' : '내쉬어요'; }
    document.getElementById('breath-time').textContent = `00:${String(remaining).padStart(2, '0')}`;
    if (remaining <= 0) { clearInterval(breathTimer); label.textContent = '잘했어요'; toast('1분 동안 내 마음 곁에 머물렀어요.'); }
  }, 1000);
}
document.querySelector('.close-breath').addEventListener('click', () => { clearInterval(breathTimer); document.getElementById('breath-dialog').close(); });

document.getElementById('chat-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const input = document.getElementById('chat-input');
  const value = input.value.trim();
  if (!value) return;
  const thread = document.getElementById('chat-thread');
  thread.insertAdjacentHTML('beforeend', `<div class="message user"><p>${escapeHtml(value)}</p></div>`);
  input.value = '';
  setTimeout(() => {
    thread.insertAdjacentHTML('beforeend', '<div class="message ai"><small>Mindily</small><p>그 마음을 말해줘서 고마워요. 지금 가장 크게 느껴지는 감정 하나를 고른다면 무엇에 가까울까요?</p></div>');
    thread.parentElement.scrollTo({ top: thread.parentElement.scrollHeight, behavior: 'smooth' });
  }, 650);
});

document.querySelector('.segmented').addEventListener('click', (event) => {
  const button = event.target.closest('[role="tab"]');
  if (!button) return;
  document.querySelectorAll('.segmented [role="tab"]').forEach((item) => item.setAttribute('aria-selected', String(item === button)));
  toast(button.textContent === '월간' ? '월간 보기는 다음 스프린트에서 실제 데이터와 연결돼요.' : '주간 기록을 보고 있어요.');
});

function renderChart() {
  const points = [54, 48, 30, 46, 72, 52, 38];
  const faces = ['😮‍💨','😐','😣','😐','🙂','😐','😔'];
  document.getElementById('emotion-chart').innerHTML = points.map((height, index) => `<div class="chart-point" style="--h:${height}%"><span aria-hidden="true">${faces[index]}</span></div>`).join('');
}

function hydrateLatest() {
  try {
    const entry = JSON.parse(localStorage.getItem('mindily-records') || '[]')[0];
    if (entry) { lastAnalysis = entry; selectedMood = entry.confirmedMood || {name: entry.detailedMood || '직접 골라주세요', color:'#b7bfce'}; updateRecordUI(entry); }
  } catch (_) {}
}

document.getElementById('delete-records').addEventListener('click', () => {
  if (!window.confirm('이 브라우저에 저장된 일기 원문과 감정 기록을 모두 삭제할까요? 복구할 수 없어요.')) return;
  try {
    localStorage.removeItem('mindily-records');
    window.location.reload();
  } catch (_) { toast('이 브라우저의 기록을 삭제할 수 없어요. 저장 설정을 확인해주세요.'); }
});

let toastTimeout;
function toast(message) {
  const element = document.getElementById('toast');
  element.textContent = message;
  element.classList.add('show');
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => element.classList.remove('show'), 2600);
}

renderChart();
hydrateLatest();
showScreen('home', false);
