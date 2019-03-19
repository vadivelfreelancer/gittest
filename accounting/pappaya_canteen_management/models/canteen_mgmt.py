# -*- coding: utf-8 -*-
###############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import logging
from odoo import models, fields, _
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo import tools, api
from odoo.exceptions import ValidationError
import re
import base64
import time
import datetime
from base64 import b64encode

import serial
BAUD_RATE = 9600
BIO_BYTES1 = 4

_logger = logging.getLogger(__name__)


import socket
HOST = '172.20.200.163' # Enter IP or Hostname of your server
PORT = 1500 # Pick an open Port (1000+ recommended), must match the server port

class pappaya_canteen_mgmt_billing(models.Model):
    _name = "pappaya.canteen.mgmt.billing"
    _description = "Canteen mgmt Billing"
    _rec_name = 'sequence'
    _order = 'sequence desc'
    # @api.model
    # def _default_company(self):
    #     user_id = self.env['res.users'].browse(self.env.uid)
    #     return user_id.company_id

    # @api.one
    # @api.constrains('contact_no')
    # def _check_unique_name(self):
    #     if self.contact_no:
    #         if len(self.search(
    #                 [('contact_no', '=', self.contact_no), ('mobile_std_code', '=', self.mobile_std_code)])) > 1:
    #             raise ValidationError("Visitor already exists")
    #
    # @api.one
    # @api.constrains('contact_no')
    # def validate_mobile(self):
    #     if self.contact_no:
    #         if re.match("^[0-9]+$", self.contact_no) != None:
    #             return True
    #         else:
    #             raise ValidationError(' Please enter a Valid Contact number')

    # @api.one
    # @api.depends('name', 'contact_no')
    # def _concat_name_no(self):
    #     if self.name and self.contact_no:
    #         self.display_name = self.name + ", " + self.contact_no
    #         if self.mobile_std_code:
    #             self.display_name = self.name + ", " + self.mobile_std_code + " " + self.contact_no
    #     else:
    #         self.display_name = self.name

    @api.model
    def _compute_sequence(self):
        prefix = 'bill-C'
        sequence = 'New'
        active_academic_year = self.env['academic.year'].search([('is_active', '=', True)], limit=1)
        if active_academic_year:
            date_split = active_academic_year.start_date.split('-')
            prefix = 'BILL-C'#date_split[0][2:]
            if prefix:
                students_details = self.search([('id', '>', 0)]).ids
                sequence_no = len(students_details) + 1
                sequence_no = "%0.5d" % sequence_no
                sequence = str(prefix) + '5' + sequence_no
        return sequence

    @api.one
    @api.depends('billing_line_o2m_id')
    def _compute_price_total(self):
        total = 0.0
        if self.billing_line_o2m_id:
            for i in self.billing_line_o2m_id:
                total += i.sum_amount

        self.total_amount = total

    sequence = fields.Char(string='Bill No.', default=_compute_sequence,size=50)
    student_id= fields.Many2one('pappaya.student', 'Student')
    company_id = fields.Many2one('res.company', 'School', select=True)
    billing_line_o2m_id = fields.One2many('pappaya.canteen.mgmt.billing.line', 'billing_id', string="Products")
    total_amount = fields.Float('Total Amount', compute=_compute_price_total)
    status = fields.Selection([('draft','Draft'),('done','Amount Debited/Done')], string='Status', default='draft')
    is_rfid_verified = fields.Boolean('RFID Verified')
    is_fingerprint_verified = fields.Boolean('FingerPrint Verified')
    

    @api.multi
    def verify_rfid_and_finger_print(self):
        #Lets loop awaiting for your input
        try:            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST,PORT))
            while True:
                command = b'3'
                s.send(command)
                reply = s.recv(1024)
                if reply:
                    student_id = self.env['pappaya.student'].search([('canteen_rf_card_id','=',str(reply)[1:])])
                    self.student_id = student_id.id    
                    self.is_rfid_verified = True
                    break
            while True:
                if self.student_id:
                    command = b'2'
                    s.send(command)
                    reply = s.recv(1024)
                    if reply and self.student_id.biometric_id == str(reply)[1:]:    
                        self.is_fingerprint_verified = True
                    if self.is_rfid_verified and self.is_fingerprint_verified:
                        if self.student_id.student_wallet_amount > self.total_amount:
                            self.student_id.student_wallet_amount -= self.total_amount
                            self.status = 'done'
                            break
                        else:
                            break
                            raise ValidationError("Insufficient Fund!.")    
            return True
        except:
            print ("##### \n connection Failed!. \n #######")
            raise ValidationError("Device Connection Failure..")        
        
       
#         ser = serial.Serial('/dev/ttyUSB1', BAUD_RATE, timeout=7)
# 
#         try:
#             print ('Wating for RFID to Scan.....')
# 
#             # Wait until a Bio is read
#             bio1 = ser.read(BIO_BYTES1)
#             print ('RFID Found==', bio1)
#             if bio1:
#                 self.is_rfid_verified = True
#             else:
#                 raise ValidationError('The RFID is not matched')
#         except Exception as e:
#             raise ValidationError('The RFID card is not matched')
#             print('Exception message: ' + str(e))



    @api.multi
    def verify_fingerprint(self):
        ser = serial.Serial('/dev/ttyUSB0', BAUD_RATE, timeout=7)
        # while True:
        try:
            print ('Wating for Fingerprint to Scan.....')

            # Wait until a Bio is read
            bio1 = ser.read(BIO_BYTES1)
            print ('Fingerprint Found ========', bio1)
            print (type(bio1))
            if bio1:
                self.is_finerprint_verified = True
                self.status='Done'
            else:
                raise ValidationError('The fingerprint is not matched')
            # break
        except Exception as e:
            raise ValidationError('The fingerprint is not matched')
            print('Exception message: ' + str(e))
            # break



class pappaya_canteen_mgmt_billing_line(models.Model):
    _name = 'pappaya.canteen.mgmt.billing.line'
    _description = "Canteen Puchasing Product"

    billing_id = fields.Many2one('pappaya.canteen.mgmt.billing')
    product_id = fields.Many2one('pappaya.canteen.product')
    amount = fields.Float('Price Per Item', default=0.0)
    quantity = fields.Integer('Quantity', default=1)
    sum_amount = fields.Float('Total Price')

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.amount = self.product_id.amt or 0.0


    @api.onchange('quantity')
    def compute_sum_amount(self):
        if (self.quantity and self.amount) and (self.quantity >0 and self.amount>0):
            self.sum_amount = self.amount * self.quantity


class pappaya_canteen_product(models.Model):
    _name = 'pappaya.canteen.product'
    _description = "Canteen Product"

    name=fields.Char('Name',size=50)
    amt = fields.Integer('Price')

# class pappaya_student(models.Model):
#     _inherit = 'pappaya.student'
# 
#     name=fields.Char('Name')
#     rf_id = fields.Char('RF ID')
#     biometric_id = fields.Char('Biometric ID')
#         
#     @api.multi
#     def enroll_rf_id(self):
#         #Lets loop awaiting for your input
#         try:
#             s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             s.connect((HOST,PORT))
#             while True:
#                 command = b'3'
#                 s.send(command)
#                 reply = s.recv(1024)
#                 if reply == 'Terminate':
#                     break
#                 self.rf_id = str(reply)
#                 print(reply)
#             return True
#         except:
#             print ("##### \n connection Failed!. \n #######")
#             return False
#     
#     @api.multi
#     def enroll_biometric_id(self):
#         #Lets loop awaiting for your input
#         try:
#             s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             s.connect((HOST,PORT))
#             while True:
#                 command = b'3'
#                 s.send(command)
#                 reply = s.recv(1024)
#                 if reply == 'Terminate':
#                     break
#                 self.rf_id = str(reply)
#                 print(reply)
#             return True
#         except:
#             return False
    
    
    
    
    
    
    
    