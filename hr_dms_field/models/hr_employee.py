# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class HrEmployee(models.Model):
    # hr.employee.base was removed in Odoo 19; attach the DMS field mixin to
    # hr.employee (and hr.employee.public) directly instead of the old base.
    _inherit = ["hr.employee", "dms.field.mixin"]
