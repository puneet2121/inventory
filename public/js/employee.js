document.addEventListener('alpine:init', () => {
    Alpine.data('employeeManager', () => ({
        searchQuery: '',

        filterEmployees() {
            const query = this.searchQuery.toLowerCase();
            document.querySelectorAll('.employee-card').forEach(card => {
                const name = card.querySelector('h5').textContent.toLowerCase();
                const position = card.querySelector('.position').textContent.toLowerCase();
                card.style.display = (name.includes(query) || position.includes(query)) ? '' : 'none';
            });
        },

        async viewDetails(id) {
            try {
                const response = await fetch(`/api/employees/${id}/`);
                if (!response.ok) throw new Error('Failed to fetch employee details');

                const data = await response.json();
                const modal = new bootstrap.Modal(document.getElementById('employeeDetailsModal'));

                // Populate modal content
                const detailsDiv = document.querySelector('.employee-details');
                detailsDiv.innerHTML = this.generateDetailsHTML(data);

                modal.show();
            } catch (error) {
                this.showNotification('Error loading employee details', 'error');
            }
        },

        editEmployee(id) {
            window.location.href = `/employees/edit/${id}/`;
        },

        async deleteEmployee(id) {
            if (!confirm('Are you sure you want to delete this employee?')) {
                return;
            }

            try {
                const response = await fetch(`/api/employees/${id}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': this.getCsrfToken()
                    }
                });

                if (!response.ok) throw new Error('Failed to delete employee');

                // Remove the employee card from DOM
                const card = document.querySelector(`[data-employee-id="${id}"]`);
                card.remove();

                this.showNotification('Employee deleted successfully', 'success');
            } catch (error) {
                this.showNotification('Error deleting employee', 'error');
            }
        },

        generateDetailsHTML(employee) {
            return `
                <div class="employee-detail-header">
                    <div class="employee-avatar large">
                        ${employee.image ? 
                            `<img src="${employee.image}" alt="${employee.full_name}">` :
                            `<div class="avatar-placeholder">${this.getInitials(employee.full_name)}</div>`
                        }
                    </div>
                    <div class="employee-basic-info">
                        <h4>${employee.full_name}</h4>
                        <p>${employee.position}</p>
                    </div>
                </div>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Email</label>
                        <p>${employee.email}</p>
                    </div>
                    <div class="detail-item">
                        <label>Phone</label>
                        <p>${employee.phone || 'N/A'}</p>
                    </div>
                    <div class="detail-item">
                        <label>Department</label>
                        <p>${employee.department || 'N/A'}</p>
                    </div>
                    <div class="detail-item">
                        <label>Hire Date</label>
                        <p>${employee.hire_date || 'N/A'}</p>
                    </div>
                </div>
            `;
        },

        getInitials(name) {
            return name.split(' ').map(n => n[0]).join('').toUpperCase();
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
            setTimeout(() => notification.remove(), 3000);
        },

        getNotificationIcon(type) {
            return {
                success: 'check-circle',
                error: 'exclamation-circle',
                info: 'info-circle'
            }[type] || 'info-circle';
        },

        getCsrfToken() {
            return document.querySelector('[name=csrfmiddlewaretoken]').value;
        }
    }));
});