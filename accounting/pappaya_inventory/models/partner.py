# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError,except_orm
import re


class ResPartnerType(models.Model):
    _name = 'res.partner.type'

    name = fields.Char('Name', required=True, size=100)
    vendor_class_code = fields.Char('Vendor Class Code', size=5)
    description = fields.Char('Description')


class ResPartnerCategory(models.Model):
    _name = 'res.category'
    _rec_name = 'vendor_category'

    vendor_category = fields.Char('Vendor Category', size=20 )
    type_id = fields.Many2one('res.partner.type', 'Vendor Class')
    vendor_class_code = fields.Char('Vendor Class Code')
    description = fields.Char('Description')

    @api.onchange('type_id')
    def onchange_type_id(self):
        if self.type_id:
            self.vendor_class_code = self.type_id.vendor_class_code or ''


class ResPartner(models.Model):
    _inherit = "res.partner"
    type_id = fields.Many2one('res.partner.type', 'Type')
    gst_reg_type = fields.Selection([('composition', 'Composition'), ('consumer', 'Consumer'), ('regular', 'Regular'),
                                     ('unregistered', 'Unregistered')], 'GST Registration Type')
    # cst_no = fields.Char('CST No', size=10)
    # sst_no = fields.Char('SST No', size=10)
    # cin_no = fields.Char('CIN Number', size=10)
    # tin_no = fields.Char('TIN', help='PAN Card No', size=10)

    #     vendor_class = fields.Many2one('vendor.class','Vendor Class')
    #     vendor_category = fields.Many2one('vendor.category','Vendor Category')

    # vendor_class = fields.Char('Vendor Class')
    vendor_category = fields.Many2one('res.category', 'Vendor Category')
    vendor_status = fields.Selection([('artificial_juridical_person', 'Artificial Juridical Person'),
                                      ('association_of_persons', 'Association of Persons'),
                                      ('body_of_individuals', 'Body of Individuals'),
                                      ('company', 'Company'),
                                      ('firm', 'Firm'),
                                      ('government', 'Government'),
                                      ('hindu_undivided_family', 'Hindu Undivided Family'),
                                      ('individual', 'Individual'),
                                      ('limited_liability_partnership', 'Limited Liability Partnership'),
                                      ('local_authority', 'Local Authority'),
                                      ('trust', 'Trust')
                                      ], 'Vendor Status')
    is_gst_registered = fields.Selection([('yes', 'Yes'), ('no', 'No')], 'Is GST Registered')
    is_gst_regular = fields.Selection([('regular ', 'Regular '), ('composit', 'Composit')], 'Is GST Regular')
    composit_status = fields.Selection([('manufacturer ', 'Manufacturer '),
                                        ('others', 'Others (Including Trader)'),
                                        ('special', 'Special Service Provider (Restaurent)')], 'Composit Status')
    pan_no = fields.Char('PAN', help='PAN Card No', size=10)
    name_pan_card = fields.Char('Name On PAN Card')
    description = fields.Char(string="Description")
    works_contract_status = fields.Selection([('non_registered ', 'Non Registered '),
                                              ('registered', 'Registered'),
                                              ('others', 'Others')], 'Works Contract Status')
    item_vendor = fields.Boolean('Item Vendor')
    service_vendor = fields.Boolean('Service Vendor')
    advertisement_vendor = fields.Boolean('Advertisement Vendor')
    printing_vendor = fields.Boolean('Printing Vendor')

    mess_vendor = fields.Boolean('Mess Vendor')
    vehicle_vendor = fields.Boolean('Vehicle Vendor')
    generator_vendor = fields.Boolean('Generator Vendor')
    security_vendor = fields.Boolean('Security Vendor')

    housekeeping_vendor = fields.Boolean('Housekeeping Vendor')
    water_vendor = fields.Boolean('Water Vendor')
    travelling_vendor = fields.Boolean('Travelling Vendor')
    building_maintenance_vendor = fields.Boolean('Building Maintenance Vendor')

    # mandal = fields.Char('Mandal')
    active = fields.Boolean('Active')
    space = fields.Char('  ', readonly=True)

    # bank_account_no = fields.Char('Bank Account No')
    # bank_name = fields.Char('Bank Name')
    # bank_branch = fields.Char('Bank Branch')
    gstin_no = fields.Char('GSTIN')
    name_pan_card = fields.Char('Name On PAN Card')
    tan_no = fields.Char('TAN')
    payee_name = fields.Char('Payee Name')
    micr = fields.Char('MICR')
    rtgs = fields.Char('RTGS')
    fax = fields.Char('Fax')

    @api.model
    def create(self, vals):
        if 'pan_no' in vals.keys() and vals.get('pan_no'):
            self.validate_pan_number(vals.get('pan_no'))
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'pan_no' in vals.keys() and vals.get('pan_no'):
            self.validate_pan_number(vals.get('pan_no'))
        return super(ResPartner, self).write(vals)

    @api.multi
    def validate_pan_number(self, value):
        """
        Validates if the given value is a valid PAN number or not, if not raise ValidationError
        """
        if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', value):
            return True
        else:
            raise ValidationError("Please enter a valid PAN number")



