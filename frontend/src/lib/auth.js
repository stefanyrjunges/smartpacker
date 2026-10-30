// This file saved the login token and email so the app can remember the user is logged in (meaning it persists the authentication information between pages and page loads)

import { writable } from 'svelte/store';

// Read whatever was saved in localStorage when the app first loads. localStorage will be providing persistence to the app because the contents remain available after refreshing/closing browser. If nothing was saved then return null
const savedToken = typeof localStorage !== 'undefined' ? localStorage.getItem('token') : null;
const savedEmail = typeof localStorage !== 'undefined' ? localStorage.getItem('email') : null;

// Creating Svelte stores. This will allow the app to share state across components
export const token = writable(savedToken);
export const userEmail = writable(savedEmail);

// Save the authentication information with the JWT returned by Flask and the user's email
export function saveAuth(newToken, email) {
	localStorage.setItem('token', newToken);
	localStorage.setItem('email', email);
	token.set(newToken);
	userEmail.set(email);
}

// Clear the authentication information for logout or when a session is rejected by the backend
export function clearAuth() {
	localStorage.removeItem('token');
	localStorage.removeItem('email');
	token.set(null);
	userEmail.set(null);
}
