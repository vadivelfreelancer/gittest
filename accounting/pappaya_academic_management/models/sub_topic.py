from odoo import fields, models, api


class SubTopic(models.Model):
    _name = 'sub.topic'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    course = fields.Many2one("course.course", string="Course")
    subject = fields.Many2one("subject.subject", string="Subject")
    topic = fields.Many2one('pappaya.topics',string="Topic")
    subtopic_type = fields.One2many('sub.topic.line','sub_topic_id')


class SubTopicLine(models.Model):
    _name = 'sub.topic.line'
    _rec_name = 'name'

    name = fields.Char(string="Sub Topic Name")
    course = fields.Many2one("course.course", string="Course")
    subject = fields.Many2one("subject.subject", string="Subject")
    topic = fields.Many2one('pappaya.topics', string="Topic")

    sub_topic_id = fields.Many2one("sub.topic")
