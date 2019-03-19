{
    'name': 'Web Export Current View',
    'version': '11.0.1.0.0',
    'category': 'Web',
    'author': 'Henry Zhou, Agile Business Group, \
            Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/web',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'web',
    ],
    "data": [
        'views/web_export_view_view.xml',
    ],
    'qweb': [
        "static/src/xml/web_export_view_template.xml",
    ],
    'installable': True,
    'auto_install': False,
}