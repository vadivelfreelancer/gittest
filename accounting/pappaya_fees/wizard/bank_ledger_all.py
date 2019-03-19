import time
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
import xlwt
import base64
from datetime import datetime
from io import BytesIO
import datetime
from xlwt import *

class BankLedgerAll(models.TransientModel):
    _name = "bank.ledger.all"

    school_ids = fields.Many2many('operating.unit','school_bank_ledger_all_rel','company_id','school_id', string='Branch')
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    bank_account_id = fields.Many2one('res.bank', string='Bank Name')
    payment_mode = fields.Selection([('paytm','Paytm'),('payumoney','PayUmoney'),('cash','Cash'),('cheque/dd','Cheque'),('dd','DD'),('neft/rtgs','Neft/RTGS'),('card','POS'),('all','All')],string='Payment Mode',default='all')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')

    @api.constrains('from_date','to_date')
    def check_date(self):
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValidationError(_('To Date should be greater than the From Date!'))
        if self.from_date and self.from_date > time.strftime('%Y-%m-%d'):
            raise ValidationError('From Date is in the future!')
        if self.to_date and self.to_date > time.strftime('%Y-%m-%d'):
            raise ValidationError('To Date is in the future!')

    @api.onchange('academic_year_id')
    def onchange_academic_year(self):
        if self.academic_year_id:
            self.bank_account_id = None
            self.from_date = None
            self.to_date = None

    @api.onchange('from_date')
    def onchange_date(self):
        if self.from_date:
            self.to_date = None

    @api.multi
    def get_school_header(self):
        school_list = []
        if (len(self.school_ids) == 1 ):
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
    def get_data(self):
        payemnt_mode = {'cash':'Cash','cheque/dd':'Cheque','dd':'DD','neft/rtgs':'Neft/RTGS','card':'POS'}
        domain = []
        non_cash_domain = []
        all_domain = []
        data=[]
        if self.school_ids:
            domain.append(('school_id','in',self.school_ids.ids))
            non_cash_domain.append(('school_id','in',self.school_ids.ids))
        if self.academic_year_id:
            domain.append(('academic_year_id','=', self.academic_year_id.id))
            non_cash_domain.append(('academic_year_id','=', self.academic_year_id.id))

        domain.append(('bank_id','=',self.bank_account_id.id))
        domain.append(('approve_date','>=',self.from_date))
        domain.append(('approve_date','<=',self.to_date))
        domain.append(('state','=','approved'))
        
        non_cash_domain.append(('c_bank_id','=',self.bank_account_id.id))
        non_cash_domain.append(('cleared_date','>=',self.from_date))
        non_cash_domain.append(('cleared_date','<=',self.to_date))
        non_cash_domain.append(('payment_line_status','=','cleared'))
        
        if not self.payment_mode == 'all':
            non_cash_domain.append(('payment_mode','=',self.payment_mode))
            
        
        total = 0.00
        s_no = 0
        if self.payment_mode == 'cash':
            cash_deposit_sr = self.env['bank.deposit'].sudo().search(domain,order='approve_date desc,id desc')
            for cash_deposit in cash_deposit_sr:
                s_no += 1
                total = total + cash_deposit.c_amt_deposit
                data.append({    
                                 's_no':s_no,
                                 'date':cash_deposit.approve_date,
                                 'school':cash_deposit.school_id.name,
                                 'payment_mode':'Cash',
                                 'description':cash_deposit.remarks,
                                 'amount':cash_deposit.c_amt_deposit,
                                 'total':total
                                
                            })
        if self.payment_mode != 'all':
            non_cash_deposit_sr = self.env['bank.deposit.clearance'].sudo().search(non_cash_domain,order='cleared_date desc,id desc')
            for non_cash_deposit in non_cash_deposit_sr:
                if non_cash_deposit.status_line_ids:
                    s_no += 1
                    total = total + non_cash_deposit.cleared_amt
                    data.append({    
                                     's_no':s_no,
                                     'date':non_cash_deposit.cleared_date,
                                     'school':non_cash_deposit.school_id.name,
                                     'payment_mode':payemnt_mode[non_cash_deposit.payment_mode],
                                     'description':non_cash_deposit.remarks,
                                     'amount':non_cash_deposit.cleared_amt,
                                     'total':total
                                    
                                })
        if self.payment_mode == 'all':
            from_date = datetime.datetime.strptime(self.from_date, '%Y-%m-%d')
            to_date = datetime.datetime.strptime(self.to_date, '%Y-%m-%d')
            from_date_time = datetime.datetime.combine(from_date, datetime.time.min)
            to_date_time = datetime.datetime.combine(to_date, datetime.time.max)

            cash_deposit_ids = self.env['bank.deposit'].sudo().search([('approve_date','>=',self.from_date),('approve_date','<=',self.to_date)]+all_domain).ids
            non_cash_deposit_ids = self.env['bank.deposit.clearance'].sudo().search([('cleared_date','>=',self.from_date),('cleared_date','<=',self.to_date)]+all_domain).ids

            cash_deposit_sr = self.env['bank.deposit'].sudo().search([('id','in', cash_deposit_ids),('state','=','approved'),('bank_id','=',self.bank_account_id.id),('approve_date','>=',self.from_date),('approve_date','<=',self.to_date)])
            non_cash_deposit_sr = self.env['bank.deposit.clearance'].sudo().search([('id','in', non_cash_deposit_ids),('payment_line_status','=','cleared'),('c_bank_id','=',self.bank_account_id.id),('cleared_date','>=',self.from_date),('cleared_date','<=',self.to_date)])

            cash_deposit_date = []
            non_cash_deposit_date = []
            all_date_and_id = []
            #cash_deposit_sr = self.env['bank.deposit'].search(domain,order='deposit_date desc,id desc')
            for cash_deposit in cash_deposit_sr:
                cash_deposit_date.append(cash_deposit.write_date)
                all_date_and_id.append({
                                        str(cash_deposit.write_date):str(cash_deposit.id),
                                        'name':'cash_deposit'
                                        })
            #non_cash_deposit_sr = self.env['bank.deposit.clearance'].search(non_cash_domain,order='write_date desc,id desc')
            for non_cash_deposit in non_cash_deposit_sr:
                non_cash_deposit_date.append(non_cash_deposit.write_date)
                all_date_and_id.append({
                                        str(non_cash_deposit.write_date):str(non_cash_deposit.id),
                                        'name':'non_cash_deposit'
                                        })
            
            cash_and_non_cash_list = list(set(cash_deposit_date + non_cash_deposit_date))
            cash_and_non_cash_list.sort()
            cash_and_non_cash_list.reverse()

            for date in cash_and_non_cash_list:
                #write_date_time = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                for date_id in all_date_and_id:
                    if date in date_id.keys():
                        if date_id[date] and date_id['name'] == 'cash_deposit':
                            cash_deposit_sr_ids = self.env['bank.deposit'].sudo().search([('id','=', int(date_id[date])),('approve_date','>=',self.from_date),('approve_date','<=',self.to_date)])
                            for cash_deposit in cash_deposit_sr_ids:
                                s_no += 1
                                total = total + cash_deposit.c_amt_deposit
                                data.append({    
                                                 's_no':s_no,
                                                 'date':cash_deposit.approve_date,
                                                 'school':cash_deposit.school_id.name,
                                                 'payment_mode':'Cash',
                                                 'description':cash_deposit.remarks,
                                                 'amount':cash_deposit.c_amt_deposit,
                                                 'total':total
                                                
                                            })

                        if date_id[date] and date_id['name'] == 'non_cash_deposit':
                            non_cash_deposit_sr_ids = self.env['bank.deposit.clearance'].sudo().search([('id','=', int(date_id[date])),('cleared_date','>=',self.from_date),('cleared_date','<=',self.to_date)])
                            for non_cash_deposit in non_cash_deposit_sr_ids:
                                if non_cash_deposit.status_line_ids:
                                    s_no += 1
                                    total = total + non_cash_deposit.cleared_amt
                                    data.append({    
                                                     's_no':s_no,
                                                     'date':non_cash_deposit.cleared_date,
                                                     'school':non_cash_deposit.school_id.name,
                                                     'payment_mode':payemnt_mode[non_cash_deposit.payment_mode],
                                                     'description':non_cash_deposit.remarks,
                                                     'amount':non_cash_deposit.cleared_amt,
                                                     'total':total
                                                    
                                                })

            
        return data
    
    @api.multi
    def from_data(self):
        workbook = xlwt.Workbook()
        company_name = xlwt.easyxf('font: name Times New Roman, height 350, bold on; align: wrap on, vert centre, horiz centre;')
        company_address = xlwt.easyxf('font: name Times New Roman, height 230, bold on; align: wrap on, vert centre, horiz centre;')
        header = xlwt.easyxf('font: name Times New Roman, height 200, bold on,italic off; align: wrap on, vert centre, horiz centre;  borders: top thin, bottom thin, left thin, right thin;')
        answer = xlwt.easyxf('font: name Times New Roman, height 200; borders: top thin, bottom thin, left thin, right thin;')

        sheet_name = 'Bank Ledger'
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

        if len(self.school_ids) == 1 :
            sheet.write_merge(row_no, row_no, 0, 7, self.school_ids.name if self.school_ids.name else '', style_header_without_border)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 7, (self.school_ids.street if self.school_ids.street else '') + ', ' + (self.school_ids.street2 if self.school_ids.street2 else '') + ', ' +(self.school_ids.city if self.school_ids.city else ''), style_center_align_without_border)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 7, 'Tel: ' + (self.school_ids.phone if self.school_ids.phone else '') + ', ' + 'Fax: ' + (self.school_ids.fax_id if self.school_ids.fax_id else '') + ', ' + 'Email: ' + (self.school_ids.email if self.school_ids.email else ''), style_center_align_without_border)
            row_no += 1
            sheet.write_merge(row_no, row_no, 0, 7, self.school_ids.website if self.school_ids.website else '', style_center_align_without_border)
            row_no += 2
            sheet.write_merge(row_no, row_no, 0, 7, 'Bank Ledger', company_address)
        
        if len(self.school_ids) > 1 :
            soc_list = ''
            obj = self.env['res.company'].sudo().search([('type', '=', 'school'),('id','in',self.school_ids.ids)])
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
            sheet.write_merge(row_no, row_no, 0, 7, 'Bank Ledger', company_address)

        row_no += 1    
        sheet.write_merge(row_no,row_no,0,7, self.bank_account_id.display_name, company_address)
        row_no += 1    
        sheet.write_merge(row_no,row_no,0,7, datetime.datetime.strptime(str(self.from_date),DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%b/%Y') + ' to ' + datetime.datetime.strptime(str(self.to_date),DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%b/%Y'), company_address)    

        row_no += 2
        sheet.row(2).height = 350;
        sheet.col(0).width = 256 * 15
        sheet.write(row_no, 0, 'S.No', header)
        sheet.col(1).width = 256 * 15
        sheet.write(row_no, 1, 'Date', header)
        sheet.col(2).width = 256 * 27
        sheet.write(row_no, 2, 'Branch', header)
        sheet.col(3).width = 256 * 17
        sheet.write(row_no, 3, 'Payment Mode', header)
        sheet.col(4).width = 256 * 17
        sheet.write(row_no, 4, 'Description', header)
        sheet.col(5).width = 256 * 17
        sheet.write(row_no, 5, 'Amount', header)
        sheet.col(6).width = 256 * 17
        sheet.write(row_no, 6, 'Total Amount', header)
        row_no += 1
        s_no = 0
        total_row_no =row_no
        for data in self.get_data():
            if data['amount'] > 0.00:
                s_no += 1
                sheet.write(row_no, 0, s_no , answer)
                sheet.write(row_no, 1, datetime.datetime.strptime(str(data['date']),DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%b/%Y') if data['date'] else '' , answer)
                sheet.write(row_no, 2, data['school'] , answer)
                sheet.write(row_no, 3, data['payment_mode'] or '', answer)
                sheet.write(row_no, 4, data['description'] or '', answer)
                sheet.write(row_no, 5, '%.2f' % data['amount'] , answer)
                #sheet.write(row_no, 6, '%.2f' % data['total'] , answer)
                row_no += 1
        
        
        total_amounts = []
        for data in self.get_data():
            if data['amount'] > 0.00:
                total_amounts.append(data['amount'])
        list_len = len(total_amounts)
        index_list = 0
        for data in total_amounts:
            total_amount = 0.00
            for amount in total_amounts[index_list:list_len]:
                total_amount += amount
            sheet.write(total_row_no, 6, '%.2f' % total_amount , answer)
            total_row_no += 1
            index_list += 1
        
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data
    
    @api.multi
    def bank_ledger_all_detail_excel_report(self):
        if not self.from_data():
            raise ValidationError(_("No record found..!"))
        data = base64.encodestring(self.from_data())
        attach_vals = {
            'name':'%s.xls' % ('Bank Ledger All'),
            'datas':data,
            'datas_fname':'%s.xls' % ('Bank Ledger All'),
         }
        doc_id = self.env['ir.attachment'].create(attach_vals)
        return {
            'type': 'ir.actions.act_url',
            'url':'web/content/%s?download=true'%(doc_id.id),
            'target': 'self',
        }
    
