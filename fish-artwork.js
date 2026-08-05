(() => {
  const artwork = [
    { matches: ['조피볼락', '우럭'], src: 'assets/fish-rockfish.png', alt: '우럭' },
    { matches: ['돌돔'], src: 'assets/fish-striped-beakfish.png', alt: '돌돔' },
    { matches: ['참돔'], src: 'assets/fish-red-seabream.png', alt: '참돔' },
    { matches: ['감성돔'], src: 'assets/fish-black-porgy.png', alt: '감성돔' }
  ];

  const findArtwork = (text = '') => artwork.find((item) => item.matches.some((name) => text.includes(name)));
  const imageMarkup = (item) => `<img class="species-art" src="${item.src}" alt="${item.alt}" />`;

  const updateCollection = () => {
    document.querySelectorAll('#collectionPage .fish-card').forEach((card) => {
      const item = findArtwork(card.querySelector('b')?.textContent || '');
      const icon = card.querySelector('span');
      if (item && icon && !icon.querySelector('img')) icon.innerHTML = imageMarkup(item);
    });
  };

  const updateRanking = () => {
    document.querySelectorAll('#rankingPage .rank').forEach((row) => {
      const item = findArtwork(row.querySelector('p')?.textContent || '');
      const photo = row.querySelector('.rank-photo');
      if (item && photo && !photo.querySelector('img')) photo.innerHTML = imageMarkup(item);
    });
  };

  const install = () => {
    updateCollection();
    updateRanking();
    const originalRenderRanking = window.renderLiveRanking;
    if (typeof originalRenderRanking === 'function') {
      window.renderLiveRanking = async (...args) => {
        const result = await originalRenderRanking(...args);
        updateRanking();
        return result;
      };
    }
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
