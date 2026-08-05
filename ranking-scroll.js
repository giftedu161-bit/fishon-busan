(() => {
  const moveRankingRows = () => {
    const page = document.querySelector('#rankingPage');
    const results = document.querySelector('#rankingResults');
    if (!page || !results) return;
    [...page.children].forEach((child) => {
      if ((child.classList.contains('rank') || child.classList.contains('ranking-empty')) && child.parentElement !== results) {
        results.appendChild(child);
      }
    });
  };

  const init = () => {
    const page = document.querySelector('#rankingPage');
    if (!page) return;
    moveRankingRows();
    new MutationObserver(moveRankingRows).observe(page, { childList: true });
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
