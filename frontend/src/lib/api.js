import { get } from 'svelte/store';
import { token } from './auth';

// A thin wrapper around fetch that adds the JWT Authorization header.
// Usage is exactly like fetch() — same arguments, same return value.
export function apiFetch(url, options = {}) {
	const currentToken = get(token);

	const headers = {
		'Content-Type': 'application/json',
		...options.headers
	};

	if (currentToken) {
		headers['Authorization'] = `Bearer ${currentToken}`;
	}

	return fetch(url, { ...options, headers });
}
