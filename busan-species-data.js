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

window.renderBusanSpeciesCandidates = function (primaryName = '감성돔') {
  const primary = window.findBusanSpecies(primaryName) || window.BUSAN_SPECIES_DATA[0];
  const alternatives = window.BUSAN_SPECIES_DATA.filter(item => item.id !== primary.id).slice(0, 3);
  const panel = document.querySelector('#busanDbPanel');
  if (!panel) return;
  document.querySelector('#dbSpeciesCount').textContent = `${window.BUSAN_SPECIES_DATA.length}종 기준`;
  document.querySelector('#dbPrimarySpecies').textContent = primary.name;
  document.querySelector('#dbPrimaryMeta').textContent = `${primary.habitats.join(' · ')} · ${primary.seasons.join(' · ')}`;
  document.querySelector('#dbPrimaryScore').textContent = primary.confidence === 'high' ? '96%' : '88%';
  document.querySelector('#dbCandidates').innerHTML = alternatives.map((item, index) => `<button type="button">후보 ${index + 2} <b>${item.name}</b> · ${82 - index * 5}%</button>`).join('');
};

window.addEventListener('DOMContentLoaded', () => window.renderBusanSpeciesCandidates());
