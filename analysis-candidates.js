(() => {
  const asPercent = (value) => {
    const number = Number(String(value ?? '').replace('%', ''));
    return Number.isFinite(number) ? (number <= 1 ? Math.round(number * 100) : Math.round(number)) : 0;
  };

  const install = () => {
    const originalVerification = window.renderAiVerification;
    if (typeof originalVerification !== 'function') return;

    window.renderBusanSpeciesCandidates = (primaryName, score, note) => {
      const data = window.BUSAN_SPECIES_DATA || [];
      const primary = window.findBusanSpecies?.(primaryName) || data[0];
      const panel = document.querySelector('#busanDbPanel');
      if (!primary || !panel) return;
      const primaryScore = asPercent(score) || (primary.confidence === 'high' ? 82 : 72);
      const candidates = [primary, ...data.filter((item) => item.id !== primary.id).slice(0, 2)]
        .map((item, index) => ({ item, score: index === 0 ? primaryScore : Math.max(18, primaryScore - (index * 11 + 3)) }));

      document.querySelector('#dbSpeciesCount').textContent = `상위 ${candidates.length}개 후보`;
      document.querySelector('#dbPrimarySpecies').textContent = `${primary.name} · 1순위`;
      document.querySelector('#dbPrimaryMeta').textContent = `${primary.habitats.join(' · ')} · ${primary.seasons.join(' · ')}`;
      document.querySelector('#dbPrimaryScore').textContent = `${primaryScore}%`;
      document.querySelector('#dbCandidates').innerHTML = candidates.slice(1).map(({ item, score: candidateScore }, index) => `
        <button type="button" class="db-candidate" data-species="${item.name}" data-score="${candidateScore}">
          <span>후보 ${index + 2}</span><b>${item.name}</b><em>${candidateScore}%</em>
        </button>`).join('');
      panel.querySelector('.db-note').textContent = note || '후보를 직접 선택할 수 있습니다. 선택한 어종은 조과 기록에 반영됩니다.';
      const primaryCard = panel.querySelector('.db-main');
      primaryCard?.setAttribute('data-selected-species', primary.name);
      primaryCard?.setAttribute('data-selected-score', String(primaryScore));
    };

    window.renderAiVerification = (result = {}) => {
      originalVerification(result);
      const confidence = asPercent(result.confidence || window.fishonAnalysisConfidence);
      const guide = document.querySelector('#analysisConfidenceGuide');
      if (guide) guide.hidden = !(confidence >= 40 && confidence <= 70);
      if (result.species) window.renderBusanSpeciesCandidates(result.species, `${confidence}%`, result.detail);
    };

    document.addEventListener('click', (event) => {
      const candidate = event.target.closest('.db-candidate, .db-main[data-selected-species]');
      if (!candidate) return;
      const species = candidate.dataset.species || candidate.dataset.selectedSpecies;
      const confidence = asPercent(candidate.dataset.score || candidate.dataset.selectedScore);
      window.fishonSelectedSpecies = species;
      window.renderAiVerification({
        species,
        confidence: confidence / 100,
        verified: confidence >= 40,
        detail: `${species} 후보를 직접 선택했습니다. 사진과 실제 어종이 일치하는지 한 번 더 확인해주세요.`
      });
      window.toast?.(`${species}(으)로 조과 어종을 선택했어요.`);
    });
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
