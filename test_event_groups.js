const assert = require('node:assert/strict');
const {groupEvents} = require('./dist/event_groups.js');

const items = [
  {id: '2026-10-01-0', date: '10월 1일', emotion: '화남', topic: '친구와 싸움', event: '친구와 다투었다.'},
  {id: '2026-10-02-1', date: '10월 2일', emotion: '안도', topic: '친구와 화해', event: '친구와 화해했다.'},
  {id: '2026-10-02-2', date: '10월 2일', emotion: '걱정', topic: '발표', event: '발표를 앞두었다.'},
];
const grouped = groupEvents(items);
assert.equal(grouped.length, 2);
assert.equal(grouped[0].title, '친구와 싸움');
assert.deepEqual(grouped[0].items.map(item => [item.date, item.emotion]),
  [['10월 1일', '화남'], ['10월 2일', '안도']]);
assert.deepEqual(grouped[1].items.map(item => item.id), ['2026-10-02-2']);

const unrelated = groupEvents([
  {id: 'a', emotion: '화남', topic: '', event: '버스를 놓쳤다.'},
  {id: 'b', emotion: '화남', topic: '', event: '지갑을 잃어버렸다.'},
]);
assert.equal(unrelated.length, 2, '감정만 같다고 다른 사건을 묶지 않는다');
console.log('event grouping and mood timeline: OK');
