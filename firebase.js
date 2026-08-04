import { initializeApp } from 'https://www.gstatic.com/firebasejs/12.16.0/firebase-app.js';
import { getAuth, GoogleAuthProvider, createUserWithEmailAndPassword, signInWithEmailAndPassword, signInWithPopup, signInAnonymously, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/12.16.0/firebase-auth.js';
import { getFirestore, addDoc, collection, doc, getDocs, limit, orderBy, query, serverTimestamp, setDoc } from 'https://www.gstatic.com/firebasejs/12.16.0/firebase-firestore.js';

const config = window.FISHON_FIREBASE_CONFIG;
if (config) {
  const app = initializeApp(config);
  const auth = getAuth(app);
  const db = getFirestore(app);
  window.fishonData = {
    async signInGoogle() { return signInWithPopup(auth, new GoogleAuthProvider()); },
    async signInGuest() { return signInAnonymously(auth); },
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
    if (user) {
      try { await window.fishonData.saveUserProfile(user); }
      catch (error) { console.warn('프로필 저장 실패', error); }
    }
  });
}
