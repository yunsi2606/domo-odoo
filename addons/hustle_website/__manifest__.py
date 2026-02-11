{
    'name': 'Hustle Website Module',
    'version': '1.0',
    'summary': 'Hustle Website summary',
    'description': 'Longer Hustle Website description',
    'license': 'LGPL-3',
    'author': 'Yout Name',
    'category': 'Website',
    'depends': ['base', 'website'],
    'data': [
        'views/main.xml',
        'views/404.xml',
        'views/contact.xml',
        'views/index.xml',
        'views/login.xml',
        'views/password-reset.xml',
        'views/register.xml',

        # Add for access control for the defined models
        # 'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_frontend': [
            # CSS files
            # 'hustle_website/static/src/css/global.css',

            # JS files
            # 'hustle_website/static/src/js/counter.js',
        ],
    },
    'installable': True,
    'application': False,
}