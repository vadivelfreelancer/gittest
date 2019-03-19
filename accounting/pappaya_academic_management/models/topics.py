from odoo import fields, models


class PappayaTopics(models.Model):
    _name = 'pappaya.topics'
    _rec_name = 'topic'

    # academic_year = fields.Many2one('academic.year', 'Academic Year')
    # institution_type = fields.Selection(string="Type",
    #                                     selection=[('school', 'School'), ('college', 'College'), ])
    course = fields.Many2one('pappaya.course', string='Course')
    subject = fields.Many2one('pappaya.subject', 'Subject')
    topic = fields.Char('Topic')
    description = fields.Text(string='Description')


class Course(models.Model):
    _name = 'course.course'
    _rec_name = 'name'

    name = fields.Char(string='Course', required=True)
    subject_ids = fields.Many2many('subject.line', string='Subject')
    # subject_topic = fields.One2many("subject.topics", "course_id", string="Topics")


class TopicsLine(models.Model):
    _name = 'topics.line'

    name = fields.Char(string='Name')
    course = fields.Many2one('pappaya.course', string='Course')
    subject = fields.Many2one('subject.line')
    description = fields.Text(string='Description')
    topic_inverse = fields.Many2one('pappaya.topics')
