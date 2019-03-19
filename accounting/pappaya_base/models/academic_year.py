# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import except_orm
from odoo.exceptions import ValidationError
from datetime import datetime

class AcademicYear(models.Model):
    _name = "academic.year"
    
    @api.constrains('name')
    def check_aca_year_name(self):
        if self.name:
            if len(self.search([('name', '=', (self.name).strip())])) > 1:
                raise ValidationError("Academic Year already exists.")

    @api.constrains('is_active','is_next_academic_year')
    def check_aca_year_is_active(self):
        if self.is_active and not self.is_next_academic_year:
            if len(self.search([('is_active', '=', True)])) > 1:
                raise ValidationError("Active Academic Year is already exists.")
        if self.is_active and self.is_next_academic_year:
            raise ValidationError('Please choose either Active/Next Academic Year option..! ')
    
    @api.constrains('is_next_academic_year')
    def check_aca_year_is_next_academic_year(self):
        if self.is_next_academic_year:
            if len(self.search([('is_next_academic_year', '=', True)])) > 1:
                raise ValidationError("Active Next Academic Year is already exists.")
    
    name = fields.Char('Academic Year', compute='_get_academic_year_name', store=True)
    is_active = fields.Boolean('Is Active?', default=True)
    is_next_academic_year = fields.Boolean('Is Next Academic Year?')
    school_id = fields.Many2one('operating.unit', 'Branch')
    all_branches = fields.Boolean(string='All Branch')
    school_ids = fields.Many2many('operating.unit', string='Branch')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    description = fields.Text(string='Description', size=100)

    @api.onchange('all_branches')
    def _get_all_branch(self):
        self.school_ids = False
        if self.all_branches:
            school_ids = self.env['operating.unit'].search([('type', '=', 'branch')])
            if school_ids:
                self.school_ids = school_ids
            else:
                raise ValidationError('Please configure new Branch..!')

    @api.one
    def update_academic_year(self):
        for rec in self.school_ids:
            if self.is_active:
                rec.write({'active_academic_year_id':self.id})
            if self.is_next_academic_year:
                rec.write({'active_next_academic_year_id': self.id})

    @api.one
    @api.depends('start_date', 'end_date')
    def _get_academic_year_name(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                start_date = str(datetime.strptime(rec.start_date,"%Y-%m-%d").date())
                end_date = str(datetime.strptime(rec.end_date,"%Y-%m-%d").date())
                rec.name = str(start_date.split('-')[0])+ ' - ' +str(end_date.split('-')[0]) 

    @api.model
    def create(self, vals):
        if vals.get('start_date') and vals.get('end_date'):
            if vals.get('start_date') > vals.get('end_date'):
                raise except_orm(_("Please ensure that the End Date is greater than the Start Date."))
        res = super(AcademicYear, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        start_date = vals.get('start_date') if 'start_date' in vals else self.start_date
        end_date = vals.get('end_date') if 'end_date' in vals else self.end_date
        if start_date > end_date:
            raise except_orm(_("Please ensure that the End Date is greater than the Start Date."))
        return super(AcademicYear, self).write(vals)

    @api.multi
    def unlink(self):
        raise ValidationError('Sorry,You are not authorized to delete record')
