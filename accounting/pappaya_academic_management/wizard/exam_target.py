from odoo import fields,models,api


class ExamTargetView(models.TransientModel):
    _name = 'exam.target.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    exam_target_lines = fields.Many2many('exam.target.line')

    @api.model
    def default_get(self, fields):
        res = super(ExamTargetView, self).default_get(fields)
        exam_target = self.env['exam.target.line'].search([])
        res['exam_target_lines'] = exam_target.ids
        return res


