# -*- coding: utf-8 -*-

{
    'name': 'Purchase Indent / Requisition Management',
    'version': '0.1',
    'summary': """Create Purchase Indents To Purchase Team.""",
    'description': """
    """,
    'author': 'Techspawn Solutions Pvt. Ltd.',
    'company': 'Techspawn Solutions Pvt. Ltd.',
    'website': 'https://www.techspawn.com',
    'category': 'Purchase',
    'currency': 'EUR',
    'images': ['static/description/main.jpg'],
    'depends': ['sale_stock', 'purchase', 'sale','hr_recruitment'],
    'license': 'LGPL-3',
    'data': [
        # 'security/ir.model.access.csv',
        'views/purchase_production_views.xml',
        'views/purchase_indent_menu.xml',
        'views/res_partner_view.xml',
        'views/stock_indent_menu.xml',
        'views/purchase_indent_sequence.xml',
        'views/stock_move_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}






