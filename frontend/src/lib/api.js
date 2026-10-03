import { get } from 'svelte/store';
import { token } from './auth';
import { PUBLIC_API_URL } from '$env/static/public';

// In production PUBLIC_API_URL is the deployed Flask URL.
// Locally it is empty, so requests stay as "/api/..." and go through the Vite proxy.
export const API_URL = PUBLIC_API_URL || '';

// A thin wrapper around fetch that adds the JWT Authorization header.
export function apiFetch(path, options = {}) {
	const currentToken = get(token);

	const headers = {
		'Content-Type': 'application/json',
		...options.headers
	};

	if (currentToken) {
		headers['Authorization'] = `Bearer ${currentToken}`;
	}

	return fetch(API_URL + path, { ...options, headers });
}
