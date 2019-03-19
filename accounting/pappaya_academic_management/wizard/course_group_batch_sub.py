from odoo import api, fields, models


class CourseGroupBatchSubbatch(models.TransientModel):
    _name = 'cg.batch.sb.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    course = fields.Many2one('course.course', string='Course')
    group = fields.Many2one('pappaya.group', string='Group')
    batch = fields.Many2one('batch.batch', string='Batch    ')

    cg_batch_lines = fields.Many2many('cg.batch.line')

    @api.model
    def default_get(self, fields):
        res = super(CourseGroupBatchSubbatch, self).default_get(fields)
        cg_batch = self.env['cg.batch.line'].search([])
        res['cg_batch_lines'] = cg_batch.ids
        return res