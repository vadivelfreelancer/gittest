# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date
import math

class PappayaApplicantAttachment(models.Model):
    _name = "pappaya.applicant.attachment"
    _inherit = ['mail.thread']
    _rec_name = 'applicant_name'


    company_id = fields.Many2one('res.company',string='Organization',default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    department_id = fields.Many2one('hr.department', string='Department')
    designation_id = fields.Many2one('hr.job', string='Designation')
    aadhaar_no = fields.Char('Aadhaar No', size=12)
    email = fields.Char('E-mail', size=60)
    mobile = fields.Char('Mobile', size=10)
    edu_qualification_ids = fields.Many2many('hr.recruitment.degree', string='Educational Qualification')
    application_id = fields.Many2one('hr.applicant', string='Application')
    applicant_name = fields.Char(related="application_id.partner_name", string="Applicant's Name")
    attachment_line = fields.One2many('pappaya.applicant.attachment.line','attachment_id', string='Attachment Line')
    state = fields.Selection([('draft', 'Draft'), ('verified', 'Verified')], default='draft', string='State')

    def confirm_attachment(self):
        for record in self:
            for line in record.attachment_line:
                if line.is_required and line.state == 'draft':
                    raise ValidationError(_("Please verify required Document: %s ") % line.attachment_name.name)
                # if line.is_required and not line.attachment_file and line.state == 'draft':
                #     raise ValidationError(_("Please verify required Document: %s ") % line.attachment_name.name)
                elif line.attachment_file and not line.is_required and line.state == 'draft':
                    raise ValidationError(_("Please verify Document: %s ") % line.attachment_name.name)
                if line.state == 'draft':
                    line.state = 'verified'
            record.application_id.doc_verified = 'yes'
            record.state = 'verified'

    @api.onchange('branch_id')
    def onchange_branch_id(self):
        for record in self:
            if record.branch_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.branch_id.office_type_id.id)])
                department = []
                for job in job_positions:
                    department.append(job.department_id.id)
                return {'domain': {'department_id': [('id', 'in', department)]}}


class PappayaApplicantAttachmentLine(models.Model):
    _name = "pappaya.applicant.attachment.line"

    attachment_id = fields.Many2one('pappaya.applicant.attachment', string='Attachment')
    attachment_name = fields.Many2one('recruitment.document', string='Document Name')
    #attachment_file = fields.Binary(string='Attachment Upload')
    attachment_file = fields.Many2many('ir.attachment','attachment_applicant_attachment_rel','attach_id','applicant_id', string="Attachment Upload")
    description = fields.Char('Description', size=200)
    is_required = fields.Boolean('Is Required')
    state = fields.Selection([('draft', 'Draft'), ('verified', 'Verified')], default='draft', string='State')
    invisible_button = fields.Boolean(compute='get_invisible_button')

    @api.depends('attachment_file','is_required','state')
    def get_invisible_button(self):
        for record in self:
            invisible_record = False
            if record.state == 'verified':
                invisible_record = True
            elif not record.is_required and not record.attachment_file.ids:
                invisible_record = True
            record.invisible_button = invisible_record


    def verify_attachment(self):
        for record in self:
            if record.is_required and not record.attachment_file:
                    raise ValidationError(_("Please upload required Document: %s ") % record.attachment_name.name)
            if record.attachment_file:
                record.attachment_file.write({'res_model':'hr.applicant',
                                              'res_id':record.attachment_id.application_id.id,
                                              'company_id':record.attachment_id.company_id.id,
                                              'branch_id':record.attachment_id.branch_id.id
                                              })
            record.state = 'verified'
