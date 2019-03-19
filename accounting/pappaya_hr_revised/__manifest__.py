# -*- coding: utf-8 -*-
{
    'name': 'Pappaya Branch Wise Revised',
    'version': '11.0.2.4.0',
    'license': 'LGPL-3',
    'category': 'PappayaEd',
    "sequence": 1,
    'summary': 'Manage Employee Revised',
    'author': 'Murugan',
    'maintainer': 'Pappaya',
    'company': 'Pappaya',
    'website': 'https://www.pappaya.com',
    'complexity': "easy",
    'description': """
        Description    ======
    """,
    'depends': ['pappaya_base','base','hr','hr_contract','hr_recruitment','pappaya_hr_attendance'], 
    'data': [
        
        'views/branch_wise_revised_view.xml',
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
