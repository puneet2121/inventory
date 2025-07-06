document.addEventListener('alpine:init', () => {
    Alpine.data('dashboardManager', () => ({
        salesChart: null,
        productsChart: null,
        currentPeriod: 'week',

        init() {
            this.initSalesChart();
            this.initTopProductsChart();
        },

        changePeriod(period) {
            this.currentPeriod = period;
            this.updateSalesChart();
        },

        initSalesChart() {
            const ctx = document.getElementById('salesTrendChart').getContext('2d');
            this.salesChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Sales',
                        data: [],
                        borderColor: '#1976d2',
                        tension: 0.4,
                        fill: true,
                        backgroundColor: 'rgba(25, 118, 210, 0.1)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                display: true,
                                drawBorder: false
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
            this.updateSalesChart();
        },

        initTopProductsChart() {
            const ctx = document.getElementById('topProductsChart').getContext('2d');
            this.productsChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Product A', 'Product B', 'Product C', 'Product D', 'Others'],
                    datasets: [{
                        data: [30, 25, 20, 15, 10],
                        backgroundColor: [
                            '#1976d2',
                            '#2e7d32',
                            '#f57c00',
                            '#7b1fa2',
                            '#757575'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right'
                        }
                    }
                }
            });
        },

        async updateSalesChart() {
            try {
                const response = await fetch(`/api/sales/trend/${this.currentPeriod}/`);
                const data = await response.json();

                this.salesChart.data.labels = data.labels;
                this.salesChart.data.datasets[0].data = data.values;
                this.salesChart.update();
            } catch (error) {
                console.error('Error fetching sales data:', error);
            }
        }
    }));
});