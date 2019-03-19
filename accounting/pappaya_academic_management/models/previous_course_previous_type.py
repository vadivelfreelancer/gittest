from odoo import fields, models, api


class PreviousCoursePreviousType(models.Model):
    _name = 'previous.course.type'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    previous_course_pre_type = fields.One2many('previous.course.type.line', 'previous_course_pre_id')


class PreviousCourseTypeLine(models.Model):
    _name = 'previous.course.type.line'

    course = fields.Many2one("course.course", string="Course")
    previous_course = fields.Many2one('courses.line',string="Previous Course")
    description = fields.Text(string="Description")
    pre_type = fields.Many2one('previous.line', string="Previous Course Type")
    previous_course_pre_id = fields.Many2one("previous.course.type")

    @api.multi
    def action_create_previous_course_previous_type(self):
        return {
            'name': 'Previous Course Previous Type',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'previous.course.previous.view',
            'target': 'inline',
        }
