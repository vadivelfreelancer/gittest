from odoo import fields,models,api


class SubTopicView(models.TransientModel):
    _name = 'subtopic.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    course = fields.Many2one("course.course", string="Course")
    subject = fields.Many2one("subject.subject", string="Subject")
    topic = fields.Many2one('pappaya.topics', string="Topic")
    sub_topic_lines = fields.Many2many('sub.topic.line')

    @api.model
    def default_get(self, fields):
        res = super(SubTopicView, self).default_get(fields)
        subtopic = self.env['sub.topic.line'].search([])
        res['sub_topic_lines'] = subtopic.ids
        return res


