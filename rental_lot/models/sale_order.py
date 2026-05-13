# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def generate_lot(self):
        rec = super().generate_lot()
        # check if auto_generate_prodlot exist as field (avoiding dependencies)
        if not hasattr(self.env["product.product"], "auto_generate_prodlot"):
            return rec
        for rec in self:
            index_lot = rec._get_max_lot_index() + 1
            for line in rec.order_line.filtered(
                lambda l: l.product_id.rented_product_id
            ):
                rented = line.product_id.rented_product_id
                if (
                    rented.auto_generate_prodlot
                    and not line.rented_lot_id
                    and rented.tracking != "none"
                ):
                    lot_id = line.create_lot(index_lot)
                    index_lot += 1
                    line.rented_lot_id = lot_id


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    rented_lot_id = fields.Many2one(
        "stock.lot",
        string="Rented Serial Number",
        copy=False,
        compute="_compute_rented_lot_id",
        store=True,
        readonly=False,
    )

    def _prepare_vals_lot_number(self, index_lot):
        res = super()._prepare_vals_lot_number(index_lot)
        if self.product_id.rented_product_id:
            res["product_id"] = self.product_id.rented_product_id.id
        return res

    @api.depends("rented_product_id")
    def _compute_rented_lot_id(self):
        for sol in self:
            if sol.rented_product_id != sol.rented_lot_id.product_id:
                sol.rented_lot_id = False

    rented_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Rented Product",
        related="product_id.rented_product_id",
    )

    def _prepare_new_rental_procurement_values(self, group=False):
        vals = super()._prepare_new_rental_procurement_values(group=group)
        if self.rented_lot_id:
            vals["restrict_lot_id"] = self.rented_lot_id.id
        return vals

    def write(self, vals):
        res = super().write(vals)
        if "rented_lot_id" in vals and self.order_id.state not in ["sale", "done"]:
            self.move_ids.write({"restrict_lot_id": vals.get("rented_lot_id")})
        elif "rented_lot_id" in vals:
            raise UserError(_("You can't change the lot on confirmed sale order."))
        return res
