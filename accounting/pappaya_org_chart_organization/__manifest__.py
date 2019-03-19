# -*- coding: utf-8 -*-
{
	'name': "Pappaya Organization Chart Department",
	'summary': """Dynamic display of your Department Organization""",
	'description': """Dynamic display of your Department Organization""",
	'author': 'Think42labs',
	'maintainer': 'Pappaya',
	'company': 'Pappaya',
	'website': 'https://www.pappaya.com',
	'category': 'PappayaEd',
	'version': '2.0',
	'license': 'AGPL-3',
	'depends': ['account'],
	'data': ['views/org_chart_views.xml'],
	'images': [
		'static/src/img/main_screenshot.png'
	],
	'qweb': [
        "static/src/xml/org_chart_department.xml",
    ],
	'installable': True,
	'application': True,
	'auto_install': False,
}
