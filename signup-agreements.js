(() => {
  const init = () => {
    const submitButton = document.querySelector('.signup-submit');
    const terms = document.querySelector('#agreeTerms');
    const privacy = document.querySelector('#agreePrivacy');

    if (!submitButton || !terms || !privacy) return;

    const updateSubmitState = () => {
      const accepted = terms.checked && privacy.checked;
      submitButton.disabled = !accepted;
      submitButton.classList.toggle('disabled', !accepted);
      submitButton.setAttribute('aria-disabled', String(!accepted));
    };

    const originalSubmit = submitButton.onclick;
    submitButton.onclick = async (event) => {
      if (!(terms.checked && privacy.checked)) {
        event?.preventDefault();
        window.toast?.('이용약관과 개인정보처리방침에 모두 동의해주세요.');
        return;
      }
      return originalSubmit?.call(submitButton, event);
    };

    [terms, privacy].forEach((checkbox) => {
      checkbox.addEventListener('change', updateSubmitState);
    });

    document.querySelectorAll('.agreement-link').forEach((link) => {
      link.addEventListener('click', () => {
        const detail = document.querySelector(`#${link.dataset.agreement}Agreement`);
        if (!detail) return;
        detail.hidden = !detail.hidden;
        link.setAttribute('aria-expanded', String(!detail.hidden));
      });
    });

    updateSubmitState();
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
