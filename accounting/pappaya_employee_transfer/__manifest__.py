# -*- coding: utf-8 -*-
###################################################################################
#
###################################################################################
{
    'name': 'Pappaya Employee Transfer',
    'version': '11.0.1.0.0',
    'summary': 'Employee transfer between branches',
    'category': 'Generic Modules/Human Resources',
    'author': 'Murugan',
    'maintainer': 'Pappaya',
    'company': 'Pappaya',
    'website': 'https://www.pappaya.com',
    'depends': ['base','hr','hr_contract','pappaya_hr'
                ],
    'data': [
        'views/employee_transfer.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
