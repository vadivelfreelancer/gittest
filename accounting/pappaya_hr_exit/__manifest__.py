#~ -*- coding: utf-8 -*-
{
 'name': 'Pappaya Employee Exit',
 'version': '11.0.1.0.0',
 'summary': """Manages Employee's  Exit Process""",
 'description': """This module used to remembering the 
                      employee's exit progress.""",
 'category': 'Generic Modules/Human Resources',
 'author':'Murugan',
 'company': 'Pappaya',
 'website': "https://www.think42labs.com",
 'depends': ['base','hr', 'hr_contract','calendar','hr_payroll','pappaya_payroll'],
 'data':[
         'demo/report_layout.xml',
         'views/hr_exit_view.xml',
		 'views/hr_exit_structure_view.xml',
		 'report/hr_exit_process_report.xml',
		 'report/offer_letter.xml',
         'report/relieving_letter_report.xml',
         'security/hr_exit_security.xml',
         #'security/ir.model.access.csv'
         ],
 'installable': True,
 'auto_install': False,
 'application': True,
}
