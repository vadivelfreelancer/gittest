from odoo import api, fields, models


class LockBatch(models.TransientModel):
    _name = 'lock.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    sub_batch = fields.Many2one('sub.batch', string='Sub Batch')
    sub_section = fields.Many2one('sub.section', string='Group')
    lock_lines = fields.Many2many('lock.line')

    @api.model
    def default_get(self, fields):
        res = super(LockBatch, self).default_get(fields)
        lock_batch = self.env['lock.line'].search([])
        res['lock_lines'] = lock_batch.ids
        return res