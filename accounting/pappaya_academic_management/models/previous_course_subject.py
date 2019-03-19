from odoo import fields, models, api


class PreviousCourseSubject(models.Model):
    _name = 'previous.course.subject'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    previous_course = fields.Many2one('course.course', string='Previous Course')
    pc_subjects = fields.One2many('pc.subject.line', 'pc_subject_id')


class PcSubjectLine(models.Model):
    _name = 'pc.subject.line'

    subject = fields.Many2one('subject.line', string="Subject")
    previous_course = fields.Many2one('course.course', string='Previous Course')
    marks = fields.Integer('Marks')
    description = fields.Text(string="Description")
    pc_subject_id = fields.Many2one('previous.course.subject')

    @api.multi
    def action_create_pc_subject_line(self):
        return {
            'name': 'Previous Course Subjects',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'previous.course.subject.view',
            'target': 'inline',
        }