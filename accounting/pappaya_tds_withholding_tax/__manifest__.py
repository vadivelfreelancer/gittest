# -*- coding: utf-8 -*-
{
    'name': 'Papaya TDS / Withholding Tax',
    'version': '1.0',
    'category': 'Accounting & Finance',
    'sequence': 1,
    'summary': 'Tax Deducted at Source(TDS) or Withholding Tax.',
    'description': """
Manage Tax Deducted at Source(TDS) or Withholding Tax
===========================================================

This application allows you to apply TDS or withholding tax at the time of invoice or payment.

    """,
    'website': 'http://www.pappaya.com/',
    'author': 'pappaya',
    'depends': ['account_invoicing'],
    'currency': 'INR',
    'license': 'Other proprietary',
    'data': [
        'views/account_view.xml',
        'views/res_partner_view.xml',
        'views/account_payment_view.xml',
        'views/account_invoice_view.xml',
    ],
    'demo': [],
    'css': [],
    'images': ['images/tds_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
