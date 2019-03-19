from odoo import api, fields, models


class NewSubBatch(models.TransientModel):
    _name = 'new.subbatch.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    sub_batch = fields.Many2one("sub.batch", string="Sub Batch")
    new_sub_batch_lines = fields.Many2many('new.subbatch.line')

    @api.model
    def default_get(self, fields):
        res = super(NewSubBatch, self).default_get(fields)
        new_sub_batch = self.env['new.subbatch.line'].search([])
        res['new_sub_batch_lines'] = new_sub_batch.ids
        return res