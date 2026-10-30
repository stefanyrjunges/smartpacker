// Shared functionality. It will display the nav bar, check if the user is allowed to access the page and allow logout

<script>
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { token, userEmail, clearAuth } from '$lib/auth';

	let { children } = $props();

	// This is creating a list of routes that won't require authentication because someone who isn't logged in still needs to be able to access login and registration pages
	const authRoutes = ['/login', '/register'];

	// Check on every navigation if the user is logged in and keeping in mind the authentication status can change when the app is running
	$effect(() => {
		// Get the currentPath and also checks if the page is on the list of routes that don't require authentication
		const currentPath = $page.url.pathname;
		const isAuthPage = authRoutes.includes(currentPath);

		// If user doesn't have a token and the user isn't on the login/registration page, redirect them back to login
		if (!$token && !isAuthPage) {
			goto('/login');
		}
	});

	function logout() {
		clearAuth();
		goto('/login');
	}
</script>

<nav>
	<a href="/" class="logo-smp">SmartPack</a>
	// Add a conditional so the email and logout button will only appear if the user has a token
	{#if $token}
		<div class="nav-right">
			<span class="nav-email">{$userEmail}</span>
			<button class="logout-btn" onclick={logout}>Log out</button>
		</div>
	{/if}
</nav>

{@render children()}

<style>
	nav {
		background: #fff;
		border-bottom: none;
		padding: 0 20px;
		height: 52px;
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.nav-right {
		display: flex;
		align-items: center;
		gap: 14px;
	}

	.nav-email {
		font-size: 13px;
		color: #666;
	}

	.logout-btn {
		background: none;
		padding: 5px 12px;
		font-size: 13px;
		color: #444;
		cursor: pointer;
	}

	.logout-btn:hover {
		background: #f5f5f5;
	}
</style>
