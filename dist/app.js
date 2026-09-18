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

const emotionRules = {
  불안: ['불안', '걱정', '긴장', '면접', '발표', '잠도 안', '신경'],
  슬픔: ['슬프', '눈물', '우울', '외롭', '속상', '허무'],
  분노: ['화가', '화났', '짜증', '억울', '열받', '답답'],
  기쁨: ['기쁘', '신나', '행복', '즐거', '좋았', '설레'],
  상처: ['상처', '무시', '배신', '서운', '실망'],
  당황: ['당황', '놀랐', '황당', '갑자기', '예상 못']
};

const emotionMeta = {
  불안: ['😰', '걱정되는'], 슬픔: ['😔', '지친'], 분노: ['😣', '답답한'], 기쁨: ['🙂', '기분 좋은'], 상처: ['🥺', '외로운'], 당황: ['😯', '초조한']
};

function analyzeDiary(text, stress) {
  const scores = Object.fromEntries(Object.keys(emotionRules).map((key) => [key, 1]));
  Object.entries(emotionRules).forEach(([emotion, keywords]) => keywords.forEach((word) => { if (text.includes(word)) scores[emotion] += 4; }));
  selectedTags.forEach((tag) => {
    if (['불안', '슬픔', '기쁨'].includes(tag)) scores[tag] += 5;
    if (tag === '스트레스' || tag === '답답함') scores.분노 += 3;
    if (tag === '외로움') scores.상처 += 4;
    if (tag === '설렘') scores.기쁨 += 4;
    if (tag === '피곤함') scores.슬픔 += 3;
  });
  const total = Object.values(scores).reduce((sum, value) => sum + value, 0);
  const ranked = Object.entries(scores).map(([name, score]) => ({ name, percent: Math.round(score / total * 100) })).sort((a, b) => b.percent - a.percent);
  const drift = 100 - ranked.reduce((sum, item) => sum + item.percent, 0);
  ranked[0].percent += drift;
  return { ranked, stress, text, date: new Date().toISOString(), detailedMood: emotionMeta[ranked[0].name][1] };
}

document.getElementById('diary-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const text = diaryText.value.trim();
  if (text.length < 8) return toast('마음을 조금만 더 들려주세요. 여덟 글자 이상이면 좋아요.');
  const stress = Number(new FormData(event.currentTarget).get('stress'));
  lastAnalysis = analyzeDiary(text, stress);
  selectedMood = { name: lastAnalysis.detailedMood, color: emotionMeta[lastAnalysis.ranked[0].name][0] === '🙂' ? '#f0d25d' : '#ec846f' };
  renderAnalysis();
  saveEntry(lastAnalysis);
  showScreen('analysis');
});

function renderAnalysis() {
  const top = lastAnalysis.ranked.slice(0, 3);
  document.getElementById('emotion-result').innerHTML = top.map((item) => `<div class="emotion-pill"><span aria-hidden="true">${emotionMeta[item.name][0]}</span><strong>${item.name}</strong><small>${item.percent}%</small></div>`).join('');
  const level = lastAnalysis.stress >= 4 ? '높은' : lastAnalysis.stress === 3 ? '조금 높은' : '낮은';
  document.getElementById('analysis-summary').textContent = `스트레스가 ${level} 상태로 보여요.`;
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
}

function saveEntry(entry) {
  try {
    const records = JSON.parse(localStorage.getItem('mindily-records') || '[]');
    records.unshift(entry);
    localStorage.setItem('mindily-records', JSON.stringify(records.slice(0, 30)));
  } catch (_) { /* localStorage may be unavailable in private contexts */ }
}

function updateRecordUI(entry) {
  const lead = entry.ranked[0].name;
  document.getElementById('record-date').textContent = '오늘';
  document.getElementById('record-emoji').textContent = emotionMeta[lead][0];
  document.getElementById('record-mood').textContent = selectedMood.name;
  document.getElementById('record-stress').textContent = `스트레스 ${entry.stress}/5`;
  document.getElementById('record-copy').textContent = entry.text;
  document.getElementById('latest-mood').textContent = `${selectedMood.name} 마음이에요`;
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
  if (lastAnalysis) updateRecordUI(lastAnalysis);
  toast(`‘${selectedMood.name}’ 마음으로 기록했어요.`);
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
    }
  }, 450);
});

document.querySelector('[data-start-breath]').addEventListener('click', () => {
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
});
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
    if (entry) { lastAnalysis = entry; selectedMood.name = entry.detailedMood || selectedMood.name; updateRecordUI(entry); }
  } catch (_) {}
}

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

