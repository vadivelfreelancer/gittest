# -*- coding: utf-8 -*-
{
    'name': 'Pappaya Payslip Mail',
    'version': '11.0.2.4.0',
    'license': 'LGPL-3',
    'category': 'PappayaEd',
    "sequence": 1,
    'summary': 'Manage Pappaya Payslip Mail',
    'complexity': "easy",
    'description': """
        Description    ======
    """,
    'author': 'murugan',
    'website': 'http://www.pappaya.education.com',
    'depends': ['hr','hr_payroll','pappaya_payroll'],
    'data': [
        
        'data/mail_template_data_payslip.xml',
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
