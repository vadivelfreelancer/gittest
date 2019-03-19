# -*- coding: utf-8 -*-
{
    "name": "Pappaya : ERP",
    "summary": "Base Module",
    "version": "11",
    "category": "Core",
    "description": """ Backend theme """,
    "author": "Nivas M",
    "sequence": -100,
    'website': 'https://pappaya.education/',
    "depends": ['base'],
    "data": [
        'views/core.xml',
        'views/model_log_view.xml',
        'views/menu.xml',
    ],
    "installable": True,
    'application': True,
    'auto_install': False,
}