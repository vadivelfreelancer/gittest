from odoo import fields,models,api


class ExamName(models.Model):
    _name = 'exam.name'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    course = fields.Many2one('course.course', string='Course')
    exam_name_line = fields.One2many('exam.name.line', 'exam_id')


class ExamNameLine(models.Model):
    _name = 'exam.name.line'
    _rec_name = 'name'

    course = fields.Many2one('course.course', string='Course')
    name = fields.Char(string="Exam Name")
    status = fields.Boolean("Status")
    description = fields.Text(string="Description")
    exam_id = fields.Many2one('exam.name')

    @api.multi
    def action_create_exam_name_line(self):
        return {
            'name': 'Exam Name',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'exam.name.view',
            'target': 'inline',
        }