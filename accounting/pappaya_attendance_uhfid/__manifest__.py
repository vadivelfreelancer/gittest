# -*- coding: utf-8 -*-
###############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech-Receptives(<http://www.techreceptives.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

{
    'name': 'Pappaya Attendance',
    'version': '9.0.2.4.0',
    'license': 'LGPL-3',
    'category': 'Pappaya Education',
    "sequence": 3,
    'summary': 'Manage Attendances',
    'complexity': "easy",
    'description': """
        This module provide feature of Attendance Management.
        RFID Implementation steps

        Step :1 
            In openerp/tools/config.py change the value of db_name ( 'False' => 'CURRENT DB NAME')
            
        Step-2:
            Current Configuration
            
            Go to Organization (school) screen and enter ip in appropriate field
            like 192.168.1.xxx:xxx,192.168.1.xxx:xxx
            
            Previous configuration
            # odoo application go to Settings -> Technical -> Parameter -> System Parameter
            # create on record 
            # Key= "RFID_DEVICE_URL"
            # Value= URL and port without http (like 192.168.1.100:200)


    """,
    'author': 'Pappaya',
    'website': 'http://www.pappaya.com',
    'depends': ['pappaya_base','pappaya_admission'],
    'data': [
        # 'security/attendance_security.xml',
        # 'security/ir.model.access.csv',
        'views/rfid_tracking_data_view.xml',
        # 'views/attendance_register_view.xml',
        # 'views/attendance_sheet_view.xml',
        # 'views/attendance_line_view.xml',
        #~ 'wizards/attendance_import_view.xml',
        # 'wizards/student_attendance_wizard_view.xml',
        # 'report/student_attendance_report.xml',
        # 'report/report_menu.xml',
        'attendance_menu.xml'
    ],
    'demo': [
        #~ 'demo/attendance_register_demo.xml',
        #~ 'demo/attendance_sheet_demo.xml',
        #~ 'demo/attendance_line_demo.xml',
    ],
    'images': [
        'static/description/pappayaed_attendance_banner.jpg',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
