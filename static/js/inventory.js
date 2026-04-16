document.addEventListener('alpine:init', () => {
    Alpine.data('inventoryManager', () => ({
        isGridView: true,
        searchQuery: '',
        importFile: null,
        isImporting: false,
        filters: {
            category: '',
            minPrice: '',
            maxPrice: '',
            stock: 'all'
        },

        init() {
            // Load view preference from localStorage
            this.isGridView = localStorage.getItem('inventoryView') !== 'list';
        },

        toggleView() {
            this.isGridView = !this.isGridView;
            localStorage.setItem('inventoryView', this.isGridView ? 'grid' : 'list');
        },

        filterItems() {
            // Implement client-side filtering logic
            const searchTerm = this.searchQuery.toLowerCase();
            const items = document.querySelectorAll('.item-card, .table tbody tr');

            items.forEach(item => {
                const name = item.querySelector('.item-name').textContent.toLowerCase();
                const category = item.querySelector('.category').textContent.toLowerCase();
                const shouldShow = name.includes(searchTerm) || category.includes(searchTerm);
                item.style.display = shouldShow ? '' : 'none';
            });
        },

        async editItem(id) {
            window.location.href = `/inventory/edit/${id}/`;
        },

        async viewDetails(id) {
            try {
                const response = await fetch(`/api/inventory/items/${id}/`);
                const data = await response.json();

                // Populate and show details modal
                const modal = new bootstrap.Modal(document.getElementById('itemDetailsModal'));
                // Populate modal content
                modal.show();
            } catch (error) {
                this.showNotification('Error loading item details', 'error');
            }
        },

        async deleteItem(id) {
            if (!confirm('Are you sure you want to delete this item?')) {
                return;
            }

            try {
                const response = await fetch(`/api/inventory/items/${id}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': this.getCsrfToken()
                    }
                });

                if (response.ok) {
                    this.showNotification('Item deleted successfully', 'success');
                    // Remove item from DOM
                    document.querySelector(`[data-item-id="${id}"]`).remove();
                } else {
                    throw new Error('Failed to delete item');
                }
            } catch (error) {
                this.showNotification('Error deleting item', 'error');
            }
        },

        openFilters() {
            const modal = new bootstrap.Modal(document.getElementById('filterModal'));
            modal.show();
        },

        applyFilters() {
            // Implement filter logic
            // This would typically make an API call with the filter parameters
            console.log('Applying filters:', this.filters);
        },

        async exportInventory() {
            try {
                // Export is a file download; use GET to avoid CSRF.
                const response = await fetch('/inventory/export_inventory/', {
                    method: 'GET'
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'inventory.xlsx';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    this.showNotification('Export completed successfully', 'success');
                } else {
                    throw new Error('Export failed');
                }
            } catch (error) {
                this.showNotification('Error exporting inventory', 'error');
            }
        },

        openImportModal() {
            const modal = new bootstrap.Modal(document.getElementById('importModal'));
            modal.show();
        },

        selectImportFile(event) {
            this.importFile = event && event.target && event.target.files ? event.target.files[0] : null;
        },

        async submitImport() {
            const file = this.importFile;
            if (!file || this.isImporting) return;

            this.isImporting = true;
            try {
                const formData = new FormData();
                formData.append('file', file);
                const response = await fetch('/inventory/import_inventory/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.getCsrfToken(),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData
                });

                if (response.ok) {
                    this.showNotification('Import completed successfully', 'success');
                    window.location.reload();
                } else {
                    let message = `Import failed (HTTP ${response.status})`;
                    try {
                        const data = await response.json();
                        if (data && data.message) message = data.message;
                    } catch (e) {
                        try {
                            const text = await response.text();
                            if (text) message = `${message}: ${text.slice(0, 200)}`;
                        } catch (e2) {
                            // ignore
                        }
                    }
                    this.showNotification(message, 'error');
                    console.error('Import failed:', response.status);
                }
            } finally {
                this.isImporting = false;
            }
        },

        printInventory() {
            window.print();
        },

        showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.innerHTML = `
                <div class="notification-content">
                    <i class="bi bi-${this.getNotificationIcon(type)}"></i>
                    <span>${message}</span>
                </div>
            `;

            document.body.appendChild(notification);
            setTimeout(() => {
                notification.remove();
            }, 3000);
        },

        getNotificationIcon(type) {
            const icons = {
                success: 'check-circle',
                error: 'exclamation-circle',
                info: 'info-circle'
            };
            return icons[type] || icons.info;
        },

        getCsrfToken() {
            // Read csrftoken from the hidden input rendered by Django.
            const el = document.querySelector('[name=csrfmiddlewaretoken]');
            return el ? el.value : '';
        }
    }));
});