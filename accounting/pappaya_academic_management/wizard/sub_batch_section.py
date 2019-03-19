from odoo import api, fields, models


class SubBatchSectionSingle(models.TransientModel):
    _name = 'sub.batch.section.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    course = fields.Many2one('course.course', string='Course')
    group = fields.Many2one('pappaya.group', string='Group')
    batch = fields.Many2one(' batch.batch', string='Batch')

    sub_batch_section_lines = fields.Many2many('sub.batch.section.line')

    @api.model
    def default_get(self, fields):
        res = super(SubBatchSectionSingle, self).default_get(fields)
        sub_batch_section = self.env['sub.batch.section.line'].search([])
        res['sub_batch_section_lines'] = sub_batch_section.ids
        return res