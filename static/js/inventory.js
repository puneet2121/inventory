document.addEventListener('alpine:init', () => {
    Alpine.data('inventoryManager', () => ({
        isGridView: true,
        searchQuery: '',
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
                const response = await fetch('/api/inventory/export/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.getCsrfToken()
                    }
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

        async handleImport(event) {
            const file = event.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/inventory/import/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    body: formData
                });

                if (response.ok) {
                    this.showNotification('Import completed successfully', 'success');
                    window.location.reload();
                } else {
                    throw new Error('Import failed');
                }
            } catch (error) {
                this.showNotification('Error importing inventory', 'error');
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
            return document.querySelector('[name=csrfmiddlewaretoken]').value;
        }
    }));
});