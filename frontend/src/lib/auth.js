import { writable } from 'svelte/store';

// Read whatever was saved in localStorage when the app first loads
const savedToken = typeof localStorage !== 'undefined' ? localStorage.getItem('token') : null;
const savedEmail = typeof localStorage !== 'undefined' ? localStorage.getItem('email') : null;

export const token = writable(savedToken);
export const userEmail = writable(savedEmail);

export function saveAuth(newToken, email) {
	localStorage.setItem('token', newToken);
	localStorage.setItem('email', email);
	token.set(newToken);
	userEmail.set(email);
}

export function clearAuth() {
	localStorage.removeItem('token');
	localStorage.removeItem('email');
	token.set(null);
	userEmail.set(null);
}
