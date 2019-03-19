# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PappayaConcessionFees(models.Model):
    _name = 'pappaya.concession.fees'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    school_id = fields.Many2one('operating.unit', string='Branch')
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]),track_visibility="onchange")
    status = fields.Selection([('draft', 'Draft'), ('request', 'Requested'), ('reject', 'Rejected'),
                               ('accept', 'Accepted')], string='Status', default='draft', track_visibility="onchange")
    date = fields.Date(string='Date', default=lambda self: fields.Date.today())
    fees_head_id = fields.Many2one('pappaya.fees.head', string='Fee Type')
    amount = fields.Float(string='Concession Amount')
    concession_line_ids = fields.One2many('pappaya.concession.fees.line', 'concession_id', string='Concession')
    user_id = fields.Many2one('res.users', string='Current User', default=lambda self: self.env.user,track_visibility="onchange")
    is_update = fields.Boolean(string='Is Update?', default=False)

    @api.constrains('admission_id')
    def check_record(self):
        if len(self.search([('admission_id', '=', self.admission_id.id), ('status', 'in', ['draft', 'request']),
                            ('school_id', '=', self.school_id.id)])) > 1:
            raise ValidationError('Concession already exists')

    @api.multi
    def action_request(self):
        for line in self.concession_line_ids:
            if not line.concession_amount > 0.0:
                raise ValidationError('Concession amount/percentage should be greater than 0')
        self.write({'status': 'request'})

    @api.multi
    def action_reset(self):
        self.write({'status': 'draft'})

    @api.multi
    def action_reject(self):
        self.write({'status': 'reject'})

    '''
    @api.multi
    def action_accept(self):
        for rec in self.concession_line_ids:
            fee_obj = self.env['student.fees.collection'].search([('enquiry_id', '=', self.admission_id.id),('name', '=', rec.fees_head_id.id),('admission_number','=',self.admission_id.res_no)])
            fee_obj.write({'concession_applied': True, 'concession_amount': rec.concession_amount if rec.concession_type == 'amount' else rec.fee_concession_percent})
            ledger_obj = self.env['pappaya.fees.ledger'].search([('enquiry_id', '=', self.admission_id.id),('admission_number', '=', self.admission_id.res_no)])
            for line in ledger_obj:
                ledger_line_obj = self.env['pappaya.fees.ledger.line'].search([('fees_ledger_id', '=', line.id),('name', '=', rec.fees_head_id.name)])
                ledger_line_obj.write({'concession_amount': rec.concession_amount if rec.concession_type == 'amount' else rec.fee_concession_percent})
        self.write({'status': 'accept'})
    '''

    @api.multi
    def action_accept(self):
        for line in self.concession_line_ids:
            fee_obj = self.env['student.fees.collection'].search(
                [('enquiry_id', '=', self.admission_id.id), ('name.is_course_fee', '!=', True),
                 ('name.is_course_fee_component', '=', True), ('admission_number', '=', self.admission_id.res_no),
                 ('less_sequence', '!=', 0), ('due_amount', '!=', 0.0), ('term_state', 'in', ['due', 'processing'])],
                order='less_sequence asc')

            course_fee_obj = self.env['student.fees.collection'].search(
                [('enquiry_id', '=', self.admission_id.id), ('admission_number', '=', self.admission_id.res_no),
                 ('name.is_course_fee_component', '=', True),  ('name.is_course_fee', '=', True)], limit=1)

            concession_amount = line.concession_amount if line.concession_type == 'amount' else line.fee_concession_percent

            # Update Concession Amount for Course Fee Head #
            course_fee_obj.write({'concession_amount': course_fee_obj.concession_amount + concession_amount if not self.admission_id.sponsor_type == 'yes' else course_fee_obj.concession_amount})
            course_ledger_line_obj = self.env['pappaya.fees.ledger.line'].search(
                [('fees_ledger_id.enquiry_id', '=', self.admission_id.id), ('fee_line_id', '=', course_fee_obj.id),
                 ('name', '=', course_fee_obj.name.name)])
            course_ledger_line_obj.write({'concession_amount': course_ledger_line_obj.concession_amount + concession_amount if not self.admission_id.sponsor_type == 'yes' else course_fee_obj.concession_amount})

            # Sponsor Concession
            if self.admission_id and self.admission_id.sponsor_type == 'yes' and self.admission_id.sponsor_value == 'partial':
                sponsor_fee_obj = self.env['student.fees.collection'].search([('enquiry_id', '=', self.admission_id.id), ('admission_number', '=', self.admission_id.res_no),('name.is_course_fee_component', '=', False)])
                for sponsor in sponsor_fee_obj:
                    sponsor.write({'concession_amount': sponsor.gst_total})
                    sponsor_ledger_line_obj = self.env['pappaya.fees.ledger.line'].search([('fees_ledger_id.enquiry_id', '=', self.admission_id.id),('fee_line_id', '=', course_fee_obj.id),('name', '=', sponsor.name.name)])
                    sponsor_ledger_line_obj.write({'concession_amount': course_ledger_line_obj.concession_amount})

            for i in fee_obj:
                ledger_line_obj = self.env['pappaya.fees.ledger.line'].search(
                    [('fees_ledger_id.enquiry_id', '=', self.admission_id.id), ('fee_line_id', '=', i.id),
                     ('name', '=', i.name.name)])
                if not concession_amount <= 0.0 and i.due_amount > concession_amount:
                    i.write({'concession_amount': i.concession_amount + concession_amount})
                    ledger_line_obj.write({'concession_amount': ledger_line_obj.concession_amount + concession_amount})
                    concession_amount = 0.0
                elif concession_amount > 0.0 and i.due_amount <= concession_amount:
                    i.write({'concession_amount':  i.concession_amount + i.due_amount,
                             'term_state': 'paid' if i.term_state != 'processing' else i.term_state})
                    ledger_line_obj.write({'concession_amount': ledger_line_obj.concession_amount + i.due_amount})
                    concession_amount -= i.due_amount
        self.write({'status': 'accept'})

    @api.multi
    def get_concession(self):
        if self.admission_id:
            if self.admission_id.cancel:
                raise ValidationError('Sorry, The admission is cancelled..!')
            fee_obj = self.env['pappaya.fees.collection'].search(
                [('school_id', '=', self.school_id.id), ('enquiry_id', '=', self.admission_id.id)])
            for fee in fee_obj:
                line_ids = []
                for fee_line in fee.fees_collection_line:
                    if fee_line.term_state != 'paid' and fee_line.name.is_course_fee and fee_line.name.is_course_fee_component:
                        line_ids.append((0, 0, {
                            'concession_id': self.id,
                            'fees_head_id': fee_line.name.id,
                            'fee_amount': fee_line.gst_total,
                            'fee_cgst': fee_line.cgst,
                            'fee_sgst': fee_line.sgst,
                            'fee_total': fee_line.amount,
                            'fee_due_amount': fee_line.due_amount,
                        }))
                    if fee_line.term_state != 'paid' and fee.enquiry_id.sponsor_type == 'yes' and not fee_line.name.is_course_fee and not fee_line.name.is_course_fee_component:
                        line_ids.append((0, 0, {
                            'concession_id': self.id,
                            'fees_head_id': fee_line.name.id,
                            'fee_amount': fee_line.gst_total,
                            'fee_cgst': fee_line.cgst,
                            'fee_sgst': fee_line.sgst,
                            'fee_total': fee_line.amount,
                            'fee_due_amount': fee_line.due_amount,
                        }))
                self.concession_line_ids = line_ids
                if len(self.concession_line_ids) == 0:
                    raise ValidationError('No records for the concession')
                self.is_update = True

    
    @api.one
    def copy(self, default=None):
        raise ValidationError('You are not allowed to Duplicate')

    @api.multi
    def unlink(self):
        raise ValidationError('Sorry,You are not authorized to delete record')


class PappayaConcessionFeesLine(models.Model):
    _name = 'pappaya.concession.fees.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    concession_id = fields.Many2one('pappaya.concession.fees', string='Concession')
    fees_head_id = fields.Many2one('pappaya.fees.head', string='Fee Type')
    fee_amount = fields.Float(string='Amount')
    fee_cgst = fields.Float(string='CGST')
    fee_sgst = fields.Float(string='SGST')
    fee_total = fields.Float(string='Total')
    fee_due_amount = fields.Float(string='Due Amount')
    concession_type = fields.Selection([('amount', 'Amount'), ('percentage', 'Percentage')], string='Concession Type',track_visibility="onchange")
    concession_amount = fields.Float(string='Concession Amount/Percentage',track_visibility="onchange")
    concession_total = fields.Float(string='Balance Amount', compute='get_concession_amount', store=True)
    fee_concession_percent = fields.Float(string='Concession Percent', compute='get_concession_amount', store=True)
    status = fields.Selection([('draft', 'Draft'), ('request', 'Requested'), ('reject','Rejected'),
                               ('accept', 'Accepted')], string='Status',related='concession_id.status')

    @api.multi
    def check_concession_fees_due(self):
        concession_amount = 0.0
        for rec in self:
            concession_amount = rec.concession_amount if rec.concession_type == 'amount' else rec.fee_concession_percent
            if rec.concession_type == 'percentage' and rec.concession_amount > 100:
                raise ValidationError('Concession percentage should not exceeds 100%')
            elif rec.concession_type and rec.concession_amount < 0:
                raise ValidationError('Concession amount/percentage should not be negative')
            if rec.concession_amount > rec.fee_due_amount:
                raise ValidationError('Concession Amount should be less than due amount')

        fee_obj = self.env['pappaya.fees.collection'].search(
            [('school_id', '=', self.concession_id.school_id.id), ('enquiry_id', '=', self.concession_id.admission_id.id)])

        for fee in fee_obj:
            due_amount = sum([fee_line.due_amount for fee_line in fee.fees_collection_line if fee_line.term_state != 'paid'
                              and not fee_line.name.is_course_fee and fee_line.name.is_course_fee_component])
            if due_amount < concession_amount:
                raise ValidationError('Sorry, You are entering amount more than Fee Due Amount..!')

    @api.depends('concession_amount','concession_type', 'fee_due_amount', 'fee_total')
    def get_concession_amount(self):
        for rec in self:
            if rec.concession_amount and rec.concession_type == 'amount' and rec.fee_due_amount == 0:
                rec.concession_total = (rec.fee_total - rec.concession_amount)
            if rec.concession_amount and rec.concession_type == 'amount' and rec.fee_due_amount != 0:
                rec.concession_total = (rec.fee_due_amount - rec.concession_amount)
            if rec.concession_amount and rec.concession_type == 'percentage' and rec.fee_due_amount == 0:
                rec.concession_total = rec.fee_total - ((rec.fee_total * rec.concession_amount) / 100)
                rec.fee_concession_percent = ((rec.fee_total * rec.concession_amount) / 100 ) or 0.0
            if rec.concession_amount and rec.concession_type == 'percentage' and rec.fee_due_amount != 0:
                rec.concession_total = rec.fee_due_amount - ((rec.fee_due_amount * rec.concession_amount) / 100)
                rec.fee_concession_percent = ((rec.fee_due_amount * rec.concession_amount) / 100) or 0.0

    @api.one
    @api.constrains('concession_amount', 'concession_type')
    def check_concession_percentage(self):
        self.check_concession_fees_due()

    @api.onchange('concession_amount', 'concession_type')
    def onchange_concession_amount(self):
        self.check_concession_fees_due()
