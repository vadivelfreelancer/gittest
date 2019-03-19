import odoo
from odoo import http
from odoo.http import request
from odoo.api import Environment
from odoo import SUPERUSER_ID
from odoo.addons.web.controllers.main import Session
import datetime
import json
import logging
# from openpyxl.pivot import record
from datetime import date, datetime as dt
from odoo.exceptions import UserError,ValidationError
# from docutils.languages import fa
_logger = logging.getLogger(__name__)
from odoo.addons.web.controllers.main import Home,serialize_exception,content_disposition
from odoo.tools.translate import _
import base64

def throwError(msg):
    return {
        'response': 'failure',
        'error': {
            'message': msg
        }
    }
    
def PayTMerror(code, msg):
    return {
        'errorcode': code,
        'error': {
            'message': msg
        }
    }    
    
    
def date_format(date_string):
    try:
        return dt.strftime( dt.strptime(date_string, "%Y-%m-%d"), "%Y-%m-%d" )
    except:
        return False
    
class ChellanController(Session):

    @http.route('/web/bank/get_student_details', type='json', auth="none")
    def get_student_details(self, Client_Code, URN, userId, UserPwd):
        if not Client_Code or not URN or not userId or not UserPwd:
            return throwError("All the arguements are mandatory!")
        user = request.env['res.users'].sudo().search([('login', '=', userId)])
        if not user:
            return throwError("Invalid login!")
        log_uid = request.session.authenticate(db=request.session.db, login=userId, password=UserPwd)
        if log_uid:
            adm_obj = request.env['pappaya.admission'].sudo().search(['|','|',('admission_no','=',URN),('res_no','=',URN),('virtual_acc_no','=',URN)], limit=1)
            if not adm_obj:
                return throwError("Invalid URN!")
            student_details = {
                'name' :adm_obj.sur_name+' '+adm_obj.name if adm_obj.sur_name else adm_obj.name,
                'father_name':adm_obj.father_name,
                'course_package': adm_obj.package_id.name,
                'branch':adm_obj.branch_id.name,
                'admission_no': adm_obj.admission_no or adm_obj.res_no,
                'residential_type':adm_obj.residential_type_id.name,
                }
        else:
            return throwError("Invalid login!")
        return {
            'response':'success',
            'student_details':student_details
            }

    @http.route('/web/bank/insert_paid_details', type='json', auth="none")
    def insert_paid_details(self, Client_Code, URN, Amount, Transaction_Date, IBANK_Transaction_Id,Pay_Mode, 
                            ISure_Id='', MICR_CODE='', Bank_Name='', Branch_Name='', Instrument_Number='', userId='', UserPwd='', Instrument_date=''):
        if not userId or not UserPwd:
            return throwError("userId and UserPwd are mandatory!.")
        user = request.env['res.users'].sudo().search([('login', '=', userId)])
        if not user:
            return throwError("Invalid login!")
        log_uid = request.session.authenticate(db=request.session.db, login=userId, password=UserPwd)
        if log_uid:
            if not IBANK_Transaction_Id:
                return throwError("IBANK_Transaction_Id is mandatory!.")
            if request.env['bank.challan.transaction'].sudo().search([('ibank_transaction_id','=',IBANK_Transaction_Id)]):
                return throwError("Given IBANK_Transaction_Id is already exists!")
            if not URN:
                return throwError("URN is mandatory!.")
            if not request.env['pappaya.admission'].sudo().search(['|','|',('admission_no','=',URN),('res_no','=',URN),('virtual_acc_no','=',URN)]):
                return throwError("Invalid URN!")
            if not Amount > 0.0:
                return throwError("Amount should be greater than 0.0!")
            
    #         if request.env['bank.challan.transaction'].sudo().search([('instrument_no','=',Instrument_Number)]):
    #             return throwError("Given Instrument_Number is already exists!")
            
            if Pay_Mode not in ['C','F','L']:
                return throwError("Invalid Pay_Mode!")
            if Pay_Mode != 'C': 
                if not MICR_CODE or not Bank_Name or not Branch_Name or not Instrument_Number or not Instrument_date:
                    return throwError("MICR_CODE,Bank_Name,Branch_Name,Instrument_Number,Instrument_date are mandatory for given Pay_Mode!.")
            if not Transaction_Date:
                return throwError("Transaction_Date is mandatory!.")
            if not ISure_Id:
                return throwError("ISure_Id is mandatory!.")
            
    #         if request.env['bank.challan.transaction'].sudo().search([('isure_id','=',ISure_Id)]):
    #             return throwError("Given ISure_Id is already exists!")
            if not Client_Code:
                return throwError("Client_Code is mandatory!.")
            
            if Instrument_date: 
                if date_format(Instrument_date):
                    Instrument_date = date_format(Instrument_date)
                else:
                    return throwError("Incorrect Date Format for Instrument_date Format should be like 'YYYY-MM-DD'")
            if date_format(Transaction_Date):
                Transaction_Date = date_format(Transaction_Date)
            else:
                return throwError("Incorrect Date Format for Transaction_Date Format should be like 'YYYY-MM-DD'")

            bank_challan_vals = {
                'ibank_transaction_id':IBANK_Transaction_Id,
                'urn':URN,
                'amount':Amount,
                'instrument_no':Instrument_Number if Instrument_Number else '',
                'instrument_date':Instrument_date if Instrument_date else '',
                'pay_mode':Pay_Mode,
                'transaction_date':Transaction_Date,
                'isure_id':ISure_Id,
                'micr_code':MICR_CODE if MICR_CODE else '',
                'bank_name': Bank_Name if Bank_Name else '',
                'branch_name': Branch_Name if Branch_Name else '',
                'client_code': Client_Code,
                'user_id':userId,
                'paswd':UserPwd,
                'is_excel':False,
                'clear_flag':'not_cleared'
                }
            try:
                new_id = request.env['bank.challan.transaction'].sudo().create(bank_challan_vals)
                if new_id:
                    return{
                        'responce':'success',
                        'reference_id':new_id.id
                        }
            except:
                request.cr.rollback()
                return{
                    'response':'failure',
                    'error':'Invalid values!'
                    }
        else:
            return throwError("Invalid login!")
        
    """ PayTM Integrations"""

    @http.route('/web/paytm/validate', type='json', auth="none")
    def validate(self, **kw):
        if 'InstituteName' not in request.params:
            return PayTMerror(102, "InstituteName is mandatory!")
        if 'userId' not in request.params or 'UserPwd' not in request.params:
            return PayTMerror(102,"userId and UserPwd are mandatory!.")
        if 'EnrolmentNo' not in request.params:
            return PayTMerror(102,"EnrolmentNo is mandatory!.")
        userId = request.params['userId'];UserPwd = request.params['UserPwd']
        InstituteName = request.params['InstituteName']; EnrolmentNo = request.params['EnrolmentNo']
        user = request.env['res.users'].sudo().search([('login', '=', userId)])
        if not user:
            return PayTMerror(102, "Invalid userId!")
        log_uid = request.session.authenticate(db=request.session.db, login=userId, password=UserPwd)
        if log_uid:
            if not request.env['res.company'].sudo().search([('paytm_institute_name','=',InstituteName.strip())]):
                return PayTMerror(102,"Invalid InstituteName!")
            admission_obj = request.env['pappaya.admission'].sudo().search(['|',('res_no','=',EnrolmentNo),('admission_no','=',EnrolmentNo)])
            if not admission_obj:
                return PayTMerror(102,"Invalid EnrolmentNo!")
            fee_collection_obj = request.env['pappaya.fees.collection'].sudo().search([('enquiry_id','=',admission_obj.id)])
            if fee_collection_obj.pay_due_total > 0.0:
                return {
                    'Name':admission_obj.student_full_name,
                    'Enrolment_no':admission_obj.res_no or admission_obj.admission_no,
                    'Class': admission_obj.course_id.name,
                    'Due_amount': fee_collection_obj.pay_due_total,
                    'error_code':100
                    }
            else:
                return PayTMerror(103, "No pending fees!")
        else:
            return PayTMerror(102, "Invalid UserPwd. Authentication Failed!")

    @http.route('/web/paytm/post_payment', type='json', auth="none")
    def post_payment(self, **kw):
        if 'Order_id' not in request.params:
            return PayTMerror(102,"Order_id is mandatory!.")
        if 'userId' not in request.params or 'UserPwd' not in request.params:
            return PayTMerror(102,"userId and UserPwd are mandatory!.")
        if 'EnrolmentNo' not in request.params:
            return PayTMerror(102,"EnrolmentNo is mandatory!.")
        if 'amount' not in request.params:
            return PayTMerror(102,"amount is mandatory!.")

        userId = request.params['userId']; UserPwd = request.params['UserPwd']
        Order_id = request.params['Order_id'];EnrolmentNo = request.params['EnrolmentNo']
        amount = request.params['amount']
        user = request.env['res.users'].sudo().search([('login', '=', userId)])
        if not user:
            return PayTMerror(102,"Invalid login!")
        log_uid = request.session.authenticate(db=request.session.db, login=userId, password=UserPwd)
        if log_uid:
            if request.env['pappaya.fees.receipt'].sudo().search([('paytm_order_ref','=',Order_id)]):
                return PayTMerror(103, "Duplicate Order_id!")
            admission_obj = request.env['pappaya.admission'].sudo().search(['|',('res_no','=',EnrolmentNo),('admission_no','=',EnrolmentNo)])
            if not admission_obj:
                return PayTMerror(102,"Invalid EnrolmentNo!")
            fee_collection_obj = request.env['pappaya.fees.collection'].sudo().search([('enquiry_id','=',admission_obj.id)])
            pay_mode_id = request.env['pappaya.paymode'].sudo().search([('is_paytm','=',True)])
            if not pay_mode_id:
                pay_mode_id = request.env['pappaya.paymode'].sudo().create({'name':'PayTM','is_paytm':True})
            fee_collection_obj.write({'paytm_order_ref':Order_id, 'pay_amount':amount, 'payment_mode_id':pay_mode_id.id})
            try:
                fee_receipt_dict = fee_collection_obj.fee_pay()
            except:
                request.env.cr.rollback()
                return PayTMerror(104, "Incorrect amount!")
            return {
                "Transaction_status": "success",
                "Receipt_id": fee_receipt_dict['context']['receipt_no'] or '',
                "errorcode":100
                }
        else:
            return PayTMerror(102, "Invalid UserPwd. Authentication Failed!")
            
    @http.route('/web/paytm/statuscheck', type='json', auth="none")
    def statuscheck(self, **kw):
        """ Params : userId, UserPwd, Order_id """
        if 'Order_id' not in request.params:
            return PayTMerror(102, "Order_id is mandatory!.")
        if 'userId' not in request.params or 'UserPwd' not in request.params:
            return PayTMerror(102, "userId and UserPwd are mandatory!.")
        user = request.env['res.users'].sudo().search([('login', '=',request.params['userId'])])
        if not user:
            return PayTMerror(104, "Invalid login!")
        log_uid = request.session.authenticate(db=request.session.db, login=request.params['userId'], password=request.params['UserPwd'])
        if log_uid:
            if request.env['pappaya.fees.receipt'].sudo().search([('paytm_order_ref','=',request.params['Order_id'])]):
                return PayTMerror(103, "Duplicate Order_id!")
            return {'errorcode':100}
        else:
            return PayTMerror(102, "Invalid UserPwd. Authentication Failed!")
 