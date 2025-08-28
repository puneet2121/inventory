import time
import logging
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)

class PerformanceMonitoringMiddleware:
    """
    Middleware to monitor and log slow database queries and request performance.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Start timing
        start_time = time.time()
        
        # Reset query count
        initial_queries = len(connection.queries)
        
        # Process request
        response = self.get_response(request)
        
        # Calculate performance metrics
        end_time = time.time()
        request_time = end_time - start_time
        final_queries = len(connection.queries)
        query_count = final_queries - initial_queries
        
        # Log slow requests
        if request_time > 1.0:  # Log requests taking more than 1 second
            logger.warning(
                f"Slow request: {request.path} took {request_time:.2f}s "
                f"with {query_count} queries"
            )
            
            # Log individual slow queries
            for query in connection.queries[initial_queries:]:
                if float(query.get('time', 0)) > 0.1:  # Log queries taking more than 100ms
                    logger.warning(
                        f"Slow query ({query.get('time', 0)}s): {query.get('sql', '')[:200]}..."
                    )
        
        # Add performance headers for debugging
        response['X-Request-Time'] = f"{request_time:.3f}"
        response['X-Query-Count'] = str(query_count)
        
        return response
