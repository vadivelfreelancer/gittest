from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta

class StudentFeesCollection(models.Model):
    _inherit = 'student.fees.collection'
     
    adjusted_amount = fields.Float(string='Adjusted Amount')
    adjustment_id = fields.Many2one('pappaya.fee.adjustment', string='Fees Adjustment')
    
class PappayaFeeAdjustment(models.Model):
    _name = 'pappaya.fee.adjustment'
    _rec_name = "admission_id"
    
    status = fields.Selection([('draft','Draft'),('request','Requested'),('confirm','Approved')], string='Status', default="draft")
    admission_id = fields.Many2one('pappaya.admission', string='Student Name')
    admission_number = fields.Char(related='admission_id.res_no', string='Admission No', store=True)
    branch_id = fields.Many2one('operating.unit', string='Branch', related='admission_id.branch_id')
    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    current_date = fields.Date(string='Date', default=lambda self:fields.Date.today())
    description = fields.Text('Description',size=300)
    from_fee_head_id = fields.Many2one('pappaya.fees.head', string='From Fee Type')
    to_fee_head_id = fields.Many2one('pappaya.fees.head', string='To Fee Type')
    amount = fields.Float(string='Amount')
    stu_transaction_ids = fields.Many2many('student.fees.collection', string='Transaction Details')
    total = fields.Float('Total', compute='compute_total')
    res_adj_amt_total = fields.Float('res_adj_amt_total', compute='compute_res_adj_amt')
    due_total = fields.Float('Total due', compute='compute_total_due')
    paid_total = fields.Float('Total paid', compute='compute_total_paid')
    adj_amt_total = fields.Float('Total paid', compute='compute_adj_amt_total')

    @api.one
    def copy(self, default=None):
        raise ValidationError("You are not allowed to Duplicate")

    @api.multi
    @api.depends('stu_transaction_ids.amount')
    def compute_total(self):
        for rec in self:
            tot = 0.0
            for line in rec.stu_transaction_ids:
                if line.name.is_course_fee or line.name.is_reservation_fee:
                    tot += line.amount
            total = round(sum(line.amount for line in rec.stu_transaction_ids))
            rec.total = total - tot

    @api.multi
    @api.depends('stu_transaction_ids.due_amount')
    def compute_total_due(self):
        for rec in self:
            due_tot = 0.0
            for line in rec.stu_transaction_ids:
                if (line.name.is_course_fee and line.name.is_course_fee_component) or (line.name.is_reservation_fee and line.due_amount > 0):
                    due_tot += line.due_amount
            total = round(sum(line.due_amount for line in rec.stu_transaction_ids))
            if self.admission_id.stage_id.sequence == 4:
                rec.due_total = total - due_tot
            if self.admission_id.stage_id.sequence != 4:
                rec.due_total = total - due_tot - self.paid_total

    @api.multi
    @api.depends('stu_transaction_ids.total_paid')
    def compute_total_paid(self):
        for rec in self:
            paid_tot = 0.0
            for line in rec.stu_transaction_ids:
                if line.name.is_course_fee and line.name.is_course_fee_component and line.total_paid == line.amount:
                    paid_tot += line.total_paid
            total = round(sum(line.total_paid for line in rec.stu_transaction_ids if line.term_state == 'paid'))
            rec.paid_total = total - paid_tot

    @api.multi
    @api.depends('stu_transaction_ids.res_adj_amt')
    def compute_res_adj_amt(self):
        for rec in self:
            rec.res_adj_amt_total = round(sum(line.res_adj_amt for line in rec.stu_transaction_ids))

    @api.multi
    @api.depends('stu_transaction_ids.adjusted_amount')
    def compute_adj_amt_total(self):
        for rec in self:
            rec.adj_amt_total = round(sum(line.adjusted_amount for line in rec.stu_transaction_ids))
        
    @api.onchange('admission_id')
    def onchange_admission_id(self):
        self.from_fee_head_id = None; self.to_fee_head_id = None; self.amount = None
        if self.admission_id:
            pfc_obj = self.env['pappaya.fees.collection'].search([('enquiry_id','=',self.admission_id.id)])
            self.stu_transaction_ids =  [(6,0, pfc_obj.fees_collection_line.ids)]
            from_fee_heads = []; to_fee_heads = []
            for fc_obj in self.stu_transaction_ids:
                if (fc_obj.name.is_caution_deposit_fee or fc_obj.name.is_pocket_money) and fc_obj.term_state == 'paid' :
                    from_fee_heads.append(fc_obj.name.id)
                elif fc_obj.term_state =='due':
                    if fc_obj.name.id not in to_fee_heads:
                        to_fee_heads.append(fc_obj.name.id)
            return {'domain': {'from_fee_head_id': [('id', 'in', from_fee_heads)], 'to_fee_head_id':[('id', 'in', to_fee_heads)]}}
    
    @api.onchange('from_fee_head_id')
    def onchange_from_fee_head_id(self):
        self.to_fee_head_id = None; self.amount = None; 
            
    @api.onchange('amount')
    def onchange_amount(self):
        if self.admission_number and len(self.search([('admission_number', '=', self.admission_number), ('status', 'in', ['draft', 'request'])])) > 1:
            raise ValidationError('Already record existed for given admission number in Draft or Request stage')
        if self.amount and self.admission_id:
            max_amount = 0
            if self.from_fee_head_id:
                # Student Caution Deposit Amount
                if self.from_fee_head_id.is_caution_deposit_fee and self.admission_id.partner_id.caution_deposit > 0.0:
                    max_amount = self.admission_id.partner_id.caution_deposit
                # Student Pocket Money Amount
                if self.from_fee_head_id.is_pocket_money and self.admission_id.partner_id.student_wallet_amount > 0.0:
                    max_amount = self.admission_id.partner_id.student_wallet_amount
            due_amount = 0
            if self.from_fee_head_id:
                for fc_obj in self.stu_transaction_ids:
                    if fc_obj.term_state == 'due':
                        if fc_obj.name.name == self.to_fee_head_id.name:
                            due_amount = fc_obj.due_amount
            if self.amount > max_amount:
                raise ValidationError('Amount should not be greater than (%s)' % max_amount)
            if self.amount > due_amount:
                raise ValidationError('Total Due amount (%s)' % (due_amount))

    @api.constrains('amount')
    def _check_amount(self):
        if self.amount:
            max_amount = 0
            if self.from_fee_head_id:
                # Student Caution Deposit Amount
                if self.from_fee_head_id.is_caution_deposit_fee and self.admission_id.partner_id.caution_deposit > 0.0:
                    max_amount = self.admission_id.partner_id.caution_deposit
                # Student Pocket Money Amount
                if self.from_fee_head_id.is_pocket_money and self.admission_id.partner_id.student_wallet_amount > 0.0:
                    max_amount = self.admission_id.partner_id.student_wallet_amount
            due_amount = 0
            if self.from_fee_head_id:
                for fc_obj in self.stu_transaction_ids:
                    if fc_obj.term_state == 'due':
                        if fc_obj.name.name == self.to_fee_head_id.name:
                            due_amount = fc_obj.due_amount
            if self.amount > max_amount:
                raise ValidationError('Amount should not be greater than (%s)' % max_amount)
            if self.amount > due_amount:
                raise ValidationError('Total Due amount (%s)' % due_amount)
        if self.amount == 0 or self.amount < 0:
            raise ValidationError('Amount should be greater than 0.' '\n' 'or' '\n' 'Amount should be lesser than or equal to Due Amount.')
        if self.admission_number and len(self.search([('admission_number', '=', self.admission_number), ('status', 'in', ['draft', 'request'])])) > 1:
            raise ValidationError('Already record existed for given admission number in Draft or Request stage')

    @api.one
    def request_status(self):
        self.status = 'request'
    
    @api.one
    def confirm_status(self):
        for fc_obj in self.stu_transaction_ids:
            if fc_obj.term_state == 'due':
                # Adjusting to other fee heads
                if fc_obj.name.name == self.to_fee_head_id.name and not (self.to_fee_head_id.is_course_fee and self.to_fee_head_id.is_course_fee_component):
                    due_amount = fc_obj.due_amount - self.amount
                    res_adj_amount = fc_obj.res_adj_amt + self.amount
                    fc_obj.write({'res_adj_amt': res_adj_amount })
                    if due_amount == 0.0:
                        fc_obj.write({'term_state': 'paid'})
                    if self.to_fee_head_id.is_caution_deposit_fee:
                        self.admission_id.partner_id.caution_deposit += self.amount
                    if self.to_fee_head_id.is_pocket_money:
                        self.admission_id.partner_id.student_wallet_amount += self.amount
                # Adjusting to Course fee heads
                if fc_obj.name.is_course_fee and fc_obj.name.is_course_fee_component:
                    course_due_amount = fc_obj.due_amount - self.amount
                    course_total_paid = fc_obj.total_paid + self.amount
                    fc_obj.write({'due_amount': course_due_amount, 'total_paid': course_total_paid })
                    if course_due_amount == 0.0 and fc_obj.name.is_course_fee and fc_obj.name.is_course_fee_component:
                        fc_obj.write({'term_state': 'paid'})
                if self.to_fee_head_id.is_course_fee and self.to_fee_head_id.is_course_fee_component and fc_obj.name.is_course_fee_component and not fc_obj.name.is_course_fee:
                    if fc_obj.name.is_course_fee_component and fc_obj.due_amount > 0.0:
                        due_amount = fc_obj.due_amount - self.amount
                        res_adj_amount = fc_obj.res_adj_amt + self.amount
                        fc_obj.write({'res_adj_amt': res_adj_amount})
                        if due_amount == 0.0:
                            fc_obj.write({'term_state': 'paid'})
        # Updating Adjusted Amount
        for fc_obj in self.stu_transaction_ids:
            # if fc_obj.term_state == 'paid':
            if fc_obj.name.name == self.from_fee_head_id.name  and not (self.from_fee_head_id.is_caution_deposit_fee or self.from_fee_head_id.is_pocket_money):
                fc_obj.adjusted_amount += self.amount
            if fc_obj.name.name == self.to_fee_head_id.name and self.from_fee_head_id.is_caution_deposit_fee:
                fc_obj.adjusted_amount += self.amount
                self.admission_id.partner_id.caution_deposit -= self.amount
            if fc_obj.name.name == self.to_fee_head_id.name and self.from_fee_head_id.is_pocket_money:
                fc_obj.adjusted_amount += self.amount
                self.admission_id.partner_id.student_wallet_amount -= self.amount

        ledger_obj = self.env['pappaya.fees.ledger'].search([('enquiry_id', '=', self.admission_id.id)])
        if ledger_obj:
            self.env['pappaya.fees.refund.ledger'].create({
                'fees_ledger_id': ledger_obj.id,
                'amount': self.amount,
                'posting_date': datetime.today().date(),
                'transaction_remarks': 'Adjustment : ' + str(self.from_fee_head_id.name) + '-' + str(self.to_fee_head_id.name)
            })
        self.status = 'confirm'
