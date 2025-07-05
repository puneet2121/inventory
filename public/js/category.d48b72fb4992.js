document.addEventListener('alpine:init', () => {
    Alpine.data('categoryManager', () => ({
        isEditing: false,
        categoryData: {
            id: null,
            name: '',
            description: ''
        },
        modal: null,

        init() {
            this.modal = new bootstrap.Modal(document.getElementById('categoryModal'));
        },

        openAddModal() {
            this.isEditing = false;
            this.categoryData = {
                id: null,
                name: '',
                description: ''
            };
            this.modal.show();
        },

        async editCategory(id) {
            try {
                const response = await fetch(`/api/categories/${id}/`);
                const data = await response.json();

                this.categoryData = {
                    id: data.id,
                    name: data.name,
                    description: data.description
                };
                this.isEditing = true;
                this.modal.show();
            } catch (error) {
                this.showNotification('Error loading category', 'error');
            }
        },

        async submitCategory() {
            const url = this.isEditing
                ? `/api/categories/${this.categoryData.id}/`
                : '/api/categories/';

            try {
                const response = await fetch(url, {
                    method: this.isEditing ? 'PUT' : 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    body: JSON.stringify(this.categoryData)
                });

                if (!response.ok) throw new Error('Failed to save category');

                this.modal.hide();
                window.location.reload();
            } catch (error) {
                this.showNotification('Error saving category', 'error');
            }
        },

        async deleteCategory(id, name) {
            if (!confirm(`Are you sure you want to delete the category "${name}"?`)) {
                return;
            }

            try {
                const response = await fetch(`/api/categories/${id}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': this.getCsrfToken()
                    }
                });

                if (!response.ok) throw new Error('Failed to delete category');

                const card = document.querySelector(`[data-category-id="${id}"]`);
                card.remove();
                this.showNotification('Category deleted successfully', 'success');
            } catch (error) {
                this.showNotification('Error deleting category', 'error');
            }
        },

        showNotification(message, type = 'info') {
            // Implementation of notification system
            // You can use your existing notification system
        },

        getCsrfToken() {
            return document.querySelector('[name=csrfmiddlewaretoken]').value;
        }
    }));
});