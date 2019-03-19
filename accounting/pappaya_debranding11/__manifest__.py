# -*- coding: utf-8 -*-
{
    "name": "Pappaya - Debranding",
    "summary": "",
    "category": "Debranding",
    "sequence": -49,
    'author': 'Think42labs',
    'website': 'https://www.think42labs.com',
    "description": """
================================================================================

================================================================================
""",
    'depends': ['base', 'base_import', 'mail', 'web'],
    'data': [
        'views/webclient_templates.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'application': True,
    'auto_install': False,
    'installable': True,
    'web_preload': True,
}