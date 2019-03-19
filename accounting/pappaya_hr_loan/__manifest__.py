# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>


#
###################################################################################
{
    'name': 'Pappaya HR Loan Management',
    'version': '11.0.1.0.0',
    'summary': 'Manage Loan Requests',
    'description': """
        Helps you to manage Loan Requests of your company's staff.
        """,
    'category': 'Human Resources',
    'author': "Pappaya",
    'company': 'Pappaya',
    'maintainer': 'Pappaya',
    'website': "pappaya.com",
    'depends': [
        'base', 'hr_payroll', 'hr', 'account', 'pappaya_payroll'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_loan_seq.xml',
        # 'data/salary_rule_loan.xml',
        'views/loan_interest.xml',
        'views/hr_loan.xml',
        # 'views/hr_payroll.xml',
    ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
