# core/templatetags/navigation_tags.py

from django import template

register = template.Library()


@register.inclusion_tag('core/navigation/navigation.html')
def render_navigation():
    # Define the navigation items
    nav_items = [
        {
            'icon': 'bi bi-house-door-fill',
            'text': 'Dashboard',
            'url': '/dashboard/',
            'is_collapse': True,
            'submenus': []
        },
        {
            'icon': 'bi bi-cart-dash',
            'text': 'Sales',
            'url': '/sales/',
            'is_collapse': True,
            'submenus': [
                {'name': 'Customers', 'url': '/customers/'},
                {'name': 'Sales Order', 'url': '/point_of_sale/pos'},
                {'name': 'Packages', 'url': '/packages/'},
                {'name': 'invoices', 'url': '/invoices/'},
            ]
        },
        {
            'icon': 'bi bi-basket-fill',
            'text': 'Inventory',
            'url': '/inventory/',
            'is_collapse': True,
            'submenus': [
                {'name': 'Items', 'url': 'item/list/'},
                {'name': 'Items Groups', 'url': '/orders/'},
                {'name': 'Inventory Adjustments', 'url': '/reports/'},
            ]
        },
        {
            'icon': 'bi bi-bag-check',
            'text': 'Purchases',
            'url': '/purchases/',
            'is_collapse': True,
            'submenus': [
                {'name': 'Vendors', 'url': '/vendors/'},
                {'name': 'Purchase Orders', 'url': '/purchaseorder/'},
                {'name': 'bills', 'url': '/bills/'},
            ]
        },
        {
            'icon': 'bi bi-file-earmark-text',
            'text': 'Reports',
            'url': '/purchases/',
            'is_collapse': True,
            'submenus': [
                {'name': 'All Reports', 'url': '/allreports/'},
            ]
        },
    ]
    return {'nav_items': nav_items}
