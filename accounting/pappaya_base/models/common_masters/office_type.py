# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class PappayaOfficeType(models.Model):
    _name = 'pappaya.office.type'
    #_rec_name = 'display_name'

    entity_id = fields.Many2one('operating.unit', 'Entity')
    name = fields.Char('Office Type Name', size=40)
    code = fields.Char('Office Type Code', size=5)
    record_id = fields.Integer('ID')
    description = fields.Text('Description', size=100)
    emp_no_ref = fields.Char('EMP REF', size=50)
    is_budget_applied = fields.Boolean('Is Budget Applied?')
    is_student_details_applied = fields.Boolean('Is Student Details Applied?')
    type = fields.Selection(
        [('school', 'School'), ('college', 'College'), ('coaching', 'Coaching Center'), ('others', 'Others')],
        string='Type')
    #display_name = fields.Char(compute="cal_display_name",store=True)

    @api.constrains('code')
    def check_code(self):
        if not re.match("^[a-zA-Z0-9-]*$", self.code):
            raise ValidationError('Please enter valid Office Type Code.')

    @api.onchange('code')
    def onchange_code(self):
        if self.code:
            self.check_code()

    @api.constrains('name', 'record_id','code','entity_id')
    def check_name(self):
        if len(self.search([('name', '=', self.name), ('code', '=', self.code), ('entity_id', '=', self.entity_id.id)])) > 1:
            raise ValidationError("Record already exists for given name, code and entity.")
        elif len(self.search([('name', '=', self.name),('entity_id', '=', self.entity_id.id)])) > 1:
            raise ValidationError("Record already exists for given name and entity.")
        elif len(self.search([('code', '=', self.code),('entity_id', '=', self.entity_id.id)])) > 1:
            raise ValidationError("Record already exists for given code and entity.")

        if self.record_id:
            if self.record_id > 0 and self.sudo().search_count([('record_id', '=', self.record_id)]) > 1:
                raise ValidationError("ID already exists")

    
    
#     @api.depends('name', 'entity_id','display_name')
#     def cal_display_name(self):
#         for office in self:
#             name = ''
#             if office and office.sudo().entity_id:
#                 name += office.name
#             if self.env.context.get('special_display_name', False):
#                 if office.sudo().entity_id.code:
#                     name += ' - ' + office.sudo().entity_id.code
#             office.display_name =  name
 
 
 
    @api.multi
    @api.depends('name','display_name', 'entity_id')
    def name_get(self):
        result = []
        for office in self:
            
            name = ''
            if office and office.sudo().entity_id:
                name += office.name
            if self.env.context.get('special_display_name', False):
                if office.sudo().entity_id.code:
                    name += ' - ' + office.sudo().entity_id.code
                    
            if self.env.context.get('special_display_name', False):
                try:
                    result.append((office.id, name))
                except:
                    result.append((office.id, office.name))
            else:
                result.append((office.id, office.name))
        return result  
