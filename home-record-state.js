(() => {
  const emptyRecord = (card) => {
    if (!card) return;
    card.classList.add('record-empty');
    card.innerHTML = '<div class="fish-art">🐟</div><div><h3>아직 등록한 조과가 없어요</h3><p>첫 조과를 인증해 기록을 남겨보세요.</p></div>';
  };

  const render = async () => {
    const card = document.querySelector('#homeLatestRecord');
    const user = window.fishonUser;
    if (!card || !user || !window.fishonData) return emptyRecord(card);

    let records = [];
    try {
      const source = window.fishonData.loadMyRecords?.(user.uid) || window.fishonData.loadRanking?.() || [];
      records = await Promise.resolve(source);
      records = records.filter((item) => item.userId === user.uid);
    } catch (_) {
      records = [];
    }

    const optimistic = window.fishonLatestCatch;
    if (optimistic && optimistic.userId === user.uid && !records.some((item) => item.clientCreatedAt === optimistic.clientCreatedAt)) {
      records.push(optimistic);
    }
    if (!records.length) return emptyRecord(card);

    records.sort((a, b) => Number(b.clientCreatedAt || 0) - Number(a.clientCreatedAt || 0));
    const latest = records[0];
    const date = latest.clientCreatedAt ? new Date(latest.clientCreatedAt).toLocaleDateString('ko-KR', { month: 'numeric', day: 'numeric' }) : '방금';
    card.classList.remove('record-empty');
    card.innerHTML = `<div class="fish-art">🐟</div><div><span class="badge verified">✓ 인증 완료</span><h3>${latest.species || '어종 미확인'} <b>${Number(latest.lengthCm).toFixed(1)} cm</b></h3><p>${date} · ${latest.area || '부산 해역'}</p></div><strong class="points">+${latest.verified ? 120 : 60}P</strong>`;
  };

  const install = () => {
    window.renderHomeRecord = render;
    render();
    window.addEventListener('fishon-auth-change', render);
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
