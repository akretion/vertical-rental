# Copyright (C) 2026 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class CreateRentalProduct(models.TransientModel):
    _inherit = "create.rental.product"

    @api.model
    def _prepare_rental_product(self):
        vals = super()._prepare_rental_product()
        vals["must_have_dates"] = False
        return vals
