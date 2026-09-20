/* Tentative topic matching for editable event timelines. */
(function (root) {
  function eventTopic(text) {
    const subjects = [
      [/친구/, '친구와의 일'], [/가족|엄마|아빠/, '가족과의 일'],
      [/연인/, '연인과의 일'], [/동료/, '동료와의 일'],
      [/회사|직장/, '직장에서 있었던 일'], [/학교/, '학교에서 있었던 일'],
      [/발표/, '발표'], [/시험/, '시험']
    ];
    const matches = subjects.map(([pattern, title]) => ({at: text.search(pattern), title})).filter(match => match.at >= 0);
    return matches.sort((a, b) => a.at - b.at)[0]?.title || '';
  }

  function groupEvents(items) {
    const groups = [];
    const byTopic = new Map();
    items.forEach((item) => {
      const topic = (item.topic || '').trim();
      const shared = eventTopic(topic) || topic;
      const key = shared ? shared.toLocaleLowerCase('ko-KR') : `individual-${item.id}`;
      let group = byTopic.get(key);
      if (!group) {
        group = {id: item.id, title: topic || item.event.slice(0, 28) || '기록된 사건', items: []};
        byTopic.set(key, group);
        groups.push(group);
      }
    group.items.push(item);
  });
  groups.forEach(group => group.items.sort((a, b) => String(a.date).localeCompare(String(b.date), 'ko')));
  return groups;
  }

  const api = {eventTopic, groupEvents};
  root.MindilyEventGroups = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
