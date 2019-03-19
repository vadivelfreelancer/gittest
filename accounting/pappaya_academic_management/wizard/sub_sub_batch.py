from odoo import fields,models,api


class SubSubBatchView(models.Model):
    _name = 'sub.sub.batch.view'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    sub_sub_batch_line = fields.Many2many('sub.sub.batch.line')

    @api.model
    def default_get(self, fields):
        res = super(SubSubBatchView, self).default_get(fields)
        sub_sub_batch = self.env['sub.sub.batch.line'].search([])
        res['sub_sub_batch_line'] = sub_sub_batch.ids
        return res