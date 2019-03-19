from odoo import models, fields, api


#class MainGroup(models.Model):
#    _name = 'main.group'

#    name = fields.Char(string='Name', required=True)
#    code = fields.Char(string='Code')
#    description = fields.Char(string='Description')


#class AccountGroup(models.Model):
#    _name = 'accounting.group'
#    _rec_name = 'group_name'

#    name_id = fields.Many2one('main.group', string='Main Group', required=True)
#    group_name = fields.Char(string='Group Name', required=True)
#    description = fields.Char(string='Description')


#class AccountSubGroup(models.Model):
#    _name = 'accounting.group.sub'
#    _rec_name = 'sub_group_name'

#    name_id = fields.Many2one('main.group', string='Main Group', required=True)
#    group_name_id = fields.Many2one('accounting.group', string='Group', required=True,
#                                    domain="[('name_id', '=', name_id)]")
#    sub_group_name = fields.Char(string='Sub Group Name', required=True)
#    description = fields.Char(string='Description')


#class SingleLedger(models.Model):
#    _name = 'single.ledger'
#    _rec_name = 'ledger_name'

#    name_id = fields.Many2one('main.group', string='Main Group', required=True)
#    group_name_id = fields.Many2one('accounting.group', string='Group', required=True,
#                                    domain="[('name_id', '=', name_id)]")
#    sub_group_name_id = fields.Many2one('accounting.group.sub', string='Sub Group Name', required=True,
#                                        domain="[('group_name_id', '=', group_name_id)]")
#    ledger_type = fields.Selection([('integrated_entry', 'Integrated Entry'), ('direct_entry', 'Direct Entry')
#                                    , ('all', 'All')],
#                               string='Ledger Type', required=True)
##    module = fields.Char(string='Module', required=True)
#    ledger_name = fields.Char(string='Ledger Name', required=True)
#    description = fields.Char(string='Description', required=True)
#    is_cash = fields.Selection([('yes', 'Yes'), ('no', 'No')],
#                                   string='Is Cash', required=True)
#    is_bank = fields.Selection([('yes', 'Yes'), ('no', 'No')],
#                                   string='Is Bank', required=True)
#    is_loan = fields.Selection([('yes', 'Yes'), ('no', 'No')],
#                                   string='Is Loan', required=True)
#    is_fdr = fields.Selection([('yes', 'Yes'), ('no', 'No')],
#                                   string='Is FDR', required=True)
#    is_unsecured_loan = fields.Selection([('yes', 'Yes'), ('no', 'No')],
#                                   string='Is Un Secured Loan', required=True)
#    is_sundry_debtor = fields.Selection([('yes', 'Yes'), ('no', 'No')],
#                                   string='Is Sundry Debtor', required=True)
#    is_sub_ledger = fields.Selection([('yes', 'Yes'), ('no', 'No')],
#                                   string='Is Sub Ledger', required=True)

#    @api.model
#    def create(self, vals):
#        result = super(SingleLedger, self).create(vals)
#        if result.is_sub_ledger == 'yes':
#            material_vals = {'name_id': result.name_id.id,
#                             'group_name_id': result.group_name_id.id,
#                             'sub_group_name_id': result.sub_group_name_id.id,
#                             'ledger_type': result.ledger_type,
#                             'sub_ledger_name': result.ledger_name,
##                             'module': result.module,
#                             'description': result.description,
#                             'ledger_name_id': result.id
#                             }
#            self.env['account.account'].create(material_vals)
#        return result


#class SubLedger(models.Model):
#    _name = 'sub.ledger'
#    _rec_name = 'ledger_name_id'

#    name_id = fields.Many2one('main.group', string='Main Group', required=True)
#    group_name_id = fields.Many2one('accounting.group', string='Group', required=True,
#                                    domain="[('name_id', '=', name_id)]")
#    sub_group_name_id = fields.Many2one('accounting.group.sub', string='Sub Group Name', required=True,
#                                        domain="[('group_name_id', '=', group_name_id)]")
#    ledger_name_id = fields.Many2one('single.ledger', string='Ledger')
#    ledger_type = fields.Selection([('integrated_entry', 'Integrated Entry'), ('direct_entry', 'Direct Entry')
#                                    , ('all', 'All')],
#                               string='Sub Ledger Type', required=True)
#    sub_ledger_name = fields.Char(string='Sub Ledger Name', required=True)
#    # module = fields.Char(string='Module', required=True)
#    description = fields.Char(string='Description', required=True)
#    fy_branches = fields.One2many("fy.branch.mapped", "sub_ledger_id", string="")
    # pan = fields.Char(string='PAN')


class Accountaccount(models.Model):
    _inherit = "account.account"

#    name_id = fields.Many2one('main.group', string='Main Group', required=True)
#    group_name_id = fields.Many2one('accounting.group', string='Group', required=True,
#                                    domain="[('name_id', '=', name_id)]")
#    sub_group_name_id = fields.Many2one('accounting.group.sub', string='Sub Group Name', required=True,
#                                        domain="[('group_name_id', '=', group_name_id)]")
#    ledger_name_id = fields.Many2one('single.ledger', string='Ledger')
#    ledger_type = fields.Selection([('integrated_entry', 'Integrated Entry'), ('direct_entry', 'Direct Entry')
#                                    , ('all', 'All')],
#                               string='Sub Ledger Type', required=True)
    fy_branches = fields.One2many("fy.branch.mapped", "sub_ledger_id", string="")



class AccountGroup(models.Model):
    _inherit = "account.group"

    is_cash = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                   string='Is Cash', required=True)
    is_bank = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                   string='Is Bank', required=True)
    is_loan = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                   string='Is Loan', required=True)
    is_fdr = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                   string='Is FDR', required=True)
    is_unsecured_loan = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                   string='Is Un Secured Loan', required=True)
    is_sundry_debtor = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                   string='Is Sundry Debtor', required=True)
    is_sub_ledger = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                   string='Is Sub Ledger', required=True)

class FinancialYear(models.Model):
    _name = 'financial.year'

    name = fields.Char(string='Financial Year', required=True)
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    ledger_financial = fields.Many2many('account.account')
    branch_financial = fields.Many2many('operating.unit')


class OperatingUnit(models.Model):
    _inherit = 'operating.unit'

#     entity = fields.Selection([('nes', 'NES'), ('ntl', 'NTL'), ('nspira', 'NSPIRA')], string='Entity', required=True)
#     office_type = fields.Selection([('schools', 'Schools'), ('college', 'College')
#                                        , ('central_office', 'Central Office'), ('zonal_office', 'Zonal Office'),
#                                     ('prof_colleges', 'Prof Colleges')
#                                        , ('ware_house', 'Ware house'), ('campaigning', 'Campaigning')],
#                                    string='Office Type', required=True)
    fy_subledgers = fields.One2many("fy.ledger.mapped", "branch_id", string="")


class LedgerFyMapping(models.Model):
    _name = 'fy.ledger.mapped'

    branch_id = fields.Many2one("operating.unit", string="Branch")
    financial_year = fields.Many2one('financial.year', string='Financial Year', required=True)
    sub_ledger = fields.Many2many('account.account', string='Sub Ledger')


class BranchFyMapping(models.Model):
    _name = 'fy.branch.mapped'

    sub_ledger_id = fields.Many2one("account.account", string="Branch")
    financial_year = fields.Many2one('financial.year', string='Financial Year', required=True)
    branches = fields.Many2many('operating.unit', string='Sub Ledger')


class BranchMappedSubledger(models.Model):
    _name = 'branch.ledger'

    financial_year = fields.Many2one('financial.year', string='Financial Year', required=True)
    branch = fields.Many2one('operating.unit', string='Branch')
    sub_ledger = fields.Many2one('account.account', string='Sub Ledger')
    ledger_branches = fields.Many2many('ledger.page')
    branch_ledger = fields.Many2many('page.ledger')


class Ledger(models.Model):
    _name = 'page.ledger'

    branch = fields.Many2one('operating.unit', string='Branch')


class LedgerSub(models.Model):
    _name = 'ledger.page'

    ledger = fields.Many2one('account.account', string='Sub Ledger')


class BankaccountMappingBranch(models.Model):
    _name = 'bank.branch'

    bank = fields.Many2one('account.group', string='Bank', required=True)
    financial_year = fields.Many2one('financial.year', string='Financial Year', required=True)
    branches = fields.Many2many('operating.unit')


class BankMapped(models.Model):
    _name = 'bank.mapped'

    branch = fields.Many2one('operating.unit', string='Branch', required=True)


class SubledgerChequeBook(models.Model):
    _name = "subledger.cheque.book"
    _rec_name = "from_cheque_no"

    name = fields.Char(string="Name", default="/", readonly=True)
    ledger_id = fields.Many2one('account.group', string='Ledger', required=True)
    sub_ledger_id = fields.Many2one('account.account', string="Sub Ledger", required=True)
    dept_id = fields.Many2one('hr.department', string="Department", required=True)
    from_cheque_no = fields.Char(string="From Cheque No", required=True)
    to_cheque_no = fields.Char(string="To Cheque No", required=True)
    type = fields.Selection([('is_cheque', 'Is Normal Cheque Book'), ('printing_role', 'Is Printing Role'),
                             ('is_online', 'Is Online Printing'), ('is_professional', 'Is Professional College')],
                            string="Type", default='is_cheque')
    is_created = fields.Boolean(string="Is Created", readonly=True)

    @api.model
    def create(self, values):
        if values['from_cheque_no'] and values['to_cheque_no']:
            values['name'] = values['from_cheque_no'] + '-' + values['to_cheque_no'] + ' /'
        res = super(SubledgerChequeBook, self).create(values)
        return res

    @api.multi
    def action_generate(self):
        if not self.is_created:
            if self.ledger_id and self.sub_ledger_id and self.dept_id:
                cheque_start = int(self.from_cheque_no)
                cheque_end = int(self.to_cheque_no)
                for i in range(cheque_start, cheque_end + 1):
                    cheque_start = i
                    self.env['cheque.book'].create({
                        'name': str(cheque_start),
                        'ledger_id': self.ledger_id.id,
                        'sub_ledger_id': self.sub_ledger_id.id,
                        'subledger_cheque_book_id': self.id})
                self.write({'is_created': True})


class ChequeBook(models.Model):
    _name = "cheque.book"

    name = fields.Char(string="Name")
    ledger_id = fields.Many2one('account.group', string='Ledger')
    sub_ledger_id = fields.Many2one('account.account', string="Sub Ledger")
    subledger_cheque_book_id = fields.Many2one('subledger.cheque.book', string="Subledger Cheque Book")
    is_cheque_used = fields.Boolean(string="Is Cheque Used", default=False, readonly=True)


class PurposeLists(models.Model):
    _name = "purpose.list"

    name = fields.Char(string="Name")


class TransactionType(models.Model):
    _name = "transaction.type"

    name = fields.Char(string="Name")

