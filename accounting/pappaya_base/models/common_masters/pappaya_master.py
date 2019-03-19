# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PappayaMaster(models.Model):
    _name = 'pappaya.master'
    _description = 'Pappaya Master Table.'
    
    def get_master_type(self):
        master_type = self._context.get('master_type')
        individual_master_type = self._context.get('individual_master_type')
        if master_type == 'module_master':
            return [('concession','Concession'),('deduction','Deduction'),
                    ('previous_course','Previous Course'),
                    ('center','Center'),('unitic','Unit IC'),('bank_machine_type', 'Bank Machine Type'),
                    ('card_type','Card Type'),('address_type','Address Type'),('transaction_type','Transaction Type'),
                    ('transport_type', 'Transport Type'),('status','Status'),('sponsor_type','Sponsor Type')]

        elif master_type == 'global_master':
            return [('caste','Caste'),('religion','Religion'),('community','Community'),('blood_group','Blood Group'),
                    ('medium','Medium'),('occupation','Occupation'),('board_type','Board Type')]

        elif individual_master_type == 'caste':
            return [('caste','Caste')]
        elif individual_master_type == 'religion':
            return [('religion','Religion')]
        elif individual_master_type == 'community':
            return [('community','Community')]
        elif individual_master_type == 'blood_group':
            return [('blood_group','Blood Group')]
        elif individual_master_type == 'medium':
            return [('medium','Medium')]
        elif individual_master_type == 'occupation':
            return [('occupation','Occupation')]
        elif individual_master_type == 'board_type':
            return [('board_type','Board Type')]

        elif individual_master_type == 'concession':
            return [('concession', 'Concession')]
        elif individual_master_type == 'deduction':
            return [('deduction', 'Deduction')]
        elif individual_master_type == 'previous_course':
            return [('previous_course', 'Previous Course')]
        elif individual_master_type == 'center':
            return [('center', 'Center')]
        elif individual_master_type == 'unitic':
            return [('unitic','Unit IC')]
        elif individual_master_type == 'card_type':
            return [('card_type','Card Type')]
        elif individual_master_type == 'address_type':
            return [('address_type','Address Type')]
        elif individual_master_type == 'transport_type':
            return [('transport_type','Transport Type')]
        elif individual_master_type == 'transaction_type':
            return [('transaction_type','Transaction Type')]
        elif individual_master_type == 'status':
            return [('status','Status')]
        elif individual_master_type == 'sponsor_type':
            return [('sponsor_type','Sponsor Type')]
        elif individual_master_type == 'bank_machine_type':
            return [('bank_machine_type','Bank Machine Type')]
        else:
            return []


    @api.constrains('name', 'type')
    def _check_unique_name(self):
        if self.name and self.type:
            if len(self.search([('name', '=', self.name), ('type', '=', self.type)])) > 1:
                raise ValidationError("Name already exists for the current Type")

    master_type = fields.Selection([('module_master','Module Master'),('global_master','Global Master'),('others','Others')], 'Master Type', default=lambda self: self._context.get('master_type'))
    type = fields.Selection(get_master_type, 'Type', default=lambda self: self._context.get('individual_master_type'))
    name = fields.Char(string='Name', size=40)
    code = fields.Char(size=10, string='Code')
    description = fields.Text(string='Description', size=100)
    is_active = fields.Boolean(string='Is Active?', default=True)
    school_id = fields.Many2one('operating.unit', 'Branch', default=lambda self: self.env.user.default_operating_unit_id)
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
