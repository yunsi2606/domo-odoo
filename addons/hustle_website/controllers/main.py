from odoo import http
from odoo.http import request

class FrontPageController(http.Controller):
    @http.route(['/'], type='http', auth="public", website=True)
    def list_blogs(self, **kwargs):
        return request.render("hustle_website.index")

class FrontPageController(http.Controller):
    @http.route(['/404'], type='http', auth="public", website=True)
    def list_blogs(self, **kwargs):
        return request.render("hustle_website.fourofour")

class FrontPageController(http.Controller):
    @http.route(['/login'], type='http', auth="public", website=True)
    def list_blogs(self, **kwargs):
        return request.render("hustle_website.login")

class FrontPageController(http.Controller):
    @http.route(['/register'], type='http', auth="public", website=True)
    def list_blogs(self, **kwargs):
        return request.render("hustle_website.register")

class FrontPageController(http.Controller):
    @http.route(['/password-reset'], type='http', auth="public", website=True)
    def list_blogs(self, **kwargs):
        return request.render("hustle_website.passwordreset")

class FrontPageController(http.Controller):
    @http.route(['/contact'], type='http', auth="public", website=True)
    def list_blogs(self, **kwargs):
        return request.render("hustle_website.contact")
