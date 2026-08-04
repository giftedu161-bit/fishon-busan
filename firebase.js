import { initializeApp } from 'https://www.gstatic.com/firebasejs/12.16.0/firebase-app.js';
import { getAuth, GoogleAuthProvider, createUserWithEmailAndPassword, signInWithEmailAndPassword, signInWithPopup, signInAnonymously, onAuthStateChanged, signOut } from 'https://www.gstatic.com/firebasejs/12.16.0/firebase-auth.js';
import { getFirestore, addDoc, collection, doc, getDocs, limit, orderBy, query, serverTimestamp, setDoc } from 'https://www.gstatic.com/firebasejs/12.16.0/firebase-firestore.js';

const config = window.FISHON_FIREBASE_CONFIG;
window.addEventListener('DOMContentLoaded', () => {
  const openButton = document.querySelector('#emailLogin');
  const modal = document.querySelector('#emailLoginModal');
  const closeButton = document.querySelector('#closeEmailLogin');
  const submitButton = document.querySelector('#emailLoginSubmit');
  if (!openButton || !modal || !closeButton || !submitButton) return;
  openButton.onclick = () => {
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    document.querySelector('#emailLoginEmail').focus();
  };
  closeButton.onclick = () => { modal.classList.remove('open'); modal.setAttribute('aria-hidden', 'true'); };
  modal.onclick = event => { if (event.target === modal) closeButton.click(); };
  submitButton.onclick = async () => {
    const email = document.querySelector('#emailLoginEmail').value.trim();
    const password = document.querySelector('#emailLoginPassword').value;
    if (!email || !password) { window.toast?.('이메일과 비밀번호를 입력해주세요.'); return; }
    try {
      await window.fishonData.signInWithEmail(email, password);
      closeButton.click();
      window.show?.('home');
      window.toast?.('로그인됐어요. 정보가 저장됐어요!');
    } catch (error) {
      window.toast?.(error.code === 'auth/invalid-credential' ? '이메일 또는 비밀번호가 맞지 않아요.' : '로그인에 실패했어요.');
    }
  };
});
if (config) {
  const app = initializeApp(config);
  const auth = getAuth(app);
  const db = getFirestore(app);
  window.fishonData = {
    async signInGoogle() { return signInWithPopup(auth, new GoogleAuthProvider()); },
    async signInGuest() { return signInAnonymously(auth); },
    async startFreshGuest() { if (auth.currentUser?.isAnonymous) await signOut(auth); return signInAnonymously(auth); },
    async signOut() { return signOut(auth); },
    async signUpWithEmail(email, password) { return createUserWithEmailAndPassword(auth, email, password); },
    async signInWithEmail(email, password) { return signInWithEmailAndPassword(auth, email, password); },
    async saveUserProfile(user, profile = {}) {
      if (!user) throw new Error('로그인이 필요합니다.');
      await setDoc(doc(db, 'users', user.uid), {
        uid: user.uid,
        nickname: profile.nickname || user.displayName || (user.isAnonymous ? '부산 낚시꾼' : '피쉬온 회원'),
        email: user.email || null,
        isAnonymous: user.isAnonymous,
        photoURL: user.photoURL || null,
        lastLoginAt: serverTimestamp(),
        ...profile
      }, { merge: true });
    },
    async saveCatch(catchData) { return addDoc(collection(db, 'catches'), { ...catchData, createdAt: serverTimestamp() }); },
    async loadRanking() { const snap = await getDocs(query(collection(db, 'catches'), orderBy('lengthCm', 'desc'), limit(50))); return snap.docs.map(doc => ({ id: doc.id, ...doc.data() })); }
  };
  onAuthStateChanged(auth, async user => {
    window.fishonUser = user;
    window.dispatchEvent(new CustomEvent('fishon-auth-change', { detail: { user } }));
    if (user) {
      try { await window.fishonData.saveUserProfile(user); }
      catch (error) { console.warn('프로필 저장 실패', error); }
    }
  });
}
