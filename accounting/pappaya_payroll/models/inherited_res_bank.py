from odoo import api, fields, models, _

# class ResPartnerBank(models.Model):
#     _inherit = 'res.partner.bank'
#     
#     bic_code = fields.Char('BIC Code', size=9)
#     emp_no = fields.Char('Employee ID')
#     acc_number = fields.Char('Account Number', required=True, size=20)
#     
#     @api.multi
#     @api.depends('name')
#     def name_get(self):
#         result = []
#         for acc in self:
# #             name = str(acc.bank_id.name) + '/' + str(acc.acc_number)
#             name = str(acc.acc_number) + ' (' + str(acc.bank_id.name) + ')'
#             result.append((acc.id, name))
#         return result
