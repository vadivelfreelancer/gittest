# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class travelling_expenditure_proposal(models.Model):
    _name='travelling.expenditure.proposal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description='Address and travelling expenditure proposal'
    
    @api.multi
    @api.depends('travelling_expenditure_proposal_line.amount')
    def _get_total_amount(self):
        for record in self:
            total_amount = 0.0
            for line in record.travelling_expenditure_proposal_line:
                total_amount += line.amount
            record.total_amount = total_amount    
    
    name = fields.Char('Name', default='New')
    proposal_date = fields.Date('Date')
    proposal_type = fields.Selection([('address_collection','Address Collection'),('travelling_expenditure', 'Travelling Expenditure')], 
                                    'Proposal Type', default='address_collection')
    is_outside_employee = fields.Boolean('Is outside employee', default=False)
    branch_id = fields.Many2one('res.company', 'Branch')
    employee_id = fields.Many2one('hr.employee',  'Employee')
    academic_year_id = fields.Many2one('academic.year', 'Academic year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    state_id = fields.Many2one('res.country.state', 'State')
    district_id = fields.Many2one('state.district', 'District')
    state = fields.Selection([('draft','Draft'),('proposed','Proposed'),('approved','Approved'),('rejected','Rejected'),('cancelled','Cancelled')],
                             'State', default='draft')
    total_amount = fields.Float(compute='_get_total_amount',string='Total Amount')
    description=fields.Text('Description',size=300)
    travelling_expenditure_proposal_line = fields.One2many('travelling.expenditure.proposal.line', 'travelling_expenditure_proposal_id', 'Travelling expenditure proposal lines')
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('travelling.expenditure.proposal') or '/'
        return super(travelling_expenditure_proposal, self).create(vals)
    
    @api.onchange('proposal_type')
    def onchange_proposal_type(self):
        self.branch_id = False
        self.academic_year_id = False
        self.employee_id = False
        self.state_id = False
        self.district_id = False
        self.travelling_expenditure_proposal_line = False
        
    @api.onchange('district_id')
    def onchange_district_id(self):
        if self.district_id:
            travelling_expenditure_proposal_line = []
            for division in self.env['pappaya.division'].search([('state_district_id','=',self.district_id.id)]):
                travelling_expenditure_proposal_line.append((0,0,{
                    'division_id': division.id,
                    'amount' : 0.0
                    }))
            if travelling_expenditure_proposal_line:
                self.travelling_expenditure_proposal_line = travelling_expenditure_proposal_line
                
    @api.multi
    def action_proposal(self):
        for record in self:
            record.state = 'proposed'
            record.travelling_expenditure_proposal_line.write({'state':'proposed'})
    @api.multi
    def action_approval(self):
        for record in self:
            record.state = 'approved'
            record.travelling_expenditure_proposal_line.write({'state':'approved'})
    @api.multi
    def action_reject(self):
        for record in self:
            record.state = 'rejected'
            record.travelling_expenditure_proposal_line.write({'state':'rejected'})
    @api.multi
    def action_cancel(self):
        for record in self:
            record.state = 'cancelled' 
            record.travelling_expenditure_proposal_line.write({'state':'cancelled'})
    @api.multi
    def action_reset(self):
        for record in self:
            record.state = 'draft'
            record.travelling_expenditure_proposal_line.write({'state':'draft'})                 
               
class travelling_expenditure_proposal_line(models.Model):
    _name='travelling.expenditure.proposal.line'
    
    travelling_expenditure_proposal_id = fields.Many2one('travelling.expenditure.proposal', 'Travelling expenditure proposal')
    division_id = fields.Many2one('pappaya.division', 'Division')
    amount = fields.Float('Amount')
    state = fields.Selection([('draft','Draft'),('proposed','Proposed'),('approved','Approved'),('rejected','Rejected'),('cancelled','Cancelled')],
                             'State', default='draft')
    