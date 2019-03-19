# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import re

class MetaDataMaster(models.Model):
    _name='meta.data.master'
    _description='Meta Data Master'


    name = fields.Selection([('organization','Organization'),('entity','Entity'),('segment','Segment'),
                             ('state','State'),('branch','Branch'),('category','Category'),('stream','Stream'),('employee','Employee')],string='Type')
    sequence = fields.Integer(size=4)
    length = fields.Integer('Length',size=6)
    description = fields.Text(string='Description', size=100)
    start_series = fields.Char('Start Series',size=20)
    increment = fields.Integer('Increment',size=4)
    last_sequence = fields.Boolean(string='Last Sequence')
    ir_sequence_id = fields.Many2one('ir.sequence',string='Sequence')
    
    model_name = fields.Char(string='Model',size=30)
    
    
    @api.onchange('name')
    def onchange_name(self):
        for record in self:
            if record.name == 'organization':
                record.model_name = 'pappaya.organization'
            elif record.name == 'entity':
                record.model_name = 'pappaya.entity'
            elif record.name == 'segment':
                record.model_name = 'pappaya.segment'
            elif record.name == 'state':
                record.model_name = 'pappaya.state'
            elif record.name == 'branch':
                record.model_name = 'pappaya.branch'
            elif record.name == 'category':
                record.model_name = 'pappaya.category'
            elif record.name == 'stream':
                record.model_name = 'pappaya.stream'
            elif record.name == 'employee':
                record.model_name = 'pappaya.hr.employee'
    
    @api.multi
    def ir_sequence_id_creation(self):
        for record in self:
            if not record.ir_sequence_id:
                sequence_id = record.ir_sequence_id.create({
                                                'name':record.name,
                                                'code':record.model_name,
                                                'padding':record.length,
                                                'number_increment':record.increment,
                                                'company_id':None
                                                })
                sequence_id.write({'number_next_actual':record.start_series})
                record.ir_sequence_id = sequence_id.id
            
    
    @api.model
    def create(self, vals):
        res = super(MetaDataMaster, self).create(vals)
        res.ir_sequence_id_creation()
        return res
    
    @api.multi
    def write(self, vals):
        if 'length' in vals.keys() and vals.get('length'):
            self.ir_sequence_id.write({'padding':vals.get('length')})
        if 'increment' in vals.keys() and vals.get('increment'):
            self.ir_sequence_id.write({'number_increment':vals.get('increment')})
        if 'start_series' in vals.keys() and vals.get('start_series'):
            self.ir_sequence_id.write({'number_next_actual':vals.get('start_series')})
        res = super(MetaDataMaster, self).write(vals)
        return res
        
    
    @api.constrains('last_sequence','name')
    def check_last_sequence(self):
        for record in self:
            if record.last_sequence:
                if len(self.search([('last_sequence', '=', record.last_sequence)])) > 1:
                    raise ValidationError("Last Sequence already exists.")
            
            if record.name:
                if len(self.search([('name', '=', record.name)])) > 1:
                    raise ValidationError("Type already exists.")

    @api.constrains('sequence')
    def check_sequence_negative(self):
        for record in self:
            if record.sequence and record.sequence < 1:
                raise ValidationError("Sequence should be greater than Zero")
