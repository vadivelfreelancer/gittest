# -*- coding: utf-8 -*-
{
    'name': 'Pappaya HR Attendance',
    'version': '1.0',
    'category': 'Narayana HR Attendance',
    'sequence': -18,
    'summary': 'Pappaya',
    'author': 'Think42labs',
    'website': 'https://www.think42labs.com',
    'depends': ['pappaya_base', 'pappaya_hr', 'hr_attendance'],
    'data': [
        'views/pappaya_attendance_view.xml',
        'views/pappaya_daily_attendance_view.xml',
        'views/pappaya_employee_attendance_view.xml',
        'wizard/attendance_report_view.xml'
       
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}