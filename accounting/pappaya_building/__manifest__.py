{
    'name': 'Pappaya Building Management',
    'version': '11.0.1.0.0',
    'category': 'Pappaya Education',
    'summary': "Manage Building",
    'website': 'http://www.pappaya.com',
    'description':""" Building module to maintain the building, block, floor, room, owner and rent agreements,
                      rent generations """,
    'depends': ['base','pappaya_base','pappaya_inventory'],
    'data': [
            #Views
            'views/pappaya_building_view.xml',
            'views/pappaya_floor_view.xml',
            'views/pappaya_block_view.xml',
            'views/pappaya_building_room_view.xml',
            'views/pappaya_building_class_view.xml',
            'views/building_group_update_view.xml',
            'views/pappaya_building_enhancement_view.xml',
            #'views/res_partner_view.xml',
            'views/pappaya_owner_view.xml',
            'views/building_agreement_view.xml',
            'views/room_usage_view.xml',
            'views/security_deposit_view.xml',
            'views/security_deposit_transfer_view.xml',
            'views/security_deposit_repayment_view.xml',
            'views/security_deposit_rental_arrears_view.xml',
            'views/building_advance_view.xml',
            'views/building_advance_transfer_view.xml',
            'views/building_advance_repayment_view.xml',
            'views/building_advance_rental_arrears_view.xml',
            'views/building_advance_security_deposit_view.xml',
            'views/main_building_mapping_view.xml',
            'views/rent_creation_view.xml',
            'views/rent_generation_view.xml',
            'views/building_vacation_view.xml',
            'views/rental_arrears_view.xml',
            'views/maintenance_arrears_view.xml',
            #data
            'data/building_purpose_data.xml',
            
            # Wizard
            'wizard/rent_invoice_creation.xml',
            # Menu
            'menu/menu.xml',
             ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
