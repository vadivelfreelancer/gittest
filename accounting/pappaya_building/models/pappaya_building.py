from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import re

class BuildingPurpose(models.Model):
    _name="building.purpose"
    _description="Building Purpose"
    name = fields.Char('Name',required=1)

class PappayaBuilding(models.Model):
    _name = 'pappaya.building'
    _description = 'Pappaya Building'

    @api.one
    @api.depends('is_update')
    def _compute_update_building(self):
        is_update = self._context.get('update_building',False)
        if is_update:
            self.is_update = True
        else:
            self.is_update = False
        
    name = fields.Char('Name', size=40)
    branch_id = fields.Many2one('operating.unit', string="Branch")
    area_type = fields.Selection([('building_area', 'Building Area'), ('open_area', 'Open Area')], string='Area Type', default='building_area')
    building_type = fields.Selection([('rent', 'Rent'),('lease', 'Lease'),('own', 'Own')], 'Building Type',default='rent')
    area = fields.Char('Area',size=100)
    house_no = fields.Char('HNo',size=20)
    street_vill = fields.Char('Street-Vill',size=100)
    pin_code = fields.Char('Pin Code', size=6)
    # ~ mandal = fields.Char('Mandal')#Clarify
    mandal_id = fields.Many2one('pappaya.mandal.marketing', string='Mandal')
    # ~ district = fields.Char('District')#Clarify
    district_id = fields.Many2one('state.district', string='District')
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    country_id = fields.Many2one('res.country', string="Country", default=lambda self: self.env.user.company_id.country_id)
    building_total_area = fields.Float(string='Building Total Area(Sft)')
    common_area = fields.Float(string='Common Area(Sft)')
    cellar_area = fields.Float(string='Cellar Area(Sft)')
    no_of_blocks = fields.Integer(string='No Of Blocks',default=1)
    others_floors_area = fields.Float(string='Others Floors Area(Sft)')
    rent = fields.Float(string='Rent')
    rent_per_sft = fields.Float(string='Rent Per Sft')
    maintenance_amount = fields.Float(string='Maintenance Amount')
    lease_period = fields.Integer(string='Lease Period(Months)')
    rent_increase_percentage = fields.Float(string='Rent Increase Percentage')
    rent_increase_interval = fields.Float(string='Rent Increase Interval(Months)', default=12)
    eviction_notice_time = fields.Char(string='Eviction Notice Time(Months)',size=20)
    lease_commencement_date =  fields.Date(string='Lease Commencement Date')
    occupancy_date = fields.Date(string='Occupancy Date')
    municipal_tax_owner = fields.Float(string='Municipal Tax Owner(%)')
    municipal_tax_tenant = fields.Float(string='Municipal Tax Tenant(%)')
    rental_duration = fields.Selection([('bimonthly', 'BIMONTHLY'), ('halfyearly', 'HALFYEARLY'), ('monthly', 'MONTHLY'), ('quarterly', 'QUARTERLY'), ('yearly', 'YEARLY')],string='Rent Duration')
    tpa = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='TPA')
    is_electricity_commercial = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Is Electricity Commercial')
    is_commercial_building = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Is Commercial Building')
    aminities_cost = fields.Char('Aminities Cost',size=100)
    is_aminities_provided = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Is Aminities Provided')
    rent_increase_on = fields.Selection([('basic_rent', 'Basic Rent'), ('present_rent', 'Present Rent')], string='Rent Increase On')
    building_purpose =  fields.Many2many('building.purpose',string='Building Purpose')#Clarify
    lock_period = fields.Char(string='Lock Period(Months)',size=30)
    electricity_category = fields.Selection([('aaa', 'AAA'), ('bbb', 'BBB')], string='Electricity Category')
    student_capacity = fields.Integer(string='Student Capacity')
    student_occupied = fields.Integer(string='Student Occupied')
    rent_agrm_expiry_date =  fields.Date(string='Rent Agreement Expiry Date')
    state = fields.Selection([('draft', 'Draft'), ('zonal_approval', 'Zonal Approved'), ('dfe_approval', 'DFE Approved')], readonly=True, default='draft')
    is_main_building = fields.Boolean(string='Is Main Building?', default=False)
    main_building = fields.Many2one('pappaya.building',string='Main Building')
    sms_no1 = fields.Char('Sms No1', size=10)
    sms_no2 = fields.Char('Sms No2', size=10)
    sms_no3 = fields.Char('Sms No3', size=10)
    sms_no4 = fields.Char('Sms No4', size=10)
    active = fields.Boolean(default=True)
    is_update = fields.Boolean(compute=_compute_update_building)

    @api.constrains('sms_no1','sms_no2','sms_no3','sms_no4','pin_code')
    def validation_sms_no(self):
        if self.pin_code:
            match_pin_code = re.match('^[\d]*$', self.pin_code)
            if not match_pin_code or len(self.pin_code) < 6:
                raise ValidationError(_("Please enter a valid Pin Code"))
        if self.sms_no1:
            match_sms_no1 = re.match('^[\d]*$', self.sms_no1)
            if not match_sms_no1 or len(self.sms_no1) < 10:
                raise ValidationError(_("Please enter a valid 10 digit Sms No 1"))
        if self.sms_no2:
            match_sms_no2 = re.match('^[\d]*$', self.sms_no2)
            if not match_sms_no2 or len(self.sms_no2) < 10:
                raise ValidationError(_("Please enter a valid 10 digit Sms No 2"))
        if self.sms_no3:
            match_sms_no3 = re.match('^[\d]*$', self.sms_no3)
            if not match_sms_no3 or len(self.sms_no3) < 10:
                raise ValidationError(_("Please enter a valid 10 digit Sms No 3"))
        if self.sms_no4:
            match_sms_no4 = re.match('^[\d]*$', self.sms_no4)
            if not match_sms_no4 or len(self.sms_no4) < 10:
                raise ValidationError(_("Please enter a valid 10 digit Sms No 4"))

    @api.constrains('building_total_area','no_of_blocks','cellar_area','others_floors_area','common_area','rent','rent_per_sft','maintenance_amount','municipal_tax_owner','municipal_tax_tenant','student_capacity','student_occupied','rent_increase_percentage','rent_increase_interval','lease_period')
    def validation_numbers(self):
        if self.building_total_area < 0:
            raise ValidationError(_("Enter valid Building Total Area(Sft)"))
        if self.no_of_blocks < 0:
            raise ValidationError(_("Enter valid No Of Blocks"))
        if self.cellar_area < 0:
            raise ValidationError(_("Enter valid Cellar Area(Sft)"))
        if self.others_floors_area < 0:
            raise ValidationError(_("Enter valid Others Floors Area(Sft)"))
        if self.common_area < 0:
            raise ValidationError(_("Enter valid Common Area(Sft)"))
        if self.rent < 0:
            raise ValidationError(_("Enter valid Rent"))
        if self.rent_per_sft < 0:
            raise ValidationError(_("Enter valid Rent Per Sft"))
        if self.maintenance_amount < 0:
            raise ValidationError(_("Enter valid Maintenance Amount"))
        if self.municipal_tax_owner < 0:
            raise ValidationError(_("Enter valid Municipal Tax Owner(%)"))
        if self.municipal_tax_tenant < 0:
            raise ValidationError(_("Enter valid Municipal Tax Tenant(%)"))
        if self.student_capacity < 0:
            raise ValidationError(_("Enter valid Student Capacity"))
        if self.student_occupied < 0:
            raise ValidationError(_("Enter valid Student Occupied"))
        if self.rent_increase_interval < 0:
            raise ValidationError(_("Enter valid Rent Increase Interval(Months)"))
        if self.rent_increase_percentage < 0:
            raise ValidationError(_("Enter valid Rent Increase Percentage"))
        if self.lease_period < 0:
            raise ValidationError(_("Enter valid Lease Period(Months)"))
        
        
    @api.multi
    def act_zonal_approval(self):
        self.state = 'zonal_approval'

    @api.multi
    def act_dfe_approval(self):
        self.state = 'dfe_approval'

    @api.onchange('municipal_tax_owner')
    def _onchange_municipal_tax_owner(self):
        if self.municipal_tax_owner and self.municipal_tax_owner > 0:
            self.municipal_tax_tenant = 100 - self.municipal_tax_owner

    @api.onchange('municipal_tax_tenant')
    def _onchange_municipal_tax_tenant(self):
        if self.municipal_tax_tenant and self.municipal_tax_tenant > 0:
            self.municipal_tax_owner = 100 - self.municipal_tax_tenant

    @api.onchange('district_id')
    def _onchange_district(self):
        if self.district_id:
            districts = self.env['state.district'].search([('id','=',self.district_id.id)])
            mandals = self.env['pappaya.mandal.marketing'].search([('district_id','=',self.district_id.id)])
        else:
            districts = self.env['state.district'].search([])
            mandals = self.env['pappaya.mandal.marketing'].search([])
        return {'domain': {'mandal_id': [('id', 'in', mandals.ids)],'district_id': [('id', 'in', districts.ids)]}}

    @api.onchange('country_id')
    def _onchange_country_id(self):
        country_id = self.env.user.company_id.country_id
        states = self.env['res.country.state'].search([('country_id', '=', country_id.id)])
        districts = self.env['state.district'].search([('state_id', 'in', states.ids)])
        mandals = self.env['pappaya.mandal.marketing'].search([('district_id', 'in', districts.ids)])
        return {'domain': {'state_id': [('id', 'in', states.ids)],'district_id': [('id', 'in', districts.ids)],'mandal_id': [('id', 'in', mandals.ids)]}}

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id:
            self.country_id = self.state_id.country_id.id
            return {'domain': {'district_id': [('state_id', 'in', [self.state_id.id])]}}
        else:
            states = self.env['res.country.state'].search([('country_id','=',self.country_id.id)])
            return {'domain': {'district_id': [('state_id', 'in', states.ids)]}}


    @api.onchange('mandal_id')
    def _onchange_mandal(self):
        if self.mandal_id:
            self.district_id = self.mandal_id.district_id.id
            self.state_id = self.district_id.state_id.id
            self.country_id = self.state_id.country_id.id
        else:
            if self.district_id:
                mandals = self.env['pappaya.mandal.marketing'].search([('district_id','=',self.district_id.id)])
            else:
                mandals = self.env['pappaya.mandal.marketing'].search([])
            return {'domain': {'mandal_id': [('id', 'in', mandals.ids)]}}
        
    @api.onchange('rent_per_sft')
    def _onchange_rent_per_sft(self):
        if self.rent_per_sft > 0.0:
            self.rent = self.rent_per_sft * self.building_total_area
        else:
            self.rent = 0.0
            
    @api.onchange('rent')
    def _onchange_rent(self):
        if self.rent > 0.0:
            self.rent_per_sft = self.rent / self.building_total_area
        else:
            self.rent_per_sft = 0.0
            
    @api.onchange('student_occupied')
    def _onchange_student_occupied(self):
        if self.student_occupied > 0.0 and self.student_occupied > self.student_capacity:
            return {
                    'warning': {'title': _('Warning'), 'message': _('Student capacity is exceeding than Student Occupied'),},
                     }

    @api.onchange('building_type')
    def _onchange_building_type(self):
        if self.building_type == 'rent':
            self.lease_commencement_date = False
            self.lease_period = 0.0
        elif self.building_type == 'lease':
            self.rent = 0.0
            self.rent_per_sft = 0.0
            self.rent_increase_interval = 0.0
            self.rent_increase_percentage = 0.0
            self.rent_increase_on = ''
            self.rental_duration = ''
            self.rent_agrm_expiry_date = False
            self.lease_period = 12.0
        else:
            self.rent = 0.0
            self.rent_per_sft = 0.0
            self.rent_increase_interval = 0.0
            self.rent_increase_percentage = 0.0
            self.rent_increase_on = ''
            self.rental_duration = ''
            self.rent_agrm_expiry_date = False
            self.lease_period = 0.0
            self.lease_commencement_date = False
            
    @api.multi
    def toggle_active(self):
        for record in self:
            if record.active:
                blocks = self.env['pappaya.block'].search([('building_id','=',self.id),('active','=',True)])
                floors = self.env['pappaya.floor'].search([('building_id','=',self.id),('active','=',True)])
                rooms = self.env['pappaya.building.room'].search([('building_id','=',self.id),('active','=',True)])
                classes = self.env['pappaya.building.class'].search([('building_id','=',self.id),('active','=',True)])
                if blocks:
                    blocks.write({'active':False})
                if floors:
                    floors.write({'active':False})
                if rooms:
                    rooms.write({'active':False})
                if classes:
                    classes.write({'active':False})
                record.active = False
            else:
                blocks = self.env['pappaya.block'].search([('building_id','=',self.id),('active','=',False)])
                floors = self.env['pappaya.floor'].search([('building_id','=',self.id),('active','=',False)])
                rooms = self.env['pappaya.building.room'].search([('building_id','=',self.id),('active','=',False)])
                classes = self.env['pappaya.building.class'].search([('building_id','=',self.id),('active','=',False)])
                if blocks:
                    blocks.write({'active':True})
                if floors:
                    floors.write({'active':True})
                if rooms:
                    rooms.write({'active':True})
                if classes:
                    classes.write({'active':True})   
                record.active = True
                
    @api.multi
    def reset_to_draft(self):
        self.state = 'draft'

