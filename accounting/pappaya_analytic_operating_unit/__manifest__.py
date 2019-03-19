# Copyright 2016-17 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Pappaya Analytic Operating Unit",
    "version": "11.0.1.0.0",
    "author": "Think42labs",
    "license": "LGPL-3",
    'website': 'http://www.pappaya.com',
    'category': 'PappayaEd',
    "depends": ["analytic", "pappaya_operating_unit"],
    "data": [
        "views/analytic_account_view.xml",
        "security/analytic_account_security.xml",
    ],
    'installable': True,
}
