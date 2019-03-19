from odoo import fields, models, api


class TopicsView(models.TransientModel):
    _name = 'topics.view'

    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    course = fields.Many2one('course.course', string='Course')
    subject = fields.Many2one('subject.line')
    topics = fields.Many2many('topics.line')

    @api.model
    def default_get(self, fields):
        res = super(TopicsView, self).default_get(fields)
        topics = self.env['topics.line'].search([])
        res['topics'] = topics.ids
        return res
