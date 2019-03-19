# -*- coding: utf-8 -*-
{
    'name': 'Pappaya Monthly Allowance and Deduction',
    'version': '11.0.2.4.0',
    'license': 'LGPL-3',
    'category': 'PappayaEd',
    "sequence": 1,
    'summary': 'Manage Employee Monthly Allowance and Deduction',
    'complexity': "easy",
    'description': """
        Description    ======
    """,
    'author': 'Murugan',
    'website': 'http://www.pappaya.com',
    'depends': ['hr','hr_payroll','pappaya_base'], 
    'data': [
        
        'views/allowance_and_deduction_view.xml',
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
