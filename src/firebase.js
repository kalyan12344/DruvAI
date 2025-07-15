import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// Your web app's Firebase configuration
// IMPORTANT: Replace this with your actual config from the Firebase console
const firebaseConfig = {
    apiKey: "AIzaSyDmMuRJpuHja69NHpvAwyhzLQa8LtLkb2s",
    authDomain: "deft-axon-455818-t8.firebaseapp.com",
    projectId: "deft-axon-455818-t8",
    storageBucket: "deft-axon-455818-t8.firebasestorage.app",
    messagingSenderId: "338967818277",
    appId: "1:338967818277:web:1831342f5795e0069d4fcc",
    measurementId: "G-YBX5PE0TG1"
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);

// Initialize and export Firebase services
export const auth = getAuth(app);
export const db = getFirestore(app);

