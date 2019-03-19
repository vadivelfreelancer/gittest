# -*- coding: utf-8 -*-
{
    'name': 'Pappaya Fees Management',
    'version': '11.0.2.4.0',
    'license': 'LGPL-3',
    'category': 'PappayaEd',
    "sequence": -16,
    'summary': 'Manage Educational Fees',
    'complexity': "easy",
    'description': """Description""",
    'author': 'Think42Labs',
    'website': 'http://www.think42labs.com',
    'depends': ['product', 'account', 'pappaya_base', 'account_group_menu', 'account_invoicing', 'web'],
    'data': [
        # Demo
        # 'demo/fees_head.xml',

        # Data
        'data/mail_template_data.xml',
        'data/ir_sequence_data.xml',

        # Security
        'security/ir.model.access.csv',

        # Wizard
        'wizard/daybook_wizard.xml',
        'wizard/cheque_deposit_lag_report_view.xml',
        #'wizard/class_wise_fee_reconciliation.xml',
        #'wizard/fee_balance.xml',
        #'wizard/fee_collection_summary.xml',
        #'wizard/fee_concession_wizard.xml',
        #'wizard/schoolwise_consolidated.xml',
        #'wizard/student_fee_collection_summary.xml',
        #'wizard/rte_payment_report_view.xml',
        #'wizard/fee_structure_report_view.xml',
        #'wizard/bank_ledger.xml',
        #'wizard/bank_ledger_all.xml',
        #'wizard/bank_ledger_school_wise_view.xml',

        # Views
        'views/ezetap_device_view.xml',
        'views/concession_reason_view.xml',
        'views/fees_head_view.xml',
        'views/fees_structure_view.xml',
        'views/fees_collection_view.xml',
        'views/fees_receipt_view.xml',
        'views/concession_fees_view.xml',
        'views/fees_ledger_view.xml',
        'views/bank_account_config_view.xml',
        'views/bank_name_config.xml',
        'views/bank_deposit_view.xml',
        'views/bank_deposit_clearance_view.xml',
        #'views/bank_status_view.xml',
        'views/payment_status_view.xml',
        'views/student_payment_view.xml',
        'views/other_payment_view.xml',
        'views/fees_refund_view.xml',
        'views/imulpay_authorize_view.xml',
        'views/sms_content_view.xml',
        'views/bank_challan_transaction_view.xml',
        # Account Groups
#       'views/accounts/account_main_group_view.xml',
#       'views/accounts/account_group_view.xml',
#       'views/accounts/account_sub_group_view.xml',
#       'views/accounts/account_ledger_view.xml',
#       'views/accounts/account_sub_ledger_view.xml',

        # Report
		'report/fee_receipt_pdf.xml',
        #  'report/fee_refund_receipt_pdf.xml',
		'report/fee_ledger_pdf.xml',
        'report/daybook_pdf.xml',
		#  'report/fee_collection_summary_pdf.xml',
        #  'report/student_fee_collection_summary_pdf.xml',
		#  'report/fee_report_refund.xml',
		#  'report/report_menu.xml',
        #  'report/fee_concession_pdf.xml',
        #  'report/fee_balance_pdf.xml',
        #  'report/class_wise_fee_reconciliation_pdf.xml',
        #  'report/rte_payment_report_pdf.xml',
        #  'report/fee_structure_report_pdf.xml',
        'views/webclient_templates.xml',
        # Menu
        'menu/pappaya_core_fees_menu.xml',
        
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
