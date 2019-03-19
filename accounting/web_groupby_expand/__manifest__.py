# -*- coding: utf-8 -*-
{
    "name": "Pappaya - Web GroupBy Expand",
    "description": "A custom Module",
    "sequence": -47,
    'author': 'Think42labs',
    'website': 'https://www.think42labs.com',
    "version": "11.0.1.0.0",
    "category": "Web",
    'summary': 'Expand all groups on single click',
    "depends": ["web"],
    "data": [
        "views/templates.xml",
    ],
    "qweb": [
        "static/src/xml/web_groups_expand.xml",
    ],
    "images": ["static/description/groupexpand.png"],
    'application': True,
    'auto_install': False,
    'installable': True,
}