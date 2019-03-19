# -*- coding: utf-8 -*-
{
    "name": "Pappaya - Theme",
    "description": "A custom theme",
    "sequence": -50,
    'author': 'Think42labs',
    'website': 'https://www.think42labs.com',
    "data": [
        "views/assets.xml",
        "views/web.xml",
        "views/webclient_templates.xml"
    ],
    "images":[
        "images/screen.png"
    ],
    "depends": [
        "web","web_widget_many2many_tags_multi_selection"
    ],
    "auto_install": False,
    "installable": True,
    "qweb": [
        "static/src/xml/web.xml",
    ],
    'application': True,
}
