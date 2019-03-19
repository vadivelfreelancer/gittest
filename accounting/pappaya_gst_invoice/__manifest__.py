{
    'name'                  : 'GST - Returns and Invoices',
    'version'               : '1.0.2',
    'category'              : 'Accounting',
    'sequence'              : 1,
    "author"                :  "Pappaya",
    "license"               :  "Other proprietary",
    'website'               : 'www.pappaya.com',
    'summary'               : 'GST Invoice Reports',
    'description'           : """

GST - Returns and Invoices
==========================

This Brilliant Module will generate csv. 
-------------------------------------------


Some of the brilliant feature of the module:
--------------------------------------------

	1. Export B2B csv.
	
	2. Export B2Cl csv.
	
	3. Export B2CS csv.
	
	4. Export HSN csv.
	
This module works very well with latest version
-----------------------------------------------
    """,
    'depends': [
        'l10n_in',
        'account_tax_python',
        'purchase',
    ],
    'data': [
        'data/port.code.csv',
        'data/data_unit_quantity_code.xml',
        'data/data_uom_mapping.xml',
        'data/data_dashboard.xml',
        'data/ir_model_fields_data.xml',
        'security/gst_security.xml',
        'security/ir.model.access.csv',
        'wizard/message_wizard_view.xml',
        'wizard/invoice_type_wizard_view.xml',
        'data/gob_server_actions.xml',
        'views/account_invoice_view.xml',
        'views/gst_view.xml',
        'views/port_code_view.xml',
        'views/gstr2_view.xml',
        'views/res_partner_views.xml',
        'views/gst_templates.xml',
        'views/gst_dashboard_view.xml',
        'views/account_fiscalyear_view.xml',
        'views/ir_attachment_view.xml',
        'views/account_period_view.xml',
        'views/gst_sequence.xml',
        'views/unit_quantity_code_view.xml',
        'report/report_invoice.xml',
        'views/uom_map_view.xml',
        'views/gst_action_view.xml',
        'views/gst_menu_view.xml',
        'views/purchase_order_view.xml',
    ],
    'sequence'      : 1,
    "images"        :  ['static/description/Banner.png'],
    'application'   : True,
    'installable'   : True,
    'auto_install'  : False,
    'currency'      :  'INR',
    'pre_init_hook' :'pre_init_check',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
