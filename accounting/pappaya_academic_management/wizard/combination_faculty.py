from odoo import api, fields, models


class CombinationFacultySingle(models.TransientModel):
    _name = 'combination.faculty.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    combination = fields.Many2one('combination.line', string='Combination')
    exam_branch = fields.Many2one('exam.branch', string='Exam Branch')
    subject = fields.Many2one('subject.line', string='Subject')
    combination_faculty_line = fields.One2many('combination.faculty.line', 'combination_faculty_id')

    combination_faculty_lines = fields.Many2many('combination.faculty.line')

    @api.model
    def default_get(self, fields):
        res = super(CombinationFacultySingle, self).default_get(fields)
        combination_faculty = self.env['combination.faculty.line'].search([])
        res['combination_faculty_lines'] = combination_faculty.ids
        return res