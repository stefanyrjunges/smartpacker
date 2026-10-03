<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { apiFetch } from '$lib/api';

	const tripId = $derived($page.params.id);
	const mode = $derived($page.url.searchParams.get('mode') || 'view');
	const isEditing = $derived(mode === 'edit');

	let trip = $state(null);
	let activities = $state([]);
	let weather = $state(null);
	let loading = $state(true);
	let error = $state('');

	let newActivity = $state('');
	let addingActivity = $state(false);
	let activityError = $state('');

	let loadingWeather = $state(false);
	let weatherError = $state('');

	let deleting = $state(false);
	let saving = $state(false);

	const luggageLabels = {
		'checked': 'Checked bag',
		'carry-on': 'Carry-on',
		'backpack': 'Backpack'
	};

	onMount(async () => {
		await loadTrip();
	});

	async function loadTrip() {
		loading = true;
		error = '';

		const [tripRes, activitiesRes] = await Promise.all([
			apiFetch(`/trips/${tripId}`),
			apiFetch(`/trips/${tripId}/activities`)
		]);

		if (!tripRes.ok) {
			error = 'Trip not found.';
			loading = false;
			return;
		}

		trip = await tripRes.json();

		// The API returns dates like "Thu, 05 Nov 2026 00:00:00 GMT"
		// but <input type="date"> needs "YYYY-MM-DD", so we convert them
		trip.start_date = new Date(trip.start_date).toISOString().split('T')[0];
		trip.end_date = new Date(trip.end_date).toISOString().split('T')[0];

		activities = activitiesRes.ok ? await activitiesRes.json() : [];
		loading = false;
	}

	// Called whenever luggage or dates change in edit mode
	async function saveTrip() {
		saving = true;

		await apiFetch(`/trips/${tripId}`, {
			method: 'PUT',
			body: JSON.stringify({
				destination: trip.destination,
				luggage_type: trip.luggage_type,
				start_date: trip.start_date,
				end_date: trip.end_date
			})
		});

		saving = false;
	}

	async function addActivity(event) {
		event.preventDefault();
		activityError = '';
		addingActivity = true;

		const res = await apiFetch(`/trips/${tripId}/activities`, {
			method: 'POST',
			body: JSON.stringify({ activities: [newActivity] })
		});

		const data = await res.json();

		if (!res.ok) {
			activityError = data.message || 'Could not add activity.';
			addingActivity = false;
			return;
		}

		newActivity = '';
		addingActivity = false;

		const activitiesRes = await apiFetch(`/trips/${tripId}/activities`);
		activities = await activitiesRes.json();
	}

	async function removeActivity(activityId) {
		await apiFetch(`/trips/${tripId}/activities/${activityId}`, { method: 'DELETE' });
		activities = activities.filter((a) => a.id !== activityId);
	}

	async function loadWeather(refresh = false) {
		loadingWeather = true;
		weatherError = '';
		weather = null;

		const url = refresh
			? `/trips/${tripId}/weather?refresh=true`
			: `/trips/${tripId}/weather`;
		const res = await apiFetch(url);
		const data = await res.json();

		if (!res.ok || data.error) {
			weatherError = data.error || 'Could not load weather.';
		} else {
			weather = data;
		}

		loadingWeather = false;
	}

	async function deleteTrip() {
		if (!confirm('Delete this trip?')) return;
		deleting = true;
		await apiFetch(`/trips/${tripId}`, { method: 'DELETE' });
		goto('/');
	}
</script>

{#if loading}
	<div class="page"><p class="muted">Loading...</p></div>
{:else if error}
	<div class="page"><p class="error">{error}</p></div>
{:else}
	<div class="page">
		<div class="top-bar">
			<a href="/" class="back-link">← All trips</a>
			<div class="top-actions">
				{#if saving}<span class="saving-note">Saving...</span>{/if}
				{#if isEditing}
					<a href="/trips/{tripId}?mode=view" class="btn-secondary action-link">View</a>
					<button class="btn-danger" onclick={deleteTrip} disabled={deleting}>Delete trip</button>
				{:else}
					<a href="/trips/{tripId}?mode=edit" class="btn-primary action-link">Edit trip</a>
				{/if}
			</div>
		</div>

		<div class="card" style="margin-bottom: 20px;">
			<h1>{trip.destination}</h1>
			{#if isEditing}
				<div class="edit-fields">
					<div class="edit-field">
						<label for="start_date">Start date</label>
						<input
							id="start_date"
							type="date"
							bind:value={trip.start_date}
							onchange={saveTrip}
						/>
					</div>
					<div class="edit-field">
						<label for="end_date">End date</label>
						<input
							id="end_date"
							type="date"
							bind:value={trip.end_date}
							onchange={saveTrip}
						/>
					</div>
					<div class="edit-field">
						<label for="luggage_type">Luggage</label>
						<select id="luggage_type" bind:value={trip.luggage_type} onchange={saveTrip}>
							<option value="checked">Checked bag</option>
							<option value="carry-on">Carry-on</option>
							<option value="backpack">Backpack</option>
						</select>
					</div>
				</div>
			{:else}
				<div class="trip-meta">
					<span>{trip.start_date} → {trip.end_date}</span>
					<span class="badge">{luggageLabels[trip.luggage_type] || trip.luggage_type}</span>
				</div>
			{/if}
		</div>

		<div class="card" style="margin-bottom: 20px;">
			<h2 style="margin-bottom: 16px;">Activities</h2>

			{#if activities.length > 0}
				<ul class="activity-list">
					{#each activities as activity}
						<li>
							<span>{activity.activity}</span>
							{#if isEditing}
								<button class="btn-danger small" onclick={() => removeActivity(activity.id)}>Remove</button>
							{/if}
						</li>
					{/each}
				</ul>
			{:else}
				<p class="muted" style="margin-bottom: 12px;">No activities added yet.</p>
			{/if}

			{#if isEditing}
				<form class="add-activity-row" onsubmit={addActivity}>
					<input
						bind:value={newActivity}
						placeholder="e.g. hiking, swimming, nightlife"
						required
					/>
					<button type="submit" class="btn-primary" disabled={addingActivity}>Add</button>
				</form>

				{#if activityError}
					<p class="error" style="margin-top: 8px;">{activityError}</p>
				{/if}
			{/if}
		</div>

		<div class="card" style="margin-bottom: 20px;">
			<div class="section-header">
				<h2>Weather</h2>
				<button class="btn-secondary" onclick={() => loadWeather(weather !== null)} disabled={loadingWeather}>
					{loadingWeather ? 'Loading...' : weather ? 'Refresh' : 'Get weather'}
				</button>
			</div>

			{#if weatherError}
				<p class="error" style="margin-top: 12px;">{weatherError}</p>
			{:else if weather}
				<div class="weather-grid">
					<div class="weather-item">
						<span class="weather-label">Min temp</span>
						<span class="weather-value">{weather.min_temperature}°C</span>
					</div>
					<div class="weather-item">
						<span class="weather-label">Max temp</span>
						<span class="weather-value">{weather.max_temperature}°C</span>
					</div>
					<div class="weather-item">
						<span class="weather-label">Total rain</span>
						<span class="weather-value">{weather.total_precipitation} mm</span>
					</div>
					<div class="weather-item">
						<span class="weather-label">Rain expected</span>
						<span class="weather-value">{weather.rain_expected ? 'Yes' : 'No'}</span>
					</div>
				</div>
			{:else}
				<p class="muted" style="margin-top: 12px;">No weather data yet.</p>
			{/if}
		</div>

		<div style="text-align: right;">
			<a href="/trips/{tripId}/packing?mode={mode}" class="btn-primary action-link" style="padding: 10px 20px;">
				View packing list →
			</a>
		</div>
	</div>
{/if}

<style>
	.top-bar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;
	}

	.top-actions {
		display: flex;
		gap: 8px;
		align-items: center;
	}

	.saving-note {
		font-size: 13px;
		color: #888;
	}

	.back-link {
		font-size: 14px;
		color: #555;
	}

	.back-link:hover {
		color: #2563eb;
	}

	.trip-meta {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-top: 8px;
		font-size: 14px;
		color: #555;
	}

	.edit-fields {
		display: flex;
		gap: 16px;
		margin-top: 14px;
		flex-wrap: wrap;
	}

	.edit-field {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.edit-field input,
	.edit-field select {
		width: auto;
		font-size: 13px;
	}

	.badge {
		background: #f0f0f0;
		padding: 3px 10px;
		border-radius: 20px;
		font-size: 12px;
		color: #555;
	}

	.activity-list {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 8px;
		margin-bottom: 14px;
	}

	.activity-list li {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 8px 12px;
		background: #f9f9f9;
		border-radius: 6px;
		font-size: 14px;
	}

	.add-activity-row {
		display: flex;
		gap: 8px;
	}

	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.weather-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 12px;
		margin-top: 16px;
	}

	.weather-item {
		background: #f9f9f9;
		border-radius: 8px;
		padding: 12px 14px;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.weather-label {
		font-size: 12px;
		color: #888;
	}

	.weather-value {
		font-size: 18px;
		font-weight: 600;
	}

	.muted {
		color: #888;
		font-size: 14px;
	}

	button.small {
		padding: 4px 10px;
		font-size: 12px;
	}

	.action-link {
		display: inline-block;
		padding: 8px 16px;
		border-radius: 6px;
		font-size: 14px;
		font-weight: 500;
	}
</style>
