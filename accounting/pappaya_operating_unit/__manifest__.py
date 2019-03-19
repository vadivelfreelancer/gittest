# Copyright 2015-2017 Eficent
# - Jordi Ballester Alomar
# Copyright 2015-2017 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License: LGPL-3 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Pappaya Operating Unit",
    "summary": "An operating unit (OU) is an organizational entity part of a "
               "company",
    "version": "11.0.1.0.0",
    'author': 'Think42labs',
    'maintainer': 'Pappaya',
    'company': 'Pappaya',
    'website': 'https://www.pappaya.com',
    'category': 'PappayaEd',
    "depends": ["base"],
    "license": "LGPL-3",
    "data": [
        "security/operating_unit_security.xml",
        "security/ir.model.access.csv",
        "view/operating_unit_view.xml",
        "view/res_users_view.xml",
        "data/operating_unit_data.xml",
    ],
    'demo': [
        "demo/operating_unit_demo.xml"
    ],
    'installable': True,
}
