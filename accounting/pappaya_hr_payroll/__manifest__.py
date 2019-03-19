# -*- coding: utf-8 -*-
{
    'name': 'Pappaya HR & Payroll Update',
    'version': '1.0',
    'category': 'Human Resources & Payroll Management',
    'sequence': -20,
    'summary': 'Pappaya',
    'author': 'Pappaya Technologies',
    'website': 'https://www.pappaya.com',
    'depends': ['base', 'hr', 'hr_contract', 'hr_holidays', 'hr_payroll', 'hr_recruitment', 'hr_attendance', \
                    'pappaya_base', 'pappaya_hr', 'pappaya_hr_recruitment', 'pappaya_hr_attendance', 'pappaya_monthly_alw_ded', \
                    'pappaya_payslip_mail', 'pappaya_hr_advance', 'pappaya_employee_transfer','pappaya_promotion', \
                    'pappaya_payroll', 'pappaya_hr_exit','pappaya_account_operating_unit', 'pappaya_hr_incentive_arrears', \
                    'pappaya_hr_loan', 'pappaya_hr_revised'],
    'data': [
        # Demo Data
	'security/security.xml',
    'security/ir.model.access.csv',
    'views/scheduled_actions_view.xml',
    'views/others_bank_paysheet_view.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
