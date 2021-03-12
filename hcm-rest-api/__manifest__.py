# -*- coding: utf-8 -*-
{
    'name': "HCM REST API",

    'summary': """
        HCM REST API""",

    'description': """
        HCM REST API
    """,

    'author': "SEIF AND KARIM",

    'category': 'developers',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    "application": True,
    "installable": True,
    "auto_install": False,

    'external_dependencies': {
        'python': ['pypeg2', 'requests']
    }
}