# -*- coding: utf-8 -*-
{
    'name': 'Pappaya Payroll Mgmt',
    'version': '11.0.2.4.0',
    'license': 'LGPL-3',
    'category': 'PappayaEd',
    "sequence": 1,
    'summary': 'Manage Educational Fees',
    'complexity': "easy",
    'description': """
        Description    ======
    """,
    'author': 'murugan',
    'website': 'http://www.pappaya.com',
    'depends': ['hr','hr_payroll','l10n_in','hr_contract','hr_payroll_account','hr_attendance','hr_holidays','hr_recruitment','pappaya_monthly_alw_ded',
                'pappaya_hr_attendance','pappaya_hr_revised','pappaya_hr_incentive_arrears'], 
    'data': [
        'data/hr_holidays_data.xml',
        'data/holiday_status_data.xml',
        'data/hr_salary_rules_data.xml',
        'data/bank_paysheet_sequence.xml',
        # 'views/payroll_view.xml',
        #'views/hr_promotion_view.xml',
        #'security/security.xml',
        # 'security/ir.model.access.csv',
        
        'views/tds_heads_view.xml',
        'views/hr_employee_view.xml',
        'views/inherited_res_bank_view.xml',
        'views/hr_holiday_view.xml',
        'views/hide_menus.xml',
        'report/report_layout.xml',
        'report/payslip_report.xml',
        'report/nspira_payslip_report.xml',
        'views/hr_payslip_view.xml',
        'views/public_holiday_view.xml',
        'views/leave_encashment_view.xml',
	    'views/hr_job_view.xml',
	    'views/lock_sublock_view.xml',
        'views/payroll_cycle_view.xml',
        'views/payment_release_view.xml',
        'views/bank_paysheet_view.xml',
        #'views/arrear_bank_paysheet_view.xml',
        #'views/incentive_bank_paysheet_view.xml',
        'views/compensatory_request_view.xml',
        

        
        
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
