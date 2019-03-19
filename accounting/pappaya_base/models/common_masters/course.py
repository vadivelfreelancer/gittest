# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PappayaCourse(models.Model):
    _name = 'pappaya.course'

    name = fields.Char('Course Name', size=124)
    segment_id = fields.Many2one('pappaya.segment', 'Segment')
    academic_year = fields.Many2one('academic.year', 'Academic Year',
                                    default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    zone_id = fields.Many2one('operating.unit', 'Zone')
    company_id = fields.Many2one('res.company', string='Organization', default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('operating.unit', string='Branch', domain=[('type', '=', 'branch')])
    # office_type_id = fields.Many2one('pappaya.office.type', string="Office Type")
    description = fields.Text('Description', size=150)
    # course_provider_id = fields.Many2many(comodel_name='operating.unit', string='Apex/Entity',
    #                                      domain=[('type', '=', 'entity')])
    show_gst = fields.Boolean('GST ?')
    cgst = fields.Integer('CGST %', size=5)
    sgst = fields.Integer('SGST %', size=5)
    final_cgst = fields.Char('CGST %', size=5)
    final_sgst = fields.Char('SGST %', size=5)
    is_two_year = fields.Boolean('Is Two Year')
    is_capacity = fields.Boolean('Is Capacity')
    is_minfee_lock = fields.Boolean('Is Minfee Lock')
    tc_name = fields.Char('TC Name', size=150)
    tc_status = fields.Char('TC Status', size=50)
    cou_name = fields.Char('Cou Name', size=150)
    short_name = fields.Char('Short Name', size=15)
    prev_clgslno = fields.Char('Prev College Sl No.', size=15)
    clg_slno = fields.Char('College Sl No.', size=15)
    type = fields.Selection(
        [('short_term', 'Short Term'), ('long_term', 'Long Term'), ('coaching_centre', 'Coaching Centre')],
        string='Type')
    duration = fields.Char(string='Duration', size=100)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        self.check_dates

    @api.constrains('start_date', 'end_date')
    def check_dates(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError('Start Date should be less than End Date..!')

    #     @api.constrains('sgst')
    #     def check_sgst(self):
    #         self.validate_sgst(self.sgst)
    #
    #     @api.constrains('cgst')
    #     def check_cgst(self):
    #         self.validate_cgst(self.cgst)

    #     def validate_sgst(self, sgst):
    #         if sgst <= 0 and self.course_provider_id.is_gst_applicable:
    #             raise ValidationError("SGST should not be 0 or negative value.")
    #
    #     def validate_cgst(self, cgst):
    #         if cgst <= 0 and self.course_provider_id.is_gst_applicable:
    #             raise ValidationError("CGST should not be 0 or negative value.")

    #     @api.onchange('sgst')
    #     def onchange_sgst(self):
    #         if self.sgst:
    #             self.validate_sgst(self.sgst)
    #
    #     @api.onchange('cgst')
    #     def onchange_cgst(self):
    #         if self.cgst:
    #             self.validate_cgst(self.cgst)

    #     @api.onchange('course_provider_id')
    #     def onchange_course_provider_id(self):
    #         if self.course_provider_id:
    #             self.show_gst = True if self.course_provider_id.is_gst_applicable else False
    #             if self.show_gst:
    #                 self.sgst = 1; self.cgst = 1

    def _validate_vals(self, vals):
        #         if 'sgst' in vals.keys() and vals.get('sgst'):
        #             self.validate_sgst(vals.get('sgst'))
        #             vals.update({'final_sgst': vals.get('sgst')})
        #         if 'cgst' in vals.keys() and vals.get('cgst'):
        #             self.validate_cgst(vals.get('cgst'))
        #             vals.update({'final_cgst': vals.get('cgst')})
        #
        if 'name' in vals.keys() and vals.get('name'):
            self.env['res.company']._validate_name(vals.get('name'))
        return True

    @api.model
    def create(self, vals):
        self._validate_vals(vals)
        res = super(PappayaCourse, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        self._validate_vals(vals)
        return super(PappayaCourse, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name)])) > 1:
            raise ValidationError("Course already exists")
