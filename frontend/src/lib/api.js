// Helper file. Here we'll send the token through the header. This is reusable to help frontend talk to the backend. It will add a login token to requests and then send the user to login if the session expired

import { get } from 'svelte/store';
import { goto } from '$app/navigation';
import { token, clearAuth } from './auth';
import { env } from '$env/dynamic/public';

// In production the variable PUBLIC_API_URL is set to the deployed Flask URL
// Locally it comes from frontend/.env. Added a fallback so if it's missing the value is empty (|| '')
export const API_URL = env.PUBLIC_API_URL || '';

// Add the JWT Authorization header. This function is available to other modules and async allows the function to use await. It's important because HTTP requests are asynchronous. It also has a path parameter for the API endpoint we want to access here. Basically we need a central place to prepare API requests
export async function apiFetch(path, options = {}) {
	// Here we read the token on every apiFetch. We could do it when the app starts but the authentication status can change (login, logout etc). By doing it here we get the latest value
	const currentToken = get(token);

	// Prepare the headers because the http requests can contain things other than just the url. So we provide more information about the request. And using "options.headers" will allow more flexibility to the function (it doesn't prevent additional headers)
	const headers = {
		'Content-Type': 'application/json',
		...options.headers
	};

	// Here we actually add the JWT to the Authorization header. Flask can retrieve the token from the Authorization header and validate it
	if (currentToken) {
		headers['Authorization'] = `Bearer ${currentToken}`;
	}

	// Communicating with Flask
	const res = await fetch(API_URL + path, { ...options, headers });

	// If the token is missing or expired, log out and send the user to login
	if (res.status === 401) {
		clearAuth();
		goto('/login');
	}

	return res;
}
