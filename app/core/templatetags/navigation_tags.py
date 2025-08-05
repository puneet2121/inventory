# core/templatetags/navigation_tags.py

from django import template
from django.urls import reverse

register = template.Library()


@register.inclusion_tag('core/navigation/navigation.html')
def render_navigation():
    # Define the navigation items
    nav_items = [
        {
            'icon': 'bi bi-house-door-fill',
            'text': 'Dashboard',
            'url': reverse('dashboard:dashboard'),
            'is_collapse': False,
            'submenus': []
        },
        {
            'icon': 'bi bi-cart-dash',
            'text': 'Sales',
            'url': '/sales/',
            'is_collapse': True,
            'submenus': [
                {'name': 'Customers', 'url': reverse('customers:list_customers')},
                {'name': 'Sales Order', 'url': reverse('point_of_sale:sales_order_list')},
                {'name': 'Packages', 'url': '/packages/'},
                {'name': 'Invoices', 'url': reverse('point_of_sale:invoice_list')},
            ]
        },
        {
            'icon': 'bi bi-basket-fill',
            'text': 'Inventory',
            'url': reverse('inventory:item_list'),
            'is_collapse': True,
            'submenus': [
                {'name': 'Items', 'url': reverse('inventory:item_list')},
                {'name': 'Item Categories', 'url': reverse('inventory:category_list')},
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
            'icon': 'bi bi-people',
            'text': 'Employee',
            'url': '/employee/',
            'is_collapse': True,
            'submenus': [
                {'name': 'Employee List', 'url': reverse('employee:employee_list')},
                {'name': 'Calendar', 'url': reverse('employee:assignment-calendar')},
            ]
        },
        {
            'icon': 'bi bi-file-earmark-text',
            'text': 'Reports',
            'url': reverse('reports:reports_dashboard'),
            'is_collapse': True,
            'submenus': [
                {'name': 'Sales Reports', 'url': reverse('reports:sales_reports')},
                {'name': 'Inventory Reports', 'url': reverse('reports:inventory_reports')},
                {'name': 'Employee Reports', 'url': reverse('reports:employee_reports')},
                {'name': 'Purchase Reports', 'url': reverse('reports:purchases_reports')},
            ]
        },
    ]
    return {'nav_items': nav_items}
