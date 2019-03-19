# -*- coding: utf-8 -*-
import datetime
from datetime import datetime
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import Warning
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp

class PappayaBuildingDetail(models.Model):
    _name = 'pappaya.building.detail'
    
    branch_id = fields.Many2one('operating.unit', string="Branch")
    building_id = fields.Many2one('pappaya.building','Building')
    is_rented = fields.Selection([('yes', 'Yes'),('no', 'No')], 'Is Rented')
    street_vill = fields.Char('Street-Vill',size=100)
    pin_code = fields.Char('Pin Code',size=6)
    mandal = fields.Char('Mandal',size=30)#Clarify
    district = fields.Char('District',size=30)#Clarify
    area = fields.Char('Area',size=100)
    house_no = fields.Char('HNo',size=20)
    area_type = fields.Selection([('building_area', 'Building Area'), ('open_area', 'Open Area')], 'Area Type')
    building_total_area = fields.Float(string='Building Total Area(Sft)')
    common_area = fields.Float(string='Common Area(Sft)')
    cellar_area = fields.Float(string='Cellar Area(Sft)')
    no_of_floors = fields.Integer('No Of Floors')
    others_floors_area = fields.Float(string='Others Floors Area(Sft)')
    rent_increase_percentage = fields.Float('Rent Increase Percentage')
    rent_increase_interval = fields.Float('Rent Increase interval(Months)')
    occupancy_date = fields.Date('Occupancy Date')
    municipal_tax_owner = fields.Float('Municipal Tax Owner(%)')
    municipal_tax_tenant = fields.Float('Municipal Tax Tenant(%)')
    lease_commencement_date =  fields.Date('Lease Commencement Date')
    rental_duration = fields.Char('Rent Duration',size=20)#Clarify
    tpa = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='TPA')
    is_electricity_commercial = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Is Electricity Commercial')
    is_commercial_building = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Is Commercial Building')
    aminities_cost= fields.Char('Aminities Cost',size=20)
    is_aminities_provided = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Is Aminities Provided')
    lock_period = fields.Char('Lock Period(Months)',size=20)
    electricity_category = fields.Char('Electricity Category',size=20)
    student_capacity = fields.Integer('Student Capacity')
    student_occupied = fields.Integer('Student Occupied')
    rent_agrm_expiry_date =  fields.Date('Rent Agrement Expiry Date')
    sms_no1 = fields.Char('Sms_No1',size=10)
    sms_no2 = fields.Char('Sms_No2',size=10)
    sms_no3 = fields.Char('Sms_No3',size=10)
    sms_no4 = fields.Char('Sms_No4',size=10)

    
