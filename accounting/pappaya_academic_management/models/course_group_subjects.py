from odoo import fields, models, api


class CourseGroupSubjects(models.Model):
    _name = 'course.group.subjects'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    course = fields.Many2one("course.course", string="Course")
    group = fields.Many2one("group.group", string="Group")

    course_group_subject_type = fields.One2many('course.group.subject.line', 'course_group_subject_id')


class CourseGroupSubjectLine(models.Model):
    _name = 'course.group.subject.line'
    _rec_name = 'name'

    name = fields.Many2one('subject.subject', string="Subject")
    course = fields.Many2one("course.course", string="Course")
    group = fields.Many2one("group.group", string="Group")
    description = fields.Text(string="Description")
    course_group_subject_id = fields.Many2one("course.group.subjects")

    @api.multi
    def action_create_course_group(self):
        return {
            'name': 'Course Group Subject',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'course.group.view',
            'target': 'inline',
        }