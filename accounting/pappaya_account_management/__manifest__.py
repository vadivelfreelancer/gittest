# -*- coding: utf-8 -*-

{
    'name': 'Pappaya Account Management',
    'version': '11.0.1.0.0',
    'summary': 'Pappaya Account Management',
    'website': 'http://www.pappaya.com',
    'category': 'Accounting',
    'description': """
    This module is used for Pappaya Account Management with Groups and Sub-groups.
        """,
    'depends': ['base', 'mail','account','account_group_menu','pappaya_electricity','pappaya_base'],
    'data': [
        'data/data_groups.xml',
        'wizards/get_branches.xml',
        'views/account_details.xml',
        'views/journal_voucher.xml',
        'wizards/sub_ledger_to_fy_view.xml',
        'wizards/branch_to_fy_wizard_view.xml',
        'wizards/branch_sub_ledger_mapping_wiz_view.xml',
        'wizards/sub_ledger_branch_mapping_view.xml',
        'wizards/bank_mapped_to_branche_view.xml'

    ],
    'installable': True,
    'auto_install': False

}
