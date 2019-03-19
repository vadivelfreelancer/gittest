# Copyright 2016 Henry Zhou (http://www.maxodoo.com)
# Copyright 2016 Rodney (http://clearcorp.cr/)
# Copyright 2012 Agile Business Group
# Copyright 2012 Therp BV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import odoo.http as http
from odoo.http import request
from odoo.addons.web.controllers.main import ExcelExport
from odoo.exceptions import UserError
from odoo import api, _
import werkzeug

import pdfkit
import io
from io import StringIO as cStringIO
import xlsxwriter
from yattag import Doc

class ExcelExportView(ExcelExport):
    def __getattribute__(self, name):
        if name == 'fmt':
            raise AttributeError()
        return super(ExcelExportView, self).__getattribute__(name)

    @http.route('/web/export/xls_view', type='http', auth='user')
    def export_xls_view(self, data, token):
        data = json.loads(data)
        model = data.get('model', [])
        columns_headers = data.get('headers', [])
        rows = data.get('rows', [])
        description = request.env[data.get('model')]._description or "PDFfile"

        return request.make_response(
            self.xl_export(columns_headers, rows, description),
            headers=[
                ('Content-Disposition', 'attachment; filename="%s"' % description + ".xls"),
                ('Content-Type', self.content_type)
            ],
            cookies={'fileToken': token}
        )

    def xl_export(self, fields, rows, description):
        if len(rows) > 65535:
            raise UserError(_('Too many rows to export(limit: 65535). Consider splitting the export.'))
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Sheet')

        # Remove Grid
        worksheet.hide_gridlines(2)

        title_format = workbook.add_format({'bold': 1, 'align': 'left', 'valign': 'vcenter', 'text_wrap': 1})
        header_format = workbook.add_format({'font_name': 'Ubuntu', 'size': 12, 'bold': 1, 'bg_color': '#1a86f9', 'border': 1, 'text_wrap': 1, 'align': 'center', 'valign': 'vcenter'})
        cell_format = workbook.add_format({'font_name': 'Ubuntu', 'size': 12, 'bg_color':'#eaeded','border': 1, 'text_wrap': 1, 'align': 'center', 'valign': 'vcenter' })
        footer_format = workbook.add_format({'font_name': 'Ubuntu', 'size': 12, 'bold': 1, 'bg_color': '#DF3A01', 'border': 1, 'text_wrap': 1, 'align': 'center', 'valign': 'vcenter'})
        
        worksheet.merge_range('A1:D1', description, title_format)
        for i, field in enumerate(fields):
            worksheet.set_column(0, i, 15)
            worksheet.write(1, i, field, header_format)
        
        footer_value = [0 for field in fields]
        for row_index, row in enumerate(rows):
            for cell_index, cell_value in enumerate(row):
                if isinstance(cell_value, int) or isinstance(cell_value, float):
                    footer_value[cell_index] += cell_value
                worksheet.write(row_index+2, cell_index, cell_value, cell_format)
        
        for index, value in enumerate(footer_value):
            value = value if value else ""
            worksheet.write(row_index+3, index, value, footer_format)

        workbook.close()
        return output.getvalue()


class PdfExportView(http.Controller):

    @http.route('/web/export/pdf_view', type='http', auth='user')
    def export_pdf_view(self, data, token):
        data = json.loads(data)
        description = request.env[data.get('model')]._description or "PDFfile"

        doc, tag, text = Doc().tagtext()
        with tag('html'):
            with tag('head'):
                doc.stag('link', rel="stylesheet", href='https://maxcdn.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css')
                with tag('script', src='https://maxcdn.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js'):
                    text("")
            with tag('body'):
                with tag('div', klass="container"):
                    with tag('h3'):
                        text(description)
                    with tag('table', klass='table table-bordered'):
                        with tag('thead'):
                            for header in data.get('headers'):
                                with tag('th'):
                                    text(header)
                        with tag('tbody'):
                            for row in data.get('rows'):
                                with tag('tr'):
                                    for col in row:
                                        with tag('td'):
                                            text(col)

        doc_string = doc.getvalue()
        pdf = pdfkit.from_string(doc_string, False)
        return request.make_response(
            pdf,
            headers=[('Content-Disposition', 'attachment; filename="%s.pdf"' % description), 
            ('Content-Type', "application/pdf")],
            cookies={'fileToken': token}
        )