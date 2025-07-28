import React, { createContext, useState, useEffect, useContext } from 'react';
import { getAuth, onAuthStateChanged } from 'firebase/auth';
import { app } from '../../firebase.js'; // Make sure you export your initialized firebase app

// Create the context
const AuthContext = createContext();

// Create a custom hook to use the context easily
export const useAuth = () => {
    return useContext(AuthContext);
};

// Create the provider component
export const AuthProvider = ({ children }) => {
    const [currentUser, setCurrentUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const auth = getAuth(app);
        const unsubscribe = onAuthStateChanged(auth, user => {
            setCurrentUser(user);
            setLoading(false);
        });

        return unsubscribe;
    }, []);

    // Function to get the current user's ID token
    const getAuthToken = async () => {
        if (!currentUser) return null;
        return await currentUser.getIdToken();
    };

    const value = {
        currentUser,
        getAuthToken
    };

    return (
        <AuthContext.Provider value={value}>
            {!loading && children}
        </AuthContext.Provider>
    );
};