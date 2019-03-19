# -*- coding: utf-8 -*-

{
    'name': 'Pappaya Vehicle Management',
    'summary': 'Pappaya Vehicle Management',
    'author': 'Think42labs',
    'website': 'https://www.think42labs.com',
    'category': 'Tools',
    'version' : '1.0',
    'description': """
    This module is used for Pappaya Vehicle Management.
        """,
    'depends': ['base', 'mail', 'pappaya_electricity'],
    'data': [
        'views/vehicle_details.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application':True
}
