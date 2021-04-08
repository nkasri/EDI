# -*- coding: utf-8 -*-
{
    'name': "EDI",

    'summary': """
        addon for managing orders and price lists with suppliers""",

    'description': """
        this addons contains:
        - EDI connection creation with suppliers systems
        - downloading price list from suppliers systems
        - uploading orders to suppliers through EDI
    """,

    'author': "Wissal Group",
    'website': "http://www.WissalGroup.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],
    'application': True,
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/sftp_conn.xml',
        'views/warning_wizard.xml',
        'data/sftp_connection.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
