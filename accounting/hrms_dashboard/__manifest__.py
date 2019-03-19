# -*- coding: utf-8 -*-
{
    'name': "Pappaya HR Dashboard",
    'version': '11.0.2.0.0',
    'summary': """HR Dashboard""",
    'category': 'Dashboard',
    'author': 'Pappaya',
    'company': 'Pappaya',
    'website': "https://www.pappaya.com",
    'depends': ['hr', 'hr_holidays', 'hr_payroll', 'hr_attendance', 'hr_recruitment', 'event', \
                    'pappaya_base', 'pappaya_hr', 'pappaya_hr_recruitment', 'pappaya_hr_payroll', 'pappaya_hr_attendance', 'pappaya_admission'],
    'external_dependencies': {
        'python': ['pandas'],
    },
    'data': [
        'security/ir.model.access.csv',
        'report/broadfactor.xml',
        'views/dashboard_views.xml'],
    'qweb': ["static/src/xml/hrms_dashboard.xml"],
    'installable': True,
    'application': True,
}
