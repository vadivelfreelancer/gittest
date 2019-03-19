# -*- coding: utf-8 -*-
{
    'name': 'Pappaya Communication Management',
    'version': '9.0.2.4.0',
    'license': 'LGPL-3',
    'category': 'Pappaya Education',
    "sequence": 3,
    'summary': 'Manage Communication related things',
    'complexity': "easy",
    'description': """
        This module provide communication details.
    """,
    'author': 'Pappaya',
    'website': 'http://www.pappaya.com',
    'depends': ['pappaya_building'],
    'data': [
        'views/communication_view.xml',
        'menu/menu.xml',
            ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
