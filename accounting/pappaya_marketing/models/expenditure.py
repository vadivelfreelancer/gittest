# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class expenditure_proposal(models.Model):
    _name='expenditure.proposal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description='Expenditure Proposal'
    
    name = fields.Char(string='Number', default='New',size=50)
    proposal_date = fields.Date('Date')
    apex_id = fields.Many2one('pappaya.course.provider', 'Apex') 
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    division_id = fields.Many2one('pappaya.division', 'Division')
    staff_type_id = fields.Many2one('staff.type', 'Staff Type')
    program_type_id = fields.Many2one('program.type', 'Program Type')
    total_amount = fields.Float(compute='_get_total_amount', string='Total Amount')
    state = fields.Selection([('draft', 'Draft'), ('proposed', 'Proposed'), ('approved', 'Approved'), ('rejected','Rejected'),('cancel','Cancel'),('archived','Archived')], string='State',default='draft')
    expenditure_proposal_line = fields.One2many('expenditure.proposal.line', 'expenditure_proposal_id', 'Staffs')
    description = fields.Text('Description',size=300)
    state_id = fields.Many2one('res.country.state', 'State')
    district_id = fields.Many2one('state.district', 'District')
    dgm_dean = fields.Selection([('dgm','DGM'),('dean','DEAN')], 'DGM / DEAN')
    cluster_id = fields.Many2one('pappaya.cluster', 'Cluster')
    total_approved_amount = fields.Float(string='Total Approved Amount', compute='_get_total_approved_amount')
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('expenditure.proposal') or '/'
        return super(expenditure_proposal, self).create(vals)
        
    @api.multi
    @api.depends('expenditure_proposal_line.amount')
    def _get_total_amount(self):
        for record in self:
            amount_total = 0.0
            for line in record.expenditure_proposal_line:
                amount_total += line.amount
            record.total_amount = amount_total
            
    @api.multi
    @api.depends('expenditure_proposal_line.approved_amount')
    def _get_total_approved_amount(self):
        for record in self:
            total_approved_amount = 0.0
            for line in record.expenditure_proposal_line:
                total_approved_amount += line.approved_amount
            record.total_approved_amount = total_approved_amount  
            
    @api.multi
    def action_proposal(self):
        for record in self:
            record.state = 'proposed'     
            record.expenditure_proposal_line.write({'state':'proposed'})   
    @api.multi
    def action_approval(self):
        for record in self:
            record.state = 'approved'
            record.expenditure_proposal_line.write({'state':'approved'})
    @api.multi
    def action_reject(self):
        for record in self:
            record.state='rejected'
            record.expenditure_proposal_line.write({'state':'rejected'})
    @api.multi
    def action_reset(self):
        for record in self:
            record.state='draft'
            record.expenditure_proposal_line.write({'state':'draft'})
    @api.multi
    def action_cancel(self):
        for record in self:
            record.state='cancel'
            record.expenditure_proposal_line.write({'state':'cancel'})
    
class expenditure_proposal_line(models.Model):
    _name='expenditure.proposal.line'
    
    expenditure_proposal_id = fields.Many2one('expenditure.proposal', 'Expenditure Proposal')
    staff_id = fields.Many2one('hr.employee', 'Staff Name')
    staff_type_id = fields.Many2one('staff.type', 'Staff Type')
    bank_id = fields.Many2one(comodel_name='res.bank', string='Bank', related='staff_id.bank_account_id.bank_id')
    staff_rtgs = fields.Char('RTGS',size=50)
    account_number = fields.Char(related='staff_id.bank_account_id.acc_number')
    state = fields.Selection([('draft', 'Draft'), ('proposed', 'Proposed'), ('approved', 'Approved'), ('rejected','Rejected'),('cancel','Cancel'),('archived','Archived')], string='State',default='draft')
    amount = fields.Float('Proposal amount')
    ref_no = fields.Char('Ref No',size=50)
    approved_amount = fields.Float('Approved Amount')
    
    
    @api.model
    def default_get(self, fields):
        res = super(expenditure_proposal_line, self).default_get(fields)
        if 'staff_type_id' in self.env.context and self.env.context['staff_type_id']:
            res['staff_type_id'] = self.env.context['staff_type_id']
        return res
    
    @api.onchange('staff_type_id')
    def onchange_staff_type_id(self):
        domain = {}
        domain['staff_id'] = [('id','in',[])]
        if self.staff_type_id:
            staff_ids = self.env['hr.employee'].search([('staff_type_id','=',self.staff_type_id.id)]).ids
        else:
            staff_ids = self.env['hr.employee'].search([]).ids
        if staff_ids:
            domain['staff_id'] = [('id','in',staff_ids)]
        return {'domain':domain}
            
    