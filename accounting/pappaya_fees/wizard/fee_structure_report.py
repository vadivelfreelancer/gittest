# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
import xlwt
#import cStringIO
import base64
from odoo.http import request
from datetime import datetime, date
from io import StringIO
from datetime import date
import datetime
from datetime import timedelta
import pytz
import os
from PIL import Image
from xlwt import *


class FeeStructureReport(models.TransientModel):
    _name = 'fee.structure.report'

    school_ids = fields.Many2many('operating.unit','school_fee_structure_report_rel','company_id','school_id', string='Branch')
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))

    @api.multi
    def get_school_header(self):
        school_list = []
        if (len(self.school_ids) == 1):
            vals = {}
            vals['school_id'] = self.school_ids.name
            vals['logo'] = self.school_ids.logo if self.school_ids.logo else ''
            vals['street'] = self.school_ids.street if self.school_ids.street else ''
            vals['street2'] = self.school_ids.street2 if self.school_ids.street2 else ''
            vals['city'] = self.school_ids.city if self.school_ids.city else ''
            vals['zip'] = self.school_ids.zip if self.school_ids.zip else ''
            vals['phone'] = self.school_ids.phone if self.school_ids.phone else ''
            vals['fax'] = self.school_ids.fax_id if self.school_ids.fax_id else ''
            vals['email'] = self.school_ids.email if self.school_ids.email else ''
            vals['website'] = self.school_ids.website if self.school_ids.website else ''
            school_list.append(vals)
        return school_list

    @api.multi
    def get_school(self):
        school_list = []
        if len(self.school_ids) > 1:
            sc_list = ''
            for record in self.school_ids:
                sc_list += str(record.name) + ', '
            vals = {}
            vals['school_id'] = sc_list[:-2]
            school_list.append(vals)
        if not self.school_ids:
            soc_list = ''
            obj = self.env['res.company'].sudo().search([('type', '=', 'school')])
            for record in obj:
                soc_list += str(record.name) + ', '
            vals = {}
            vals['school_id'] = soc_list[:-2]
            school_list.append(vals)
        return school_list

    @api.multi
    def get_data(self):
        domain = []
        if self.academic_year_id:
            domain.append(('academic_year','=', self.academic_year_id.id))
        data=[]
        for school_wise in self.school_ids:
            fee_structure_sr = self.env['pappaya.fees.structure'].search(domain + [('school_id','=',school_wise.id)])
            for structure in fee_structure_sr:
                fee_list, tot_amt, tot_min_amt, tot_percentage = [],0.0,0.0,0.0
                for line in structure.structure_line_ids:
                    head_list = {}
                    head_list['fee_head'] = line.fees_id.name
                    head_list['fee_amt'] = line.amount
                    head_list['min_amt'] = line.min_amount
                    head_list['percentage'] = line.percentage
                    fee_list.append(head_list)
                    tot_amt += line.amount
                    tot_min_amt += line.min_amount
                    tot_percentage += line.percentage
                branch_dict = {'school': 'Branch', 'college': 'College'}
                data.append({
                    'school':str(structure.school_id.code or '') + ' ' + str(structure.school_id.name) + ' ' + branch_dict[structure.school_id.branch_type],
                    'academic_year':structure.academic_year.name,
                    'class':structure.course_id.name,
                    'batch':structure.batch_id.name,
                    'head_list':fee_list,
                    'tot_amt':tot_amt,
                    'tot_min_amt':tot_min_amt,
                    'tot_percentage':tot_percentage
                })
            return data

    @api.multi
    def generate_pdf_report(self):
        if not self.get_data():
            raise ValidationError(_("No record found..!"))
        return self.env['report'].get_action(self, 'pappaya_fees.generate_fee_structure_pdf_report')
    
    
    
    
    
