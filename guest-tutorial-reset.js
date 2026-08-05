(() => {
  const init = () => {
    const guestButton = document.querySelector('#guestLogin');
    if (!guestButton) return;
    const originalGuestLogin = guestButton.onclick;
    guestButton.onclick = async (event) => {
      const result = await originalGuestLogin?.call(guestButton, event);
      setTimeout(() => window.showFishonOnboarding?.(), 0);
      return result;
    };
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
