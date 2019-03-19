# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from openerp.exceptions import ValidationError,except_orm
import re

class PappayaOwner(models.Model):
    _name = 'pappaya.owner'
    _rec_name = 'owner_id'
    
    owner_id = fields.Many2one('res.partner', string='Owner Name',domain=[('type_id','ilike','building')])
    owner_status = fields.Selection([('individual', 'Individual'), ('company', 'Company'), ('partners', 'Partners')],string='Owner Status')
    branch_id = fields.Many2one('operating.unit', string='Branch')
    building_id = fields.Many2one('pappaya.building', string='Building')
    building_rent = fields.Float(string='Building Rent', related='building_id.rent')
    building_maitanance_amt = fields.Float(string='Building Maintenance Amount', related='building_id.maintenance_amount')
    cheque_in_favour_of =  fields.Char(string='Cheque in favour of',size=100)
    rent = fields.Float(string='Rent', track_visibility='onchange')
    maintanance_amt = fields.Float(string='Maintenance Amount', track_visibility='onchange')
    active = fields.Boolean('Active',default=True)
    active_owners_rent = fields.Char(string='Active Owners Rent',size=100)
    active_owners_maintanance = fields.Char(string='Active Owners Maintenance',size=100)
    hno = fields.Char(string='HNO',size=100)
    street_vill = fields.Char(string='Street-Vill',size=100)
    area = fields.Char(string='Area',size=100)
    # ~ mandal = fields.Char('Mandal')#Clarify
    mandal_id = fields.Many2one('pappaya.mandal.marketing', string='Mandal')
    # ~ district = fields.Char('District')#Clarify
    district_id = fields.Many2one('state.district', string='District')
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=lambda self: self.env.user.company_id.country_id)
    pin_code = fields.Char(string='Pin Code', size=6)
    phone_no = fields.Char(string='Phone No', size=10)
    mobile_no = fields.Char(string='Mobile No', size=10)
    email = fields.Char(string='Email')
    is_tds_applicable = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Is Tds applicable?')
    tds_percentage = fields.Float(string='TDS(Percentage)')
    maintanance_tds_per = fields.Float(string='Maintenance Tds(Percentage)')
    is_st_applicable = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Is Service Tax Applicable?')
    service_percentage = fields.Float(string='Service(Percentage)')
    is_tpa = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='TPA')
    tpa_name = fields.Char(string='TPA Name',size=100)
    owner_percentage = fields.Float(string='Owner Percentage', track_visibility='onchange')
    tenant_percentage = fields.Float(string='Tenant Percentage', track_visibility='onchange')
    incl_excl = fields.Selection([('inclusive', 'Inclusive'), ('exclusive', 'Exclusive')], string='Inclusive/Exclusive')
    state = fields.Selection([('draft', 'Draft'), ('building_owner_approval', 'Building Owner zonal approval'),('buiding_owner_dfe_approval', 'Building Owner DFE Approval')], string='State', required=True, default='draft', track_visibility='onchange')
    # Bank Details
    account_no = fields.Char(string='Bank Account No', track_visibility='onchange',size=20)
    bank = fields.Char(string='Bank Name', track_visibility='onchange',size=100)
    bank_branch = fields.Char(string='Bank Branch', track_visibility='onchange',size=100)
    rtgs = fields.Char(string='RTGS', track_visibility='onchange',size=100)
    # GST and PAN
    pan_no = fields.Char(string='Pan No', track_visibility='onchange',size=16)
    pan_name = fields.Char(string='Name on PAN',size=100)
    is_gst_registered = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Is GST Registered?')
    gst_no = fields.Char(string='GST No', size=15, track_visibility='onchange')
    gst_type = fields.Selection([('regular', 'Regular'), ('composit', 'Composit')], default='regular', string='GST Type')
    gst_regular = fields.Selection([('composition', 'Composition'), ('consumer', 'Consumer'), ('regular', 'Regular'),('unregistered', 'Unregistered')], string='GST Registration Type')
    gst_composit = fields.Selection([('manufacturer ', 'Manufacturer '),('others', 'Others (Including Trader)'),('special', 'Special Service Provider (Restaurent)')], string='Composit Status')
    cst_no = fields.Char(string='CST No', size=10)
    sst_no = fields.Char(string='SST No', size=10)
    cin_no = fields.Char(string='CIN', size=21)
    tin_no = fields.Char(string='TIN', size=9)
    owner_id_number = fields.Char(string='Owner Identification Number',size=10)
    arrear_amount = fields.Float()
    maintenance_arrears_amt = fields.Float()

    @api.constrains('pin_code','phone_no','mobile_no','pan_no','email')
    def validation_sms_no(self):
        if self.pin_code:
            match_pin_code = re.match('^[\d]*$', self.pin_code)
            if not match_pin_code or len(self.pin_code) < 6:
                raise ValidationError(_("Please enter a valid Pin Code"))
        if self.phone_no:
            match_phone_no = re.match('^[\d]*$', self.phone_no)
            if not match_phone_no or len(self.phone_no) < 10:
                raise ValidationError(_("Please enter a valid 10 digit Phone No"))
        if self.mobile_no:
            match_mobile_no = re.match('^[\d]*$', self.mobile_no)
            if not match_mobile_no or len(self.mobile_no) < 10:
                raise ValidationError(_("Please enter a valid 10 digit Mobile No"))
        if self.pan_no:
            match_pan_no = re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}', self.pan_no)
            if not match_pan_no or len(self.pan_no) < 10:
                raise ValidationError(_("Please enter a valid PAN number"))
        if self.email:
            match_email = re.match(r'\w+@\w+', self.email)
            if not match_email:
                raise ValidationError(_("Please enter a valid Email Address"))

    @api.one
    def act_zonal_approval(self):
        self.state = 'building_owner_approval'

    @api.one
    def act_dfe_approval(self):
        self.state = 'buiding_owner_dfe_approval'

    @api.one
    def act_active(self):
        self.active = True

    @api.one
    def act_inactive(self):
        self.active = False

    @api.onchange('district_id')
    def _onchange_district(self):
        domain = []
        if self.district_id:
            district_obj = self.env['state.district'].search([('id', '=', self.district_id.id)])
            for obj in district_obj:
                domain.append(obj.id)
            return {'domain': {'mandal_id': [('district_id', 'in', domain)]}}

    @api.onchange('mandal_id')
    def _onchange_mandal(self):
        domain = []
        if self.mandal_id:
            mandal_obj = self.env['pappaya.mandal.marketing'].search([('id', '=', self.mandal_id.id)])
            for obj in mandal_obj:
                domain.append(obj.state_id.id)
            return {'domain': {'state_id': [('id', 'in', domain)]}}

    @api.onchange('owner_id')
    def _onchange_owner(self):
        if self.owner_id:
            existing_owner = self.search([('building_id','=',self.building_id.id),('branch_id','=',self.branch_id.id),('owner_id','=',self.owner_id.id)])
            if existing_owner:
                raise ValidationError(_("Owner is already exists"))

    @api.multi
    @api.depends('name')
    def name_get(self):
        result = []
        for rec in self:
            name = str(rec.owner_id.name) + ' - ' + str(rec.owner_id_number or '')
            result.append((rec.id, name))
        return result