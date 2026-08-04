// 부산 연안 낚시·관찰용 1차 종 후보 데이터. 모델 학습 완료 데이터가 아닌 판별 보조 사전입니다.
// 출처: 국립수산과학원·부산광역시 공개 자료(2026-08 확인).
window.BUSAN_SPECIES_DATA = [
  { id:'black_porgy', name:'감성돔', scientificName:'Acanthopagrus schlegelii', group:'어류', habitats:['암초','해조류','모래'], maxDepthM:50, seasons:['봄','가을','겨울'], traits:['검은빛 은회색 몸','강한 등지느러미 가시','둥근 체형'], confidence:'high' },
  { id:'rockfish', name:'조피볼락(우럭)', scientificName:'Sebastes schlegelii', group:'어류', habitats:['암초','방파제'], seasons:['봄','가을','겨울'], traits:['짙은 갈색 얼룩','가시 많은 등지느러미','넓은 입'], confidence:'high' },
  { id:'olive_flounder', name:'넙치(광어)', scientificName:'Paralichthys olivaceus', group:'어류', habitats:['모래','펄'], seasons:['사계절'], traits:['두 눈이 몸의 왼쪽','납작한 타원형 몸','갈색 반점'], confidence:'high' },
  { id:'sea_bass', name:'농어', scientificName:'Lateolabrax japonicus', group:'어류', habitats:['연안','하구','방파제'], seasons:['봄','가을'], traits:['은회색 길쭉한 몸','큰 입','두 갈래 꼬리'], confidence:'medium' },
  { id:'mullet', name:'숭어', scientificName:'Mugil cephalus', group:'어류', habitats:['연안','하구','항만'], seasons:['사계절'], traits:['굵은 비늘','둥근 머리','은색 몸'], confidence:'medium' },
  { id:'chub_mackerel', name:'고등어', scientificName:'Scomber japonicus', group:'어류', habitats:['연안','외해'], seasons:['여름','가을'], traits:['등쪽 물결무늬','방추형 몸','갈라진 꼬리'], confidence:'medium' },
  { id:'japanese_horse_mackerel', name:'전갱이', scientificName:'Trachurus japonicus', group:'어류', habitats:['방파제','연안'], seasons:['여름','가을'], traits:['옆줄의 단단한 비늘','큰 눈','은회색 몸'], confidence:'medium' },
  { id:'conger_eel', name:'붕장어', scientificName:'Conger myriaster', group:'어류', habitats:['모래','암초','항만'], seasons:['봄','여름','가을'], traits:['긴 뱀장어형 몸','등지느러미가 길게 이어짐'], confidence:'medium' },
  { id:'common_octopus', name:'참문어', scientificName:'Octopus vulgaris', group:'두족류', habitats:['암초','방파제'], seasons:['봄','가을'], traits:['팔 8개','둥근 머리','색 변화'], confidence:'medium' },
  { id:'webfoot_octopus', name:'주꾸미', scientificName:'Amphioctopus fangsiao', group:'두족류', habitats:['모래','펄'], seasons:['봄'], traits:['작은 몸','팔 8개','둥근 외투막'], confidence:'medium' },
  { id:'sea_cucumber', name:'해삼', scientificName:'Apostichopus japonicus', group:'극피동물', habitats:['암초','모래'], seasons:['사계절'], traits:['원통형 몸','돌기','느린 이동'], confidence:'medium' },
  { id:'sea_urchin', name:'성게', scientificName:'Mesocentrotus nudus', group:'극피동물', habitats:['암초','해조류'], seasons:['사계절'], traits:['구형 몸','긴 가시'], confidence:'medium' }
];

window.findBusanSpecies = function (name) {
  const key = String(name || '').replace(/\s/g, '');
  return window.BUSAN_SPECIES_DATA.find(item => item.name.replace(/\([^)]*\)/g, '').replace(/\s/g, '') === key) || null;
};

window.renderBusanSpeciesCandidates = function (primaryName = '감성돔', score = null, note = null) {
  const primary = window.findBusanSpecies(primaryName) || window.BUSAN_SPECIES_DATA[0];
  const alternatives = window.BUSAN_SPECIES_DATA.filter(item => item.id !== primary.id).slice(0, 3);
  const panel = document.querySelector('#busanDbPanel');
  if (!panel) return;
  document.querySelector('#dbSpeciesCount').textContent = `${window.BUSAN_SPECIES_DATA.length}종 기준`;
  document.querySelector('#dbPrimarySpecies').textContent = primary.name;
  document.querySelector('#dbPrimaryMeta').textContent = `${primary.habitats.join(' · ')} · ${primary.seasons.join(' · ')}`;
  document.querySelector('#dbPrimaryScore').textContent = score || (primary.confidence === 'high' ? '96%' : '88%');
  document.querySelector('#dbCandidates').innerHTML = alternatives.map((item, index) => `<button type="button">후보 ${index + 2} <b>${item.name}</b> · ${82 - index * 5}%</button>`).join('');
  if (note) panel.querySelector('.db-note').textContent = note;
};

window.addEventListener('DOMContentLoaded', () => window.renderBusanSpeciesCandidates());

window.addEventListener('DOMContentLoaded', () => {
  const grid = document.querySelector('#collectionPage .collection-grid');
  if (!grid) return;
  const collection = [
    ['감성돔', '🐟', '42.8 cm', true], ['우럭', '🐠', '31.2 cm', true], ['복어', '🐡', '18.4 cm', true],
    ['참돔', '🐟', '?', false], ['광어', '🐟', '?', false], ['농어', '🐟', '?', false],
    ['숭어', '🐟', '?', false], ['고등어', '🐟', '?', false], ['전갱이', '🐠', '?', false],
    ['붕장어', '🐍', '?', false], ['돌돔', '🐟', '?', false], ['벵에돔', '🐟', '?', false],
    ['볼락', '🐠', '?', false], ['망상어', '🐟', '?', false], ['학공치', '🐟', '?', false],
    ['삼치', '🐟', '?', false], ['갈치', '🐟', '?', false], ['도다리', '🐟', '?', false],
    ['쥐노래미', '🐠', '?', false], ['성대', '🐟', '?', false], ['쭈꾸미', '🐙', '?', false],
    ['문어', '🐙', '?', false], ['갑오징어', '🦑', '?', false], ['해삼', '🪸', '?', false], ['성게', '🦔', '?', false]
  ];
  grid.innerHTML = collection.map(([name, icon, size, found]) => `<article class="fish-card${found ? ' found' : ''}"><span>${icon}</span><b>${name}</b><strong>${size.includes(' ') ? size.replace(' ', ' <small>') + '</small>' : size}</strong><i></i></article>`).join('');
});

window.analyzeBusanPhotoFeatures = async function (image) {
  await image.decode?.().catch(() => {});
  const canvas = document.createElement('canvas');
  canvas.width = 64; canvas.height = 64;
  const context = canvas.getContext('2d', { willReadFrequently: true });
  context.drawImage(image, 0, 0, 64, 64);
  const pixels = context.getImageData(0, 0, 64, 64).data;
  let red = 0, green = 0, blue = 0, brightness = 0, saturation = 0;
  for (let i = 0; i < pixels.length; i += 4) {
    const r = pixels[i], g = pixels[i + 1], b = pixels[i + 2];
    red += r; green += g; blue += b; brightness += (r + g + b) / 3;
    saturation += Math.max(r, g, b) - Math.min(r, g, b);
  }
  const count = pixels.length / 4;
  red /= count; green /= count; blue /= count; brightness /= count; saturation /= count;
  let name = '감성돔';
  if (blue > red + 12 && saturation > 48) name = '고등어';
  else if (red > blue + 15 && brightness < 150) name = '조피볼락(우럭)';
  else if (brightness > 168 && saturation < 44) name = '숭어';
  else if (brightness < 108) name = '붕장어';
  const confidence = `${Math.max(58, Math.min(82, Math.round(62 + Math.abs(red - blue) / 4 + saturation / 13)))}%`;
  return { name, confidence, note: `사진 특징 기반 베타 분석 · 밝기 ${Math.round(brightness)} · 색상 대비 ${Math.round(saturation)}. 측정매트·어종 특징을 함께 확인해주세요.` };
};

window.renderAiVerification = function ({ species = null, confidence = 0, verified = false, detail = '' }) {
  const submit = document.querySelector('#submitRecord');
  const length = Number(document.querySelector('#lengthInput')?.value);
  if (verified && confidence) window.fishonAnalysisConfidence = confidence;
  const displayedConfidence = window.fishonAnalysisConfidence || confidence;
  window.fishonAnalysisVerified = verified;
  document.querySelector('#analysisSpecies').textContent = species || '미확인';
  document.querySelector('#analysisConfidence').textContent = verified ? `AI 신뢰도 ${Math.round(displayedConfidence * 100)}%` : 'AI 어종 판별 실패';
  document.querySelector('#analysisLength').innerHTML = Number.isFinite(length) && length > 0 ? `${length.toFixed(1)} <small>cm</small>` : '- <small>cm</small>';
  const badge = document.querySelector('#analysisBadge');
  badge.textContent = verified ? '✓ AI 어종 검증 완료' : 'AI 검증 실패';
  badge.classList.toggle('verified', verified);
  document.querySelector('#analysisEvidenceTitle').textContent = verified ? 'AI Hub EfficientDet-D2 모델 검증 완료' : 'AI 모델이 물고기를 확실히 찾지 못했습니다';
  document.querySelector('#analysisEvidenceText').textContent = detail || (verified ? '사진에서 물고기와 어종 후보를 판별했습니다. 길이는 직접 측정값으로 확정합니다.' : '물고기 전체가 보이도록 밝은 곳에서 다시 촬영해주세요.');
  document.querySelector('#analysisVerification').innerHTML = verified ? '<span>✓</span><p><b>공식 랭킹 인증 가능</b><br>AI 어종 판별을 통과했습니다. 직접 측정 길이로 기록을 제출하세요.</p>' : '<span>!</span><p><b>공식 랭킹 인증 불가</b><br>AI가 물고기를 판별한 사진에서만 공식 기록을 제출할 수 있습니다.</p>';
  submit.disabled = !verified;
  submit.classList.toggle('disabled', !verified);
};

window.addEventListener('load', () => {
  const collectionProgress = document.querySelector('#collectionPage .collection-progress');
  if (collectionProgress && !document.querySelector('.collection-visual')) {
    collectionProgress.insertAdjacentHTML('beforebegin', `<article class="collection-visual"><img src="https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=900&q=80" alt="바다 물고기 디자인 사진" /><div class="collection-visual-copy"><span>BUSAN SEA FIELD GUIDE</span><b>부산 바다를<br>기록하는 도감</b><small>내가 인증한 조과 사진으로 도감을 채워보세요.</small></div><a class="collection-source" href="https://unsplash.com/s/photos/fish" target="_blank" rel="noopener">Photo · Unsplash ↗</a></article>`);
  }
  const analyzeButton = document.querySelector('#analyzeButton');
  if (!analyzeButton) return;
  analyzeButton.onclick = async () => {
    const image = document.querySelector('#analysisImage');
    if (!image?.src) { window.toast?.('먼저 물고기 사진을 촬영하거나 선택해주세요.'); return; }
    let apiResult;
    try {
      apiResult = await window.fishonAi?.analyze(image);
    } catch (error) { console.info('AI 서버 연결 실패', error); }
    const verified = Boolean(apiResult?.status === 'ready' && apiResult?.species);
    window.renderAiVerification({ species: apiResult?.species, confidence: apiResult?.confidence || 0, verified, detail: apiResult?.message });
    if (verified) window.renderBusanSpeciesCandidates(apiResult.species, `${Math.round(apiResult.confidence * 100)}%`, 'AI Hub EfficientDet-D2 실제 추론 결과');
    window.show?.('analysis');
    window.toast?.(verified ? `${apiResult.species} AI 검증을 완료했어요.` : 'AI가 물고기를 판별하지 못했어요. 다시 촬영해주세요.');
  };
  document.querySelector('#lengthInput')?.addEventListener('input', () => {
    if (window.fishonAnalysisVerified) window.renderAiVerification({ species: document.querySelector('#analysisSpecies')?.textContent, verified: true });
  });
});
