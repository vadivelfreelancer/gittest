from odoo import fields, models, api


class CombinationFaculty(models.Model):
    _name = 'combination.faculty'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    combination = fields.Many2one('combination.line', string='Combination')
    exam_branch = fields.Many2one('exam.branch', string='Exam Branch')
    subject = fields.Many2one('subject.line', string='Subject')
    combination_faculty_line = fields.One2many('combination.faculty.line', 'combination_faculty_id')


class CourseGroupBatchLine(models.Model):
    _name = 'combination.faculty.line'

    combination = fields.Many2one('combination.line', string='Combination')
    branch = fields.Many2one("branch.branch", string="Branch")
    course = fields.Many2one('course.course', string='Course')
    employee_name = fields.Many2one('employee.name', string='Employee Name')
    subject = fields.Many2one('subject.line', string='Subject')
    sub_batch = fields.Many2one('subbatch.line',string='')
    status = fields.Selection(string="Status", selection=[('open', 'Open'), ('lock', 'Lock'), ])
    description = fields.Text(string="Description")

    combination_faculty_id = fields.Many2one('combination.faculty')

    @api.multi
    def action_create_combination_faculty(self):
        return {
            'name': 'Combination Faculty',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'combination.faculty.view',
            'target': 'inline',
        }


class ExamBranch(models.Model):
    _name = 'exam.branch'
    _rec_name = 'name'

    name = fields.Char(string='Exam Branch')


class ExamBranch(models.Model):
    _name = 'employee.name'
    _rec_name = 'name'

    name = fields.Char(string='Employee Name')
