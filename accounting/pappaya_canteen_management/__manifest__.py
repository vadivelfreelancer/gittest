# -*- coding: utf-8 -*-
{
    'name': 'Canteen Management',
    'version': '1.0',
    'category': 'Management',
    'sequence': 20,
    'summary': """Selling and managing Canteen""",
    'description': """ - POC purpose - 
               Here we handled Serial port connection need to change TCP protocol
               Using Below command to find the serial port 
                $ python -m serial.tools.list_ports
                need to change permission
                $ sudo chmod 666 /dev/ttyUSB1""",
    'author': 'Pappaya',
    'website': 'http:\\pappaya.education',
    'depends': ['base', 'pappaya_attendance_uhfid'],
    'data': [
        'views/canteen_mgmt_view.xml',
        'menu/menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
