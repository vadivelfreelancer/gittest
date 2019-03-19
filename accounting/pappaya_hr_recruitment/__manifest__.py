# -*- coding: utf-8 -*-
{
    'name': 'Pappaya HR Recruitment Management',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': -19,
    'summary': 'Pappaya',
    'author': 'Murugan',
    'website': 'https://www.pappaya.com',
    'depends': ['base', 'pappaya_base', 'hr', 'hr_recruitment', 'utm', 'hr_payroll', 'pappaya_hr'],
    'data': [
        # configurations
        # 'security/ir.model.access.csv',
        'views/configurations/work_hours_subject_view.xml',
        'views/configurations/number_hours_week_view.xml',
        'views/configurations/number_of_students_view.xml',
        'views/configurations/budget_hr_view.xml',
        'views/configurations/document_view.xml',

        #'views/manpower_wrf_view.xml',
        'views/requisition_form_view.xml',
        'views/application_view.xml',
        'views/pappaya_screening_view.xml',
        'views/hr_job_view.xml',
        'views/applicant_attachment_view.xml',
        'views/hr_job_description_view.xml',
        # menu
        'menu/menu.xml',
        'report/job_offer_letter_report.xml',
        'report/confirmation_letter_report.xml',
        'report/nspira_offer_letter_report.xml',
        'report/nspira_appointment_letter_report.xml',

        'data/mail_template_data_recruitment.xml',
        'data/mail_template_data_dept_wise_open_recruitment.xml',
        'data/employee_id_sequence.xml',
        'demo/report_layout.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
