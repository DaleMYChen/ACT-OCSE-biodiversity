import { initializeApp } from 'https://www.gstatic.com/firebasejs/11.0.1/firebase-app.js'
    
// If you enabled Analytics in your project, add the Firebase SDK for Google Analytics
import { getAnalytics } from 'https://www.gstatic.com/firebasejs/11.0.1/firebase-analytics.js'

// Add Firebase products that you want to use
import { getAuth, signInWithEmailAndPassword, onAuthStateChanged, signOut } from 'https://www.gstatic.com/firebasejs/11.0.1/firebase-auth.js'
import { getFirestore, doc, onSnapshot, query } from 'https://www.gstatic.com/firebasejs/11.0.1/firebase-firestore.js'

export default class FirebaseAuthManager {
    constructor(firebaseConfig) {
        // Initialize Firebase
        const app = initializeApp(firebaseConfig);
        this.auth = getAuth(app)
        this.db = getFirestore(app);
        this.setupAuthStateListener();
    }

    setupAuthStateListener() {
        onAuthStateChanged(this.auth, async (user) => {
            if (user) {
                this.user = user;
                // const hasAccess = await this.checkUserAccess(user.uid);
                // if (!hasAccess) {
                //     console.error('User does not have access');
                //     await logout();
                //     return;


                htmx.ajax('GET', '/main', {
                    headers: {"uid": user.uid}
                })
            } else {
                this.user = null;
                htmx.ajax('GET', '/login')
            }
        });
    }

    async login(email, password) {
        try {
            await signInWithEmailAndPassword(this.auth, email, password)
            return { success: true };
        } catch (error) {
            console.error('Login Error:', error);
            return { success: false, error: error.code };
        }
    }

    async logout() {
        try {
            await signOut(this.auth);
            return { success: true };
        } catch (error) {
            console.error('Logout Error:', error);
            return { success: false, error: error.message };
        }
    }

    // setupSnapshotListener(variable, element){
    //     const unsub = onSnapshot(docRef, (doc) => {
    //         element.value = doc.data().name;
    //     }
    // }

    setupHtmxAuth(element) {
        element.addEventListener('htmx:configRequest', (event) => {
            event.detail.headers = { ...event.detail.headers, ...{ 'uid': this.user.uid } };
        });
    }

    async checkUserAccess(uid) {
        try {
            const usersRef = collection(this.db, 'users');
            const q = query(usersRef, where('uid', '==', uid));
            const querySnapshot = await getDocs(q);
            
            if (querySnapshot.empty) {
                console.error('No user document found');
                return false;
            }

            const userData = querySnapshot.docs[0].data();
            const groups = userData.group || [];
            
            return groups.includes('act-biodiversity');
        } catch (error) {
            console.error('Error checking user access:', error);
            return false;
        }
    }

}