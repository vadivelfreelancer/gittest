import uuid

from itertools import groupby
from datetime import datetime, timedelta
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

from odoo.tools.misc import formatLang

from odoo.addons import decimal_precision as dp

class PappayaCommunicationMaster(models.Model):
    _name = 'pappaya.communication.master'
    _description = 'Communication Master'
    

    @api.one
    def act_zonal_approval(self):
        self.state = 'zonal_approval'

    @api.one
    def act_rfo_approval(self):
        self.state = 'rfo_approval'


    branch = fields.Many2one('res.company', 'Branch')
    building_id = fields.Many2one('pappaya.building', 'Building')
    floor_id = fields.Many2one('pappaya.floor','Floor')
    name = fields.Many2one('pappaya.owner', 'Owner Name')
    communication_no = fields.Char('Communication No', size=256)
    material_user = fields.Char('Material User', size=256)
    connection_type = fields.Char('Connection Type', size=256)
    service_provider = fields.Char('Service Provider', size=256)
    billing_duration = fields.Char('Billing Duration', size=256)
    billing_due_date_gap = fields.Integer('Billing Due Date Gap-In days')
    tds_percentage = fields.Float('TDS(%)')
    state = fields.Selection([('draft', 'Draft'), ('zonal_approval', 'Zonal Approved'), ('rfo_approval', 'RFO Approved')], 
                             'State', select=True, readonly=True, default='draft', track_visibility='onchange')
    state_active = fields.Selection([('active', 'Active'), ('in_active', 'In Active')], string="Status")
    #page
    appex = fields.Selection([('1', 'sri chaitanya Education Society'), ('2', 'sri chaitanya Learning PVT.LTD'),('3','sri chaitanya Education Trust'),
                                ('4','Rama sri chaitanya Education Trust'),('5','sri chaitanya Management Services PVT.LTD'),('6','sri chaitanya Educational Trust')], string='Appex')
    
    communication_group = fields.One2many('pappaya.communication.group','communication_id','Communication Groups')
    #Broadband
    plan_type = fields.Selection([('limited', 'Limited'), ('unlimited', 'Unlimited')], string="Plan Type")
    plan_name = fields.Char('Plan Name', size=256)
    down_speed = fields.Char('Download Speed', size=256)
    down_limit = fields.Char('Download Limit', size=256)
    beyond_down = fields.Char('Beyond Download Speed', size=256)
    monthly_charges = fields.Float('Monthly Charges', size=256)
    additional_charges = fields.Float('Additional Charges per MB', size=256)
    is_night = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Is Night Unlimited")
    static_ip_cost = fields.Float('Static IP Cost', size=256)
    #Centrex
    centrex_name = fields.Char('Centrex Name', size=256)
    centrex_status = fields.Selection([('1', 'Artificial Juridical Person'), ('2', 'Association of Persons'),('3','Body of Individuals'),
                                ('4','Company'),('5','Firm'),('6','Government'),('7','Hindhu Undivided family'),('8','Individual'),
				('9','Limited Liability  Partnership'),('9','Local Authority'),('10','Trust')], string='centrex Status')
    centrex_pan_no = fields.Char('PAN NO.', size=256)
    centrex_name_of_pan = fields.Char('Name on PAN Card', size=256)
    #communication
    communication_status = fields.Selection([('1', 'Artificial Juridical Person'), ('2', 'Association of Persons'),('3','Body of Individuals'),
                                ('4','Company'),('5','Firm'),('6','Government'),('7','Hindhu Undivided family'),('8','Individual'),
				('9','Limited Liability  Partnership'),('9','Local Authority'),('10','Trust')], string='centrex Status')
    pan_no = fields.Char('PAN NO.', size=256)
    name_of_pan = fields.Char('Name on PAN Card', size=256)
    
class PappayaCommunicationGroup(models.Model):
    _name = 'pappaya.communication.group'
    _description = 'Communication Group'    
    
    #Communication Group No's Mapping
    communication = fields.Char('Communication', size=256)
    payroll_branch = fields.Char('Payroll Branch', size=256)
    employee_id = fields.Char('Employee', size=256)
    payment_type = fields.Char('Payment Type', size=256)
    pay_amount = fields.Char('Pay Amount', size=256)
    communication_id = fields.Many2one('pappaya.communication.master','Communication')
    
    
    
    
    
    
    
    

