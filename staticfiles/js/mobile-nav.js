// Mobile Navigation JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Ensure Bootstrap offcanvas is properly initialized
    const offcanvasElement = document.getElementById('offcanvasSidebar');
    const offcanvas = new bootstrap.Offcanvas(offcanvasElement);
    
    // Add click event to close offcanvas when clicking on actual navigation links
    const navLinks = document.querySelectorAll('#offcanvasSidebar .nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Check if this is a collapsible menu header (has data-bs-toggle="collapse")
            const isCollapsibleHeader = this.getAttribute('data-bs-toggle') === 'collapse';
            
            // Only close offcanvas if it's NOT a collapsible header
            if (!isCollapsibleHeader) {
                // Close offcanvas after a short delay to allow navigation
                setTimeout(() => {
                    offcanvas.hide();
                }, 100);
            }
        });
    });
    
    // Debug: Log to console to ensure script is loaded
    console.log('Mobile navigation script loaded');
}); 