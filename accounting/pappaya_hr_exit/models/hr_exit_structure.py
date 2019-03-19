# -*- coding:utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from odoo.addons import decimal_precision as dp


class HrExitStructure(models.Model):
    _name = 'hr.exit.structure'
    _description = 'Exit Structure'
    
    
    
    
    name = fields.Char(required=True,size=100)
    code = fields.Char(string='Reference', required=True,size=100)
    company_id = fields.Many2one('res.company', string='Company', required=True,
        copy=False, default=lambda self: self.env['res.company']._company_default_get())
    note = fields.Text(string='Description',size=300)
    #~ parent_id = fields.Many2one('hr.exit.structure', string='Parent', default=_get_parent)
    rule_ids = fields.Many2many('hr.salary.rule',  'exit_struct_id_rel','hr_exit_str','rule_id', string='Salary Rules')

# 
# class HrSalaryRule(models.Model):
#     _inherit='hr.salary.rule'
# 
#     exit_struct_id =fields.Many2one('hr.exit','Exit Structure')
