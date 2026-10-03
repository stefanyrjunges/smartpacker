<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { apiFetch } from '$lib/api';

	const tripId = $derived($page.params.id);
	const mode = $derived($page.url.searchParams.get('mode') || 'view');
	const isEditing = $derived(mode === 'edit');

	let items = $state([]);
	let loading = $state(true);
	let error = $state('');

	let newItemName = $state('');
	let newItemQuantity = $state(1);
	let addingItem = $state(false);
	let addError = $state('');

	let regenerating = $state(false);

	// Groups items by category for display
	let grouped = $derived(() => {
		const groups = {};
		for (const item of items) {
			if (!groups[item.category]) groups[item.category] = [];
			groups[item.category].push(item);
		}
		return groups;
	});

	let packedCount = $derived(items.filter((i) => i.packed).length);

	onMount(async () => {
		if (isEditing) {
			await regenerate(true);
		} else {
			await loadPackingList();
		}
	});

	async function loadPackingList() {
		loading = true;
		error = '';

		const res = await apiFetch(`/trips/${tripId}/packing-list`);
		const data = await res.json();

		if (!res.ok) {
			error = data.message || data.error || 'Could not load packing list.';
		} else {
			items = data.items || [];
		}

		loading = false;
	}

	async function togglePacked(item) {
		const newPacked = !item.packed;

		const res = await apiFetch(`/trips/${tripId}/packing-list/${item.id}`, {
			method: 'PATCH',
			body: JSON.stringify({ packed: newPacked })
		});

		if (res.ok) {
			items = items.map((i) => i.id === item.id ? { ...i, packed: newPacked } : i);
		}
	}

	async function deleteItem(itemId) {
		const res = await apiFetch(`/trips/${tripId}/packing-list/${itemId}`, {
			method: 'DELETE'
		});

		if (res.ok) {
			items = items.filter((i) => i.id !== itemId);
		}
	}

	async function addItem(event) {
		event.preventDefault();
		addError = '';
		addingItem = true;

		const res = await apiFetch(`/trips/${tripId}/packing-list`, {
			method: 'POST',
			body: JSON.stringify({ name: newItemName, quantity: newItemQuantity })
		});

		const data = await res.json();

		if (!res.ok) {
			addError = data.message || 'Could not add item.';
			addingItem = false;
			return;
		}

		items = [...items, data];
		newItemName = '';
		newItemQuantity = 1;
		addingItem = false;
	}

	async function regenerate(silent = false) {
		if (!silent && !confirm('This will replace all generated items. Custom items you added will stay. Continue?')) return;

		regenerating = true;

		const res = await apiFetch(`/trips/${tripId}/packing-list/regenerate`, {
			method: 'POST'
		});

		if (res.ok) {
			await loadPackingList();
		} else {
			const data = await res.json();
			error = data.error || data.message || 'Could not regenerate the list.';
			loading = false;
		}

		regenerating = false;
	}</script>

<div class="page">
	<div class="top-bar">
		<a href="/trips/{tripId}?mode={mode}" class="back-link">← Back to trip</a>
		{#if isEditing && items.length > 0}
			<button class="btn-secondary" onclick={regenerate} disabled={regenerating}>
				{regenerating ? 'Regenerating...' : 'Regenerate list'}
			</button>
		{/if}
	</div>

	<div class="list-header">
		<h1>Packing list</h1>
		{#if items.length > 0}
			<span class="progress-text">{packedCount} / {items.length} packed</span>
		{/if}
	</div>

	{#if loading}
		<p class="muted">Loading...</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else if items.length === 0}
		<p class="muted">No items yet. Go back to the trip page and the list will be generated when you open this page.</p>
	{:else}
		{#each Object.entries(grouped()) as [category, categoryItems]}
			<div class="category-section">
				<h3 class="category-title">{category}</h3>
				<div class="card" style="padding: 0; overflow: hidden;">
					{#each categoryItems as item, index}
						<div class="item-row" class:packed={item.packed} class:last={index === categoryItems.length - 1}>
							<label class="item-check">
								<input
									type="checkbox"
									checked={item.packed}
									onchange={() => togglePacked(item)}
								/>
								<span class="item-name" class:strikethrough={item.packed}>{item.name}</span>
								{#if item.quantity > 1}
									<span class="item-qty">x{item.quantity}</span>
								{/if}
							</label>
							{#if isEditing}
								<button class="btn-danger small" onclick={() => deleteItem(item.id)}>✕</button>
							{/if}
						</div>
					{/each}
				</div>
			</div>
		{/each}
	{/if}

	{#if isEditing}
		<div class="card add-section">
			<h3 style="margin-bottom: 14px;">Add item</h3>
			<form onsubmit={addItem} class="add-form">
				<div style="flex: 1;">
					<input bind:value={newItemName} placeholder="Item name" required />
				</div>
				<div style="width: 80px;">
					<input type="number" bind:value={newItemQuantity} min="1" placeholder="Qty" required />
				</div>
				<button type="submit" class="btn-primary" disabled={addingItem}>Add</button>
			</form>
			{#if addError}
				<p class="error" style="margin-top: 8px;">{addError}</p>
			{/if}
		</div>
	{/if}

	<div class="done-bar">
		<a href="/" class="btn-primary done-btn">Done</a>
	</div>
</div>

<style>
	.top-bar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;
	}

	.back-link {
		font-size: 14px;
		color: #555;
	}

	.back-link:hover {
		color: #2563eb;
	}

	.list-header {
		display: flex;
		align-items: baseline;
		gap: 14px;
		margin-bottom: 24px;
	}

	.progress-text {
		font-size: 14px;
		color: #888;
	}

	.category-section {
		margin-bottom: 20px;
	}

	.category-title {
		font-size: 11px;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #888;
		margin-bottom: 8px;
	}

	.item-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 12px 16px;
		border-bottom: 1px solid #f0f0f0;
	}

	.item-row.last {
		border-bottom: none;
	}

	.item-row.packed {
		background: #fafafa;
	}

	.item-check {
		display: flex;
		align-items: center;
		gap: 10px;
		cursor: pointer;
		flex: 1;
	}

	.item-check input[type='checkbox'] {
		width: 16px;
		height: 16px;
		flex-shrink: 0;
		cursor: pointer;
	}

	.item-name {
		font-size: 14px;
	}

	.item-name.strikethrough {
		text-decoration: line-through;
		color: #aaa;
	}

	.item-qty {
		font-size: 12px;
		color: #888;
		background: #f0f0f0;
		padding: 2px 7px;
		border-radius: 10px;
	}

	.item-actions {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.add-section {
		margin-top: 24px;
	}

	.add-form {
		display: flex;
		gap: 8px;
		align-items: flex-end;
	}

	.muted {
		color: #888;
		font-size: 14px;
	}

	button.small {
		padding: 4px 8px;
		font-size: 12px;
	}

	.done-bar {
		display: flex;
		justify-content: flex-end;
		margin-top: 24px;
		padding-top: 20px;
		border-top: 1px solid #e5e5e5;
	}

	.done-btn {
		display: inline-block;
		padding: 9px 22px;
		border-radius: 6px;
		font-size: 14px;
		font-weight: 500;
	}
</style>
