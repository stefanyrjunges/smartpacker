import { get } from 'svelte/store';
import { goto } from '$app/navigation';
import { token, clearAuth } from './auth';
import { env } from '$env/dynamic/public';

// In production PUBLIC_API_URL is set to the deployed Flask URL.
// Locally it comes from frontend/.env. If it is missing the value is empty.
export const API_URL = env.PUBLIC_API_URL || '';

// A thin wrapper around fetch that adds the JWT Authorization header.
export async function apiFetch(path, options = {}) {
	const currentToken = get(token);

	const headers = {
		'Content-Type': 'application/json',
		...options.headers
	};

	if (currentToken) {
		headers['Authorization'] = `Bearer ${currentToken}`;
	}

	const res = await fetch(API_URL + path, { ...options, headers });

	// If the token is missing or expired, log out and send the user to login
	if (res.status === 401) {
		clearAuth();
		goto('/login');
	}

	return res;
}
