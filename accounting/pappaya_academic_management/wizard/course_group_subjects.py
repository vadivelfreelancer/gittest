from odoo import api, fields, models


class CourseGroupBatch(models.TransientModel):
    _name = 'course.group.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    course = fields.Many2one("course.course", string="Course")
    group = fields.Many2one("group.group", string="Group")
    description = fields.Text(string="Description")
    name = fields.Many2one('subject.subject', string="Subject")

    course_group_lines = fields.Many2many('course.group.subject.line')

    @api.model
    def default_get(self, fields):
        res = super(CourseGroupBatch, self).default_get(fields)
        course_group_batch = self.env['course.group.subject.line'].search([])
        res['course_group_lines'] = course_group_batch.ids
        return res