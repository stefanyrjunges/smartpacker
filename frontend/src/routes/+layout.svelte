<script>
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { token, userEmail, clearAuth } from '$lib/auth';

	let { children } = $props();

	const authRoutes = ['/login', '/register'];

	// Check on every navigation if the user is logged in
	$effect(() => {
		const currentPath = $page.url.pathname;
		const isAuthPage = authRoutes.includes(currentPath);

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
