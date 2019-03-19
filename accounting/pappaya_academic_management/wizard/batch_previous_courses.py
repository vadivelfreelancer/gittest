from odoo import fields,models,api


class BatchPreviousCourses(models.Model):

    _name = 'batch.previous.course'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    previous_id = fields.Many2one('previous.course', 'Previous Courses')
    previous_courses = fields.One2many('batch.courses.line', 'batch_id')

    @api.model
    def default_get(self, fields):
        res = super(BatchPreviousCourses, self).default_get(fields)
        courses = [(0, 0, {
            'name': '',
            'is_external': '',
            'result_entry': '',
            'description': '',
            'previous_id': self.id,
            })for x in range(0, 10)]
        res['previous_courses'] = courses
        return res

    @api.multi
    def action_create_courses(self):
        course_obj = self.env['courses.line']
        for rec in self.previous_courses:
            if rec.name or rec.is_external or rec.result_entry or rec.description:
                course_obj.create({
                    'name': rec.name,
                    'is_external': rec.is_external,
                    'result_entry': rec.result_entry,
                    'description': rec.description,
                    'previous_id': self.previous_id.id,
                })
        return {
            'name': 'Previous Course',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'previous.view',
            'target': 'inline',
        }


class BatchCoursesLine(models.Model):
    _name = 'batch.courses.line'

    name = fields.Char(string="Course")
    is_external = fields.Boolean(string="External Exam")
    description = fields.Text(string="Description")
    result_entry = fields.Selection(string="Result Entry", selection=[('manual', 'Manual'), ('results', 'Results'), ])
    batch_id = fields.Many2one('batch.previous.course')