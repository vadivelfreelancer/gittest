# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class EmployeeDynamicStage(models.Model):
    _name = 'employee.dynamic.stage'
    _rec_name = 'menu'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    
    
    menu = fields.Selection([('employees', 'Employees'), ('contracts', 'Contracts')],track_visibility='onchange')
    line_ids = fields.One2many('employee.dynamic.stage.line','dynamic_stage_id',string='Employee Dynamic Stage Line',track_visibility='onchange')
    
    
    @api.constrains('menu')
    def check_name(self):
        if len(self.search([('menu', '=', self.menu)])) > 1:
            raise ValidationError("Menu already exists")
        
        
#     @api.constrains('line_ids')
#     def final_stage_constrains(self):
#         for record in self:
#             if len(record.line_ids.search([('final_stage', '=', True)])) > 1:
#                 raise ValidationError("Final stage already exists")
            
        
class EmployeeDynamicStageLine(models.Model):
    _name = 'employee.dynamic.stage.line'
    _rec_name = 'stage_name'
    _order = "sequence_no"
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    
    dynamic_stage_id = fields.Many2one('employee.dynamic.stage',string='Stage')
    menu = fields.Selection(string='Menu',related='dynamic_stage_id.menu')
    stage_name = fields.Char(String='Stage Name',size=128,track_visibility='onchange')
    sequence_no = fields.Integer(String='Sequence',size=2,track_visibility='onchange')
    groups_id = fields.Many2many('res.groups', 'employee_dynamic_workflow_groups_rel','employee_dynamic_id','group_id', String='Groups')
    action_type = fields.Selection([('approve', 'Approve'), ('cancel', 'Cancel')],default='approve',string='Action')
    active_id = fields.Boolean(String='Active',default=False)
    
                        
    
    @api.constrains('stage_name','sequence_no')
    def check_name(self):
        if len(self.search([('stage_name', '=', self.stage_name)])) > 1:
            raise ValidationError("Stage already exists")
        if len(self.search([('sequence_no', '=', self.sequence_no)])) > 1:
            raise ValidationError("Sequence already exists")
        if self.sequence_no == 0:
            raise ValidationError("Sequence Invalid")
        

# Groups Rec rename

        
class ResGroups(models.Model):
    _inherit = 'res.groups'
    _rec_name = 'name'

