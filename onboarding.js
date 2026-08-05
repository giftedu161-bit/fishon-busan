(() => {
  const storageKey = 'fishon-onboarding-complete';

  const init = () => {
    const overlay = document.querySelector('#onboarding');
    const slides = [...document.querySelectorAll('.onboarding-slide')];
    const dots = [...document.querySelectorAll('.onboarding-dots i')];
    const previous = document.querySelector('#onboardingPrev');
    const next = document.querySelector('#onboardingNext');
    const skip = document.querySelector('#onboardingSkip');
    if (!overlay || !slides.length) return;

    let current = 0;
    const complete = () => {
      localStorage.setItem(storageKey, 'true');
      overlay.hidden = true;
      document.body.classList.remove('onboarding-open');
    };
    const render = () => {
      slides.forEach((slide, index) => slide.classList.toggle('active', index === current));
      dots.forEach((dot, index) => dot.classList.toggle('active', index === current));
      previous.disabled = current === 0;
      next.textContent = current === slides.length - 1 ? '시작하기' : '다음';
    };

    const showTutorial = () => {
      current = 0;
      localStorage.removeItem(storageKey);
      overlay.hidden = false;
      document.body.classList.add('onboarding-open');
      render();
    };
    window.showFishonOnboarding = showTutorial;

    previous.addEventListener('click', () => { current = Math.max(0, current - 1); render(); });
    next.addEventListener('click', () => {
      if (current === slides.length - 1) complete();
      else { current += 1; render(); }
    });
    skip.addEventListener('click', complete);

    if (localStorage.getItem(storageKey) === 'true') return;
    overlay.hidden = false;
    document.body.classList.add('onboarding-open');
    render();
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
