# Copyright (C) 2026 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class CreateRentalProduct(models.TransientModel):
    _inherit = "create.rental.product"

    @api.model
    def _prepare_rental_product(self):
        vals = super()._prepare_rental_product()
        if self.env.company.rental_duration:
            vals["uom_id"] = self.env.company.rental_uom_id.id
            vals["uom_po_id"] = self.env.company.rental_uom_id.id
            vals["must_have_duration"] = True
        return vals
