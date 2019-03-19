from odoo import api, fields, models


class PackageSubBatchSingle(models.TransientModel):
    _name = 'package.sub.batch.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    course = fields.Many2one('course.course', string='Course')
    group = fields.Many2one('pappaya.group', string='Group')
    batch = fields.Many2one(' batch.batch', string='Batch')

    package_sub_batch_lines = fields.Many2many('package.sub.batch.line')

    @api.model
    def default_get(self, fields):
        res = super(PackageSubBatchSingle, self).default_get(fields)
        package_subbatch = self.env['package.sub.batch.line'].search([])
        res['package_sub_batch_lines'] = package_subbatch.ids
        return res