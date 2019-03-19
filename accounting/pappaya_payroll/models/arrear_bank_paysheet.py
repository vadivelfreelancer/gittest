import time
from datetime import datetime
from dateutil import relativedelta
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError
import babel
import xlsxwriter
import base64
import csv
import os
import xlwt
from io import BytesIO
from xlwt import *
import dateutil.parser

    
class ArrearBankPaySheet(models.Model):
    _name = 'arrear.bank.paysheet'
    _inherit = 'mail.thread'
    _order = "id desc"
    _rec_name = 'bank_id'

    bank_id = fields.Many2one('res.bank', string="Bank")
    month_id                = fields.Many2one('calendar.generation.line',string='Month')
    date_start              = fields.Date(string='Date From')
    date_end                = fields.Date(string='Date To')
    
    region_ids              = fields.Many2many('pappaya.region','pappaya_region_cycle_rel','region_id','cycle_id',string="Region")
    state_ids               = fields.Many2many('res.country.state','res_country_state_cycle_rel','state_id','cycle_id',string="State",domain=[('country_id.is_active','=',True)])
    district_ids            = fields.Many2many("state.district", 'state_district_cycle_rel','state_id','cycle_id',string='District')
    office_type_ids         = fields.Many2many('pappaya.office.type','office_type_cycle_rel','state_id','cycle_id',string="Office Type")
    branch_ids              = fields.Many2many('operating.unit', 'branch_cycle_rel','branch_id','cycle_id',string='Branch',domain=[('type','=','branch')])
    state                   = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string="Status", default='draft', track_visibility='onchange', copy=False)
    paysheet_line = fields.One2many('arrear.bank.paysheet.line','bank_paysheet_id', string='Paysheet Lines')

    @api.onchange('month_id')
    def onchange_month_id(self):
        for record in self:
            if record.month_id:
                record.date_start   = record.month_id.date_start
                record.date_end     = record.month_id.date_end
    
                
    @api.onchange('region_ids')
    def onchange_region_id(self):
        for record in self:
            domain = []
            region_domain = []
            if record.region_ids:
                domain.append(('region_id','in',record.region_ids.ids))
                state_ids = []
                for region_id in record.region_ids:
                    state_ids += region_id.state_id.ids
                region_domain.append(('id', 'in', state_ids))
            if record.district_ids:
                domain.append(('district_id','in',record.district_ids.ids))
            if record.office_type_ids:
                domain.append(('office_type_id','in',record.office_type_ids.ids))
            if record.state_ids:
                domain.append(('state_id','in',record.state_ids.ids))
            domain.append(('type','=','branch'))
            record.state_ids = record.district_ids = record.branch_ids = None
            return {'domain': {'state_ids': region_domain,'branch_ids': domain}}
    
    @api.onchange('state_ids')
    def onchange_state_id(self):
        for record in self:
            domain = []
            state_domain = []
            if record.region_ids:
                domain.append(('region_id','in',record.region_ids.ids))
            if record.district_ids:
                domain.append(('district_id','in',record.district_ids.ids))
            if record.office_type_ids:
                domain.append(('office_type_id','in',record.office_type_ids.ids))
            if record.state_ids:
                domain.append(('state_id','in',record.state_ids.ids))
                state_domain.append(('state_id', 'in', record.state_ids.ids))
            domain.append(('type','=','branch'))
            record.district_ids = record.branch_ids = None
            return {'domain': {'district_ids': state_domain,'branch_ids': domain}}
            
            
    @api.onchange('district_ids')
    def onchange_district_id(self):
        for record in self:
            domain = []
            if record.state_ids:
                domain.append(('state_id','in',record.state_ids.ids))
            if record.region_ids:
                domain.append(('region_id','in',record.region_ids.ids))
            if record.district_ids:
                domain.append(('district_id','in',record.district_ids.ids))
            if record.office_type_ids:
                domain.append(('office_type_id','in',record.office_type_ids.ids))
            domain.append(('type','=','branch'))
            record.branch_ids = None
            return {'domain': {'branch_ids': domain}}
        
    @api.onchange('office_type_ids')
    def onchange_office_type_id(self):
        for record in self:
            domain = []
            if record.state_ids:
                domain.append(('state_id','in',record.state_ids.ids))
            if record.region_ids:
                domain.append(('region_id','in',record.region_ids.ids))
            if record.district_ids:
                domain.append(('district_id','in',record.district_ids.ids))
            if record.office_type_ids:
                domain.append(('office_type_id','in',record.office_type_ids.ids))
            domain.append(('type','=','branch'))
            record.state_ids = record.district_ids = record.branch_ids = None
            return {'domain': {'branch_ids': domain}}

    

    @api.multi
    def action_reset(self):
        for record in self:
            record.state = 'draft'
                            
    @api.multi
    def action_done(self):
        for record in self:
            record.state = 'done'

    @api.multi
    def generate_paysheet(self):
        workbook = xlwt.Workbook()
        company_name = xlwt.easyxf('font: name Times New Roman, height 350, bold on; align: wrap on, vert centre, horiz centre;')
        company_address = xlwt.easyxf('font: name Times New Roman, height 230, bold on; align: wrap on, vert centre, horiz centre;')
        header = xlwt.easyxf('font: name Times New Roman, height 200, bold on,italic off; align: wrap on, vert centre, horiz centre;  borders: top thin, bottom thin, left thin, right thin;')
        answer = xlwt.easyxf('font: name Times New Roman, height 200; borders: top thin, bottom thin, left thin, right thin;')

        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd/mm/yyyy hh:mm:ss'

        sheet_name = 'Arrear Bank Pay Sheet'
        sheet = workbook.add_sheet(sheet_name)
        sheet.row(0).height = 450;

        style_header_without_border = XFStyle()
        fnt = Font()
        fnt.bold = True
        fnt.height = 12 * 0x14
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

        row_no = 1;
        sheet.row(1).height = 350;

        sheet.col(0).width = 256 * 20; sheet.col(1).width = 256 * 20; sheet.col(2).width = 256 * 20; sheet.col(3).width = 256 * 20;
        sheet.col(4).width = 256 * 20; sheet.col(5).width = 256 * 20; sheet.col(6).width = 256 * 14; sheet.col(7).width = 256 * 14;
        sheet.col(8).width = 256 * 20; sheet.col(9).width = 256 * 20; sheet.col(10).width = 256 * 40; sheet.col(11).width = 256 * 20;
        sheet.col(12).width = 256 * 30; sheet.col(13).width = 256 * 20; sheet.col(14).width = 256 * 15; sheet.col(15).width = 256 * 15;
        sheet.col(16).width = 256 * 20; sheet.col(17).width = 256 * 25; sheet.col(18).width = 256 * 25; sheet.col(19).width = 256 * 25;
        sheet.col(20).width = 256 * 25; sheet.col(21).width = 256 * 25; sheet.col(22).width = 256 * 20; sheet.col(23).width = 256 * 20;
        sheet.col(24).width = 256 * 20; sheet.col(25).width = 256 * 20; sheet.col(26).width = 256 * 20; sheet.col(27).width = 256 * 20;
        sheet.col(28).width = 256 * 20; sheet.col(29).width = 256 * 20; sheet.col(30).width = 256 * 20; sheet.col(31).width = 256 * 20;
        sheet.col(32).width = 256 * 20; sheet.col(33).width = 256 * 20; sheet.col(34).width = 256 * 20; sheet.col(35).width = 256 * 20;
        sheet.col(36).width = 256 * 20; sheet.col(37).width = 256 * 20; sheet.col(38).width = 256 * 20; sheet.col(39).width = 256 * 20;
        sheet.col(40).width = 256 * 20; sheet.col(41).width = 256 * 20; sheet.col(42).width = 256 * 20; sheet.col(43).width = 256 * 20;
        sheet.col(44).width = 256 * 20; sheet.col(45).width = 256 * 20; sheet.col(46).width = 256 * 20; sheet.col(47).width = 256 * 20; sheet.col(48).width = 256 * 20;
 
        sheet.write(row_no, 0, "Client_Code", header); sheet.write(row_no, 1, "Product_Code", header); sheet.write(row_no, 2, "Payment_Type", header); sheet.write(row_no, 3, "Payment Ref No", header);
        sheet.write(row_no, 4, "Payment_Date", header); sheet.write(row_no, 5, "Instrument Date", header); sheet.write(row_no, 6, "Dr_Ac_No", header); sheet.write(row_no, 7, "Amount", header);
        sheet.write(row_no, 8, "Bank_Code_Indicator", header); sheet.write(row_no, 9, "Beneficiary_Code", header); sheet.write(row_no, 10, "Beneficiary_Name", header);sheet.write(row_no, 11, "Beneficiary_Bank", header);
        sheet.write(row_no, 12, "Beneficiary_Branch / IFSC Code", header); sheet.write(row_no, 13, "Beneficiary_Acc_No", header); sheet.write(row_no, 14, "Location", header); sheet.write(row_no, 15, "Print_Location", header);
        sheet.write(row_no, 16, "Instrument_Number", header); sheet.write(row_no, 17, "Ben_Add1", header); sheet.write(row_no, 18, "Ben_Add2", header); sheet.write(row_no, 19, "Ben_Add3", header);
        sheet.write(row_no, 20, "Ben_Add4", header); sheet.write(row_no, 21, "Beneficiary_Email", header); sheet.write(row_no, 22, "Beneficiary_Mobile", header); sheet.write(row_no, 23, "Debit_Narration", header);
        sheet.write(row_no, 24, "Credit_Narration", header); sheet.write(row_no, 25, "Payment Details 1", header); sheet.write(row_no, 26, "Payment Details 2", header); sheet.write(row_no, 27, "Payment Details 3", header);
        sheet.write(row_no, 28, "Payment Details 4", header); sheet.write(row_no, 29, "Enrichment_1", header); sheet.write(row_no, 30, "Enrichment_2", header); sheet.write(row_no, 31, "Enrichment_3", header);
        sheet.write(row_no, 32, "Enrichment_4", header); sheet.write(row_no, 33, "Enrichment_5", header); sheet.write(row_no, 34, "Enrichment_6", header); sheet.write(row_no, 35, "Enrichment_7", header);
        sheet.write(row_no, 36, "Enrichment_8", header); sheet.write(row_no, 37, "Enrichment_9", header); sheet.write(row_no, 38, "Enrichment_10", header); sheet.write(row_no, 39, "Enrichment_11", header);
        sheet.write(row_no, 40, "Enrichment_12", header); sheet.write(row_no, 41, "Enrichment_13", header); sheet.write(row_no, 42, "Enrichment_14", header); sheet.write(row_no, 43, "Enrichment_15", header);
        sheet.write(row_no, 44, "Enrichment_16", header); sheet.write(row_no, 45, "Enrichment_17", header); sheet.write(row_no, 46, "Enrichment_18", header); sheet.write(row_no, 47, "Enrichment_19", header); sheet.write(row_no, 48, "Enrichment_20", header)

        if self.month_id:
            domain = []
            if self.state_ids:
                domain.append(('state_id','in',self.state_ids.ids))
            if self.region_ids:
                domain.append(('region_id','in',self.region_ids.ids))
            if self.district_ids:
                domain.append(('district_id','in',self.district_ids.ids))
            if self.office_type_ids:
                domain.append(('office_type_id','in',self.office_type_ids.ids))
            if self.branch_ids:
                domain.append(('id','in',self.branch_ids.ids))
            domain.append(('type','=','branch'))
            branch_sr = self.env['operating.unit'].search(domain)
            start = datetime.strptime(self.date_start, '%Y-%m-%d').date()
            end = datetime.strptime(self.date_end, '%Y-%m-%d').date()
            
            
            arrears_domain = []
            arrears_domain.append(('branch_id','in',branch_sr.ids))
            arrears_domain.append(('date','>=',start))
            arrears_domain.append(('date','<=',end))
            arrears_domain.append(('payment_state','=','pending'))
            arrears_domain.append(('state','=','approve'))
            hr_arrears_sr = self.env['hr.arrears'].search(arrears_domain, order="branch_id")
            
            
            
            if not hr_arrears_sr:
                raise ValidationError(_("No Records found to generate Arrear Bank Paysheet"))

            
            ttyme = datetime.fromtimestamp(time.mktime(time.strptime(self.date_start, "%Y-%m-%d")))
            locale = self.env.context.get('lang') or 'en_US'
            month_name = tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))

            title = self.bank_id.name + '  ' + self.month_id.name

            sheet.write_merge(0, 0, 0, 8, title , company_address)
            row_no += 1
            for arrears_id in  hr_arrears_sr:
                for arrears_line in self.env['hr.arrears.line'].search([('arrears_id','=',arrears_id.id)]):
                    sheet.write(row_no, 0, None, answer); sheet.write(row_no, 1, None, answer); sheet.write(row_no, 2, None, answer); sheet.write(row_no, 3, None, answer);
                    sheet.write(row_no, 4, None, answer); sheet.write(row_no, 5, None, answer); sheet.write(row_no, 6, None, answer); sheet.write(row_no, 7, '%.2f' % arrears_line.approved_amount, answer);
                    sheet.write(row_no, 8, None, answer); sheet.write(row_no, 9, None, answer); sheet.write(row_no, 10, arrears_line.employee_id.name, answer); sheet.write(row_no, 11, arrears_line.employee_id.bank_id.name, answer);
                    sheet.write(row_no, 12, arrears_line.employee_id.ifsc, answer); sheet.write(row_no, 13, arrears_line.employee_id.account_number, answer); sheet.write(row_no, 14, None, answer); sheet.write(row_no, 15, None, answer);
                    sheet.write(row_no, 16, None, answer); sheet.write(row_no, 17, None, answer); sheet.write(row_no, 18, None, answer); sheet.write(row_no, 19, None, answer);
                    sheet.write(row_no, 20, None, answer); sheet.write(row_no, 21, arrears_line.employee_id.work_email, answer); sheet.write(row_no, 22, arrears_line.employee_id.work_mobile, answer); sheet.write(row_no, 23, None, answer);
                    sheet.write(row_no, 24, None, answer); sheet.write(row_no, 25, None, answer); sheet.write(row_no, 26, None, answer); sheet.write(row_no, 27, None, answer);
                    sheet.write(row_no, 28, None, answer); sheet.write(row_no, 29, None, answer); sheet.write(row_no, 30, None, answer); sheet.write(row_no, 31, None, answer);
                    sheet.write(row_no, 32, None, answer); sheet.write(row_no, 33, None, answer); sheet.write(row_no, 34, None, answer); sheet.write(row_no, 35, None, answer);
                    sheet.write(row_no, 36, None, answer); sheet.write(row_no, 37, None, answer); sheet.write(row_no, 38, None, answer); sheet.write(row_no, 39, None, answer);
                    sheet.write(row_no, 40, None, answer); sheet.write(row_no, 41, None, answer); sheet.write(row_no, 42, None, answer); sheet.write(row_no, 43, None, answer);
                    sheet.write(row_no, 44, None, answer); sheet.write(row_no, 45, None, answer); sheet.write(row_no, 46, None, answer); sheet.write(row_no, 47, None, answer); sheet.write(row_no, 48, None, answer)
                    row_no += 1
                row_no += 1
                arrears_id.payment_state = 'paid'

            date_value = time.strftime('%d-%m-%Y %H:%M:%S')
            footer = 'Generated By' + ' : ' + self.env.user.partner_id.name + '    ' + 'Dated on' + ' : ' + date_value
            sheet.write_merge(row_no, row_no, 0, 8, footer, answer)

            # sheet.write(row_no, 0, 'Generated By', answer); sheet.write(row_no, 1, self.env.user.partner_id.name, answer);
            # sheet.write(row_no, 2, 'Dated on', answer); sheet.write(row_no, 3, datetime.now(), date_format);

        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()

        data = base64.encodebytes(data)

        sequence_no = self.env['ir.sequence'].next_by_code('arrear.bank.paysheet') or _('New')

        self.write({
            'paysheet_line':[(0, 0, {'bank_paysheet_id':self.id, 'sequence_no':sequence_no, 'dated_on':datetime.now(), 'generated_by':self.env.user.id, 'filedata': data, 'filename': 'Arrear Bank Pay Sheet.xls'})]
        })

class ArrearPaysheetLine(models.Model):
    _name = 'arrear.bank.paysheet.line'

    bank_paysheet_id = fields.Many2one('arrear.bank.paysheet')
    sequence_no = fields.Char('Sequence')
    dated_on = fields.Datetime('Dated on')
    generated_by = fields.Many2one('res.users', string='Generated By')
    filedata = fields.Binary('Paysheet file', readonly=True)
    filename = fields.Char('Filename', size=64, readonly=True)