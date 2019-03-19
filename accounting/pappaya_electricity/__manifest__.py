# -*- coding: utf-8 -*-

{
    'name': 'Pappaya Electricity Master',
    'version': '9.0.2.4.0',
    'license': 'LGPL-3',
    'category': 'Pappaya Education',
    "sequence": 3,
    'summary': 'Manage Electricity',
    'complexity': "easy",
    'description': """
        This module provide electricity management and calculation of building.
    """,
    'author': 'Think42Labs',
    'website': 'http://www.think42labs.com',
    'depends': ['base', 'mail','pappaya_base','pappaya_building'],
    'data': [
        'views/electricity_details.xml',
        'views/communication.xml',
        'security/security_electricity.xml',
        'wizard/service_confirmation.xml',
        'wizard/electricity_bill_reversal.xml',
        'wizard/bill_pending_posting.xml',
        'wizard/communication_no_branch_update.xml',
    ],
    'installable': True,
    'auto_install': False

}
