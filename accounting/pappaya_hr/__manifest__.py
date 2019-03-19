# -*- coding: utf-8 -*-
{
    'name': 'Pappaya HR Management',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': -19,
    'summary': 'Pappaya',
    'author': 'Murugan',
    'website': 'https://www.pappaya.com',
    'depends': ['base', 'hr', 'hr_contract', 'pappaya_base', 'hr_recruitment','hr_payroll'],
    'data': [
        # Security
        #'security/record_rules.xml',
        #'security/ir.model.access.csv',
        # Demo Data
        'demo/report_layout.xml',
        #'data/hr_contract_data.xml',
        'data/employee_id_sequence.xml',
        'data/type_of_employment_data.xml',
        'data/employee_relationships_data.xml',

        # Common Master
        'views/employee_category_view.xml',
        'views/employee_subcategory_view.xml',
        'views/inherited_department_view.xml',
        # HR Master Configuration
        'views/employee_type_view.xml',
        'views/teaching_type_view.xml',
        'views/pf_zone_view.xml',
        'views/pt_zone_view.xml',
        'views/pappaya_asset_view.xml',
        'views/employee_dynamic_stage_view.xml',
        'views/hr_contract_view.xml',
        'views/hr.xml',
        'views/employee_relationships_view.xml',
#         'views/configurations/pappaya_object11_view.xml',
#         'views/configurations/pappaya_object12_view.xml',
#         'views/configurations/pappaya_object13_view.xml',
#         'views/configurations/pappaya_object14_view.xml',
#         'views/configurations/pappaya_object15_view.xml',
#         'views/configurations/pappaya_object16_view.xml',
#         'views/configurations/pappaya_object17_view.xml',
#         'views/configurations/pappaya_object18_view.xml',
#         'views/configurations/pappaya_object19_view.xml',
#         'views/configurations/pappaya_object20_view.xml',

        # Report
        'report/narayana_offer_letter_report.xml',
        'report/nspira_appointment_letter_report.xml',
        'data/mail_template_data_hr.xml',
        # Menu
        'menu/menu.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
