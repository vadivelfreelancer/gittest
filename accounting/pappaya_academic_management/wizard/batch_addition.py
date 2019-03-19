from odoo import fields, models, api


class BatchSubject(models.TransientModel):
    _name = 'batch.subject'

    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type", selection=[('school', 'School'), ('college', 'College')])
    subject_id = fields.Many2one('subject.subject', 'Subject')
    batch_subjects = fields.One2many('batch.subjects.line', 'batch_id')

    @api.model
    def default_get(self, fields):
        res = super(BatchSubject, self).default_get(fields)
        subjects = [(0, 0, {
            'name': '',
            'description': '',
            'subject_id': self.id
        }) for x in range(0, 10)]
        res['batch_subjects'] = subjects
        return res

    @api.multi
    def action_create_subjects(self):
        sub_line_obj = self.env['subject.line']
        for rec in self.batch_subjects:
            if not self.subject_id:
                sub_obj = self.env['subject.subject'].search([('academic_year', '=', self.academic_year.id),
                                                              ('institution_type', '=', self.institution_type)],
                                                             limit=1)
                if sub_obj:
                    subject_id = sub_obj.id
                else:
                    subject_id = self.env['subject.subject'].create({
                        'academic_year': self.academic_year.id,
                        'institution_type': self.institution_type
                    }).id
            if rec.name or rec.description:
                sub_line_obj.create({
                    'name': rec.name,
                    'description': rec.description,
                    'subject_id': subject_id
                })
        return {
            'name': 'Subjects',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'subjects.view',
            'target': 'inline',
        }


class BatchSubjectsLine(models.TransientModel):
    _name = 'batch.subjects.line'

    name = fields.Char()
    description = fields.Text()
    batch_id = fields.Many2one('batch.subject')


class BatchTracks(models.TransientModel):
    _name = 'batch.tracks'

    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type", selection=[('school', 'School'), ('college', 'College')])
    tracks_id = fields.Many2one('pappaya.tracks', 'Subject')
    batch_tracks = fields.One2many('batch.tracks.line', 'batch_id')

    @api.model
    def default_get(self, fields):
        res = super(BatchTracks, self).default_get(fields)
        tracks = [(0, 0, {
            'name': '',
            'description': '',
            'tracks_id': self.id
        }) for x in range(0, 10)]
        res['batch_tracks'] = tracks
        return res

    @api.multi
    def action_create_tracks(self):
        tracks__obj = self.env['tracks.line']
        for rec in self.batch_tracks:
            if rec.name or rec.description:
                tracks__obj.create({
                    'name': rec.name,
                    'description': rec.description,
                    'tracks_id': self.tracks_id.id
                })
        return {
            'name': 'Tracks',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'tracks.view',
            'target': 'inline',
        }


class BatchTracksLine(models.TransientModel):
    _name = 'batch.tracks.line'

    name = fields.Char()
    description = fields.Text()
    batch_id = fields.Many2one('batch.tracks')


class CourseTopic(models.TransientModel):
    _name = 'batch.course.topic'

    course_id = fields.Many2one("course.course", string="Course")
    subject_id = fields.Many2one("subject.line", string="Subject")
    topics_id = fields.Many2one('pappaya.topics', 'Topic')
    batch_topics = fields.One2many('batch.topic.line', 'batch_id')

    @api.model
    def default_get(self, fields):
        res = super(CourseTopic, self).default_get(fields)
        topics = [(0, 0, {
            'name': '',
            'description': '',
            'batch_id': self.id
        }) for x in range(0, 10)]
        res['batch_topics'] = topics
        return res

    @api.multi
    def action_create_topics(self):
        topics__obj = self.env['topics.line']
        for rec in self.batch_topics:
            if rec.name or rec.description:
                topics__obj.create({
                    'name': rec.name,
                    'description': rec.description,
                    'course': self.course_id.id,
                    'subject': self.subject_id.id,
                    'topic_inverse': self.topics_id.id
                })


class BatchTopicLIne(models.TransientModel):
    _name = 'batch.topic.line'

    name = fields.Char()
    description = fields.Text()
    batch_id = fields.Many2one('batch.course.topic')
    

class BatchPreviousType(models.TransientModel):
    _name = 'batch.previous.type'

    batch_subjects = fields.One2many('batch.previous.type.line', 'batch_id')

    @api.model
    def default_get(self, fields):
        res = super(BatchPreviousType, self).default_get(fields)
        subjects = [(0, 0, {
            'name': '',
            'description': '',
            'batch_id': self.id
        }) for x in range(0, 10)]
        res['batch_subjects'] = subjects
        return res

    @api.multi
    def action_create_subjects(self):
        sub_line_obj = self.env['previous.line']
        for rec in self.batch_subjects:
            if rec.name or rec.description:
                sub_line_obj.create({
                    'name': rec.name,
                    'description': rec.description,
                })
        return {
            'name': 'Previous Type',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'previous.type.view',
            'target': 'inline',
        }


class BatchPreviewTypeLine(models.TransientModel):
    _name = 'batch.previous.type.line'

    name = fields.Char()
    description = fields.Text()
    batch_id = fields.Many2one('batch.previous.type')


class BatchCombinationCombination(models.TransientModel):
    _name = 'batch.combination.view'

    group = fields.Many2one('pappaya.group', 'Group')
    exam_type = fields.Many2one('exam.type', 'Exam Type')
    course = fields.Many2one('course.course', string='Course')
    batch_subjects = fields.One2many('batch.combination.view.line', 'batch_id')

    @api.model
    def default_get(self, fields):
        res = super(BatchCombinationCombination, self).default_get(fields)
        subjects = [(0, 0, {
            'name': '',
            'description': '',
            'batch_id': self.id
        }) for x in range(0, 10)]
        res['batch_subjects'] = subjects
        return res

    @api.multi
    def action_create_subjects(self):
        sub_line_obj = self.env['combination.line']
        for rec in self.batch_subjects:
            if rec.name or rec.description:
                sub_line_obj.create({
                    'name': rec.name,
                    'description': rec.description,
                    'group': self.group.id,
                    'exam_type': self.exam_type.id,
                    'course': self.course.id,
                })
        return {
            'name': 'Combinations',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'combination.view',
            'target': 'inline',
        }


class BatchCominationViewLine(models.TransientModel):
    _name = 'batch.combination.view.line'

    name = fields.Char()
    description = fields.Text(string="Description")
    batch_id = fields.Many2one('batch.combination.view.line')


class BatchSubBatch(models.TransientModel):
    _name = 'batch.sub.batch.view'

    batch_subbatches = fields.One2many('batch.sub.batch.line', 'batch_id')

    @api.model
    def default_get(self, fields):
        res = super(BatchSubBatch, self).default_get(fields)
        subjects = [(0, 0, {
            'name': '',
            'description': '',
            'batch_id': self.id
        }) for x in range(0, 10)]
        res['batch_subbatches'] = subjects
        return res

    @api.multi
    def action_create_subjects(self):
        sub_line_obj = self.env['subbatch.line']
        for rec in self.batch_subbatches:
            if rec.name or rec.description:
                sub_line_obj.create({
                    'name': rec.name,
                    'description': rec.description,
                })
        return {
            'name': 'Sub Batch',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'sub.batch.view',
            'target': 'inline',
        }


class BatchSubBAtchLine(models.TransientModel):
    _name = 'batch.sub.batch.line'

    name = fields.Char()
    description = fields.Text(string="Description")
    batch_id = fields.Many2one('batch.sub.batch.view')


class AreaBatch(models.TransientModel):
    _name = 'area.batch.view'

    area_batches = fields.One2many('area.batch.line', 'area_batch_id')

    @api.model
    def default_get(self, fields):
        res = super(AreaBatch, self).default_get(fields)
        area = [(0, 0, {
            'name': '',
            'description': '',
            'area_batch_id': self.id
        }) for x in range(0, 10)]
        res['area_batches'] = area
        return res

    @api.multi
    def action_create_area(self):
        area_line_obj = self.env['area.line']
        for rec in self.area_batches:
            if rec.name or rec.description:
                area_line_obj.create({
                    'name': rec.name,
                    'description': rec.description,
                })
        return {
            'name': 'Area',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'area.view',
            'target': 'inline',
        }


class AreaBatchLine(models.TransientModel):
    _name = 'area.batch.line'

    name = fields.Char(string="Area")
    description = fields.Text(string="Description")
    area_batch_id = fields.Many2one('area.batch.view')


class SubTopicBatch(models.TransientModel):
    _name = 'sub.topic.batch.view'

    course = fields.Many2one("course.course", string="Course")
    subject = fields.Many2one("subject.subject", string="Subject")
    topic = fields.Many2one('pappaya.topics', string="Topic")
    description = fields.Text(string="Description")
    sub_topic_batches = fields.One2many('sub.topic.batch.line', 'sub_topic_batch_id')

    @api.model
    def default_get(self, fields):
        res = super(SubTopicBatch, self).default_get(fields)
        subtopic = [(0, 0, {
            'name': '',
            'topic_name': '',
            'subject_name': '',
            'course_name': '',

            'sub_topic_batch_id': self.id
        }) for x in range(0, 10)]
        res['sub_topic_batches'] = subtopic
        return res

    @api.multi
    def action_create_subtopic(self):
        sub_topic_obj = self.env['sub.topic.line']
        for rec in self.sub_topic_batches:
            if rec.name or rec.topic_name or rec.subject_name or rec.course_name:
                sub_topic_obj.create({
                    'name': rec.name,
                    'topic_name': rec.topic_name,
                    'subject_name': rec.subject_name,
                    'course_name': rec.course_name,
                })
        return {
            'name': 'Area',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'subtopic.view',
            'target': 'inline',
        }


class SubTopicBatchLine(models.TransientModel):
    _name = 'sub.topic.batch.line'

    name = fields.Char(string="Sub Topic Name")
    topic_name = fields.Char(string="Topic Name")
    subject_name = fields.Char(string="Subject")
    course_name = fields.Char(string="Course Name")
    description = fields.Text(string="Description")

    sub_topic_batch_id = fields.Many2one('sub.topic.batch.view')


class SpecialBatch(models.TransientModel):
    _name = 'batch.special.batch.view'

    batch_subbatches = fields.One2many('batch.special.batch.line', 'batch_id')

    @api.model
    def default_get(self, fields):
        res = super(SpecialBatch, self).default_get(fields)
        subjects = [(0, 0, {
            'name': '',
            'description': '',
            'batch_id': self.id
        }) for x in range(0, 10)]
        res['batch_subbatches'] = subjects
        return res

    @api.multi
    def action_create_subjects(self):
        sub_line_obj = self.env['special.batch.line']
        for rec in self.batch_subbatches:
            if rec.name or rec.description:
                sub_line_obj.create({
                    'name': rec.name,
                    'description': rec.description,
                })
        return {
            'name': 'Sub Batch',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'special.batch.view',
            'target': 'inline',
        }


class BatchSpecialBatchLine(models.TransientModel):
    _name = 'batch.special.batch.line'

    name = fields.Char()
    description = fields.Text(string="Description")
    batch_id = fields.Many2one('batch.special.batch.line')


class UniversityBatch(models.TransientModel):
    _name = 'university.batch.view'

    university_batches = fields.One2many('university.batch.line', 'university_batch_id')

    @api.model
    def default_get(self, fields):
        res = super(UniversityBatch, self).default_get(fields)
        university = [(0, 0, {
            'name': '',
            'description': '',
            'university_batch_id': self.id
        }) for x in range(0, 10)]
        res['university_batches'] = university
        return res

    @api.multi
    def action_create_subjects(self):
        university_line_obj = self.env['university.line']
        for rec in self.university_batches:
            if rec.name or rec.description:
                university_line_obj.create({
                    'name': rec.name,
                    'description': rec.description,
                })


class UniversityBatchLine(models.TransientModel):
    _name = 'university.batch.line'

    name = fields.Char(string="University")
    description = fields.Text(string="Description")
    university_batch_id = fields.Many2one('university.batch.view')


class NewSubBatch(models.TransientModel):
    _name = 'newsubbatch.batch.view'
    sub_batch = fields.Many2one("sub.batch", string="Sub Batch")
    new_sub_batches = fields.One2many('newsubbatch.batch.line', 'newsubbatch_batch_id')

    @api.model
    def default_get(self, fields):
        res = super(NewSubBatch, self).default_get(fields)
        newsubbatch = [(0, 0, {
            'name': '',
            'sub_batch': '',
            'description': '',
            'newsubbatch_batch_id': self.id
        }) for x in range(0, 10)]
        res['new_sub_batches'] = newsubbatch
        return res

    @api.multi
    def action_create_new_sub_batch(self):
        new_sub_batches_line_obj = self.env['new.subbatch.line']
        for rec in self.new_sub_batches:
            if rec.name or rec.description :
                new_sub_batches_line_obj.create({
                    'name': rec.name,
                    'description': rec.description,
                })
        return {
            'name': 'New Sub Batch',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'new.subbatch.view',
            'target': 'inline',
        }


class NewSubBatchLine(models.TransientModel):
    _name = 'newsubbatch.batch.line'
    name = fields.Char(string="New Sub Batch")
    description = fields.Text(string="Description")
    newsubbatch_batch_id = fields.Many2one('newsubbatch.batch.view')


class SubSubBatchBatch(models.TransientModel):
    _name = 'sub.sub.batch.batch.view'

    sub_sub_batch_batches = fields.One2many('sub.sub.batch.batch.line', 'sub_sub_batch_batch_id')

    @api.model
    def default_get(self, fields):
        res = super(SubSubBatchBatch, self).default_get(fields)
        sub_sub_batch = [(0, 0, {
            'name': '',
            'description': '',
            'sub_sub_batch_batch_id': self.id
        }) for x in range(0, 10)]
        res['sub_sub_batch_batches'] = sub_sub_batch
        return res

    @api.multi
    def action_create_sub_sub_batch(self):
        sub_sub_batch_line_obj = self.env['sub.sub.batch.line']
        for rec in self.sub_sub_batch_batches:
            if rec.name or rec.description:
                sub_sub_batch_line_obj.create({
                    'name': rec.name,
                    'description': rec.description,
                })
        return {
            'name': 'Sub Sub Batch',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'sub.sub.batch.view',
            'target': 'inline',
        }


class SubSubBatchBatchLine(models.TransientModel):
    _name = 'sub.sub.batch.batch.line'

    name = fields.Char(string="Sub Sub Batch")
    description = fields.Text(string="Description")
    sub_sub_batch_batch_id = fields.Many2one('sub.sub.batch.batch.view')


class ExamNameBatch(models.TransientModel):
    _name = 'exam.name.batch.view'

    exam_name_batches = fields.One2many('exam.name.batch.line', 'exam_name_batch_id')

    @api.model
    def default_get(self, fields):
        res = super(ExamNameBatch, self).default_get(fields)
        exam_name = [(0, 0, {
            'name': '',
            'description': '',
            'exam_name_batch_id': self.id
        }) for x in range(0, 10)]
        res['exam_name_batches'] = exam_name
        return res

    @api.multi
    def action_create_exam_name(self):
        exam_name_line_obj = self.env['exam.name.line']
        for rec in self.exam_name_batches:
            if rec.name or rec.description:
                exam_name_line_obj.create({
                    'name': rec.name,
                    'description': rec.description,
                    'course': rec.course.id,
                    'status': rec.status,
                })
        return {
            'name': 'Exam Name',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'exam.name.view',
            'target': 'inline',
        }


class ExamNameBatchLine(models.TransientModel):
    _name = 'exam.name.batch.line'

    name = fields.Char(string="Exam Name")
    description = fields.Text(string="Description")
    course = fields.Many2one('course.course', string='Course')
    status = fields.Boolean("Status")
    exam_name_batch_id = fields.Many2one('exam.name.batch.view')


class CourseGroupBatch(models.TransientModel):
    _name = 'course.group.batch.view'
    course = fields.Many2one("course.course", string="Course")
    group = fields.Many2one("pappaya.group", string="Group")

    course_group_batches = fields.One2many('course.group.batch.line', 'course_group_batch_id')

    @api.model
    def default_get(self, fields):
        res = super(CourseGroupBatch, self).default_get(fields)
        course_group = [(0, 0, {
            'name': '',
            'description': '',
            'course_group_batch_id': self.id
        }) for x in range(0, 10)]
        res['course_group_batches'] = course_group
        return res

    @api.multi
    def action_create_course_group_subjects(self):
        course_group_line_obj = self.env['course.group.subject.line']
        for rec in self.course_group_batches:
            if rec.name or rec.description:
                course_group_line_obj.create({
                    'name': rec.name,
                    'description': rec.description,
                })
        return {
            'name': 'Exam Name',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'exam.course.view',
            'target': 'inline',
        }


class CourseGroupBatchLine(models.TransientModel):
    _name = 'course.group.batch.line'
    name = fields.Many2one('subject.subject', string="Subject")
    description = fields.Text(string="Description")

    course_group_batch_id = fields.Many2one('course.group.batch.view')


class PreviousCourseTypeBatch(models.TransientModel):
    _name = 'previous.course.type.batch.view'
    course = fields.Many2one("course.course", string="Course")

    previous_course_type_batches = fields.One2many('previous.course.type.batch.line', 'previous_course_type_batch_id')

    @api.model
    def default_get(self, fields):
        res = super(PreviousCourseTypeBatch, self).default_get(fields)
        previous_type = [(0, 0, {
            'name': '',
            'description': '',
            'previous_course': '',
            'pre_type': '',
            'previous_course_type_batch_id': self.id
        }) for x in range(0, 10)]
        res['previous_course_type_batches'] = previous_type
        return res

    @api.multi
    def action_create_previous_course_subjects(self):
        previous_course_subjects_line_obj = self.env['course.group.subject.line']
        for rec in self.previous_course_type_batches:
            if rec.name or rec.description or rec.previous_course or rec.pre_type:
                previous_course_subjects_line_obj.create({
                    'name': rec.name,
                    'previous_course': rec.previous_course,
                    'pre_type': rec.pre_type,
                    'description': rec.description,
                })
        return {
            'name': 'Previous Course Previous Type',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'exam.course.view',
            'target': 'inline',
        }


class PreviousCourseTypeBatchLine(models.TransientModel):
    _name = 'previous.course.type.batch.line'

    previous_course = fields.Many2one('courses.line',string="Previous Course")
    pre_type = fields.Many2one('previous.line', string="Previous Course Type")
    description = fields.Text(string="Description")

    previous_course_type_batch_id = fields.Many2one('previous.course.type.batch.view')

class PcSubjectBatch(models.TransientModel):
    _name = 'pc.subject.batch.view'

    previous_course = fields.Many2one('courses.line', string='Previous Course')
    pc_subject_batches = fields.One2many('pc.subject.batch.line', 'pc_subject_batch_id')

    @api.model
    def default_get(self, fields):
        res = super(PcSubjectBatch, self).default_get(fields)
        pc_subject_batches = [(0, 0, {
            'description': '',
            'pc_subject_batch_id': self.id
        }) for x in range(0, 10)]
        res['pc_subject_batches'] = pc_subject_batches
        return res

    @api.multi
    def action_create_previous_course_subject(self):
        pc_subject_line_obj = self.env['pc.subject.line']
        for rec in self.pc_subject_batches:
            if rec.subject or rec.description or rec.previous_course or rec.marks:
                pc_subject_line_obj.create({
                    'subject': rec.subject.id,
                    'previous_course': rec.previous_course.id,
                    'marks': rec.marks,
                    'description': rec.description,
                })
        return {
            'name': 'Previous Course Subjects',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'previous.course.subject.view',
            'target': 'inline',
        }


class PcSubjectBatchLine(models.TransientModel):
    _name = 'pc.subject.batch.line'

    subject = fields.Many2one('subject.line', string="Subject")
    previous_course = fields.Many2one('courses.line', string='Previous Course')
    marks = fields.Integer('Marks')
    description = fields.Text(string="Description")
    pc_subject_batch_id = fields.Many2one('pc.subject.batch.view')


class LanguageMappingBatch(models.TransientModel):
    _name = 'language.mapping.batch.view'

    subject = fields.Many2one('subject.line', string="Subject")
    lang_mapping_batches = fields.One2many('language.mapping.batch.line', 'lang_mapping_batch_id')

    @api.model
    def default_get(self, fields):
        res = super(LanguageMappingBatch, self).default_get(fields)
        lang_mapping_batches = [(0, 0, {
            'description': '',
            'pc_subject_batch_id': self.id
        }) for x in range(0, 10)]
        res['lang_mapping_batches'] = lang_mapping_batches
        return res

    @api.multi
    def action_create_language_mapping(self):
        lang_mapping_line_obj = self.env['language.mapping.line']
        for rec in self.lang_mapping_batches:
            if rec.subject or rec.description:
                lang_mapping_line_obj.create({
                    'subject': rec.subject.id,
                    'description': rec.description,
                })
        return {
            'name': 'Subject Mapping Wise Details',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'language.mapping.view',
            'target': 'inline',
        }


class LanguageMappingBatchLine(models.TransientModel):
    _name = 'language.mapping.batch.line'

    subject = fields.Many2one('subject.line', string="Subject")
    description = fields.Text(string="Description")
    lang_mapping_batch_id = fields.Many2one('language.mapping.batch.view')


class HolidayEntryBatch(models.TransientModel):
    _name = 'holiday.entry.batch.view'

    holiday_entry_batches = fields.One2many('holiday.entry.batch.line', 'holiday_entry_batch_id')

    @api.model
    def default_get(self, fields):
        res = super(HolidayEntryBatch, self).default_get(fields)
        holiday_entry_batches = [(0, 0, {
            'description': '',
            'holiday_name': '',
            'holiday_entry_batch_id': self.id
        }) for x in range(0, 10)]
        res['holiday_entry_batches'] = holiday_entry_batches
        return res

    @api.multi
    def action_create_holiday_entry(self):
        holiday_entry_obj = self.env['holiday.entry.line']
        for rec in self.holiday_entry_batches:
            if rec.holiday_name or rec.description:
                holiday_entry_obj.create({
                    'holiday_name': rec.holiday_name.id,
                    'description': rec.description,
                })
        return {
            'name': 'Holiday Entry Details',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'holiday.entry.view',
            'target': 'inline',
        }


class HolidayEntryBatchLine(models.TransientModel):
    _name = 'holiday.entry.batch.line'

    holiday_name = fields.Char(string="Holiday Name")
    description = fields.Text(string="Description")
    holiday_entry_batch_id = fields.Many2one('holiday.entry.batch.view')


class AttendanceTypeBatch(models.TransientModel):
    _name = 'attendance.type.batch.view'

    attendance_type_batches = fields.One2many('attendance.type.batch.line', 'attendance_batch_id')

    @api.model
    def default_get(self, fields):
        res = super(AttendanceTypeBatch, self).default_get(fields)
        attendance_type_batches = [(0, 0, {
            'attendance_type': '',
            'description': '',
            'period_from': '',
            'period_to': '',
            'attendance_batch_id': self.id
        }) for x in range(0, 10)]
        res['attendance_type_batches'] = attendance_type_batches
        return res

    @api.multi
    def action_create_attendance_type(self):
        attendance_type_obj = self.env['attendance.type.line']
        for rec in self.attendance_type_batches:
            if rec.attendance_type or rec.description or rec.period_from or rec.period_to:
                attendance_type_obj.create({
                    'attendance_type': rec.attendance_type,
                    'description': rec.description,
                    'period_from': rec.period_from,
                    'period_to': rec.period_to,
                })
        return {
            'name': 'Attendance Type Details',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'attendance.type.view',
            'target': 'inline',
        }


class AttendanceTypeBatchLine(models.TransientModel):
    _name = 'attendance.type.batch.line'

    attendance_type = fields.Char(string="Attendance Type")
    description = fields.Text(string="Description")
    period_from = fields.Char(string="Period From")
    period_to = fields.Char(string="Period To")
    attendance_batch_id = fields.Many2one('attendance.type.batch.view')


class AttendanceRemarkBatch(models.TransientModel):
    _name = 'attendance.remark.batch.view'

    attendance_remark_batches = fields.One2many('attendance.remark.batch.line', 'attendance_remark_batch_id')

    @api.model
    def default_get(self, fields):
        res = super(AttendanceRemarkBatch, self).default_get(fields)
        attendance_remark_batches = [(0, 0, {
            'attendance_remark': '',
            'remark_code': '',
            'attendance_remark_batch_id': self.id
        }) for x in range(0, 10)]
        res['attendance_remark_batches'] = attendance_remark_batches
        return res

    @api.multi
    def action_create_attendance_remark(self):
        attendance_remark_obj = self.env['attendance.type.line']
        for rec in self.attendance_remark_batches:
            if rec.attendance_remark or rec.remark_code:
                attendance_remark_obj.create({
                    'attendance_remark': rec.attendance_remark,
                    'remark_code': rec.remark_code,
                })
        return {
            'name': 'Attendance Type Details',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'attendance.remark.view',
            'target': 'inline',
        }


class AttendanceRemarkBatchLine(models.TransientModel):
    _name = 'attendance.remark.batch.line'

    attendance_remark = fields.Char(string="Attendance Remark")
    remark_code = fields.Char(string="Remark Code")
    attendance_remark_batch_id = fields.Many2one('attendance.type.batch.view')
