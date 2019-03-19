# -*- coding: utf-8 -*-
{
    'name': 'Pappaya Promotion',
    'version': '11.0.2.4.0',
    'license': 'LGPL-3',
    'category': 'PappayaEd',
    "sequence": 1,
    'summary': 'Manage Employee Promotion',
    'author': 'Murugan',
    'maintainer': 'Pappaya',
    'company': 'Pappaya',
    'website': 'https://www.pappaya.com',
    'complexity': "easy",
    'description': """
        Description    ======
    """,
    'depends': ['hr','hr_payroll','hr_contract','hr_payroll_account','hr_attendance','hr_holidays','hr_recruitment','pappaya_payroll'], 
    'data': [
        
        'views/employee_promotion_view.xml',
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
