{
    "name": "nConnect Base",
    'version': '1.0',
    'category': 'nConnect',
    'sequence': 6,
    'summary': 'nConnect mobile application base',
    'author': 'Think42labs',
    'website': 'https://www.think42labs.com',
    'depends': ['base', 'base_setup', 'web', 'web_settings_dashboard', 'mail', 'fetchmail'],
    'data': [
        'views/nconnect_base_view.xml',
        'views/nconnect_sequence.xml',
        'security/nconnect_groups.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
