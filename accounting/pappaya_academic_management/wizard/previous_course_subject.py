from odoo import fields, models, api


class PreviousCourseSubject(models.Model):
    _name = 'previous.course.subject.view'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    previous_course = fields.Many2one('course.course', string='Previous Course')
    pc_subjects = fields.Many2many('pc.subject.line')

    @api.model
    def default_get(self, fields):
        res = super(PreviousCourseSubject, self).default_get(fields)
        pc_subjects = self.env['pc.subject.line'].search([])
        res['pc_subjects'] = pc_subjects.ids
        return res
