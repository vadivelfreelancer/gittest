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
from io import BytesIO
from datetime import date
import datetime
from datetime import timedelta
import pytz
import os
from PIL import Image
from xlwt import *


class StudentFeeCollectionSummary(models.TransientModel):
    _name = 'student.fee.collection.summary'

    # society_ids = fields.Many2many('res.company', 'society_rel_student_fee_collection_summary', 'company_id', 'society_id', string='Society')
    school_ids = fields.Many2many('operating.unit','school_rel_student_collection_summary','company_id','school_id', string='Branch')
    from_date = fields.Date('From Date',required=True)
    to_date = fields.Date('To Date',required=True)
    
    @api.onchange('from_date','to_date')
    def onchange_date(self):
        if self.from_date and self.from_date > time.strftime('%Y-%m-%d'):
            self.from_date = None
            raise ValidationError(_('From Date is in the future!'))
        elif self.to_date and self.to_date > time.strftime('%Y-%m-%d'):
            self.to_date = None
            raise ValidationError(_('To Date is in the future!'))
        elif self.to_date and self.from_date and self.from_date > self.to_date:
            raise ValidationError(_(' Check in To Date should be greater than the From Date!'))
        
    # @api.onchange('society_ids')
    # def _onchange_society_ids(self):
    #     if self.society_ids:
    #         self.school_ids = []
    #         return {'domain': {'school_ids': [('type', '=', 'school'),('parent_id', 'in', self.society_ids.ids)]}}

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
        school_list= []
        if (len(self.school_ids) > 1):
            sc_list = ''
            for record in self.school_ids:
                sc_list += str(record.name) + ', '
                vals = {}
                vals['school_id'] = sc_list[:-2]
                school_list.append(vals)
        if not self.school_ids:
            soc_list = ''
            obj = self.env['res.company'].search([('type', '=', 'school')])
            for record in obj:
                soc_list += str(record.name) + ', '
                vals = {}
                vals['school_id'] = soc_list[:-2]
                school_list.append(vals)
        return school_list

    @api.multi
    def get_data(self):
        if self.from_date and self.from_date > time.strftime('%Y-%m-%d'):
            self.from_date = None
            raise ValidationError(_('From Date is in the future!'))
        elif self.to_date and self.to_date > time.strftime('%Y-%m-%d'):
            self.to_date = None
            raise ValidationError(_('To Date is in the future!'))
        elif self.to_date and self.from_date and self.from_date > self.to_date:
            raise ValidationError(_(' Check in To Date should be greater than the From Date!'))
        
        domain = []
        student_domain = []
        data=[]
        # if self.society_ids:
        #     domain.append(('society_id','in',self.society_ids.ids))
        #     student_domain.append(('society_id','in',self.society_ids.ids))
        if self.school_ids:
            domain.append(('school_id','in',self.school_ids.ids))
            student_domain.append(('branch_id','in',self.school_ids.ids))
        domain.append(('receipt_date','>=',self.from_date))
        domain.append(('receipt_date','<=',self.to_date))
        receipt_sr = self.env['pappaya.fees.receipt'].search(domain)
        
        student_ids = self.env['pappaya.admission'].search(student_domain)
        s_no=0
        for student in student_ids:
            reg = 0.0
            fee_head = ''
            receipt_student = receipt_sr.search([('id','in',receipt_sr.ids),('name','=', student.id)])
            if receipt_student:
                for receipt in receipt_student:
                    for line in receipt.fees_receipt_line:
                        if line.total_paid > 0.00:
                            if line.name:
                                fee_head = line.name.name
                                reg = line.total_paid
                            s_no += 1
                            data.append({
                                's_no':s_no,
                                'school':student.branch_id.name,
                                'course':student.course_id.name,
                                'group':student.group_id.name,
                                'batch':student.batch_id.name,
                                'package':student.package.name,
                                'package_course':student.package_id.name,
                                'student_no':student.res_no,
                                'student':student.name,
                                'receipt_no':receipt.id,
                                'fee_head':fee_head,
                                'mode':receipt.payment_mode,
                                'reg':reg,
                                # 'total':reg
                                })
        return data
    
    @api.multi
    def from_data(self):
        workbook = xlwt.Workbook()
        company_name = xlwt.easyxf('font: name Times New Roman, height 350, bold on; align: wrap on, vert centre, horiz centre;')
        company_address = xlwt.easyxf('font: name Times New Roman, height 230, bold on; align: wrap on, vert centre, horiz centre;')
        header = xlwt.easyxf('font: name Times New Roman, height 200, bold on,italic off; align: wrap on, vert centre, horiz centre;  borders: top thin, bottom thin, left thin, right thin;')
        answer = xlwt.easyxf('font: name Times New Roman, height 200; borders: top thin, bottom thin, left thin, right thin;')
        
        answer_center = xlwt.easyxf('font: name Times New Roman, height 200; borders: top thin, bottom thin, left thin, right thin; align: wrap on, vert centre, horiz centre;')
        
        sheet_name = 'Student Fee Collection Details'
        sheet = workbook.add_sheet(sheet_name)
        sheet.row(0).height = 450; 
    
        style_header_without_border = XFStyle()        
        fnt = Font()
        fnt.bold = True
        fnt.height = 12*0x14
        style_header_without_border.font = fnt        
        al1 = Alignment()
        al1.horz = Alignment.HORZ_CENTER
        al1.vert = Alignment.VERT_CENTER        
        pat2 = Pattern()        
        style_header_without_border.alignment = al1
        style_header_without_border.pattern = pat2
        
        style_center_align_without_border = XFStyle()
        al_c = Alignment()
        al_c.horz = Alignment.HORZ_CENTER
        al_c.vert = Alignment.VERT_CENTER
        style_center_align_without_border.alignment = al_c
        
        row_no = 0
        
        # cwd = os.path.abspath(__file__)
        # path = cwd.rsplit('/', 2)
        # image_path = path[0] + '/static/src/img/dis_logo1.bmp'
        # image_path = image_path.replace("pappaya_fees", "pappaya_core")
        # sheet.write_merge(0,4,0,0,'',style_center_align_without_border)
        #
        # sheet.insert_bitmap(image_path, 0, 0, scale_x = .3, scale_y = .4)
        
        if (len(self.school_ids) == 1) :
            sheet.write_merge(row_no, row_no, 0, 12, self.school_ids.name if self.school_ids.name else '', style_header_without_border)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 12, (self.school_ids.street if self.school_ids.street else '') + ', ' + (self.school_ids.street2 if self.school_ids.street2 else '') + ', ' +(self.school_ids.city if self.school_ids.city else ''), style_center_align_without_border)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 12, 'Tel: ' + (self.school_ids.phone if self.school_ids.phone else '') + ', ' + 'Fax: ' + (self.school_ids.fax_id if self.school_ids.fax_id else '') + ', ' + 'Email: ' + (self.school_ids.email if self.school_ids.email else ''), style_center_align_without_border)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 12, self.school_ids.website if self.school_ids.website else '', style_center_align_without_border)
            row_no += 2
            sheet.write_merge(row_no, row_no, 0, 12, 'Student Fee Collection Details', company_address)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 12,'For the period of ' + datetime.datetime.strptime(str(self.from_date),DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y") + ' To ' + datetime.datetime.strptime(str(self.to_date),DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y"), answer_center)

        if not self.school_ids:
            soc_list = ''
            obj = self.env['res.company'].search([('type', '=', 'school')])
            for record in obj:
                soc_list += str(record.name) + ', '
            sheet.write_merge(row_no, row_no, 0, 12,'')
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 12,soc_list[:-2],company_address)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 12,'')
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 12,'')
            row_no += 2
            sheet.write_merge(row_no, row_no, 0, 12, 'Student Fee Collection Details', company_address)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 12,'For the period of ' + datetime.datetime.strptime(str(self.from_date),DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y") + ' To ' + datetime.datetime.strptime(str(self.to_date),DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y"), answer_center)
        if (len(self.school_ids) > 1):
            sc_list = ''
            for record in self.school_ids:
                sc_list += str(record.name) + ', '
            sheet.write_merge(row_no, row_no, 0, 12,'')
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 12, sc_list[:-2],company_address)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 12,'')
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 12,'')
            row_no += 2
            sheet.write_merge(row_no, row_no, 0, 12, 'Student Fee Collection Details', company_address)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 12,'For the period of ' + datetime.datetime.strptime(str(self.from_date),DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y") + ' To ' + datetime.datetime.strptime(str(self.to_date),DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y"), answer_center)

        row_no = 9;
        sheet.row(9).height = 350; 
            
        sheet.col(0).width = 256 * 12
        sheet.write(row_no, 0, 'S.No', header)

        sheet.col(1).width = 256 * 27
        sheet.write(row_no, 1, 'Branch', header)
        
        sheet.col(2).width = 256 * 15
        sheet.write(row_no, 2, 'Course', header)
        
        sheet.col(3).width = 256 * 15
        sheet.write(row_no, 3, 'Group', header)
        
        sheet.col(4).width = 256 * 15
        sheet.write(row_no, 4, 'Batch', header)
        
        sheet.col(5).width = 256 * 15
        sheet.write(row_no, 5, 'Package', header)
        
        
        sheet.col(6).width = 256 * 15
        sheet.write(row_no, 6, 'Package Course', header)

        sheet.col(7).width = 256 * 17
        sheet.write(row_no, 7, 'Reservation No', header)
        
        sheet.col(8).width = 256 * 15
        sheet.write(row_no, 8, 'Student', header)
                
        sheet.col(9).width = 256 * 17
        sheet.write(row_no, 9, 'Fee Type', header)
        
        sheet.col(10).width = 256 * 17
        sheet.write(row_no, 10, 'Receipt No', header)
        
        sheet.col(11).width = 256 * 17
        sheet.write(row_no, 11, 'Mode of Payment', header)

        sheet.col(12).width = 256 * 17
        sheet.write(row_no, 12, 'Amount', header)

        # sheet.col(8).width = 256 * 17
        # sheet.write(row_no, 8, 'Total', header)
        row_no += 1
        reg = 0.0
        total_total = 0.0
        for data in self.get_data():
            sheet.write(row_no, 0, data['s_no'] , answer_center)
            sheet.write(row_no, 1, data['school'] , answer)
            sheet.write(row_no, 2, data['course'] , answer)
            sheet.write(row_no, 3, data['group'] , answer)
            sheet.write(row_no, 4, data['batch'] , answer)
            sheet.write(row_no, 5, data['package'] , answer)
            sheet.write(row_no, 6, data['package_course'] , answer)
            sheet.write(row_no, 7, data['student_no'] , answer)
            sheet.write(row_no, 8, data['student'] , answer)
            sheet.write(row_no, 9, data['fee_head'], answer)
            sheet.write(row_no, 10, data['receipt_no'], answer)
            sheet.write(row_no, 11, data['mode'], answer)
            sheet.write(row_no, 12, '%.2f' % data['reg'] , answer)
            # sheet.write(row_no, 8, '%.2f' % data['total'] , answer)
            reg += data['reg']
            # total_total += data['total']
            row_no += 1
        
        sheet.write_merge(row_no,row_no, 0,11, 'Total', header)
        sheet.write(row_no,12, '%.2f' % reg, answer)
        # sheet.write(row_no,8, '%.2f' % total_total, answer)
        row_no += 1
        
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data
    
    @api.multi
    def generate_pdf_report(self):
        if not self.get_data():
            raise ValidationError(_("No record found..!"))
        start_date = fields.Date.from_string(self.from_date)
        end_date = fields.Date.from_string(self.to_date)
        if start_date > end_date:
            raise ValidationError(_("To date should not be less than from date."))
        return self.env['report'].get_action(self, 'pappaya_fees.student_report_fee_collect_summary_receipt')
    
    @api.multi
    def fees_collection_detail_excel_report(self):
        if not self.get_data():
            raise ValidationError(_("No record found..!"))
        start_date = fields.Date.from_string(self.from_date)
        end_date = fields.Date.from_string(self.to_date)
        if start_date > end_date:
            raise ValidationError(_("To date should not be less than from date."))
        #if not self.get_data():
            # ValidationError(_("No record found..!"))
        data = base64.encodestring(self.from_data())
        attach_vals = {
            'name':'%s.xls' % ('Student Fee Collection Details'),
            'datas':data,
            'datas_fname':'%s.xls' % ('Student Fee Collection Details'),
         }
        doc_id = self.env['ir.attachment'].create(attach_vals)
        return {
            'type': 'ir.actions.act_url',
            'url':'web/content/%s?download=true'%(doc_id.id),
            'target': 'self',
        }
    
    
    
    
