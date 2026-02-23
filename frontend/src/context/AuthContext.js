import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('nexus_token'));
    const [loading, setLoading] = useState(true);
    const [meetStatus, setMeetStatus] = useState(null);

    const api = axios.create({
        baseURL: API,
        headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    // Add token to all requests
    api.interceptors.request.use((config) => {
        const currentToken = localStorage.getItem('nexus_token');
        if (currentToken) {
            config.headers.Authorization = `Bearer ${currentToken}`;
        }
        return config;
    });

    const fetchUser = useCallback(async () => {
        if (!token) {
            setLoading(false);
            return;
        }
        try {
            const response = await api.get('/auth/me');
            setUser(response.data);
            // Fetch meet status for adults
            if (response.data.age_band === 'adult') {
                try {
                    const meetResponse = await api.get('/meet/status');
                    setMeetStatus(meetResponse.data);
                } catch (e) {
                    console.error('Failed to fetch meet status');
                }
            }
        } catch (error) {
            console.error('Failed to fetch user:', error);
            logout();
        } finally {
            setLoading(false);
        }
    }, [token]);

    useEffect(() => {
        fetchUser();
    }, [fetchUser]);

    const login = async (email, password) => {
        const response = await api.post('/auth/login', { email, password });
        const { access_token, user: userData } = response.data;
        localStorage.setItem('nexus_token', access_token);
        setToken(access_token);
        setUser(userData);
        return userData;
    };

    const signup = async (data) => {
        const response = await api.post('/auth/signup', data);
        const { access_token, user: userData } = response.data;
        localStorage.setItem('nexus_token', access_token);
        setToken(access_token);
        setUser(userData);
        return userData;
    };

    const logout = () => {
        localStorage.removeItem('nexus_token');
        setToken(null);
        setUser(null);
        setMeetStatus(null);
    };

    const ageAssure = async () => {
        const response = await api.post('/meet/age-assure');
        setMeetStatus({
            meet_locked: false,
            reason: 'Meet is unlocked',
            age_assured_18plus: true,
            meet_enabled: true,
        });
        return response.data;
    };

    const refreshMeetStatus = async () => {
        if (user?.age_band === 'adult') {
            try {
                const response = await api.get('/meet/status');
                setMeetStatus(response.data);
            } catch (e) {
                console.error('Failed to refresh meet status');
            }
        }
    };

    const value = {
        user,
        token,
        loading,
        login,
        signup,
        logout,
        api,
        meetStatus,
        ageAssure,
        refreshMeetStatus,
        isAdult: user?.age_band === 'adult',
        canAccessMeet: meetStatus && !meetStatus.meet_locked,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
