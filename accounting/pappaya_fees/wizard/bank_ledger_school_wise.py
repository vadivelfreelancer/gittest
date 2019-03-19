from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
import xlwt
import base64
from datetime import datetime
from io import BytesIO
import datetime
from xlwt import *

class BankLedgerSchoolWise(models.TransientModel):
    _name = "bank.ledger.school.wise"

    school_ids = fields.Many2many('operating.unit','school_bank_ledger_school_wise_rel','company_id','school_id', string='Branch')
    academic_year_id = fields.Many2one('academic.year',string='Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    bank_account_id = fields.Many2one('res.bank', string='Bank Name')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')

    @api.multi
    def get_school_header(self):
        school_list = []
        if len(self.school_ids) == 1:
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
        data=[]
        domain = []
        if self.school_ids:
            domain.append(('school_id','in',self.school_ids.ids))
        if self.academic_year_id:
            domain.append(('academic_year_id','=',self.academic_year_id.id))
        if self.bank_account_id:
            domain.append(('bank_id', '=', self.bank_account_id.id))
        domain.append(('state','in',['requested','approved']))
        deposit_obj = self.env['bank.deposit'].sudo().search(domain, order="id desc",limit=1)
        s_no = 0 
        for obj in deposit_obj:
            s_no += 1
            unclr,clr = 0.0,0.0
            date = datetime.datetime.strptime(str(obj.deposit_date),DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y')
            if obj.state == 'requested':
                unclr += obj.c_amt_deposit
            if obj.state == 'approved':
                clr += obj.c_amt_deposit
            
            data.append({
                        's_no':s_no,
                        'date':date,
                        'school':obj.school_id.name,
                        'opening_balance':obj.opening_bal,
                        'cash_collection':obj.total_cash_amt,
                        'bank_deposit':clr,
                        'closing_balance':obj.closing_bal,
                        'uncleared_deposit':unclr
                        })
        return data
    
    @api.multi
    def from_data(self):
        workbook = xlwt.Workbook()
        company_name = xlwt.easyxf('font: name Times New Roman, height 350, bold on; align: wrap on, vert centre, horiz centre;')
        company_address = xlwt.easyxf('font: name Times New Roman, height 230, bold on; align: wrap on, vert centre, horiz centre;')
        header = xlwt.easyxf('font: name Times New Roman, height 200, bold on,italic off; align: wrap on, vert centre, horiz centre;  borders: top thin, bottom thin, left thin, right thin;')
        answer = xlwt.easyxf('font: name Times New Roman, height 200; borders: top thin, bottom thin, left thin, right thin;')

        sheet_name = 'Cask Book Branch Wise'
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
        sheet.write_merge(row_no, row_no, 0, 7, 'Cask Book Branch Wise', company_address)
            
        row_no += 1    
        sheet.write_merge(row_no,row_no,0,7, self.bank_account_id.display_name, company_address)
#         row_no += 1    
#         sheet.write_merge(row_no,row_no,0,7, datetime.datetime.strptime(str(self.from_date),DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%b/%Y') + ' to ' + datetime.datetime.strptime(str(self.to_date),DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%b/%Y'), company_address)    

        row_no += 2
        sheet.row(row_no).height = 350;
        sheet.col(0).width = 256 * 17
        sheet.write(row_no, 0, 'S.No', header)
        sheet.col(1).width = 256 * 17
        sheet.write(row_no, 1, 'Date', header)
        sheet.col(2).width = 256 * 17
        sheet.write(row_no, 2, 'Branch', header)
        sheet.col(3).width = 256 * 17
        sheet.write(row_no, 3, 'Opening Balance', header)
        sheet.col(4).width = 256 * 17
        sheet.write(row_no, 4, 'Cash Collection', header)
        sheet.col(5).width = 256 * 17
        sheet.write(row_no, 5, 'Bank Deposit', header)
        sheet.col(6).width = 256 * 17
        sheet.write(row_no, 6, 'Closing Balance', header)
        sheet.col(7).width = 256 * 17
        sheet.write(row_no, 7, 'Uncleared Deposit', header)
        row_no += 1
        
        for data in self.get_data():
            sheet.write(row_no, 0, data['s_no'] , answer)
            sheet.write(row_no, 1, data['date'] , answer)
            sheet.write(row_no, 2, data['school'] , answer)
            sheet.write(row_no, 3, '%.2f' % data['opening_balance'] or '', answer)
            sheet.write(row_no, 4, '%.2f' % data['cash_collection'] or '', answer)
            sheet.write(row_no, 5, '%.2f' % data['bank_deposit'] , answer)
            sheet.write(row_no, 6, '%.2f' % data['closing_balance'] , answer)
            sheet.write(row_no, 7, '%.2f' % data['uncleared_deposit'] , answer)
            row_no += 1
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data
    
    @api.multi
    def bank_ledger_school_wise_detail_excel_report(self):
        if not self.from_data():
            raise ValidationError(_("No record found..!"))
        data = base64.encodestring(self.from_data())
        attach_vals = {
            'name':'%s.xls' % ('Cask Book Branch Wise'),
            'datas':data,
            'datas_fname':'%s.xls' % ('Cask Book Branch Wise'),
         }
        doc_id = self.env['ir.attachment'].create(attach_vals)
        return {
            'type': 'ir.actions.act_url',
            'url':'web/content/%s?download=true'%(doc_id.id),
            'target': 'self',
        }