import { initializeApp } from 'https://www.gstatic.com/firebasejs/12.16.0/firebase-app.js';
import { getAuth, GoogleAuthProvider, signInWithPopup, signInAnonymously, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/12.16.0/firebase-auth.js';
import { getFirestore, addDoc, collection, getDocs, limit, orderBy, query, serverTimestamp } from 'https://www.gstatic.com/firebasejs/12.16.0/firebase-firestore.js';

const config = window.FISHON_FIREBASE_CONFIG;
if (config) {
  const app = initializeApp(config);
  const auth = getAuth(app);
  const db = getFirestore(app);
  window.fishonData = {
    async signInGoogle() { return signInWithPopup(auth, new GoogleAuthProvider()); },
    async signInGuest() { return signInAnonymously(auth); },
    async saveCatch(catchData) { return addDoc(collection(db, 'catches'), { ...catchData, createdAt: serverTimestamp() }); },
    async loadRanking() { const snap = await getDocs(query(collection(db, 'catches'), orderBy('lengthCm', 'desc'), limit(50))); return snap.docs.map(doc => ({ id: doc.id, ...doc.data() })); }
  };
  onAuthStateChanged(auth, user => { window.fishonUser = user; });
}
