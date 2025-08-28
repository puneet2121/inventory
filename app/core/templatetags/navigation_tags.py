from django import template
from django.urls import reverse

register = template.Library()


@register.inclusion_tag('core/navigation/navigation.html', takes_context=True)
def render_navigation(context):
    request = context['request']
    user = request.user

    nav_items = [
        {
            'icon': 'bi bi-house-door-fill',
            'text': 'Dashboard',
            'url': reverse('dashboard:dashboard'),
            'is_collapse': False,
            'submenus': [],
            'permission': 'dashboard.view_dashboard',
        },
        {
            'icon': 'bi bi-cart-dash',
            'text': 'Sales',
            'url': '/sales/',
            'is_collapse': True,
            'submenus': [
                {'name': 'Customers', 'url': reverse('customers:list_customers'), 'permission': 'customers.view_customer'},
                {'name': 'Sales Order', 'url': reverse('point_of_sale:sales_order_list'), 'permission': 'point_of_sale.view_salesorder'},
                {'name': 'Invoices', 'url': reverse('point_of_sale:invoice_list'), 'permission': 'point_of_sale.view_invoice'},
            ],
            'permission': 'sales.view_salesorder',
        },
        {
            'icon': 'bi bi-basket-fill',
            'text': 'Inventory',
            'url': reverse('inventory:item_list'),
            'is_collapse': True,
            'submenus': [
                {'name': 'Items', 'url': reverse('inventory:item_list'), 'permission': 'inventory.view_product'},
                {'name': 'Item Categories', 'url': reverse('inventory:category_list'), 'permission': 'inventory.view_category'},
                {'name': 'Inventory Adjustments', 'url': '/reports/', 'permission': 'inventory.view_inventory'},
            ],
            'permission': 'inventory.view_product',
        },
        {
            'icon': 'bi bi-bag-check',
            'text': 'Purchases',
            'url': reverse('purchase:purchase_order_list'),
            'is_collapse': True,
            'submenus': [
                {'name': 'Vendors', 'url': reverse('purchase:vendor_list'), 'permission': 'purchase.view_vendor'},
                {'name': 'Purchase Orders', 'url': reverse('purchase:purchase_order_list'), 'permission': 'purchase.view_purchaseorder'},
                {'name': 'Bills', 'url': reverse('purchase:bill_list'), 'permission': 'purchase.view_bill'},
            ],
            'permission': 'purchase.view_purchaseorder',
        },
        {
            'icon': 'bi bi-people',
            'text': 'Employee',
            'url': '/employee/',
            'is_collapse': True,
            'submenus': [
                {'name': 'Employee List', 'url': reverse('employee:employee_list'), 'permission': 'employees.view_employeeprofile'},
                {'name': 'Calendar', 'url': reverse('employee:assignment-calendar'), 'permission': 'employees.view_employeeassignment'},
            ],
            'permission': 'employees.view_employeeprofile',
        },
        {
            'icon': 'bi bi-file-earmark-text',
            'text': 'Reports',
            'url': reverse('reports:reports_dashboard'),
            'is_collapse': True,
            'submenus': [
                {'name': 'Sales Reports', 'url': reverse('reports:sales_reports'), 'permission': 'reports.view_salesreport'},
                {'name': 'Inventory Reports', 'url': reverse('reports:inventory_reports'), 'permission': 'reports.view_inventoryreport'},
                {'name': 'Employee Reports', 'url': reverse('reports:employee_reports'), 'permission': 'reports.view_employeereport'},
                {'name': 'Purchase Reports', 'url': reverse('reports:purchases_reports'), 'permission': 'reports.view_purchasereport'},
            ],
            'permission': 'reports.view_reportsdashboard',
        },
    ]

    # Filter navigation items based on permissions
    visible_nav_items = []
    for item in nav_items:
        # Filter submenus based on user permission
        item['submenus'] = [
            submenu for submenu in item.get('submenus', [])
            if user.has_perm(submenu.get('permission', ''))
        ]

        has_parent_permission = item.get('permission') and user.has_perm(item['permission'])
        has_visible_submenus = bool(item['submenus'])

        # Show parent item if:
        # - it’s not collapsible (like Dashboard), or
        # - user has the main permission, or
        # - user has permission to at least one submenu
        if not item.get('is_collapse', False) or has_parent_permission or has_visible_submenus:
            visible_nav_items.append(item)

    return {'nav_items': visible_nav_items}
