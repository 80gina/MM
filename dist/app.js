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

const defaultQuote = '조금 느려도 괜찮아요.\n당신은 지금도 충분히 잘하고 있어요.';
const quoteKey = 'mindily-personal-quote';
function renderPersonalQuote() {
  let value = defaultQuote;
  try { value = localStorage.getItem(quoteKey) || defaultQuote; } catch (_) {}
  document.getElementById('personal-quote').textContent = `“${value}”`;
  document.getElementById('home-personal-quote').textContent = `“${value}”`;
  document.getElementById('quote-input').value = value;
}
document.getElementById('quote-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const value = document.getElementById('quote-input').value.trim();
  if (!value) return toast('문구를 적어주세요.');
  try {
    localStorage.setItem(quoteKey, value);
    renderPersonalQuote();
    document.getElementById('quote-dialog').close();
    toast('내 문구를 이 브라우저에 저장했어요.');
  } catch (_) { toast('문구를 저장하지 못했어요.'); }
});
document.getElementById('quote-reset').addEventListener('click', () => {
  try { localStorage.removeItem(quoteKey); renderPersonalQuote(); toast('처음 문구로 되돌렸어요.'); }
  catch (_) { toast('문구를 되돌리지 못했어요.'); }
});

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
  const closer = event.target.closest('[data-close-dialog]');
  if (closer) document.getElementById(closer.dataset.closeDialog)?.close();
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
  const response = await fetch('/api/agent/coach', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text, self_reported_stress: stress, context: 'diary', memory_token: memoryToken}),
    signal: AbortSignal.timeout(60000)
  });
  if (!response.ok) throw new Error('지금은 분석할 수 없어요. 잠시 후 다시 시도해주세요.');
  const data = await response.json();
  const analysis = data.analysis;
  return {id: crypto.randomUUID(), ranked: analysis.labels.map(x => ({name:x.name, score:x.score})),
    model: analysis.model, revision: analysis.revision, chunks: analysis.chunks,
    agentMessage: data.message, recommendation: data.recommendation, comfort: data.comfort,
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
    renderAnalysis(); saveEntry(lastAnalysis); renderChart(); showScreen('analysis');
  } catch (error) {
    toast(error.name === 'TimeoutError' ? '분석 시간이 길어졌어요. 글은 그대로 있으니 다시 시도해주세요.' : '분석 서버에 연결하지 못했어요. 글은 그대로 보관 중이에요.');
  } finally { button.disabled = false; button.textContent = 'AI에게 마음 맡기기 ✨'; }
});

// 6개 감정 분류 점수를 레이더로 그린다.
// 반지름은 sqrt(점수)에 비례하고 최소 반지름을 두어, 한 감정에 쏠렸을 때도
// 도형이 한 점으로 무너지지 않게 했다. 정확한 값은 꼭짓점 숫자로 함께 보여준다.
const RADAR_ORDER = ['기쁨', '당황', '불안', '슬픔', '상처', '분노'];
function emotionRadar(ranked) {
  const CX = 150, CY = 132, R = 78, FLOOR = 0.2;
  const score = Object.fromEntries(ranked.map(x => [x.name, x.score]));
  const lead = ranked[0].name;
  const at = (index, ratio) => {
    const angle = (-90 + index * 60) * Math.PI / 180;
    const radius = R * (FLOOR + (1 - FLOOR) * ratio);
    return [CX + radius * Math.cos(angle), CY + radius * Math.sin(angle)];
  };
  const ringPoints = (ratio) => RADAR_ORDER
    .map((_, i) => at(i, ratio).map(n => n.toFixed(1)).join(',')).join(' ');
  const scaled = RADAR_ORDER.map(name => Math.sqrt(Math.max(score[name] || 0, 0)));
  const shape = RADAR_ORDER
    .map((_, i) => at(i, scaled[i]).map(n => n.toFixed(1)).join(',')).join(' ');

  let svg = '<svg class="emo-radar" viewBox="0 0 300 265" role="img" aria-label="6개 감정 분류 점수">';
  [1, 0.66, 0.33].forEach(r => { svg += `<polygon class="emo-grid" points="${ringPoints(r)}"/>`; });
  RADAR_ORDER.forEach((_, i) => {
    const [x, y] = at(i, 1);
    svg += `<line class="emo-spoke" x1="${CX}" y1="${CY}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}"/>`;
  });
  svg += `<polygon class="emo-shape" points="${shape}"/>`;
  RADAR_ORDER.forEach((name, i) => {
    const [x, y] = at(i, scaled[i]);
    const isLead = name === lead;
    const value = (score[name] || 0).toFixed(3);
    svg += `<circle class="emo-dot${isLead ? ' lead' : ''}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${isLead ? 5 : 3.5}"/>`;
    const [lx, ly] = at(i, 1.34);
    const anchor = lx > CX + 6 ? 'start' : lx < CX - 6 ? 'end' : 'middle';
    const dy = ly < CY ? -2 : 12;
    svg += `<text class="emo-label${isLead ? ' lead' : ''}" x="${lx.toFixed(1)}" y="${(ly + dy).toFixed(1)}" text-anchor="${anchor}">${emotionMeta[name][0]} ${name}</text>`;
    svg += `<text class="emo-score${isLead ? ' lead' : ''}" x="${lx.toFixed(1)}" y="${(ly + dy + 13).toFixed(1)}" text-anchor="${anchor}">${value}</text>`;
  });
  svg += '</svg>';
  const readable = RADAR_ORDER.map(n => `${n} ${(score[n] || 0).toFixed(3)}`).join(', ');
  return `${svg}<p class="sr-only">${readable}</p>`;
}

// 저작권 만료 인용구 · 추천 꽃 · 추천 향을 그린다. 효능은 주장하지 않는다.
function renderComfort(comfort) {
  const quoteBox = document.getElementById('comfort-quote');
  const careBox = document.getElementById('comfort-care');
  if (!comfort) { if (quoteBox) quoteBox.hidden = true; if (careBox) careBox.hidden = true; return; }
  const { quote, flower, scent } = comfort;
  quoteBox.hidden = false;
  quoteBox.innerHTML =
    `<blockquote class="quote-text">${quote.text}</blockquote>` +
    `<cite class="quote-by">— <a href="${quote.source_url}" target="_blank" rel="noopener">${quote.author}</a>` +
    `<span class="quote-license">${quote.license}</span></cite>`;
  careBox.hidden = false;
  careBox.innerHTML =
    `<div class="card-label">오늘 곁에 두면 좋은 것</div>` +
    `<div class="care-row"><span class="care-icon" aria-hidden="true">🌼</span>` +
    `<div><strong>${flower.name}</strong><span class="care-meaning">꽃말 · ${flower.meaning}</span>` +
    `<p>${flower.note}</p></div></div>` +
    `<div class="care-row"><span class="care-icon" aria-hidden="true">🌿</span>` +
    `<div><strong>${scent.name}</strong><p>${scent.note}</p></div></div>` +
    `<small class="model-note">${scent.safety}</small>`;
}

function renderAnalysis() {
  const top = lastAnalysis.ranked.slice(0, 3);
  document.getElementById('emotion-result').innerHTML = emotionRadar(lastAnalysis.ranked);
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
  document.getElementById('analysis-message').textContent = lastAnalysis.agentMessage || messages[lead];
  renderComfort(lastAnalysis.comfort);
  updateMoodUI();
  updateRecordUI(lastAnalysis);
  loadHealingRecommendations();
}

let healingCards = [];
let selectedHealingId = null;

const KIND_ICON = {
  '호흡': '🌱', '감각활동': '◌', '자연의 소리': '🎧', '걷기': '👣',
  '꽃·나무': '🌿', '필사': '✎', '음악': '♫', '취미': '✦'
};

async function loadHealingRecommendations() {
  if (!lastAnalysis) return;
  try {
    let data = lastAnalysis.recommendation;
    if (!data) {
      const response = await fetch('/api/healing/recommend', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({emotion: lastAnalysis.ranked[0].name, stress: lastAnalysis.stress, minutes: 20,
          allow_location: false, memory_token: memoryToken})
      });
      if (!response.ok) throw new Error('recommendation');
      data = await response.json();
      lastAnalysis.recommendation = data;
    }
    healingCards = data.cards.slice(0, 8);
    if (!healingCards.some(card => card.id === selectedHealingId)) {
      selectedHealingId = healingCards[0] ? healingCards[0].id : null;
    }
    renderHealing();
  } catch (_) {
    const host = document.getElementById('healing-host');
    if (host) host.innerHTML = '<p class="model-note">추천을 불러오지 못했어요. 잠시 후 다시 열어주세요.</p>';
  }
}

// 활동 목록은 한 화면에 전부 펼쳐 두고, 고른 하나만 아래에서 자세히 본다.
// 고를 때마다 전체를 다시 그리면 화면이 위로 튀므로, 상세 영역만 갈아끼운다.
function healingDetailHtml(card) {
  const steps = (card.steps || []).map(step => `<li>${escapeHtml(step)}</li>`).join('');
  let action = '';
  if (card.id === 'breathing-1m') {
    action = '<button class="secondary-button" type="button" data-start-breath>1분 호흡 시작하기</button>';
  } else if (card.sound) {
    const playing = currentSound && currentSound.kind === card.sound;
    action = `<button class="secondary-button${playing ? ' playing' : ''}" type="button" data-sound="${escapeHtml(card.sound)}">${playing ? '■ 정지' : '▶ 소리 재생'}</button>`;
  }
  return `<div class="heal-head"><span class="soft-chip">${escapeHtml(card.kind)}</span>
       <span class="heal-min">약 ${card.minutes}분</span></div>
     <h3>${escapeHtml(card.title)}</h3>
     <p class="heal-desc">${escapeHtml(card.description)}</p>
     ${steps ? `<ol class="heal-steps">${steps}</ol>` : ''}
     ${action}
     <small class="model-note">출처 · ${card.source_url && card.source_url.startsWith('https://')
       ? `<a href="${escapeHtml(card.source_url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(card.source_title)} ↗</a>`
       : escapeHtml(card.source_title)}</small>`;
}

function renderHealing() {
  const host = document.getElementById('healing-host');
  if (!host || !healingCards.length) return;
  const card = healingCards.find(item => item.id === selectedHealingId) || healingCards[0];

  let list = host.querySelector('.heal-tabs');
  let detail = host.querySelector('.heal-detail');

  if (!list || !detail) {
    const tabs = healingCards.map((item) => {
      const on = item.id === card.id;
      return `<button class="heal-tab${on ? ' active' : ''}" type="button" role="tab" aria-selected="${on}"
        data-heal="${escapeHtml(item.id)}"><span aria-hidden="true">${KIND_ICON[item.kind] || '✦'}</span>${escapeHtml(item.title)}${item.title.includes(`${item.minutes}분`) ? '' : `<small>${item.minutes}분</small>`}</button>`;
    }).join('');
    host.innerHTML =
      `<p class="heal-guide">활동을 하나 고르면 아래에 방법이 나와요.</p>` +
      `<div class="heal-tabs" role="tablist" aria-label="추천 활동 고르기">${tabs}</div>` +
      `<article class="card heal-detail" role="tabpanel" aria-live="polite"></article>`;
    list = host.querySelector('.heal-tabs');
    detail = host.querySelector('.heal-detail');
  } else {
    // 목록은 그대로 두고 선택 표시만 바꾼다 (화면 위치가 흔들리지 않게)
    list.querySelectorAll('[data-heal]').forEach((button) => {
      const on = button.dataset.heal === card.id;
      button.classList.toggle('active', on);
      button.setAttribute('aria-selected', String(on));
    });
  }
  detail.innerHTML = healingDetailHtml(card);
}

document.addEventListener('click', (event) => {
  const tab = event.target.closest('[data-heal]');
  if (tab) {
    selectedHealingId = tab.dataset.heal;
    renderHealing();
    return;
  }
  const soundButton = event.target.closest('[data-sound]');
  if (soundButton) { toggleNatureSound(soundButton.dataset.sound); }
});

// 자연의 소리는 녹음 파일이 아니라 브라우저가 실시간으로 만든다.
// 저작권 문제가 없고 앱 용량도 늘지 않는다.
let audioContext = null;
let currentSound = null;

function toggleNatureSound(kind) {
  if (currentSound && currentSound.kind === kind) { stopNatureSound(); renderHealing(); return; }
  stopNatureSound();
  try {
    currentSound = startNatureSound(kind);
  } catch (_) {
    toast('이 브라우저에서는 소리를 만들 수 없어요.');
    currentSound = null;
  }
  renderHealing();
}

function stopNatureSound() {
  if (!currentSound) return;
  currentSound.stop();
  currentSound = null;
}

function startNatureSound(kind) {
  audioContext = audioContext || new (window.AudioContext || window.webkitAudioContext)();
  const ctx = audioContext;
  if (ctx.state === 'suspended') ctx.resume();
  const buffer = ctx.createBuffer(1, ctx.sampleRate * 3, ctx.sampleRate);
  const data = buffer.getChannelData(0);
  let brown = 0;
  for (let i = 0; i < data.length; i += 1) {
    const white = Math.random() * 2 - 1;
    brown = (brown + 0.02 * white) / 1.02;
    data[i] = kind === 'rain' ? white * 0.45 : brown * 3.2;
  }
  const source = ctx.createBufferSource();
  source.buffer = buffer;
  source.loop = true;
  const filter = ctx.createBiquadFilter();
  const gain = ctx.createGain();
  gain.gain.value = 0;
  let lfo = null;
  if (kind === 'rain') {
    filter.type = 'highpass';
    filter.frequency.value = 750;
  } else if (kind === 'wind') {
    filter.type = 'lowpass';
    filter.frequency.value = 420;
    lfo = ctx.createOscillator();
    lfo.frequency.value = 0.06;
    const depth = ctx.createGain();
    depth.gain.value = 240;
    lfo.connect(depth); depth.connect(filter.frequency); lfo.start();
  } else {
    filter.type = 'lowpass';
    filter.frequency.value = 700;
    lfo = ctx.createOscillator();
    lfo.frequency.value = 0.09;
    const depth = ctx.createGain();
    depth.gain.value = 0.16;
    lfo.connect(depth); depth.connect(gain.gain); lfo.start();
  }
  source.connect(filter); filter.connect(gain); gain.connect(ctx.destination);
  const level = kind === 'rain' ? 0.16 : kind === 'wind' ? 0.22 : 0.2;
  gain.gain.setValueAtTime(0, ctx.currentTime);
  gain.gain.linearRampToValueAtTime(level, ctx.currentTime + 1.4);
  source.start();
  return {
    kind,
    stop() {
      const now = ctx.currentTime;
      gain.gain.cancelScheduledValues(now);
      gain.gain.setValueAtTime(gain.gain.value, now);
      gain.gain.linearRampToValueAtTime(0, now + 0.6);
      setTimeout(() => { try { source.stop(); if (lfo) lfo.stop(); } catch (_) {} }, 700);
    }
  };
}

const organizerKey = 'mindily-thoughts';
const organizerFields = ['event', 'feeling', 'need'];
function hydrateOrganizer() {
  try {
    const saved = JSON.parse(localStorage.getItem(organizerKey) || 'null');
    if (!saved) return;
    organizerFields.forEach((name) => { document.getElementById(`organize-${name}`).value = saved[name] || ''; });
    document.getElementById('organize-status').textContent = '이 브라우저에 저장된 내용을 다시 볼 수 있어요.';
  } catch (_) {}
}

document.getElementById('organize-draft-button').addEventListener('click', async (event) => {
  const entry = lastAnalysis?.text ? lastAnalysis : readRecords()[0];
  if (!entry?.text) return toast('먼저 감정 일기를 작성해 주세요.');
  if (!document.getElementById('organize-draft-consent').checked) return toast('초안 생성 전 전송 안내에 동의해 주세요.');
  const eventField = document.getElementById('organize-event');
  const feelingField = document.getElementById('organize-feeling');
  if ((eventField.value.trim() || feelingField.value.trim()) &&
      !window.confirm('현재 작성한 첫 두 칸을 새 초안으로 바꿀까요?')) return;
  const button = event.currentTarget;
  button.disabled = true; button.textContent = '일기를 정리하고 있어요…';
  try {
    const response = await fetch('/api/diary/organizer-draft', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text: entry.text, emotion: entryMood(entry) || '', consent: true}),
      signal: AbortSignal.timeout(90000)
    });
    if (!response.ok) throw new Error('draft');
    const draft = await response.json();
    eventField.value = draft.event || '';
    feelingField.value = draft.feeling || '';
    document.getElementById('organize-status').textContent = draft.generation === 'llm_draft'
      ? 'AI 초안을 만들었어요. 사실과 감정 표현을 확인하고 자유롭게 고쳐 주세요.'
      : '일기 문장과 감정 분류로 임시 초안을 만들었어요. 직접 확인하고 고쳐 주세요.';
    eventField.focus();
  } catch (_) { toast('초안을 만들지 못했어요. 잠시 후 다시 시도해 주세요.'); }
  finally { button.disabled = false; button.textContent = '일기로 초안 만들기'; }
});

document.getElementById('organize-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const values = Object.fromEntries(organizerFields.map((name) =>
    [name, document.getElementById(`organize-${name}`).value.trim()]));
  if (!Object.values(values).some(Boolean)) return toast('한 칸 이상 적어주세요.');
  try {
    localStorage.setItem(organizerKey, JSON.stringify({...values, saved_at: new Date().toISOString()}));
    document.getElementById('organize-status').textContent = '이 브라우저에 저장했어요.';
    document.getElementById('organize-dialog').close();
    toast('마음을 정리한 내용을 이 브라우저에 저장했어요.');
  } catch (_) { toast('이 브라우저에 저장할 수 없어요. 저장 설정을 확인해주세요.'); }
});

document.getElementById('delete-organized-thoughts').addEventListener('click', () => {
  if (!window.confirm('이 브라우저에 저장한 감정 정리 내용을 삭제할까요? 복구할 수 없어요.')) return;
  try {
    localStorage.removeItem(organizerKey);
    document.getElementById('organize-form').reset();
    document.getElementById('organize-status').textContent = '저장된 정리 내용이 없어요.';
    toast('정리 내용을 삭제했어요.');
  } catch (_) { toast('정리 내용을 삭제하지 못했어요.'); }
});

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
    if (lastAnalysis) lastAnalysis.recommendation = null;
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
    if (lastAnalysis) lastAnalysis.recommendation = null;
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
    localStorage.setItem('mindily-records', JSON.stringify(records.slice(0, 400)));
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

document.getElementById('chat-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const input = document.getElementById('chat-input');
  const value = input.value.trim();
  if (!value) return;
  const submit = event.currentTarget.querySelector('[type="submit"]');
  if (submit.disabled) return;
  submit.disabled = true;
  const thread = document.getElementById('chat-thread');
  thread.insertAdjacentHTML('beforeend', `<div class="message user"><p>${escapeHtml(value)}</p></div>`);
  input.value = '';
  try {
    const response = await fetch('/api/agent/coach', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text: value, self_reported_stress: lastAnalysis?.stress || 3,
        context: 'chat', memory_token: memoryToken, known_emotion: lastAnalysis?.ranked?.[0]?.name || null}),
      signal: AbortSignal.timeout(60000)});
    if (!response.ok) throw new Error('coach');
    const result = await response.json();
    const card = result.recommendation?.cards?.[0];
    const source = card?.source_url?.startsWith('https://')
      ? `<p><a href="${escapeHtml(card.source_url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(card.source_title)} 자료 보기 ↗</a></p>` : '';
    thread.insertAdjacentHTML('beforeend', `<div class="message ai"><small>Mindily · 규칙 기반 응답</small><p>${escapeHtml(result.message)}</p>${source}</div>`);
    thread.parentElement.scrollTo({ top: thread.parentElement.scrollHeight, behavior: 'smooth' });
  } catch (_) { thread.insertAdjacentHTML('beforeend', '<div class="message ai"><small>Mindily</small><p>지금은 연결이 어려워요. 잠시 후 다시 이야기해 주세요.</p></div>'); }
  finally { submit.disabled = false; }
});


// 마음 기록 그래프 — 이 브라우저에 저장된 실제 일기 기록으로 그린다.
// 막대 높이는 사용자가 직접 기록한 스트레스(1~5), 막대 위 얼굴은 그날의 대표 감정이다.
// 모델 점수를 높이로 쓰지 않는 이유: 점수가 높다고 기분이 좋은 게 아니라 오해를 부른다.
let chartRange = 7;

function readRecords() {
  try { return JSON.parse(localStorage.getItem('mindily-records') || '[]'); } catch (_) { return []; }
}

function dayKey(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function entryMood(entry) {
  const picked = entry.confirmedMood && entry.confirmedMood.name;
  if (picked && picked !== '직접 골라주세요') return picked;
  return entry.ranked && entry.ranked[0] ? entry.ranked[0].name : null;
}

const MOOD_FACE = {
  '기분 좋은': '🙂', '설레는': '😊', '활기찬': '😄', '집중되는': '🙂', '편안한': '😌',
  '걱정되는': '😰', '불안한': '😰', '답답한': '😣', '지친': '😔', '외로운': '🥺', '초조한': '😯',
};

function faceFor(mood) {
  if (!mood) return '';
  if (MOOD_FACE[mood]) return MOOD_FACE[mood];
  return emotionMeta[mood] ? emotionMeta[mood][0] : '•';
}

function chartDays(records, days) {
  const byDay = new Map();
  records.forEach((entry) => {
    if (!entry || !entry.date) return;
    const key = dayKey(new Date(entry.date));
    if (!byDay.has(key)) byDay.set(key, entry);   // 기록은 최신순이라 그날의 마지막 기록이 남는다
  });
  const out = [];
  for (let i = days - 1; i >= 0; i -= 1) {
    const date = new Date();
    date.setHours(0, 0, 0, 0);
    date.setDate(date.getDate() - i);
    const entry = byDay.get(dayKey(date));
    out.push({date, entry: entry || null});
  }
  return out;
}

function chartMonths(records, months) {
  const buckets = [];
  for (let i = months - 1; i >= 0; i -= 1) {
    const date = new Date();
    date.setDate(1); date.setHours(0, 0, 0, 0);
    date.setMonth(date.getMonth() - i);
    buckets.push({date, key: `${date.getFullYear()}-${date.getMonth()}`, entries: []});
  }
  const index = new Map(buckets.map(bucket => [bucket.key, bucket]));
  records.forEach((entry) => {
    if (!entry || !entry.date) return;
    const date = new Date(entry.date);
    const bucket = index.get(`${date.getFullYear()}-${date.getMonth()}`);
    if (bucket) bucket.entries.push(entry);
  });
  return buckets;
}

function renderChart() {
  const host = document.getElementById('emotion-chart');
  if (!host) return;
  const axis = document.getElementById('chart-axis');
  const title = document.getElementById('chart-title');
  const badge = document.getElementById('chart-badge');
  const readout = document.getElementById('chart-readout');
  const records = readRecords();
  const weekday = ['일', '월', '화', '수', '목', '금', '토'];

  if (chartRange === 365) {
    // 연간은 하루씩 그리면 읽을 수 없어서 달 평균으로 묶는다.
    const months = chartMonths(records, 12);
    const kept = months.filter(month => month.entries.length);
    if (title) title.textContent = '최근 12개월 스트레스 흐름';
    if (badge) badge.textContent = kept.length ? `기록 ${kept.length}개월` : '기록 없음';
    host.innerHTML = months.map((month) => {
      if (!month.entries.length) return '<div class="chart-point empty" style="--h:6%"></div>';
      const average = month.entries.reduce((sum, entry) => sum + (Number(entry.stress) || 0), 0) / month.entries.length;
      return `<div class="chart-point" style="--h:${16 + (average / 5) * 72}%" title="${month.date.getMonth() + 1}월 기록 ${month.entries.length}일"><span class="chart-value" aria-hidden="true">${average.toFixed(1)}</span></div>`;
    }).join('');
    if (axis) axis.innerHTML = months.map((month, i) => `<span>${i === 0 || month.date.getMonth() === 0 || i === months.length - 1 ? `${month.date.getMonth() + 1}월` : ''}</span>`).join('');
    if (readout) {
      readout.textContent = kept.length
        ? kept.map(month => `${month.date.getMonth() + 1}월 기록 ${month.entries.length}일`).join(', ')
        : '아직 기록이 없어요.';
    }
    renderPattern(kept.flatMap(month => month.entries.map(entry => ({date: new Date(entry.date), entry}))));
    renderReport();
    return;
  }

  const days = chartDays(records, chartRange);
  const filled = days.filter(day => day.entry);
  const showFaces = chartRange <= 10;

  if (title) title.textContent = chartRange === 7 ? '최근 7일 스트레스 흐름' : '최근 30일 스트레스 흐름';
  if (badge) badge.textContent = filled.length ? `내 기록 ${filled.length}일` : '기록 없음';

  host.innerHTML = days.map((day) => {
    if (!day.entry) return '<div class="chart-point empty" style="--h:6%"></div>';
    const stress = Number(day.entry.stress) || 1;
    const face = showFaces ? `<span aria-hidden="true">${faceFor(entryMood(day.entry))}</span>` : '';
    return `<div class="chart-point" style="--h:${16 + (stress / 5) * 72}%">${face}</div>`;
  }).join('');

  if (axis) {
    axis.innerHTML = days.map((day, index) => {
      if (chartRange === 7) return `<span>${weekday[day.date.getDay()]}</span>`;
      const show = index === 0 || index === days.length - 1 || index === Math.floor(days.length / 2);
      return `<span>${show ? `${day.date.getMonth() + 1}/${day.date.getDate()}` : ''}</span>`;
    }).join('');
  }

  if (readout) {
    readout.textContent = filled.length
      ? filled.map(day => `${day.date.getMonth() + 1}월 ${day.date.getDate()}일 스트레스 ${day.entry.stress}/5`).join(', ')
      : '아직 기록이 없어요.';
  }
  renderPattern(filled);
  renderReport();
}

// 감정 분석 보고서 — 기간별 요약.
// 기록에 있는 값만 계산해 적고, 원인·진단·조언은 만들지 않는다.
const RANGE_LABEL = {7: '최근 7일', 30: '최근 30일', 365: '최근 12개월'};
const reportEventKey = (range) => `mindily-report-events-${range}`;

function rangeEntries() {
  const records = readRecords();
  const from = new Date();
  from.setHours(0, 0, 0, 0);
  if (chartRange === 365) { from.setMonth(from.getMonth() - 11); from.setDate(1); }
  else from.setDate(from.getDate() - (chartRange - 1));
  return records
    .filter(entry => entry && entry.date && new Date(entry.date) >= from)
    .sort((a, b) => new Date(a.date) - new Date(b.date));
}

function summarize(entries) {
  const values = entries.map(entry => Number(entry.stress) || 0);
  const average = values.reduce((sum, value) => sum + value, 0) / values.length;
  const top = entries.reduce((best, entry) => (Number(entry.stress) > Number(best.stress) ? entry : best), entries[0]);
  const low = entries.reduce((best, entry) => (Number(entry.stress) < Number(best.stress) ? entry : best), entries[0]);
  const counted = {};
  entries.forEach((entry) => {
    const mood = entryMood(entry);
    if (mood) counted[mood] = (counted[mood] || 0) + 1;
  });
  const moods = Object.entries(counted).sort((a, b) => b[1] - a[1]);
  const half = Math.floor(entries.length / 2);
  const mean = list => list.reduce((sum, entry) => sum + (Number(entry.stress) || 0), 0) / (list.length || 1);
  return {average, top, low, moods, days: entries.length,
          early: mean(entries.slice(0, half)), late: mean(entries.slice(half))};
}

function dateText(value) {
  const date = new Date(value);
  return `${date.getMonth() + 1}월 ${date.getDate()}일`;
}

function reportLines() {
  const entries = rangeEntries();
  const label = RANGE_LABEL[chartRange] || '최근 기록';
  if (!entries.length) return {label, lines: [], empty: '이 기간에는 기록이 없어요. 일기를 쓰면 여기에 요약이 만들어져요.'};
  const info = summarize(entries);
  const lines = [
    ['기록', `${label} 동안 ${info.days}번 기록했어요.`],
    ['평균 스트레스', `${info.average.toFixed(1)} / 5`],
    ['가장 높았던 날', `${dateText(info.top.date)} · ${info.top.stress}/5`],
    ['가장 낮았던 날', `${dateText(info.low.date)} · ${info.low.stress}/5`],
  ];
  if (info.moods.length) {
    lines.push(['자주 기록한 감정',
      info.moods.slice(0, 3).map(([mood, count]) => `${mood} ${count}번`).join(' · ')]);
  }
  if (info.days >= 4) {
    const gap = info.late - info.early;
    const word = Math.abs(gap) < 0.3 ? '비슷했어요'
      : (gap < 0 ? `${Math.abs(gap).toFixed(1)}만큼 낮아졌어요` : `${gap.toFixed(1)}만큼 높아졌어요`);
    lines.push(['기간 전반 대비 후반', `${word} (앞 ${info.early.toFixed(1)} → 뒤 ${info.late.toFixed(1)})`]);
  }
  return {label, lines, moods: info.moods, days: info.days};
}

function renderReport() {
  const body = document.getElementById('report-body');
  if (!body) return;
  const eventsField = document.getElementById('report-events');
  try { eventsField.value = localStorage.getItem(reportEventKey(chartRange)) || ''; }
  catch (_) { eventsField.value = ''; }
  document.getElementById('report-draft-status').textContent = '';
  const report = reportLines();
  if (report.empty) {
    body.innerHTML = `<p class="report-empty">${report.empty}</p>`;
    return;
  }
  const rows = report.lines.map(([name, value]) =>
    `<div class="report-row"><dt>${escapeHtml(name)}</dt><dd>${escapeHtml(value)}</dd></div>`).join('');
  const most = report.moods && report.moods.length ? report.moods[0][1] : 1;
  const bars = (report.moods || []).slice(0, 5).map(([mood, count]) =>
    `<div class="report-bar"><span>${escapeHtml(mood)}</span>
       <i style="--w:${Math.round((count / most) * 100)}%"></i><small>${count}</small></div>`).join('');
  body.innerHTML = `<dl class="report-rows">${rows}</dl>${bars ? `<div class="report-bars">${bars}</div>` : ''}`;
}

document.getElementById('report-events').addEventListener('input', (event) => {
  try { localStorage.setItem(reportEventKey(chartRange), event.currentTarget.value); }
  catch (_) { document.getElementById('report-draft-status').textContent = '수정한 요약을 저장하지 못했어요.'; }
});

document.getElementById('report-draft-button').addEventListener('click', async (event) => {
  const requestedRange = chartRange;
  const entries = rangeEntries().filter(entry => entry.text?.trim()).slice(-10);
  if (!entries.length) return toast('선택한 기간에 일기 기록이 없어요.');
  if (!document.getElementById('report-draft-consent').checked) return toast('초안 생성 전 전송 안내에 동의해 주세요.');
  const field = document.getElementById('report-events');
  if (field.value.trim() && !window.confirm('직접 수정한 사건 요약을 새 초안으로 바꿀까요?')) return;
  const button = event.currentTarget;
  button.disabled = true; button.textContent = '사건을 정리하고 있어요…';
  try {
    const response = await fetch('/api/report/events', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({entries: entries.map(entry => ({date: dateText(entry.date), text: entry.text})), consent: true}),
      signal: AbortSignal.timeout(90000)
    });
    if (!response.ok) throw new Error('report');
    const draft = await response.json();
    if (chartRange === requestedRange) field.value = draft.events || '';
    try { localStorage.setItem(reportEventKey(requestedRange), draft.events || ''); }
    catch (_) { toast('초안은 표시했지만 이 브라우저에 저장하지 못했어요.'); }
    if (chartRange !== requestedRange) return;
    document.getElementById('report-draft-status').textContent = draft.generation === 'llm_draft'
      ? 'AI가 사건을 요약했어요. 사실을 확인하고 수정해 주세요.'
      : '일기에서 문장을 발췌한 임시 요약이에요. 직접 확인하고 수정해 주세요.';
    field.focus();
  } catch (_) { toast('사건 요약을 만들지 못했어요. 다시 시도해 주세요.'); }
  finally { button.disabled = false; button.textContent = '주요 사건 초안 만들기'; }
});

function reportText() {
  const report = reportLines();
  const head = `Mindily 감정 분석 보고서 — ${report.label}\n만든 날짜: ${dateText(new Date())}\n`;
  if (report.empty) return `${head}\n${report.empty}\n`;
  const body = report.lines.map(([name, value]) => `- ${name}: ${value}`).join('\n');
  const events = document.getElementById('report-events').value.trim();
  return `${head}\n${body}${events ? `\n\n주요 사건 (사용자 확인·수정)\n${events}` : ''}\n\n이 보고서는 기록과 사용자가 확인한 사건 요약을 담고 있으며, 의학적 판단이나 진단이 아닙니다.\n일기 원문 전체는 포함하지 않습니다.\n`;
}

document.addEventListener('click', (event) => {
  if (!event.target.closest('#report-save')) return;
  try {
    const blob = new Blob([reportText()], {type: 'text/plain;charset=utf-8'});
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `mindily-보고서-${RANGE_LABEL[chartRange] || '기록'}.txt`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    toast('보고서를 내려받았어요.');
  } catch (_) { toast('이 브라우저에서는 저장이 안 돼요.'); }
});

// 기록에서 읽어낸 사실만 적는다. 원인을 해석하거나 진단하지 않는다.
function renderPattern(filled) {
  const title = document.getElementById('pattern-title');
  const copy = document.getElementById('pattern-copy');
  if (!title || !copy) return;

  if (!filled.length) {
    title.textContent = '아직 기록이 없어요';
    copy.textContent = '일기를 쓰면 이 그래프에 그날의 스트레스와 감정이 하나씩 쌓여요.';
    return;
  }
  if (filled.length < 3) {
    title.textContent = `기록 ${filled.length}일`;
    copy.textContent = '3일 이상 쌓이면 흐름을 함께 살펴볼 수 있어요.';
    return;
  }
  const values = filled.map(day => Number(day.entry.stress) || 0);
  const average = values.reduce((sum, value) => sum + value, 0) / values.length;
  const peak = filled.reduce((top, day) => (Number(day.entry.stress) > Number(top.entry.stress) ? day : top), filled[0]);
  const moods = filled.map(day => entryMood(day.entry)).filter(Boolean);
  const counted = {};
  moods.forEach((mood) => { counted[mood] = (counted[mood] || 0) + 1; });
  const common = Object.keys(counted).sort((a, b) => counted[b] - counted[a])[0];

  title.textContent = `기록 ${filled.length}일`;
  const parts = [`평균 스트레스는 ${average.toFixed(1)}/5였어요.`,
                 `가장 높았던 날은 ${peak.date.getMonth() + 1}월 ${peak.date.getDate()}일(${peak.entry.stress}/5)이에요.`];
  if (common && counted[common] > 1) parts.push(`‘${common}’이 ${counted[common]}번으로 가장 자주 기록됐어요.`);
  copy.textContent = parts.join(' ');
}

document.addEventListener('click', (event) => {
  const range = event.target.closest('[data-range]');
  if (!range) return;
  chartRange = Number(range.dataset.range) || 7;
  document.querySelectorAll('[data-range]').forEach((button) => {
    button.setAttribute('aria-selected', String(button === range));
  });
  renderChart();
});

function hydrateLatest() {
  try {
    const entry = JSON.parse(localStorage.getItem('mindily-records') || '[]')[0];
    if (entry) { lastAnalysis = entry; selectedMood = entry.confirmedMood || {name: entry.detailedMood || '직접 골라주세요', color:'#b7bfce'}; updateRecordUI(entry); }
  } catch (_) {}
}

document.getElementById('delete-records').addEventListener('click', () => {
  if (!window.confirm('이 브라우저에 저장된 일기·감정 기록·정리 내용을 모두 삭제할까요? 복구할 수 없어요.')) return;
  try {
    localStorage.removeItem('mindily-records');
    localStorage.removeItem(organizerKey);
    [7, 30, 365].forEach(range => localStorage.removeItem(reportEventKey(range)));
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
hydrateOrganizer();
renderPersonalQuote();
showScreen('home', false);

/* ── 앱 설치(PWA) ──────────────────────────────────────────────
   홈 화면에 추가하면 주소창 없이 앱처럼 열린다.
   서비스 워커는 화면 자원만 캐시하고 /api/ 응답은 캐시하지 않는다. */
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  });
}

let installPrompt = null;
const installBar = document.createElement('div');
installBar.className = 'install-bar';
installBar.hidden = true;
installBar.innerHTML = '<span>홈 화면에 추가하면 앱처럼 열려요.</span>'
  + '<button type="button" id="install-yes">설치</button>'
  + '<button type="button" id="install-no" class="ghost" aria-label="설치 안내 닫기">닫기</button>';
document.body.appendChild(installBar);

window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  installPrompt = event;
  try { if (localStorage.getItem('mindily-install-dismissed') === '1') return; } catch (_) {}
  installBar.hidden = false;
});

installBar.addEventListener('click', async (event) => {
  const target = event.target.closest('button');
  if (!target) return;
  if (target.id === 'install-no') {
    installBar.hidden = true;
    try { localStorage.setItem('mindily-install-dismissed', '1'); } catch (_) {}
    return;
  }
  installBar.hidden = true;
  if (!installPrompt) return;
  installPrompt.prompt();
  await installPrompt.userChoice.catch(() => {});
  installPrompt = null;
});

window.addEventListener('appinstalled', () => {
  installBar.hidden = true;
  installPrompt = null;
  toast('홈 화면에 추가했어요.');
});

/* 오프라인이면 분석이 안 된다는 사실을 미리 알린다. */
window.addEventListener('offline', () => toast('인터넷이 끊겼어요. 일기는 쓸 수 있지만 감정 분석은 연결된 뒤에 가능해요.'));
window.addEventListener('online', () => toast('다시 연결됐어요.'));
