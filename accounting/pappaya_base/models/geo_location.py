# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import re

class address_import_template(models.Model):
    _name='address.import.template'
    _description='Address Import Template'
    
    name = fields.Char('Name')
    file = fields.Binary('File')
    file_name = fields.Char('File Name')
    
    @api.onchange('file','file_name')
    def update_record_name(self):
        if self.file_name:
            self.name = self.file_name

class PappayaCity(models.Model):
    _name='pappaya.city'
    _description='City'
    _order='name asc'
    
    record_id = fields.Integer('ID')
    name = fields.Char(required=1,size=20)
    state_id = fields.Many2one('res.country.state','State', domain=[('country_id.is_active','=',True)])
    district_id = fields.Many2one('state.district', string='District')

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaCity, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaCity, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name_lower = str(self.name.strip()).lower()
            name = self.env['res.company']._validate_name(name_lower)
            self.name = name

    @api.onchange('state_id')
    def onchange_state_id(self):
        if self.state_id:
            self.district_id = None

    @api.constrains('name','district_id', 'state_id')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name), ('state_id','=',self.state_id.id), ('district_id','=',self.district_id.id)]).ids) > 1:
            raise ValidationError("City already exists")
        
    @api.constrains('record_id')
    def validate_of_record_id(self):
        if self.record_id > 0 and len(self.sudo().search([('record_id', '=', self.record_id)]).ids) > 1:
            raise ValidationError("ID already exists.")
        
class marketingPopulation(models.Model):
    _name='marketing.population'
    _description='Population Master'
    
    year = fields.Selection([(year, str(year)) for year in range(1900, (datetime.now().year)+1 )], 'Year', required=True)
    population = fields.Integer('Population', required=True)
    is_active = fields.Boolean('Active')
    record_id = fields.Integer('ID')
    ward_id = fields.Many2one('pappaya.ward', 'Ward')
    mandal_id = fields.Many2one('pappaya.mandal.marketing', 'Mandal')
    
    @api.constrains('ward_id','year','mandal_id')
    def check_validate(self):
        if self.ward_id and self.year:
            if self.sudo().search_count([('ward_id','=',self.ward_id.id),('year','=',self.year)]) > 1:
                raise ValidationError("Year must be unique.")
        elif self.mandal_id and self.year:
            if self.sudo().search_count([('mandal_id','=',self.mandal_id.id),('year','=',self.year)]) > 1:
                raise ValidationError("Year must be unique.")
    
    @api.constrains('record_id')
    def validate_of_record_id(self):
        if self.record_id > 0 and len(self.sudo().search([('record_id', '=', self.record_id)]).ids) > 1:
            raise ValidationError("ID already exists.")
            
class PappayaWard(models.Model):
    _name='pappaya.ward'
    _description='Ward'
    _order='name asc'
        
    state_id = fields.Many2one('res.country.state','State', domain=[('country_id.is_active','=',True)])
    district_id = fields.Many2one('state.district', string='District')
    city_id = fields.Many2one('pappaya.city', string='City', required=True)
    name = fields.Char('Name', required=True)
    record_id = fields.Integer('ID')
    population_ids = fields.One2many('marketing.population', 'ward_id', 'Population')

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaWard, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaWard, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name','city_id')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name),('city_id','=',self.city_id.id)]).ids) > 1:
            raise ValidationError("Ward already exists")
        
    @api.constrains('record_id')
    def check_record_id(self):
        if self.record_id > 0 and len(self.sudo().search([('record_id', '=', self.record_id)]).ids) > 1:
            raise ValidationError("ID already exists.")

class PappayaArea(models.Model):
    _name='pappaya.area'
    _description='Area'
    _order='name asc'
    
    record_id = fields.Integer('ID')
    state_id = fields.Many2one('res.country.state','State', domain=[('country_id.is_active','=',True)])
    district_id = fields.Many2one('state.district', string='District')
    city_id = fields.Many2one('pappaya.city', string='City')    
    ward_id = fields.Many2one('pappaya.ward', string='Ward', required=True)
    name = fields.Char(required=1)

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaArea, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaArea, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name','ward_id')
    def check_name(self):
        if len(self.sudo().search([('name', '=', self.name),('ward_id','=',self.ward_id.id)]).ids) > 1:
            raise ValidationError("Area already exists.")
    
    @api.constrains('record_id')
    def check_record_id(self):
        if self.record_id > 0 and len(self.sudo().search([('record_id', '=', self.record_id)]).ids) > 1:
            raise ValidationError("ID already exists.")
#------------------------------------------------------------------------------------------------------------

class PappayaMandal(models.Model):
    _name='pappaya.mandal.marketing'
    _description='Mandal'
    _order='name asc'
    
    state_id = fields.Many2one('res.country.state','State', domain=[('country_id.is_active','=',True)])
    district_id = fields.Many2one('state.district', string='District', required=True)
    name = fields.Char(required=1)
    record_id = fields.Integer('ID')
    population_ids = fields.One2many('marketing.population', 'mandal_id', 'Population')
    description = fields.Text('Description' ,size=200)
    taluka_slno = fields.Char('Talulka Sl No.',size=50)
    disthead_slno = fields.Char('Dist Head Sl No.',size=50)
    status = fields.Char('Status',size=50)
    strength = fields.Char('Strength',size=50)
    population = fields.Char('Population',size=150)
    user_slno = fields.Char('User Sl No.',size=50)
    city_slno = fields.Char('City Sl No.',size=50)
    is_update = fields.Boolean('Is Update')

    
    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaMandal, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaMandal, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name','district_id')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name),('district_id','=',self.district_id.id)]).ids) > 1:
            raise ValidationError("Mandal already exists")
        
    @api.constrains('record_id')
    def check_record_id(self):
        if self.record_id > 0 and len(self.sudo().search([('record_id', '=', self.record_id)]).ids) > 1:
            raise ValidationError("ID already exists.")
        
class PappayaVillage(models.Model):
    _name='pappaya.village'
    _description='Village'
    _order='name asc'
    
    state_id = fields.Many2one('res.country.state','State', domain=[('country_id.is_active','=',True)])
    district_id = fields.Many2one('state.district', string='District')
    mandal_id = fields.Many2one('pappaya.mandal.marketing', string='Mandal', required=True)
    name = fields.Char('Name',required=1,size=100)
    record_id = fields.Integer('ID')
    description = fields.Text(string='Description',size=200)
    user_slno = fields.Char('User Sl No.',size=50)
    is_update = fields.Boolean('Is Update')

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaVillage, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaVillage, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name','mandal_id')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name),('mandal_id','=',self.mandal_id.id)]).ids) > 1:
            raise ValidationError("Village already exists")
        
    @api.constrains('record_id')
    def check_record_id(self):
        if self.record_id > 0 and len(self.sudo().search([('record_id', '=', self.record_id)]).ids) > 1:
            raise ValidationError("ID already exists.")

class PappayaLeadSchool(models.Model):
    _name='pappaya.lead.school'
    _description = 'Lead School'
    _order='name asc'
    
    record_id = fields.Integer('ID')
    name = fields.Char('School Name',size=100)
    state_id = fields.Many2one('res.country.state', 'State', required=True)
    district_id = fields.Many2one('state.district', 'District', required=True)
    mandal_id = fields.Many2one('pappaya.mandal.marketing', 'Mandal', required=True)

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaLeadSchool, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name':self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaLeadSchool, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.onchange('state_id')
    def onchange_state_id(self):
        domain = {}
        domain['state_id'] = [('id','in',[])]
        domain['school_state_id'] = [('id','in',[])]
        state_ids = self.env['res.country.state'].search([('country_id','in',self.env['res.country'].sudo().search([('is_active','=',True)]).ids)])
        if state_ids:
            domain['state_id'] = [('id','in',state_ids.ids)]
        return {'domain':domain}
    
#     @api.constrains('state_id','district_id','mandal_id')
#     def _check_duplicate(self):
#         if self.sudo().search_count([('name','=',self.name),('state_id','=',self.state_id.id),
#                                ('district_id','=',self.district_id.id),('mandal_id','=',self.mandal_id.id)]) > 1:
#             raise ValidationError("Record already exists with given data.")
# 
#     @api.constrains('name')
#     def validate_of_name(self):
#         if len(self.sudo().search([('name', '=', self.name)]).ids) > 1:
#             raise ValidationError("Lead School name already exists.")
        
    @api.constrains('record_id')
    def check_record_id(self):
        if self.record_id > 0 and len(self.sudo().search([('record_id', '=', self.record_id)]).ids) > 1:
            raise ValidationError("ID already exists.")
        
class ResCompanyInherit(models.Model):
    _inherit = "res.company"
    _order = "name asc"
    
    pappaya_mandal_id = fields.Many2one('pappaya.mandal.marketing', string="Mandal")
    
    
    
class PappayaRegion(models.Model):
    _name='pappaya.region'
    _description='Region'
    _order='name asc'
    
    name = fields.Char(required=1,size=100)
    state_id = fields.Many2many('res.country.state','res_country_state_region_rel','state_id','region_id',string='State',domain=[('country_id.is_active','=',True)])

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaRegion, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaRegion, self).write(vals)
    
    @api.onchange('state_id')
    def onchange_state_id(self):
        if self.name and self.state_id:
            existing_regions = self.search([('name','=',self.name),('state_id','in',self.state_id.ids)])
            if existing_regions:
                raise ValidationError("You are not allowed to Duplicate")

    @api.constrains('name')
    def check_name(self):
        for record in self:
            if record.name:
                region = record.env['pappaya.region'].search([('name','=',record.name)])
                if len(region) > 1:
                    raise ValidationError("Region already exists")

