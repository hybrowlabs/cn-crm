/**
 * pending_tasks_widget.js
 *
 * Frappe Dashboard widget that shows all CRM Tasks that are not "Done"
 * for the current user, with:
 *  - Task title, status badge, priority, due-date
 *  - Linked Lead / Deal / Customer name + organisation
 *  - "Mark Done" button per task
 *
 * Usage in a Frappe Number Card / Custom HTML widget script:
 *   crm.pending_tasks_widget.render(wrapper);
 */

frappe.provide('crm.pending_tasks_widget');

crm.pending_tasks_widget = {

	// -------------------------------------------------------------------------
	//  PUBLIC API
	// -------------------------------------------------------------------------

	render(wrapper) {
		const container = $(wrapper);
		container.empty();

		container.html(`
			<style>
				/* ---- Widget shell ---- */
				.ptw-widget {
					font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
					border-radius: 10px;
					overflow: hidden;
					border: 1px solid #e2e8f0;
					box-shadow: 0 1px 4px rgba(0,0,0,.06);
				}

				/* ---- Header ---- */
				.ptw-header {
					display: flex;
					justify-content: space-between;
					align-items: center;
					padding: 12px 16px;
					background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
					color: #fff;
				}
				.ptw-title {
					font-size: 15px;
					font-weight: 600;
					letter-spacing: 0.3px;
					display: flex;
					align-items: center;
					gap: 8px;
				}
				.ptw-badge-total {
					background: rgba(255,255,255,0.2);
					border-radius: 10px;
					font-size: 11px;
					font-weight: 700;
					padding: 2px 8px;
					min-width: 22px;
					text-align: center;
				}
				.ptw-refresh-btn {
					background: rgba(255,255,255,0.15) !important;
					border: 1px solid rgba(255,255,255,0.2) !important;
					color: #fff !important;
					font-size: 12px;
					padding: 4px 12px;
					border-radius: 6px;
					cursor: pointer;
					transition: background .2s;
				}
				.ptw-refresh-btn:hover { background: rgba(255,255,255,0.28) !important; }

				/* ---- Filter pills ---- */
				.ptw-filters {
					display: flex;
					gap: 6px;
					padding: 10px 16px 6px;
					background: #f8fafc;
					border-bottom: 1px solid #e2e8f0;
					flex-wrap: wrap;
				}
				.ptw-filter-pill {
					font-size: 11px;
					font-weight: 600;
					padding: 3px 10px;
					border-radius: 12px;
					cursor: pointer;
					border: 1.5px solid transparent;
					transition: all .15s;
					user-select: none;
				}
				.ptw-filter-pill.all    { background:#eff6ff; color:#3b82f6; border-color:#bfdbfe; }
				.ptw-filter-pill.overdue{ background:#fef2f2; color:#dc2626; border-color:#fecaca; }
				.ptw-filter-pill.today  { background:#fffbeb; color:#d97706; border-color:#fde68a; }
				.ptw-filter-pill.none   { background:#f1f5f9; color:#64748b; border-color:#cbd5e1; }
				.ptw-filter-pill.active { box-shadow: 0 0 0 2px currentColor; }

				/* ---- Body ---- */
				.ptw-loading { text-align:center; padding:28px; color:#94a3b8; font-size:13px; }
				.ptw-content {
					background:#f8fafc;
					max-height: 520px;
					overflow-y: auto;
				}
				.ptw-content::-webkit-scrollbar      { width: 5px; }
				.ptw-content::-webkit-scrollbar-thumb{ background:#cbd5e1; border-radius:10px; }
				.ptw-empty {
					text-align:center; padding:36px 16px;
					color:#94a3b8; font-size:14px;
				}

				/* ---- Task card ---- */
				.ptw-task-card {
					display: flex;
					justify-content: space-between;
					align-items: flex-start;
					gap: 12px;
					padding: 13px 16px;
					background: #fff;
					border-bottom: 1px solid #f1f5f9;
					transition: background .12s;
				}
				.ptw-task-card:last-child { border-bottom: none; }
				.ptw-task-card:hover      { background: #f8fafc; }

				.ptw-task-left  { flex: 1; min-width: 0; }
				.ptw-task-right { flex-shrink: 0; display:flex; align-items:center; gap:8px; }

				.ptw-task-title {
					font-size: 14px;
					font-weight: 600;
					color: #1e293b;
					margin-bottom: 4px;
					white-space: nowrap;
					overflow: hidden;
					text-overflow: ellipsis;
				}
				.ptw-task-meta {
					display: flex;
					flex-wrap: wrap;
					gap: 6px;
					align-items: center;
					font-size: 12px;
					color: #64748b;
				}
				.ptw-ref-link {
					color: #3b82f6;
					font-weight: 600;
					text-decoration: none;
					white-space: nowrap;
					overflow: hidden;
					text-overflow: ellipsis;
					max-width: 160px;
					display: inline-block;
					vertical-align: middle;
				}
				.ptw-ref-link:hover { text-decoration: underline; }
				.ptw-org {
					color: #475569;
					background: #f1f5f9;
					border-radius: 4px;
					padding: 1px 6px;
					font-size: 11px;
				}

				/* ---- Status / priority badges ---- */
				.ptw-badge {
					font-size: 10px;
					font-weight: 700;
					padding: 2px 7px;
					border-radius: 8px;
					white-space: nowrap;
				}
				.ptw-badge.backlog    { background:#f1f5f9; color:#64748b; }
				.ptw-badge.todo       { background:#eff6ff; color:#3b82f6; }
				.ptw-badge.inprogress { background:#fffbeb; color:#d97706; }
				.ptw-badge.priority-high   { background:#fef2f2; color:#dc2626; }
				.ptw-badge.priority-medium { background:#fffbeb; color:#d97706; }
				.ptw-badge.priority-low    { background:#f0fdf4; color:#16a34a; }

				/* ---- Due-date chip ---- */
				.ptw-due {
					font-size: 11px;
					font-weight: 600;
					padding: 1px 7px;
					border-radius: 8px;
					white-space: nowrap;
				}
				.ptw-due.overdue  { background:#fef2f2; color:#dc2626; }
				.ptw-due.today    { background:#fffbeb; color:#d97706; }
				.ptw-due.upcoming { background:#f0fdf4; color:#16a34a; }
				.ptw-due.none     { background:#f1f5f9; color:#94a3b8; }

				/* ---- Mark-Done button ---- */
				.ptw-done-btn {
					font-size: 11px;
					font-weight: 700;
					padding: 5px 12px;
					border-radius: 6px;
					border: 1.5px solid #22c55e;
					background: #f0fdf4;
					color: #16a34a;
					cursor: pointer;
					white-space: nowrap;
					transition: all .2s;
				}
				.ptw-done-btn:hover:not(:disabled) {
					background: #22c55e;
					color: #fff;
				}
				.ptw-done-btn:disabled {
					opacity: .5;
					cursor: not-allowed;
				}
				.ptw-done-btn.marking {
					border-color: #94a3b8;
					background: #f1f5f9;
					color: #64748b;
				}

				/* ---- Cancel button ---- */
				.ptw-cancel-btn {
					font-size: 11px;
					font-weight: 700;
					padding: 5px 12px;
					border-radius: 6px;
					border: 1.5px solid #ef4444;
					background: #fef2f2;
					color: #dc2626;
					cursor: pointer;
					white-space: nowrap;
					transition: all .2s;
				}
				.ptw-cancel-btn:hover:not(:disabled) {
					background: #ef4444;
					color: #fff;
				}
				.ptw-cancel-btn:disabled {
					opacity: .5;
					cursor: not-allowed;
				}
				.ptw-cancel-btn.canceling {
					border-color: #94a3b8;
					background: #f1f5f9;
					color: #64748b;
				}
			</style>

			<div class="ptw-widget">
				<div class="ptw-header">
					<div class="ptw-title">
						📋 Pending Tasks
						<span class="ptw-badge-total ptw-total-count">—</span>
					</div>
					<button class="btn ptw-refresh-btn">⟳ Refresh</button>
				</div>

				<div class="ptw-filters" style="display:none;">
					<span class="ptw-filter-pill all active"    data-bucket="all">All</span>
					<span class="ptw-filter-pill overdue"       data-bucket="overdue">🔴 Overdue</span>
					<span class="ptw-filter-pill today"         data-bucket="today">🟡 Due Today</span>
					<span class="ptw-filter-pill none"          data-bucket="none">⚪ No Date</span>
				</div>

				<div class="ptw-loading">Loading tasks…</div>

				<div class="ptw-content" style="display:none;">
					<div class="ptw-task-list"></div>
					<div class="ptw-empty" style="display:none;">🎉 No pending tasks!</div>
				</div>
			</div>
		`);

		// Wire up events
		container.off('click', '.ptw-refresh-btn');
		container.on('click', '.ptw-refresh-btn', () => this.load_data(container));

		container.off('click', '.ptw-filter-pill');
		container.on('click', '.ptw-filter-pill', (e) => {
			const pill = $(e.currentTarget);
			const bucket = pill.data('bucket');
			container.find('.ptw-filter-pill').removeClass('active');
			pill.addClass('active');
			this._apply_filter(container, bucket);
		});

		container.off('click', '.ptw-done-btn');
		container.on('click', '.ptw-done-btn', (e) => {
			e.stopPropagation();
			const btn = $(e.currentTarget);
			const taskName = btn.data('task');
			this._mark_done(btn, taskName, container);
		});

		container.off('click', '.ptw-cancel-btn');
		container.on('click', '.ptw-cancel-btn', (e) => {
			e.stopPropagation();
			const btn = $(e.currentTarget);
			const taskName = btn.data('task');
			this._cancel_task(btn, taskName, container);
		});

		this.load_data(container);
	},

	// -------------------------------------------------------------------------
	//  DATA LOADING
	// -------------------------------------------------------------------------

	load_data(container) {
		const loading = container.find('.ptw-loading');
		const content = container.find('.ptw-content');
		const filters = container.find('.ptw-filters');

		loading.show();
		content.hide();
		filters.hide();

		frappe.call({
			method: 'crm.api.pending_tasks_widget.get_pending_tasks',
			callback: (r) => {
				loading.hide();

				if (!r.message) return;

				const tasks = r.message.tasks || [];
				this._all_tasks = tasks;

				container.find('.ptw-total-count').text(tasks.length || '0');

				if (tasks.length) {
					filters.show();
					content.show();
					// Reset filter to "All"
					container.find('.ptw-filter-pill').removeClass('active');
					container.find('.ptw-filter-pill[data-bucket="all"]').addClass('active');
					this._render_tasks(container, tasks);
				} else {
					content.show();
					container.find('.ptw-task-list').empty();
					container.find('.ptw-empty').show();
				}
			}
		});
	},

	// -------------------------------------------------------------------------
	//  RENDERING
	// -------------------------------------------------------------------------

	_render_tasks(container, tasks) {
		const list = container.find('.ptw-task-list');
		const empty = container.find('.ptw-empty');

		list.empty();

		if (!tasks.length) {
			empty.show();
			return;
		}
		empty.hide();

		tasks.forEach(task => {
			list.append(this._build_card(task));
		});
	},

	_build_card(task) {
		// Status badge
		const statusClass = {
			'Backlog': 'backlog',
			'Todo': 'todo',
			'In Progress': 'inprogress',
		}[task.status] || 'backlog';

		const priorityClass = {
			'High': 'priority-high',
			'Medium': 'priority-medium',
			'Low': 'priority-low',
		}[task.priority] || 'priority-low';

		// Due-date chip
		const dueLabel = task.due_date
			? frappe.datetime.str_to_user(task.due_date)
			: 'No Date';
		const dueBucket = task.due_bucket || 'none';

		// Reference link
		let refHtml = '';
		if (task.ref_name) {
			const url = task.ref_url || '#';
			refHtml = `
				<a class="ptw-ref-link" href="${url}" target="_blank" title="${task.ref_name}">
					${task.reference_doctype === 'CRM Lead' ? '👤' : (task.reference_doctype === 'CRM Deal' ? '🤝' : '🏢')}
					${frappe.utils.escape_html(task.ref_name)}
				</a>`;
		}

		const orgHtml = task.organization && task.organization !== task.ref_name
			? `<span class="ptw-org" title="Company">${frappe.utils.escape_html(task.organization)}</span>`
			: '';

		const card = $(`
			<div class="ptw-task-card" data-task="${task.name}" data-bucket="${dueBucket}">
				<div class="ptw-task-left">
					<div class="ptw-task-title" title="${frappe.utils.escape_html(task.title)}">
						${frappe.utils.escape_html(task.title)}
					</div>
					<div class="ptw-task-meta">
						<span class="ptw-badge ${statusClass}">${task.status}</span>
						${task.priority ? `<span class="ptw-badge ${priorityClass}">${task.priority}</span>` : ''}
						<span class="ptw-due ${dueBucket}">${dueLabel}</span>
						${refHtml}
						${orgHtml}
					</div>
				</div>
				<div class="ptw-task-right">
					<button class="ptw-cancel-btn btn" data-task="${task.name}">✗ Cancel</button>
					<button class="ptw-done-btn btn" data-task="${task.name}">✓ Done</button>
				</div>
			</div>
		`);

		return card;
	},

	// -------------------------------------------------------------------------
	//  FILTER
	// -------------------------------------------------------------------------

	_apply_filter(container, bucket) {
		const tasks = this._all_tasks || [];
		const filtered = bucket === 'all'
			? tasks
			: tasks.filter(t => t.due_bucket === bucket);
		this._render_tasks(container, filtered);
	},

	// -------------------------------------------------------------------------
	//  MARK DONE
	// -------------------------------------------------------------------------

	_mark_done(btn, taskName, container) {
		btn.addClass('marking').prop('disabled', true).text('⌛ Saving…');

		frappe.call({
			method: 'crm.api.pending_tasks_widget.mark_task_done',
			args: { task_name: taskName },
			callback: (r) => {
				if (r.message && r.message.success) {
					this._animate_card_away(taskName, container);
					frappe.show_alert({ message: __('Task marked as Done'), indicator: 'green' });
				} else {
					btn.removeClass('marking').prop('disabled', false).text('✓ Done');
					frappe.show_alert({ message: __('Failed to update task'), indicator: 'red' });
				}
			},
			error: () => {
				btn.removeClass('marking').prop('disabled', false).text('✓ Done');
				frappe.show_alert({ message: __('Error updating task'), indicator: 'red' });
			}
		});
	},

	// -------------------------------------------------------------------------
	//  CANCEL TASK
	// -------------------------------------------------------------------------

	_cancel_task(btn, taskName, container) {
		btn.addClass('canceling').prop('disabled', true).text('⌛ Saving…');

		frappe.call({
			method: 'crm.api.pending_tasks_widget.cancel_task',
			args: { task_name: taskName },
			callback: (r) => {
				if (r.message && r.message.success) {
					this._animate_card_away(taskName, container);
					frappe.show_alert({ message: __('Task marked as Canceled'), indicator: 'orange' });
				} else {
					btn.removeClass('canceling').prop('disabled', false).text('✗ Cancel');
					frappe.show_alert({ message: __('Failed to cancel task'), indicator: 'red' });
				}
			},
			error: () => {
				btn.removeClass('canceling').prop('disabled', false).text('✗ Cancel');
				frappe.show_alert({ message: __('Error canceling task'), indicator: 'red' });
			}
		});
	},

	_animate_card_away(taskName, container) {
		const card = container.find(`.ptw-task-card[data-task="${taskName}"]`);
		card.css({ transition: 'opacity .35s, max-height .35s', overflow: 'hidden' });
		card.css({ opacity: 0, 'max-height': 0 });
		setTimeout(() => {
			card.remove();

			// Update internal cache
			if (this._all_tasks) {
				this._all_tasks = this._all_tasks.filter(t => t.name !== taskName);
			}

			// Update count badge
			const remaining = container.find('.ptw-task-card').length;
			container.find('.ptw-total-count').text(remaining || '0');

			if (remaining === 0) {
				container.find('.ptw-empty').show();
				container.find('.ptw-filters').hide();
			}
		}, 370);
	},

	// Store data for filtering
	_all_tasks: null,
};
