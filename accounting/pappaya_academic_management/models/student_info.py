from odoo import fields, models, api


class StudentInfo(models.Model):
    _name = 'student.info'
    _rec_name = 'student_name_first'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    admission_number = fields.Char(string="Admission No.")
    branch = fields.Many2one("branch.branch",string="Branch")
    group = fields.Many2one("pappaya.group",string="Group")
    course = fields.Many2one("course.course", string="Course")
    batch = fields.Many2one("batch.batch", string="Batch")
    sub_batch = fields.Many2one("subbatch.line", string="Sub Batch")
    section = fields.Many2one("section.line", string="Section")

    student_name_first = fields.Char(string="Student Name")
    student_name_last = fields.Char()
    date_of_birth = fields.Date(string="Date Of Birth")
    gender = fields.Selection(string="Gender", selection=[('male', 'Male'), ('female', 'Female'), ])
    aadhar_no = fields.Char(string="Aadhar Number")
    blood_group = fields.Selection([
        ('a+', "A+"), ('a-', "A-"), ('b+', "B+"),
        ('b-', "B-"), ('ab+', "AB+"), ('ab-', "AB-"),
        ('o+', "O+"), ('o-', "O-")],
        "Blood Group", )
    religion = fields.Many2one('religion.religion',string="Religion")
    caste = fields.Many2one('caste.caste',string="Caste")

    father_name = fields.Char(string="Father Name")
    mother_name = fields.Char(string="Mother Name")
    father_occupation = fields.Many2one("occupation.occupation", string="Father Occupation")
    father_email = fields.Char(string="Father E-mail")
    father_mobile = fields.Char(string="Father Mobile")
    mother_mobile = fields.Char(string="Mother Mobile")
    section = fields.Char(string="Section")
    sub_section = fields.Char(string="Sub Section")
    university = fields.Many2one('university.line',string="University ")

    # academic info
    date_of_admission = fields.Date(string="Date of Admission/Reservation")
    date_of_joining = fields.Date(string="Date of Joining")
    first_language = fields.Many2one('first.language', string="First Language")
    second_language = fields.Many2one('second.language', string="Second Language")
    third_language = fields.Many2one('third.language', string="Third Language")

    # present_ address

    present_street = fields.Char(string="Street")
    present_city = fields.Many2one('city.city', string="City")
    present_district = fields.Many2one('district.district', string="District")
    present_mandal = fields.Many2one('mandal.mandal', string="Mandal")
    present_state = fields.Many2one('res.country.state', string="State")
    present_country = fields.Many2one('res.country', string="Country")
    present_zipcode = fields.Char(string="Zip Code")

    # permanent_ address

    permanent_street = fields.Char(string="Street")
    permanent_city = fields.Many2one('city.city', string="City")
    permanent_district = fields.Many2one('district.district', string="District")
    permanent_mandal = fields.Many2one('mandal.mandal', string="Mandal")
    permanent_state = fields.Many2one('res.country.state', string="State")
    permanent_country = fields.Many2one('res.country', string="Country")
    permanent_zipcode = fields.Char(string="Zip Code")

    # ntr student info father_

    father_qualification = fields.Char(string="Qualification")
    father_annual_income = fields.Char(string="Annual Income")
    father_alive = fields.Selection(string="Alive", selection=[('alive', 'Alive'), ('expired', 'Expired'), ])
    father_profession = fields.Char(string="Profession")
    father_party_worker = fields.Many2one(string="Parent Party Worker")
    father_date_of_expiry = fields.Date(string="Date Of Expiry")
    father_cause_of_death = fields.Char(string="Cause Of Death")
    father_designation = fields.Char(string="Designation")

    # ntr student info mother

    mother_qualification = fields.Char(string="Qualification")
    mother_annual_income = fields.Char(string="Annual Income")
    mother_alive = fields.Selection(string="Alive", selection=[('alive', 'Alive'), ('expired', 'Expired'), ])
    mother_profession = fields.Char(string="Profession")
    mother_party_worker = fields.Many2one(string="Parent Party Worker")
    mother_date_of_expiry = fields.Date(string="Date Of Expiry")
    mother_cause_of_death = fields.Char(string="Cause Of Death")
    mother_designation = fields.Char(string="Designation")

    # gen info
    admission_ref = fields.Char(string="Admission Ref ")
    contact_no = fields.Char(string="Contact No")
    admission_type = fields.Selection(string="Admission Type", selection=[('free', 'Free'), ('paid', 'Paid'), ])
    cause = fields.Many2one("cause.cause", string="Cause")
    concession_ref = fields.Char(string="Concession Ref")
    no_of_brothers = fields.Char(string="No Of Brothers")
    no_of_sisters = fields.Char(string="No Of Sisters")
    join_of_year = fields.Char(string="Join Of Year")
    previous_class = fields.Char(string="Previous Class,Place")


class Religion(models.Model):
    _name = 'religion.religion'
    _rec_name = 'name'

    name = fields.Char(string="Religion")


class Caste(models.Model):
    _name = 'caste.caste'
    _rec_name = 'name'

    name = fields.Char(string="Caste")


class Occupation(models.Model):
    _name = 'occupation.occupation'
    _rec_name = 'name'

    name = fields.Char(string="Occupation")


class FirstLang(models.Model):
    _name = 'first.language'
    _rec_name = 'name'

    name = fields.Char(string="First Language")


class SecondLang(models.Model):
    _name = 'first.language'
    _rec_name = 'name'

    name = fields.Char(string="Second Language")


class SecondLang(models.Model):
    _name = 'first.language'
    _rec_name = 'name'

    name = fields.Char(string="Third Language")


class Cause(models.Model):
    _name = 'cause.cause'
    _rec_name = 'name'

    name = fields.Char(string='Cause')








