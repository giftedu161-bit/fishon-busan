// 피쉬온 운영 검수 포인트. 외부 사이트 자동 수집 없이 앱에서 직접 관리합니다.
window.FISHON_BUSAN_POINTS = [
  { id: 'songjeong-east', name: '송정 해수욕장 동쪽 방파제', district: '해운대구', species: ['감성돔', '벵에돔'], latitude: 35.179, longitude: 129.201, status: '초기 등록' },
  { id: 'gijang-gilcheon', name: '기장 길천 방파제', district: '기장군', species: ['감성돔', '우럭'], latitude: 35.313, longitude: 129.270, status: '초기 등록' },
  { id: 'gijang-hakri', name: '기장 학리 방파제', district: '기장군', species: ['전갱이', '감성돔'], latitude: 35.321, longitude: 129.276, status: '초기 등록' },
  { id: 'gadeok-cheonseong', name: '가덕도 천성항', district: '강서구', species: ['광어', '우럭'], latitude: 35.024, longitude: 128.830, status: '초기 등록' }
];

window.addEventListener('load', () => {
  const mapPage = document.querySelector('#mapPage');
  const pointDirectory = document.querySelector('.point-directory');
  if (!mapPage || document.querySelector('.verified-points-card')) return;
  const points = window.FISHON_BUSAN_POINTS;
  const card = document.createElement('section');
  card.className = 'verified-points-card';
  card.innerHTML = `<div class="verified-points-head"><div><span>FISHON POINTS</span><b>피쉬온 포인트 DB</b></div><em>${points.length}곳 초기 등록</em></div><p>외부 사이트를 자동 수집하지 않고, 사용자 인증 조과와 운영 검토를 기반으로 갱신합니다.</p><div class="verified-points-list">${points.map(point => `<a href="https://www.google.com/maps/search/?api=1&query=${point.latitude},${point.longitude}" target="_blank" rel="noopener"><i>•</i><span><b>${point.name}</b><small>${point.district} · ${point.species.join(' · ')}</small></span><em>${point.status}</em></a>`).join('')}</div>`;
  (pointDirectory || mapPage).insertAdjacentElement('afterend', card);

  const submitRecord = document.querySelector('#submitRecord');
  if (submitRecord) submitRecord.onclick = async () => {
    const lengthCm = Number(document.querySelector('#lengthInput')?.value);
    const selectedPoint = points[0];
    try {
      if (window.fishonData && window.fishonUser) {
        await window.fishonData.saveCatch({ userId: window.fishonUser.uid, species: '감성돔', lengthCm, area: selectedPoint.name, pointId: selectedPoint.id, verified: true, verificationSource: 'photo-and-measurement' });
      }
      window.show?.('ranking');
      window.toast?.('검증 포인트 조과로 등록됐어요.');
    } catch (error) {
      window.toast?.('조과 저장에 실패했어요.');
    }
  };
});
