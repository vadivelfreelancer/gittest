# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PappayaiMulPayAuthorize(models.Model):
    _name = 'pappaya.imulpay.authorize'

    @api.one
    @api.constrains('entity_id', 'branch_ids')
    def check_branch_ids(self):
        if len(self.search(
                [('state', '=', 'draft'), ('refund_type', '=', self.refund_type), ('entity_id', '=', self.entity_id.id),
                 ('branch_ids', 'in', self.branch_ids.ids)])) > 1:
            raise ValidationError('The iMulPay Request already exists for current branch..!')

    academic_year_id = fields.Many2one('academic.year', "Academic Year",
                                       default=lambda self: self.env['academic.year'].search(
                                           [('is_active', '=', True)]))
    name = fields.Char('Ref. No.', size=30, copy=False, default=lambda self: _('New'))
    account_id = fields.Many2one('account.account', string='A/C No.')
    entity_id = fields.Many2one('operating.unit', string='Entity')
    branch_ids = fields.Many2many('operating.unit', string='Branch')
    transaction_date = fields.Date(string='Transaction Date')
    state = fields.Selection([('draft', 'Draft'), ('request', 'Requested'), ('authorize', 'Authorized')],
                             string='Status', default='draft')
    refund_type = fields.Selection(
        [('reservation', 'Reservation'), ('admission', 'Admission'), ('internal_transfer', 'Internal Transfer'),
         ('external_transfer', 'External Transfer'), ('transport', 'Transport'),
         ('other_collection', 'Other Collection'), ('material', 'Material')], string='Refund Type')

    authorize_line_ids = fields.One2many('pappaya.fees.refund', 'authorize_id', string='Fees Refund')
    is_update = fields.Boolean(string='Is Update?', default=False)
    total_amount = fields.Float('Total Amount', compute='compute_total_amount')

    @api.multi
    @api.depends('authorize_line_ids.refund_amount')
    def compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum([i.refund_amount for i in rec.authorize_line_ids])

    @api.onchange('entity_id')
    def onchange_entity(self):
        self.branch_ids = False

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('imulpay.authorize') or _('New')
        return super(PappayaiMulPayAuthorize, self).create(vals)

    @api.multi
    def get_refund_students(self):
        fees_refund = self.env['pappaya.fees.refund'].search(
            [('branch_id', 'in', self.branch_ids.ids), ('refund_type', '=', self.refund_type),
             ('is_authorize', '=', False), ('authorize_id', '=', False), ('state', '=', 'approve')])
        if fees_refund:
            for record in fees_refund:
                record.write({'authorize_id': self.id})
        else:
            raise ValidationError('No Record Found..!')
        self.is_update = True

    @api.multi
    def action_request(self):
        self.state = 'request'

    @api.multi
    def action_approve(self):
        for line in self.authorize_line_ids:
            line.update_refund()
        self.state = 'authorize'
