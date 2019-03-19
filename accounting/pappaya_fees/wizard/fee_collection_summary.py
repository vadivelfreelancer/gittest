# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
import xlwt
from io import BytesIO

import base64
from odoo.http import request
from datetime import datetime, date
#from cStringIO import StringIO
from datetime import date
import datetime
from datetime import timedelta
import pytz
import os
from PIL import Image
from xlwt import *

class FeeCollectionSummary(models.TransientModel):
    _name = 'fee.collection.summary'
    
    school_ids = fields.Many2many('operating.unit','school_rel_collection_summary','company_id','school_id', string='Branch')
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')

#     @api.onchange('school_ids')
#     def onchange_school(self):
#         self.academic_year_id = None
#         academic_year_id_list = []
#         for school_id in self.school_ids:
#             for ac_obj in self.env['academic.year'].sudo().search([('is_active','=',True)]):
#                 if school_id.id in ac_obj.school_id.ids and ac_obj.id not in academic_year_id_list:
#                     academic_year_id_list.append(ac_obj.id)
#         return {'domain': {'academic_year_id': [('id', 'in', academic_year_id_list)]}}

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

    def get_data(self):
        domain = domain1 = []
        data = []
        if self.school_ids:
            domain.append(('school_id', 'in', self.school_ids.ids))
        if self.academic_year_id:
            domain.append(('academic_year_id','=',self.academic_year_id.id))
            domain1.append(('academic_year_id','=',self.academic_year_id.id))
        if self.from_date:
            domain.append(('receipt_date', '>=', self.from_date))
        if self.to_date:
            domain.append(('receipt_date', '<=', self.to_date))
        date_list = []
        receipt_sr = self.env['pappaya.fees.receipt'].sudo().search(domain,order='receipt_date asc')
        for obj in receipt_sr:
            if obj.receipt_date not in date_list:
                date_list.append(obj.receipt_date)
        if self.school_ids:
            school_ids = self.school_ids
        else:
            school_ids = self.env['res.company'].sudo().search([('type', '=', 'school')])
        s_no = 0
        for date in date_list:
            for school in school_ids:
                cash = cheque = dd = neft = card = total = 0.0
                receipt_date = ''
                receipt_school = receipt_sr.sudo().search([('school_id', '=', school.id),('receipt_date','=',date)]+domain1)
                if receipt_school:
                    s_no += 1
                    for receipt in receipt_school:
                        receipt_date = (datetime.datetime.strptime(str(receipt.receipt_date), DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y'))
                        if receipt.payment_mode == 'cash':
                            cash += receipt.total
                            total += receipt.total
                        if receipt.payment_mode == 'cheque/dd':
                            cheque += receipt.total
                            total += receipt.total
                        if receipt.payment_mode == 'dd':
                            dd += receipt.total
                            total += receipt.total
                        if receipt.payment_mode == 'neft/rtgs':
                            neft += receipt.total
                            total += receipt.total
                        if receipt.payment_mode == 'card':
                            card += receipt.total
                            total += receipt.total
                    branch_dict = {'school':'Branch','college':'College'}
                    data.append({
                        's_no': s_no,
                        'date':receipt_date,
                        'school': str(school.code or '') + ' ' + str(school.name) + ' ' + branch_dict[school.branch_type],
                        'cash': cash,
                        'cheque': cheque,
                        'dd':dd,
                        'neft': neft,
                        'card': card,
                        'total': total
                    })
        return data

    @api.multi
    def from_data(self):
        workbook = xlwt.Workbook()
        company_name = xlwt.easyxf('font: name Times New Roman, height 350, bold on; align: wrap on, vert centre, horiz centre;')
        company_address = xlwt.easyxf('font: name Times New Roman, height 230, bold on; align: wrap on, vert centre, horiz centre;')
        header = xlwt.easyxf('font: name Times New Roman, height 200, bold on,italic off; align: wrap on, vert centre, horiz centre;  borders: top thin, bottom thin, left thin, right thin;')
        answer = xlwt.easyxf('font: name Times New Roman, height 200; borders: top thin, bottom thin, left thin, right thin;')

        sheet_name = 'Fee collection Summary'
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

        if (len(self.school_ids) == 1):
            sheet.write_merge(row_no, row_no, 0, 7, self.school_ids.name if self.school_ids.name else '', style_header_without_border)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 7, (self.school_ids.street if self.school_ids.street else '') + ', ' + (self.school_ids.street2 if self.school_ids.street2 else '') + ', ' +(self.school_ids.city if self.school_ids.city else ''), style_center_align_without_border)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 7, 'Tel: ' + (self.school_ids.phone if self.school_ids.phone else '') + ', ' + 'Fax: ' + (self.school_ids.fax_id if self.school_ids.fax_id else '') + ', ' + 'Email: ' + (self.school_ids.email if self.school_ids.email else ''), style_center_align_without_border)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 7, self.school_ids.website if self.school_ids.website else '', style_center_align_without_border)
            row_no += 2
            sheet.write_merge(row_no, row_no, 0, 7, 'Fee Collection Summary', company_address)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 7, ''+(datetime.datetime.strptime(str(self.from_date), DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')) + ' to ' +(datetime.datetime.strptime(str(self.to_date),DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')), company_address)
            row_no += 1
        if (len(self.school_ids) > 1):
            sc_list = ''
            for record in self.school_ids:
                sc_list += str(record.name) + ', '
            sheet.write_merge(row_no, row_no, 0, 7,'')
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 7, sc_list[:-2],company_address)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 7,'')
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 7,'')
            row_no += 2
            sheet.write_merge(row_no,row_no,0,7, 'Fee Collection Summary', company_address)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 7, '' + (datetime.datetime.strptime(str(self.from_date), DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')) + ' to ' + (datetime.datetime.strptime(str(self.to_date), DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')), company_address)
            row_no += 1
        if (not self.school_ids):
            soc_list = ''
            obj = self.env['res.company'].sudo().search([('type', '=', 'school')])
            for record in obj:
                soc_list += str(record.name) + ', '
            sheet.write_merge(row_no, row_no, 0, 7,'')
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 7,soc_list[:-2],company_address)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 7,'')
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 7,'')
            row_no += 2
            sheet.write_merge(row_no, row_no, 0, 7, 'Fee Collection Summary', company_address)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 7, '' + (datetime.datetime.strptime(str(self.from_date), DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')) + ' to ' +(datetime.datetime.strptime(str(self.to_date), DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')), company_address)
            row_no += 1

        row_no = 9;
        sheet.row(9).height = 350;
        sheet.col(0).width = 256 * 15
        sheet.write(row_no, 0, 'S.No', header)
        sheet.col(1).width = 256 * 22
        sheet.write(row_no, 1, 'Date of Transaction', header)
        sheet.col(2).width = 256 * 28
        sheet.write(row_no, 2, 'Branch', header)
        sheet.col(3).width = 256 * 17
        sheet.write(row_no, 3, 'Cash', header)
        sheet.col(4).width = 256 * 17
        sheet.write(row_no, 4, 'Cheque', header)
        sheet.col(5).width = 256 * 17
        sheet.write(row_no, 5, 'DD', header)
        sheet.col(6).width = 256 * 17
        sheet.write(row_no, 6, 'Neft/RTGS', header)
        sheet.col(7).width = 256 * 17
        sheet.write(row_no, 7, 'Card', header)
        sheet.col(8).width = 256 * 17
        sheet.write(row_no, 8, 'Total Amount', header)
        row_no += 1
        for data in self.get_data():
            sheet.write(row_no, 0, data['s_no'] , answer)
            sheet.write(row_no, 1, data['date'], answer)
            sheet.write(row_no, 2, data['school'] , answer)
            sheet.write(row_no, 3, '%.2f' % data['cash'] , answer)
            sheet.write(row_no, 4, '%.2f' % data['cheque'] , answer)
            sheet.write(row_no, 5, '%.2f' % data['dd'], answer)
            sheet.write(row_no, 6, '%.2f' % data['neft'] , answer)
            sheet.write(row_no, 7, '%.2f' % data['card'] , answer)
            sheet.write(row_no, 8, '%.2f' % data['total'] , answer)
            row_no += 1
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data
    
    @api.multi
    def generate_pdf_report(self):
        start_date = fields.Date.from_string(self.from_date)
        end_date = fields.Date.from_string(self.to_date)
        if start_date > end_date:
            raise ValidationError(_("To date should not be less than from date."))
        return self.env['report'].get_action(self, 'pappaya_fees.report_fee_collect_summary_receipt')
    
    @api.multi
    def fees_collection_detail_excel_report(self):
        start_date = fields.Date.from_string(self.from_date)
        end_date = fields.Date.from_string(self.to_date)
        if start_date > end_date:
            raise ValidationError(_("To date should not be less than from date."))
        #if not self.get_data():
            # ValidationError(_("No record found..!"))
        data = base64.encodestring(self.from_data())
        attach_vals = {
            'name':'%s.xls' % ('Fee Collection Summary'),
            'datas':data,
            'datas_fname':'%s.xls' % ('Fee Collection Summary'),
         }
        doc_id = self.env['ir.attachment'].create(attach_vals)
        return {
            'type': 'ir.actions.act_url',
            'url':'web/content/%s?download=true'%(doc_id.id),
            'target': 'self',
        }
    
    
    
    
