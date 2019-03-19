# -*- coding: utf-8 -*-

{
    'name': 'Pappaya Dynamic List',
    'version': '1.1',
    'author': 'Pappaya',
    'category': 'Dynamic ListView',
    'website': 'pappaya',
    'summary': 'Dynamic List',
    'description': """

Dynamic List
============
Dynamic List module is made to show/hide the column(s) on the list/tree view of Pappaya. After installing the module a "Select Columns" button will be show to the list view before the pagination.

    """,
    'images': ['static/description/saleorders.png'
    ],
    'depends': ['web'],
    'data': [
    'views/listview_button.xml',
    ],
    'demo': [],
    'test': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': ['static/src/xml/listview_button_view.xml'],
    'license': 'Other proprietary'
}

