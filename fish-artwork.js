(() => {
  const artwork = [
    { matches: ['조피볼락', '우럭'], src: 'assets/fish-rockfish.png', alt: '우럭' },
    { matches: ['돌돔'], src: 'assets/fish-striped-beakfish.png', alt: '돌돔' },
    { matches: ['참돔'], src: 'assets/fish-red-seabream.png', alt: '참돔' },
    { matches: ['감성돔'], src: 'assets/fish-black-porgy.png', alt: '감성돔' },
    { matches: ['성게'], src: 'assets/species-sea-urchin.png', alt: '성게' },
    { matches: ['해삼'], src: 'assets/species-sea-cucumber.png', alt: '해삼' },
    { matches: ['망상어'], src: 'assets/species-surfperch.png', alt: '망상어' },
    { matches: ['전갱이'], src: 'assets/species-horse-mackerel.png', alt: '전갱이' }
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

  const updateHomeRecord = () => {
    const card = document.querySelector('#homeLatestRecord');
    const item = findArtwork(card?.querySelector('h3')?.textContent || '');
    const icon = card?.querySelector('.fish-art');
    if (item && icon && !icon.querySelector('img')) icon.innerHTML = imageMarkup(item);
  };

  const updateMyRecords = () => {
    document.querySelectorAll('#myRecordsList .my-record').forEach((row) => {
      const item = findArtwork(row.querySelector('b')?.textContent || '');
      const icon = row.querySelector(':scope > span');
      if (item && icon && !icon.querySelector('img')) icon.innerHTML = imageMarkup(item);
    });
  };

  const install = () => {
    updateCollection();
    updateRanking();
    updateHomeRecord();
    updateMyRecords();
    window.addEventListener('load', () => { updateCollection(); updateRanking(); updateHomeRecord(); updateMyRecords(); });
    const originalRenderRanking = window.renderLiveRanking;
    if (typeof originalRenderRanking === 'function') {
      window.renderLiveRanking = async (...args) => {
        const result = await originalRenderRanking(...args);
        updateRanking();
        return result;
      };
    }
    const originalRenderHome = window.renderHomeRecord;
    if (typeof originalRenderHome === 'function') {
      window.renderHomeRecord = async (...args) => {
        const result = await originalRenderHome(...args);
        updateHomeRecord();
        return result;
      };
    }
    const originalRenderRecords = window.renderMyRecords;
    if (typeof originalRenderRecords === 'function') {
      window.renderMyRecords = async (...args) => {
        const result = await originalRenderRecords(...args);
        updateMyRecords();
        return result;
      };
    }
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
