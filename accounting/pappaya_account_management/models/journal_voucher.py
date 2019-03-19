from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import except_orm
from odoo.exceptions import RedirectWarning, UserError, ValidationError


class PappayaJournalVoucher(models.Model):
    _name = "pappaya.journal.voucher"
    _inherit = ['mail.thread']
    _description = "Journal Voucher"
    _order = 'date desc, id desc'

    @api.one
    @api.depends('type')
    def _compute_cash_in_hand(self):
        debit = credit = cash_in_hand = 0.0
        if self.type == 'cash_payment' or 'cash_receipt':
            account_id = self.env['account.account'].search([('name', '=', 'Cash')])
            for line in self.env['account.move.line'].search([('account_id', '=', account_id.id)]):
                if line.debit:
                    debit += line.debit
                elif line.credit:
                    credit += line.credit
            cash_in_hand = debit-credit
            self.cash_in_hand = cash_in_hand

    name = fields.Char(string="Name", readonly=True)
    type = fields.Selection([('voucher', 'Voucher'), ('cash_payment', 'Cash Payment'), ('cash_receipt', 'Cash Receipt'),
                             ('bank_payment', 'Bank Payment'), ('bank_receipt', 'Bank Receipt'),
                             ('multiple_bank_payment', 'Multiple Bank Payment'), ('contra_voucher', 'Contra Voucher')],
                            string="Type", index=True, change_default=True,
                            default=lambda self: self._context.get('type', 'voucher'), track_visibility='always')
    branch = fields.Many2one('operating.unit', string='Branch')
    date = fields.Date('Date', default=fields.Date.today())
    payee_name = fields.Char(string="Payee Name")
    cash_in_hand = fields.Float(string="Cash in Hand", readonly=True, compute='_compute_cash_in_hand')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('check_approved', 'Check Approved'),
        ('check_authorised', 'Check Authorised'),
        ('check_issued', 'Check Issued'),
        ('posted', 'Posted')], string="State", default='draft', track_visibility='onchange', copy=False)
    voucher_debits = fields.One2many('pappaya.voucher.debit.lines', 'voucher_id', string="Voucher Debit Lines")
    voucher_credits = fields.One2many('pappaya.voucher.credit.lines', 'voucher_id', string="Voucher Credit Lines")
    narration = fields.Text(string="Narration", required=True)
    move_id = fields.Many2one('account.move', string='Journal Entry',
                              readonly=True, index=True, ondelete='restrict', copy=False,
                              help="Link to the automatically generated Journal Items.")

    # Bank Payment Voucher fields #
    bank_account_no = fields.Many2one('res.partner.bank','Bank')
    bank_account_id = fields.Many2one('account.account', string="Bank Account")
    bank_branch_id = fields.Many2one('operating.unit', string="Branch")
    cheque_lot_id = fields.Many2one('subledger.cheque.book', string="Cheque Lot",
                                    domain="[('sub_ledger_id', '=', bank_account_id)]")
    cheque_no = fields.Many2one('cheque.book', string="Cheque No",
                                domain="[('subledger_cheque_book_id', '=', cheque_lot_id),('is_cheque_used', '=', False)]")
    bank_balance = fields.Float(string="Bank Balance")
    cheque_type = fields.Selection([('bank_cheque', 'Bank Cheques'), ('dd_cheque', 'DD Cheques')], string="Cheque Type", default='bank_cheque')
    cheque_date = fields.Date(string="Cheque date")
    amount = fields.Float(string="Amount")
    purpose_id = fields.Many2one('purpose.list', string="Purpose", required=True)

    #Bank Receipt Voucher Fields #
    bank_account_number = fields.Many2one('res.partner.bank','Bank')
    bank_receipt_account_id = fields.Many2one('account.account', string="Bank Account Number")
    cheque_number = fields.Char(string='Cheque No')

    #Multiple Branch Bank Payment Fields#
    branch_ledger_id = fields.Many2one('account.account', string="Ledger")

    # Contra Voucher Fields #
    ledger_id = fields.Many2one('account.account', string="Ledger")
    contra_cheque_no = fields.Char(string="Cheque No")
    contra_cheque_date = fields.Date(string="Cheque Date")
    contra_amount = fields.Float(string="Amount")
    bank_charges = fields.Float(string="Bank Charges")
    cheque_bool = fields.Boolean(string="Cheque Bool", default=False)

    @api.model
    def create(self, values):
        if self._context.get('type') not in ('bank_payment', 'cash_payment', 'contra_voucher','multiple_bank_payment'):
            res = super(PappayaJournalVoucher, self).create(values)
            res.action_confirm()
            return res
        else:
            res = super(PappayaJournalVoucher, self).create(values)
            if self._context.get('type') == 'cash_payment':
                if 'voucher_credits' in values:
                    if values['voucher_credits']:
                        if len(values['voucher_credits']) > 1:
                            raise except_orm('Error!', 'You cannot create more than one Cash Entry.')
                        else:
                            res.action_confirm()
                            return res
            elif self._context.get('type') == 'contra_voucher':
                return res
            elif self._context.get('type') == 'bank_payment':
                return res
            elif self._context.get('type') == 'multiple_bank_payment':
                return res
            else:
                res.action_confirm()
                return res

    @api.onchange('ledger_id', 'branch')
    def _onchange_ledger_id(self):
        res = dict()
        sub_ledgers = []
        branch_ledger_ids = self.env['branch.ledger'].search([('branch', '=', self.branch.id)])
        for line in branch_ledger_ids.ledger_branches:
            for sub_ledger in line.ledger:
                if self.type == 'contra_voucher':
                    if sub_ledger.group_id.is_cash != 'yes' and sub_ledger.group_id.is_bank != 'yes':
                        sub_ledgers.append(sub_ledger.id)
                else:
                    sub_ledgers.append(sub_ledger.id)

        res['domain'] = {'ledger_id': [('id', 'in', sub_ledgers)]}
        return res

    @api.onchange('bank_account_number', 'bank_receipt_account_id')
    def _onchange_bank_account_number(self):
        branch_account_id = self.env['branch.bank.account.mapping'].search([('account_no_id', '=', self.bank_account_number.id)], limit=1)
        self.bank_receipt_account_id = branch_account_id.credit_account_id.id or branch_account_id.debit_account_id.id

    @api.onchange('bank_account_no', 'bank_branch_id', 'bank_account_id')
    def _onchange_bank_account_no(self):
        branch_account_id = self.env['branch.bank.account.mapping'].search([('account_no_id', '=', self.bank_account_no.id)], limit=1)
        print("branch account", branch_account_id)
        self.bank_branch_id = branch_account_id.operating_unit_id.id
        self.bank_account_id = branch_account_id.credit_account_id.id or branch_account_id.debit_account_id.id

    @api.multi
    def action_approval1(self):
        if self.cheque_no:
            cheque_book_id = self.env['cheque.book'].search([('id', '=', self.cheque_no.id)])
            cheque_book_id.write({'is_cheque_used': True})
        self.write({'state': 'check_approved'})

    @api.multi
    def action_approval2(self):
        self.write({'state': 'check_authorised'})

    @api.multi
    def action_approval3(self):
        move_lines = []
        journal_obj = self.env['account.journal'].search([('code', '=', 'NARFC')], limit=1)
#        if self.type == 'bank_payment':
#            for debit_line in self.voucher_debits:
#                debit_acc_id = debit_line.account_id
#                move_lines.append((0, 0, {
#                    'name': 'Bank Payment Voucher',
#                    'debit': debit_line.amount,
#                    'credit': 0,
#                    'account_id': debit_acc_id.id,
#                    'date': str(datetime.today().date()),
#                    'partner_id': None,
#                    'journal_id': journal_obj.id,
#                    'company_id': journal_obj.company_id.id,
#                    'currency_id': journal_obj.company_id.currency_id.id,  # currency id of narayana
#                    'date_maturity': self.date,
#                    'operating_unit_id': self.branch.id,
#                    }))

        if self.type == 'bank_payment':
            debit = 0.0
            name = 'Bank Payment Voucher'
            account_id = self.branch.debit_account_id or self.branch.credit_account_id
            if not account_id:
                raise UserError(_('You have to map debit and credit ledger in %s Branch') % (self.branch.name))
            for debit_line in self.voucher_debits:
                debit += debit_line.amount
            move_lines.append((0, 0, {
                'name': name,  # a label so accountant can understand where this line come from
                'debit': debit or 0.0,
                'credit': 0.0,
                'account_id': account_id.id,
                'date': str(datetime.today().date()),
                'partner_id': None,
                'journal_id': journal_obj.id,  # Cash journal
                'company_id': journal_obj.company_id.id,
                'currency_id': journal_obj.company_id.currency_id.id,
                'date_maturity': self.date,
                'operating_unit_id': self.branch.id,
            }))
            
            if self.voucher_credits:
                account_id = self.bank_account_id
                move_lines.append((0, 0, {
                    'name': name,  # a label so accountant can understand where this line come from
                    'debit': 0.0,
                    'credit': self.amount or 0.0,
                    'account_id': account_id.id,
                    'date': str(datetime.today().date()),
                    'partner_id': None,
                    'journal_id': journal_obj.id,
                    'company_id': journal_obj.company_id.id,
                    'currency_id': journal_obj.company_id.currency_id.id,
                    'date_maturity': self.date,
                    'operating_unit_id': self.branch.id,
                }))

            name = 'Bank Payment Voucher'
            for credit_line in self.voucher_credits:
                credit_account_id = credit_line.account_id
                move_lines.append((0, 0, {
                    'name': name,  # a label so accountant can understand where this line come from
                    'debit': 0,
                    'credit': credit_line.amount,
                    'account_id': credit_account_id.id,
                    'date': str(datetime.today().date()),
                    'partner_id': None,
                    'journal_id': journal_obj.id,  # Cash journal
                    'company_id': journal_obj.company_id.id,
                    'currency_id': journal_obj.company_id.currency_id.id,
                    'date_maturity': self.date,
                    'operating_unit_id': self.branch.id,
                }))

        if self.type == 'contra_voucher':
            move_lines = []
            journal_obj = self.env['account.journal'].search([('code', '=', 'NARFC')], limit=1)
            debit_acc_id = self.ledger_id
            move_lines.append((0, 0, {
                'name': 'Contra Voucher',
                'debit': self.contra_amount,
                'credit': 0,
                'account_id': debit_acc_id.id,
                'date': str(datetime.today().date()),
                'partner_id': None,
                'journal_id': journal_obj.id,
                'company_id': journal_obj.company_id.id,
                'currency_id': journal_obj.company_id.currency_id.id,  # currency id of narayana
                'date_maturity': self.date,
                'operating_unit_id': self.branch.id,
                }))

            if self.bank_charges:
                debit_acc_id = self.env['account.account'].search([('name', '=', 'Bank Charges A/C')])
                move_lines.append((0, 0, {
                    'name': name,  # a label so accountant can understand where this line come from
                    'credit': 0,
                    'debit': self.bank_charges,
                    'account_id': debit_acc_id.id,
                    'date': str(datetime.today().date()),
                    'partner_id': None,
                    'journal_id': journal_obj.id,  # Cash journal
                    'company_id': journal_obj.company_id.id,
                    'currency_id': journal_obj.company_id.currency_id.id,
                    'date_maturity': self.date,
                    'operating_unit_id': self.branch.id,
                }))

            credit_account_id = self.bank_account_id
            move_lines.append((0, 0, {
                'name': name,  # a label so accountant can understand where this line come from
                'debit': 0,
                'credit': self.amount,
                'account_id': credit_account_id.id,
                'date': str(datetime.today().date()),
                'partner_id': None,
                'journal_id': journal_obj.id,  # Cash journal
                'company_id': journal_obj.company_id.id,
                'currency_id': journal_obj.company_id.currency_id.id,
                'date_maturity': self.date,
                'operating_unit_id': self.branch.id,
            }))

        print("Move lines", move_lines)
        debit_amount = credit_amount = 0.0
        for debit in move_lines:
            debit_amount += debit[2]['debit']
        for credit in move_lines:
            print("credit", credit[2]['credit'])
            credit_amount += credit[2]['credit']
        if debit_amount != credit_amount:
            raise UserError(_('Debit - %s and Credit - %s values are not matched. Please enter proper values') % (debit_amount, credit_amount))
        account_move = self._create_move_entry_from_adj(journal_obj, self.branch, move_lines)
        account_move.post()
        self.write({'state': 'check_issued', 'move_id': account_move.id})


    @api.multi
    def action_confirm(self):
        move_lines = []
        journal_obj = self.env['account.journal'].search([('code', '=', 'NARFC')], limit=1)
        name = ''
        if self.type == 'voucher':
            name = 'Journal Voucher'
        elif self.type == 'cash_payment':
            name = 'Cash Payment Voucher'
        if self.type != ('cash_receipt', 'bank_receipt'):
            for debit_line in self.voucher_debits:
                debit_acc_id = debit_line.account_id
                move_lines.append((0, 0, {
                    'name': name,
                    'debit': debit_line.amount,
                    'credit': 0,
                    'account_id': debit_acc_id.id,
                    'date': str(datetime.today().date()),
                    'partner_id': None,
                    'journal_id': journal_obj.id,
                    'company_id': journal_obj.company_id.id,
                    'currency_id': journal_obj.company_id.currency_id.id,  # currency id of narayana
                    'date_maturity': self.date,
                    'operating_unit_id': self.branch.id,
                    }))

        name = ''
        if self.type == 'voucher':
            name = 'Journal Voucher'
        elif self.type == 'cash_payment':
            name = 'Cash Payment Voucher'
        elif self.type == 'cash_receipt':
            name = 'Cash Receipt Voucher'
        elif self.type == 'bank_receipt':
            name = 'Bank Receipt Voucher'
        for credit_line in self.voucher_credits:
            credit_account_id = credit_line.account_id
            move_lines.append((0, 0, {
                'name': name,  # a label so accountant can understand where this line come from
                'debit': 0,
                'credit': credit_line.amount,
                'account_id': credit_account_id.id,
                'date': str(datetime.today().date()),
                'partner_id': None,
                'journal_id': journal_obj.id,  # Cash journal
                'company_id': journal_obj.company_id.id,
                'currency_id': journal_obj.company_id.currency_id.id,
                'date_maturity': self.date,
                'operating_unit_id': self.branch.id,
                }))

        name = ''
        account_id = []
        credit_cash = 0.0
        if self.type == 'cash_receipt':
            name = 'Cash Receipt Voucher'
            paymode = self.env['pappaya.paymode'].search([('is_cash','=',True)])
            print("paymode", paymode)
            account_id = paymode.credit_account_id
            if account_id:
                for cash_line in self.voucher_credits:
                    credit_cash += cash_line.amount
                move_lines.append((0, 0, {
                    'name': name,  # a label so accountant can understand where this line come from
                    'debit': credit_cash,
                    'credit': 0.0,
                    'account_id': account_id.id,  # Course Fee chart of account.
                    'date': str(datetime.today().date()),
                    'partner_id': None,
                    'journal_id': journal_obj.id,  # Cash journal
                    'company_id': journal_obj.company_id.id,
                    'currency_id': journal_obj.company_id.currency_id.id,
                    'date_maturity': self.date,
                    'operating_unit_id': self.branch.id,
                }))

        credit_cash = 0.0
        if self.type == 'bank_receipt':
            name = 'Bank Receipt Voucher'
            account_id = self.bank_receipt_account_id.id
            move_lines.append((0, 0, {
                'name': name,  # a label so accountant can understand where this line come from
                'debit': self.amount,
                'credit': 0.0,
                'account_id': account_id,  # Course Fee chart of account.
                'date': str(datetime.today().date()),
                'partner_id': None,
                'journal_id': journal_obj.id,  # Cash journal
                'company_id': journal_obj.company_id.id,
                'currency_id': journal_obj.company_id.currency_id.id,
                'date_maturity': self.date,
                'operating_unit_id': self.branch.id,
            }))

        debit_amount = credit_amount = 0.0
        for debit in move_lines:
            debit_amount += debit[2]['debit']
        for credit in move_lines:
            credit_amount += credit[2]['credit'] 
        if debit_amount != credit_amount:
            raise UserError(_('Debit - %s and Credit - %s values are not matched. Please enter proper values') % (debit_amount, credit_amount))
        account_move = self._create_move_entry_from_adj(journal_obj, self.branch, move_lines)
        account_move.post()
        self.write({'state': 'posted', 'move_id': account_move.id })

    @api.multi
    def _create_move_entry_from_adj(self, journal_obj, operating_unit_obj, line_ids):
        account_move_obj = self.env['account.move'].create({
            'journal_id': journal_obj.id,  # journal ex: sale journal, cash journal, bank journal....
            'date': self.date,
            'state': 'draft',
            'company_id': journal_obj.company_id.id,
            'operating_unit_id': operating_unit_obj.id,
            'line_ids': line_ids,  # this is one2many field to account.move.line
        })
        return account_move_obj

    @api.multi
    def action_draft(self):
        return self.write({'state': 'draft'})


class PappayaVoucherDebits(models.Model):
    _name = 'pappaya.voucher.debit.lines'

    voucher_id = fields.Many2one('pappaya.journal.voucher', string="Journal Voucher")
    # name = fields.Char(string="Sno")
    type = fields.Selection([('voucher', 'Voucher'), ('case_payment', 'Cash Payment'), ('cash_receipt', 'Cash Receipt'),
                             ('bank_receipt', 'Bank Receipt')], related="voucher_id.type", string="Type")
    branch_id = fields.Many2one('operating.unit', string="Branch")
    account_id = fields.Many2one('account.account', string="Ledger")
    amount = fields.Float(string="Amount")
    bill_number = fields.Char(string="Bill Number")
    bill_date = fields.Date(string="Bill Date")

    @api.onchange('account_id')
    def _onchange_account_id(self):
        res = dict()
        sub_ledgers = []
        branch_ledger_ids = self.env['branch.ledger'].search([('branch', '=', self.voucher_id.branch.id)])
        for line in branch_ledger_ids.ledger_branches:
            for sub_ledger in line.ledger:
                if self._context.get('type') in ('voucher', 'cash_payment', 'bank_payment'):
                    if sub_ledger.group_id:
                        print("Ledger", sub_ledger.group_id)
                        if sub_ledger.group_id.is_cash != 'yes' and sub_ledger.group_id.is_bank != 'yes':
                            sub_ledgers.append(sub_ledger.id)
                else:
                    sub_ledgers.append(sub_ledger.id)

        res['domain'] = {'account_id': [('id', 'in', sub_ledgers)]}
        return res


class PappayaVoucherCredits(models.Model):
    _name = 'pappaya.voucher.credit.lines'

    @api.model
    def _default_account_id(self):
        if self._context.get('type'):
            if self._context.get('type') == 'cash_payment':
                paymode = self.env['pappaya.paymode'].search([('is_cash','=',True)])
                print("paymode", paymode)
                if paymode:
                    account_id = paymode.credit_account_id
                    return account_id

    voucher_id = fields.Many2one('pappaya.journal.voucher', string="Journal Voucher")
    # name = fields.Char(string="Sno")
    type = fields.Selection([('voucher', 'Voucher'), ('case_payment', 'Cash Payment'), ('cash_receipt', 'Cash Receipt'),
                             ('bank_receipt', 'Bank Receipt')], related="voucher_id.type", string="Type")
    account_id = fields.Many2one('account.account', string="Ledger", default=_default_account_id)
    amount = fields.Float(string="Amount")
    bill_number = fields.Char(string="Bill Number")
    bill_date = fields.Date(string="Bill Date")

    @api.onchange('account_id')
    def _onchange_account_id(self):
        res = dict()
        sub_ledgers = []
        branch_ledger_ids = self.env['branch.ledger'].search([('branch', '=', self.voucher_id.branch.id)])
        for line in branch_ledger_ids.ledger_branches:
            for sub_ledger in line.ledger:
                if self._context.get('type') in ('voucher', 'cash_receipt', 'bank_payment', 'bank_receipt'):
                    if sub_ledger.group_id:
                        if sub_ledger.group_id.is_cash != 'yes' and sub_ledger.group_id.is_bank != 'yes':
                            sub_ledgers.append(sub_ledger.id)
                else:
                    sub_ledgers.append(sub_ledger.id)

        res['domain'] = {'account_id': [('id', 'in', sub_ledgers)]}
        return res
