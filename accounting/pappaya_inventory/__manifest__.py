# -*- coding: utf-8 -*-
{
    'name': 'Pappaya Inventory Management',
    'version': '11.0.1.0.0',
    'category': 'Pappaya Inventory',
    'summary': "Manage Inventory",
    'website': 'http://www.pappaya.com',
    'description':"""  Inventory Management manages all daily consumables and assets requires in all the apex bodies of Narayana Group.This module includes purchase order management, warehouse management, asset management, distributions,invoice and inventory reports.
                       """,
    'depends': ['base','pappaya_base','stock','product','purchase','purchase_indent'],
    'data': [
        #Views
        # ITEM Related Masters
        'views/masters/item_class_view.xml',
        'views/masters/store_type_view.xml',
	    #Mapping Related Masters
        'views/item_head_master_view.xml',
        'views/itemhead_with_usermapping_view.xml',
        'views/branch_wise_item_mapping_view.xml',
        'views/branch_wise_item_category_mapping_view.xml',
        'views/subcategory_with_subledger_view.xml',
        'views/inherit_product_view.xml',
        # Vendor Related Masters
        'views/res_partner_view.xml',
        # Tax Masters
        'wizard/tax_update_view.xml',
        # Menu Masters
        'views/menu_view.xml',
        'views/menu_items_view.xml',
        'views/menu_items_mapping_view.xml',
        'views/menu_ingredients_mapping_view.xml',
        'views/branch_mi_mapping_view.xml',
        'views/daily_menu_consum_view.xml',
        # Menu
        'menu/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
