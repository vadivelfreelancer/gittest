# -*- coding: utf-8 -*-
{
    'name': 'Pappaya Incentive and Arrears',
    'version': '11.0.2.4.0',
    'license': 'LGPL-3',
    'category': 'PappayaEd',
    "sequence": 1,
    'summary': 'Manage Employee Incentive and Arrears',
    'author': 'Murugan',
    'maintainer': 'Pappaya',
    'company': 'Pappaya',
    'website': 'https://www.pappaya.com',
    'complexity': "easy",
    'description': """
        Description    ======
    """,
    'depends': ['pappaya_base','base','hr','hr_contract','hr_recruitment','pappaya_hr_attendance','pappaya_hr'], 
    'data': [
           'views/arrears_view.xml',
	       'views/incentive_view.xml',
	       'views/arrear_incentive_sequence.xml',
           ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
