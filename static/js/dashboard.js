document.addEventListener('alpine:init', () => {
    Alpine.data('dashboardManager', () => ({
        salesChart: null,
        productsChart: null,
        categoryChart: null,
        monthlySalesChart: null,
        currentPeriod: 'week',

        init() {
            console.log('Dashboard Manager Initializing...');
            console.log('Dashboard Data:', window.dashboardData);
            
            // Check if Chart.js is loaded
            if (typeof Chart === 'undefined') {
                console.error('Chart.js is not loaded!');
                return;
            }
            
            // Simple test - create one basic chart
            this.createSimpleTestChart();
            
            // Initialize real charts
            try {
            this.initSalesChart();
            this.initTopProductsChart();
                this.initCategoryChart();
                this.initMonthlySalesChart();
            } catch (error) {
                console.error('Error initializing charts:', error);
            }
        },

        createSimpleTestChart() {
            const testCtx = document.getElementById('salesTrendChart');
            if (testCtx) {
                console.log('Creating simple test chart...');
                new Chart(testCtx.getContext('2d'), {
                    type: 'line',
                    data: {
                        labels: ['Jan', 'Feb', 'Mar'],
                        datasets: [{
                            label: 'Test Sales',
                            data: [10, 20, 30],
                            borderColor: '#ff0000',
                            backgroundColor: 'rgba(255, 0, 0, 0.1)',
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
                console.log('Simple test chart created successfully');
            } else {
                console.error('Sales trend chart canvas not found for test');
            }
        },

        changePeriod(period) {
            this.currentPeriod = period;
            this.updateSalesChart();
        },

        initSalesChart() {
            const ctx = document.getElementById('salesTrendChart');
            const debugDiv = document.getElementById('salesChartDebug');
            
            if (!ctx) {
                console.error('Sales trend chart canvas not found');
                if (debugDiv) {
                    debugDiv.style.display = 'block';
                    debugDiv.textContent = 'Error: Sales trend chart canvas not found';
                }
                return;
            }
            
            const context = ctx.getContext('2d');
            const salesData = window.dashboardData.salesTrendData || [];
            const salesLabels = window.dashboardData.salesTrendLabels || [];
            
            console.log('Sales Trend Data:', salesData);
            console.log('Sales Trend Labels:', salesLabels);
            
            if (debugDiv) {
                debugDiv.style.display = 'block';
                debugDiv.textContent = `Data: ${JSON.stringify(salesData)}, Labels: ${JSON.stringify(salesLabels)}`;
            }
            
            this.salesChart = new Chart(context, {
                type: 'line',
                data: {
                    labels: salesLabels,
                    datasets: [{
                        label: 'Sales',
                        data: salesData,
                        borderColor: '#1976d2',
                        backgroundColor: 'rgba(25, 118, 210, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#1976d2',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#ffffff',
                            bodyColor: '#ffffff',
                            borderColor: '#1976d2',
                            borderWidth: 1,
                            cornerRadius: 8,
                            displayColors: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                display: true,
                                drawBorder: false,
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                maxRotation: 45
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });
        },

        initTopProductsChart() {
            const ctx = document.getElementById('topProductsChart');
            if (!ctx) {
                console.error('Top products chart canvas not found');
                return;
            }
            
            const context = ctx.getContext('2d');
            const topProducts = window.dashboardData.topProducts || [];
            
            console.log('Top Products Data:', topProducts);
            
            const labels = topProducts.map(item => item[0]);
            const data = topProducts.map(item => item[1]);
            
            this.productsChart = new Chart(context, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: [
                            '#1976d2',
                            '#2e7d32',
                            '#f57c00',
                            '#7b1fa2',
                            '#757575',
                            '#e53935',
                            '#8e24aa',
                            '#43a047'
                        ],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                padding: 20,
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#ffffff',
                            bodyColor: '#ffffff',
                            borderColor: '#1976d2',
                            borderWidth: 1,
                            cornerRadius: 8,
                            callbacks: {
                                label: function(context) {
                                    return context.label + ': ' + context.parsed + ' units';
                                }
                            }
                        }
                    },
                    cutout: '60%'
                }
            });
        },

        initCategoryChart() {
            const ctx = document.getElementById('categoryChart');
            if (!ctx) {
                console.error('Category chart canvas not found');
                return;
            }
            
            const context = ctx.getContext('2d');
            const categorySales = window.dashboardData.categorySales || {};
            
            console.log('Category Sales Data:', categorySales);
            
            const labels = Object.keys(categorySales);
            const data = Object.values(categorySales);
            
            this.categoryChart = new Chart(context, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Sales by Category',
                        data: data,
                        backgroundColor: [
                            '#1976d2',
                            '#2e7d32',
                            '#f57c00',
                            '#7b1fa2',
                            '#757575',
                            '#e53935',
                            '#8e24aa',
                            '#43a047'
                        ],
                        borderRadius: 6,
                        borderSkipped: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#ffffff',
                            bodyColor: '#ffffff',
                            borderColor: '#1976d2',
                            borderWidth: 1,
                            cornerRadius: 8,
                            callbacks: {
                                label: function(context) {
                                    return '$' + context.parsed.toLocaleString();
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                display: true,
                                drawBorder: false,
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                maxRotation: 45
                            }
                        }
                    }
                }
            });
        },

        initMonthlySalesChart() {
            const ctx = document.getElementById('monthlySalesChart');
            if (!ctx) {
                console.error('Monthly sales chart canvas not found');
                return;
            }
            
            const context = ctx.getContext('2d');
            const monthlyData = window.dashboardData.monthlySalesData || [];
            const monthlyLabels = window.dashboardData.monthlyLabels || [];
            
            console.log('Monthly Sales Data:', monthlyData);
            console.log('Monthly Labels:', monthlyLabels);
            
            this.monthlySalesChart = new Chart(context, {
                type: 'line',
                data: {
                    labels: monthlyLabels,
                    datasets: [{
                        label: 'Monthly Sales',
                        data: monthlyData,
                        borderColor: '#2e7d32',
                        backgroundColor: 'rgba(46, 125, 50, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#2e7d32',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#ffffff',
                            bodyColor: '#ffffff',
                            borderColor: '#2e7d32',
                            borderWidth: 1,
                            cornerRadius: 8,
                            callbacks: {
                                label: function(context) {
                                    return '$' + context.parsed.toLocaleString();
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                display: true,
                                drawBorder: false,
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                maxRotation: 45
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });
        },

        async updateSalesChart() {
            try {
                // Show loading state
                const chartContainer = document.getElementById('salesTrendChart').parentElement;
                chartContainer.classList.add('loading');
                
                const response = await fetch(`/
                api/sales/trend/${this.currentPeriod}/`);
                const data = await response.json();

                this.salesChart.data.labels = data.labels;
                this.salesChart.data.datasets[0].data = data.values;
                this.salesChart.update();
                
                // Remove loading state
                chartContainer.classList.remove('loading');
            } catch (error) {
                console.error('Error fetching sales data:', error);
                // Remove loading state on error
                const chartContainer = document.getElementById('salesTrendChart').parentElement;
                chartContainer.classList.remove('loading');
            }
        },

        // Utility function to format currency
        formatCurrency(amount) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(amount);
        },

        // Utility function to format numbers
        formatNumber(num) {
            return new Intl.NumberFormat('en-US').format(num);
        }
    }));
});