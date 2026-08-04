// 피쉬온 포인트 DB: 공개 지도상의 항·방파제 중심 좌표를 기준으로 수동 관리합니다.
// 실제 입장·낚시 가능 여부는 현장 표지와 관계 기관 안내를 반드시 확인해야 합니다.
window.FISHON_BUSAN_POINTS = [
  { id: 'songjeong-port', name: '송정항 동쪽 방파제', district: '해운대구', species: ['감성돔', '벵에돔'], latitude: 35.1791, longitude: 129.2009, status: '참고 포인트' },
  { id: 'mipo-port', name: '미포항 방파제', district: '해운대구', species: ['농어', '전갱이'], latitude: 35.1595, longitude: 129.1701, status: '참고 포인트' },
  { id: 'gongsu-port', name: '기장 공수항', district: '기장군', species: ['감성돔', '볼락'], latitude: 35.1888, longitude: 129.2189, status: '참고 포인트' },
  { id: 'daebyeon-port', name: '기장 대변항', district: '기장군', species: ['전갱이', '고등어'], latitude: 35.2316, longitude: 129.2265, status: '참고 포인트' },
  { id: 'gijang-gilcheon', name: '기장 길천 방파제', district: '기장군', species: ['감성돔', '숭어'], latitude: 35.3130, longitude: 129.2700, status: '참고 포인트' },
  { id: 'gijang-hakri', name: '기장 학리 방파제', district: '기장군', species: ['우럭', '감성돔'], latitude: 35.3213, longitude: 129.2756, status: '참고 포인트' },
  { id: 'songdo-beach', name: '송도해수욕장 일원', district: '서구', species: ['우럭', '볼락'], latitude: 35.0755, longitude: 129.0173, status: '참고 포인트' },
  { id: 'gamcheon-port', name: '감천항 중앙부두', district: '사하구', species: ['전갱이', '고등어'], latitude: 35.0824, longitude: 128.9985, status: '현장 규정 확인' },
  { id: 'dadaepo-port', name: '다대포항', district: '사하구', species: ['삼치', '볼락'], latitude: 35.0578, longitude: 128.9713, status: '참고 포인트' },
  { id: 'natgae-breakwater', name: '다대포 낫개방파제', district: '사하구', species: ['감성돔', '볼락'], latitude: 35.0470, longitude: 128.9656, status: '참고 포인트' },
  { id: 'gadeok-cheonseong', name: '가덕도 천성항', district: '강서구', species: ['광어', '우럭'], latitude: 35.0241, longitude: 128.8302, status: '참고 포인트' },
  { id: 'taejongdae', name: '태종대 해안 일원', district: '영도구', species: ['볼락', '감성돔'], latitude: 35.0514, longitude: 129.0878, status: '현장 규정 확인' }
];

window.addEventListener('load', () => {
  const points = window.FISHON_BUSAN_POINTS;
  const directory = document.querySelector('.point-directory');
  if (directory) {
    directory.innerHTML = `<div class="directory-head"><span>FISHON POINTS</span><b>부산 낚시 포인트</b><small>${points.length}곳</small></div>${points.map((point, index) => `<a class="point-row" href="https://www.openstreetmap.org/?mlat=${point.latitude}&mlon=${point.longitude}#map=15/${point.latitude}/${point.longitude}" target="_blank" rel="noopener"><span class="point-number">${index + 1}</span><span><b>${point.name}</b><small>${point.district} · ${point.species.join(' · ')}</small></span><em>${point.status} ↗</em></a>`).join('')}`;
  }

  const submitRecord = document.querySelector('#submitRecord');
  if (submitRecord) submitRecord.onclick = async () => {
    const lengthCm = Number(document.querySelector('#lengthInput')?.value);
    if (!window.fishonPhotoReady) { window.toast?.('사진을 먼저 선택하거나 촬영해주세요.'); return; }
    if (!Number.isFinite(lengthCm) || lengthCm <= 0) { window.toast?.('직접 측정한 길이를 입력해주세요.'); return; }
    const selectedPoint = points[0];
    const user = window.fishonUser;
    const species = document.querySelector('#dbPrimarySpecies')?.textContent?.trim() || '감성돔';
    const userName = user?.isAnonymous ? '게스트 사용자' : (localStorage.getItem('fishon-nickname') || user?.displayName || user?.email?.split('@')[0] || '부산 낚시꾼');
    try {
      if (!window.fishonData || !user) { window.toast?.('로그인 상태를 확인해주세요.'); return; }
      await window.fishonData.saveCatch({ userId: user.uid, userName, species, lengthCm, area: selectedPoint.name, pointId: selectedPoint.id, verified: true, verificationSource: 'photo-and-measurement' });
      window.show?.('ranking');
      await window.renderLiveRanking?.();
      window.toast?.('검증 사진 조건으로 등록되었어요');
    } catch (error) {
      console.error('기록 저장 실패', error);
      window.toast?.(error?.code === 'permission-denied' ? '저장 권한이 없어요. 다시 로그인해주세요.' : `기록 저장 실패: ${error?.message || '네트워크를 확인해주세요.'}`);
    }
  };
});
