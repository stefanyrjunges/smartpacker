<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { apiFetch } from '$lib/api';

	let trips = $state([]);
	let loading = $state(true);
	let error = $state('');
	let showForm = $state(false);

	let destination = $state('');
	let luggage_type = $state('checked');
	let start_date = $state('');
	let end_date = $state('');
	let submitting = $state(false);
	let formError = $state('');

	const luggageLabels = {
		'checked': 'Checked bag',
		'carry-on': 'Carry-on',
		'backpack': 'Backpack'
	};

	onMount(async () => {
		const res = await apiFetch('/trips');
		if (res.ok) {
			trips = await res.json();
		} else {
			error = 'Could not load trips.';
		}
		loading = false;
	});

	async function createTrip(event) {
		event.preventDefault();
		formError = '';
		submitting = true;

		const res = await apiFetch('/trips', {
			method: 'POST',
			body: JSON.stringify({ destination, luggage_type, start_date, end_date })
		});

		const data = await res.json();

		if (!res.ok) {
			formError = data.message || 'Something went wrong.';
			submitting = false;
			return;
		}

		goto(`/trips/${data.id}?mode=edit`);
	}
</script>

<div class="page">
	<div class="header">
		<h1>Your trips</h1>
		<button class="btn-primary" onclick={() => (showForm = !showForm)}>
			{showForm ? 'Cancel' : 'New trip'}
		</button>
	</div>

	{#if showForm}
		<div class="card" style="margin-bottom: 28px;">
			<h2 style="margin-bottom: 18px;">Plan a new trip</h2>
			<form onsubmit={createTrip} class="form-row">
				<div>
					<label for="destination">Destination</label>
					<input id="destination" bind:value={destination} placeholder="e.g. Paris" required />
				</div>

				<div>
					<label for="luggage">Luggage type</label>
					<select id="luggage" bind:value={luggage_type}>
						<option value="checked">Checked bag</option>
						<option value="carry-on">Carry-on</option>
						<option value="backpack">Backpack</option>
					</select>
				</div>

				<div class="date-row">
					<div>
						<label for="start">Start date</label>
						<input id="start" type="date" bind:value={start_date} required />
					</div>
					<div>
						<label for="end">End date</label>
						<input id="end" type="date" bind:value={end_date} required />
					</div>
				</div>

				{#if formError}
					<p class="error">{formError}</p>
				{/if}

				<button type="submit" class="btn-primary" disabled={submitting}>
					{submitting ? 'Creating...' : 'Create trip'}
				</button>
			</form>
		</div>
	{/if}

	{#if loading}
		<p class="muted">Loading...</p>
	{:else if error}
		<p class="error">{error}.</p>
	{:else if showForm}
		<!-- Hide the trip list while the create form is open -->
	{:else if trips.length === 0}
		<p class="muted">No trips yet. Click "New trip" to create one.</p>
	{:else}
		<div class="trip-list">
			{#each trips as trip}
				<div class="trip-card">
					<div class="trip-info">
						<span class="trip-destination">{trip.destination}</span>
						<span class="trip-dates">{trip.start_date} → {trip.end_date}</span>
						<span class="trip-luggage">{luggageLabels[trip.luggage_type] || trip.luggage_type}</span>
					</div>
					<div class="trip-actions">
						<a href="/trips/{trip.id}?mode=view" class="btn-secondary action-btn">View</a>
						<a href="/trips/{trip.id}?mode=edit" class="btn-primary action-btn">Edit</a>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 24px;
	}

	.date-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 12px;
	}

	.trip-list {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.trip-card {
		display: flex;
		justify-content: space-between;
		align-items: center;
		background: #fff;
		border: 1px solid #e5e5e5;
		border-radius: 10px;
		padding: 16px 20px;
	}

	.trip-info {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}

	.trip-destination {
		font-size: 16px;
		font-weight: 500;
	}

	.trip-dates {
		font-size: 13px;
		color: #666;
	}

	.trip-luggage {
		font-size: 12px;
		color: #888;
	}

	.trip-actions {
		display: flex;
		gap: 8px;
	}

	.action-btn {
		display: inline-block;
		padding: 7px 16px;
		border-radius: 6px;
		font-size: 13px;
		font-weight: 500;
	}

	.muted {
		color: #888;
		font-size: 14px;
	}
</style>
