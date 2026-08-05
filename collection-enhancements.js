(() => {
  const catalog = [
    ['감성돔','어류','assets/fish-black-porgy.png'],['우럭','어류','assets/fish-rockfish.png'],['복어','어류',''],['참돔','어류','assets/fish-red-seabream.png'],['광어','어류',''],['농어','어류',''],['숭어','어류',''],['고등어','어류',''],['전갱이','어류','assets/species-horse-mackerel.png'],['붕장어','어류',''],['돌돔','어류','assets/fish-striped-beakfish.png'],['벵에돔','어류',''],['볼락','어류',''],['망상어','어류','assets/species-surfperch.png'],['학공치','어류',''],['삼치','어류',''],['갈치','어류',''],['도다리','어류',''],['쥐노래미','어류',''],['성대','어류',''],['주꾸미','두족류',''],['문어','두족류',''],['갑오징어','두족류',''],['해삼','기타','assets/species-sea-cucumber.png'],['성게','기타','assets/species-sea-urchin.png']
  ].map(([name, category, image]) => ({ name, category, image }));
  let records = [];
  let filter = 'all';
  let category = 'all';
  let sort = 'name';

  const canonicalName = (value = '') => {
    const name = String(value).replace(/\s/g, '');
    if (name.includes('조피볼락') || name.includes('우럭')) return '우럭';
    if (name.includes('넙치') || name.includes('광어')) return '광어';
    if (name.includes('참문어') || name === '문어') return '문어';
    return catalog.find((item) => name.includes(item.name))?.name || String(value).replace(/\([^)]*\)/g, '').trim();
  };
  const recordTime = (record) => record.createdAt?.toDate?.()?.getTime?.() || Number(record.clientCreatedAt) || 0;
  const groupedRecords = () => {
    const groups = new Map();
    records.forEach((record) => {
      const name = canonicalName(record.species);
      if (!groups.has(name)) groups.set(name, []);
      groups.get(name).push(record);
    });
    return groups;
  };
  const artwork = (item, locked = false) => item.image
    ? `<img class="collection-species-image${locked ? ' locked' : ''}" src="${item.image}" alt="${item.name}" />`
    : locked
      ? `<img class="collection-species-image locked collection-generic-image" src="assets/fish-striped-beakfish.png" alt="미발견 어종 실루엣" />`
      : '<span class="collection-silhouette" aria-hidden="true">🐟</span>';

  const updateSummary = (foundCount) => {
    const total = catalog.length;
    const percent = Math.round(foundCount / total * 100);
    document.querySelector('.collection-count').textContent = `${foundCount} / ${total}`;
    const summary = document.querySelectorAll('.collection-summary>div');
    if (summary[0]) summary[0].querySelector('strong').innerHTML = `${foundCount} <small>/ ${total}</small>`;
    if (summary[1]) summary[1].querySelector('strong').innerHTML = `${percent} <small>%</small>`;
    summary.forEach((item) => { const bar = item.querySelector('i em'); if (bar) bar.style.width = `${percent}%`; });
    const reward = document.querySelector('#collectionReward');
    if (reward) reward.innerHTML = `<b>신규 어종 최초 인증 +50P</b><span>현재 발견 보너스 기준 ${foundCount * 50}P</span>`;
  };

  const renderCards = () => {
    const grid = document.querySelector('#collectionPage .collection-grid');
    if (!grid) return;
    const groups = groupedRecords();
    updateSummary(catalog.filter((item) => groups.has(item.name)).length);
    let items = catalog.map((item) => {
      const catches = groups.get(item.name) || [];
      const best = catches.reduce((max, record) => Math.max(max, Number(record.lengthCm) || 0), 0);
      const latest = catches.reduce((max, record) => Math.max(max, recordTime(record)), 0);
      return { ...item, catches, found: catches.length > 0, best, latest };
    });
    if (filter === 'found') items = items.filter((item) => item.found);
    if (filter === 'unfound') items = items.filter((item) => !item.found);
    if (category !== 'all') items = items.filter((item) => item.category === category);
    if (sort === 'recent') items.sort((a, b) => b.latest - a.latest || a.name.localeCompare(b.name, 'ko'));
    else if (sort === 'largest') items.sort((a, b) => b.best - a.best || a.name.localeCompare(b.name, 'ko'));
    else items.sort((a, b) => a.name.localeCompare(b.name, 'ko'));

    grid.innerHTML = items.map((item) => `<button type="button" class="fish-card collection-card${item.found ? ' found' : ' locked'}" data-collection-species="${item.name}">
      <span class="collection-artwork">${artwork(item, !item.found)}</span>
      <b>${item.name}</b>
      <strong>${item.found ? `${item.best.toFixed(1)} <small>cm</small>` : '미발견'}</strong>
      ${item.found ? '<em class="collection-new-badge">최초 발견 +50P</em>' : '<em class="collection-lock">LOCKED</em>'}<i></i>
    </button>`).join('') || '<p class="collection-no-result">조건에 맞는 어종이 없어요.</p>';
  };

  const speciesMetadata = (name) => {
    const source = (window.BUSAN_SPECIES_DATA || []).find((item) => item.name.includes(name) || (name === '우럭' && item.name.includes('조피볼락')) || (name === '광어' && item.name.includes('넙치')) || (name === '문어' && item.name.includes('참문어')));
    return source || { habitats: ['부산 연안'], seasons: ['시기 정보 준비 중'], traits: ['상세 특징 준비 중'] };
  };
  const openDetail = (name) => {
    const item = catalog.find((entry) => entry.name === name);
    const catches = groupedRecords().get(name) || [];
    const best = catches.reduce((max, record) => Math.max(max, Number(record.lengthCm) || 0), 0);
    const firstTime = catches.reduce((min, record) => Math.min(min, recordTime(record) || Infinity), Infinity);
    const metadata = speciesMetadata(name);
    const modal = document.querySelector('#collectionDetailModal');
    modal.querySelector('.collection-detail-art').innerHTML = artwork(item, !catches.length);
    modal.querySelector('#collectionDetailName').textContent = name;
    modal.querySelector('#collectionDetailStatus').textContent = catches.length ? `발견 완료 · ${catches.length}회 기록` : '아직 발견하지 못한 어종';
    modal.querySelector('#collectionDetailHabitat').textContent = metadata.habitats.join(' · ');
    modal.querySelector('#collectionDetailSeason').textContent = metadata.seasons.join(' · ');
    modal.querySelector('#collectionDetailTraits').textContent = metadata.traits.join(' · ');
    modal.querySelector('#collectionDetailBest').textContent = best ? `${best.toFixed(1)} cm` : '-';
    modal.querySelector('#collectionDetailFirst').textContent = Number.isFinite(firstTime) ? new Date(firstTime).toLocaleDateString('ko-KR') : '-';
    modal.querySelector('.collection-detail-reward').hidden = !catches.length;
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
  };

  const loadRecords = async () => {
    const user = window.fishonUser;
    records = [];
    if (user && window.fishonData) {
      try {
        const source = window.fishonData.loadMyRecords?.(user.uid) || window.fishonData.loadRanking?.() || [];
        records = (await Promise.resolve(source)).filter((record) => record.userId === user.uid);
      } catch (_) { records = []; }
    }
    renderCards();
  };

  const init = () => {
    const page = document.querySelector('#collectionPage');
    const copy = page?.querySelector('.collection-copy');
    if (!page || !copy || document.querySelector('#collectionTools')) return;
    copy.insertAdjacentHTML('afterend', `<section class="collection-reward" id="collectionReward"></section><section class="collection-tools" id="collectionTools"><div class="collection-filter"><button class="selected" data-filter="all">전체</button><button data-filter="found">발견</button><button data-filter="unfound">미발견</button></div><div class="collection-selects"><select id="collectionCategory" aria-label="생물 분류"><option value="all">모든 분류</option><option value="어류">어류</option><option value="두족류">두족류</option><option value="기타">기타</option></select><select id="collectionSort" aria-label="도감 정렬"><option value="name">가나다순</option><option value="recent">최근 발견순</option><option value="largest">최대 길이순</option></select></div></section>`);
    document.body.insertAdjacentHTML('beforeend', `<div class="collection-detail-modal" id="collectionDetailModal" aria-hidden="true"><section role="dialog" aria-modal="true" aria-label="어종 상세 정보"><button class="collection-detail-close" aria-label="닫기">×</button><div class="collection-detail-art"></div><p class="eyebrow">BUSAN SPECIES GUIDE</p><h2 id="collectionDetailName"></h2><p id="collectionDetailStatus" class="collection-detail-status"></p><div class="collection-detail-stats"><div><small>내 최대 길이</small><b id="collectionDetailBest">-</b></div><div><small>첫 발견</small><b id="collectionDetailFirst">-</b></div></div><dl><div><dt>서식 환경</dt><dd id="collectionDetailHabitat"></dd></div><div><dt>출현 시기</dt><dd id="collectionDetailSeason"></dd></div><div><dt>주요 특징</dt><dd id="collectionDetailTraits"></dd></div></dl><p class="collection-detail-reward">✦ 도감 최초 발견 보너스 +50P</p></section></div>`);
    document.querySelector('#collectionTools').addEventListener('click', (event) => {
      const button = event.target.closest('[data-filter]');
      if (!button) return;
      filter = button.dataset.filter;
      document.querySelectorAll('#collectionTools [data-filter]').forEach((item) => item.classList.toggle('selected', item === button));
      renderCards();
    });
    document.querySelector('#collectionCategory').addEventListener('change', (event) => { category = event.target.value; renderCards(); });
    document.querySelector('#collectionSort').addEventListener('change', (event) => { sort = event.target.value; renderCards(); });
    page.querySelector('.collection-grid').addEventListener('click', (event) => { const card = event.target.closest('[data-collection-species]'); if (card) openDetail(card.dataset.collectionSpecies); });
    const modal = document.querySelector('#collectionDetailModal');
    const close = () => { modal.classList.remove('open'); modal.setAttribute('aria-hidden', 'true'); };
    modal.querySelector('.collection-detail-close').addEventListener('click', close);
    modal.addEventListener('click', (event) => { if (event.target === modal) close(); });
    document.querySelectorAll('[data-go="collection"]').forEach((button) => button.addEventListener('click', () => setTimeout(loadRecords, 0)));
    window.addEventListener('fishon-auth-change', loadRecords);
    window.addEventListener('load', loadRecords);
    window.renderFishonCollection = loadRecords;
    loadRecords();
    setTimeout(loadRecords, 0);
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
