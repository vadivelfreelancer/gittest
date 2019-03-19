# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import except_orm, ValidationError, UserError

class BatchTransaction_Dt(models.Model):
    _name = 'batchtransaction.dt'
    _description = "BATCHTRANSACTION_DT fr CO entry"

    # sta_batchtransactionid - table id
    pappaya_batchtransactionid = fields.Char('PAPPAYA_BATCHTRANSACTIONID')
    pappaya_userid = fields.Many2one('res.users', 'PAPPAYA_USERID')

class Transaction_DT(models.Model):
    _name = 'transaction.dt'
    _description = 'TRANSACTION_DT orcale updt acc.mov'

    # sta_transactionid - table id
    # sta_batchtransactionid =
    sta_batchtransactionid = fields.Char('STA_BATCHTRANSACTIONID')
    vouchertypeslno = fields.Char('VOUCHERTYPESLNO')
    transdate = fields.Char('TRANSDATE')
    serverdate = fields.Char('SERVERDATE')
    accbranchslno = fields.Char('ACCBRANCHSLNO')
    narration = fields.Text('NARRATION')
    finslno = fields.Char('FINSLNO')
    moduleslno = fields.Char('MODULESLNO')
    transtype = fields.Char('TRANSTYPE')
    student_emp_id = fields.Char('STUDENT_EMP_ID')
    chq_imp_pt_no = fields.Char('CHQ_IMP_PT_NO')
    pappaya_transactionid = fields.Char('PAPPAYA_TRANSACTIONID')
    pappaya_voucherno = fields.Char('PAPPAYA_VOUCHERNO')
    pappaya_userid = fields.Char('PAPPAYA_USERID')
    nerp_transactionid = fields.Char('NERP_TRANSACTIONID')
    nerp_gvoucherno = fields.Char('NERP_GVOUCHERNO')
    status = fields.Char('STATUS') #0-PENING,1-POSTED,2-NOT POSTED
    transaction_ddt_o2m = fields.One2many('transaction.ddt','sta_transactionid', string="Line")


class Transaction_DDT(models.Model):
    _name = 'transaction.ddt'
    _description = 'TRANSACTION_DDT orcale updt acc.mov.lin'

    # STA_TRANSACTIONDDTID - table id
    sta_transactionid = fields.Many2one('transaction.dt','STA_TRANSACTIONID')
    subledgerslno = fields.Char('SUBLEDGERSLNO')
    accbranchslno = fields.Char('ACCBRANCHSLNO')
    amount = fields.Char('AMOUNT')
    drorcr = fields.Char('DRORCR')
