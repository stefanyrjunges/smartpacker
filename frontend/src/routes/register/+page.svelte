<script>
	import { goto } from '$app/navigation';
	import { saveAuth } from '$lib/auth';

	let email = $state('');
	let password = $state('');
	let error = $state('');
	let submitting = $state(false);

	async function register(event) {
		event.preventDefault();
		error = '';
		submitting = true;

		const res = await fetch('/api/auth/register', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email, password })
		});

		const data = await res.json();

		if (!res.ok) {
			error = data.message || 'Registration failed.';
			submitting = false;
			return;
		}

		saveAuth(data.token, data.email);
		goto('/');
	}
</script>

<div class="auth-page">
	<div class="auth-card">
		<h1>SmartPack</h1>
		<p class="subtitle">Create an account</p>

		<form onsubmit={register} class="form-row">
			<div>
				<label for="email">Email</label>
				<input id="email" type="email" bind:value={email} required />
			</div>
			<div>
				<label for="password">Password</label>
				<input id="password" type="password" bind:value={password} required />
				<span class="hint">At least 6 characters</span>
			</div>

			{#if error}
				<p class="error">{error}</p>
			{/if}

			<button type="submit" class="btn-primary" disabled={submitting}>
				{submitting ? 'Creating account...' : 'Create account'}
			</button>
		</form>

		<p class="switch-link">
			Already have an account? <a href="/login">Sign in</a>
		</p>
	</div>
</div>

<style>
	.auth-page {
		min-height: calc(100vh - 52px);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 20px;
	}

	.auth-card {
		background: #fff;
		border: 1px solid #e5e5e5;
		border-radius: 10px;
		padding: 36px;
		width: 100%;
		max-width: 380px;
	}

	h1 {
		font-size: 22px;
		font-weight: 700;
		color: #2563eb;
		margin-bottom: 4px;
	}

	.subtitle {
		font-size: 14px;
		color: #666;
		margin-bottom: 24px;
	}

	.hint {
		font-size: 12px;
		color: #999;
		margin-top: 4px;
		display: block;
	}

	.switch-link {
		margin-top: 18px;
		font-size: 13px;
		color: #666;
		text-align: center;
	}

	.switch-link a {
		color: #2563eb;
	}
</style>
