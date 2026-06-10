# Copyright (C) 2026 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models


class CreateRentalProduct(models.TransientModel):
    _inherit = "create.rental.product"

    @api.model
    def default_get(self, fields_list):
        if self.env.context.get("active_model") == "product.template":
            hw_product_tmpl = self.env["product.template"].browse(
                self.env.context["active_id"]
            )
            if len(hw_product_tmpl.product_variant_ids) != 1:
                # Bypass super() qui contient un assert == 1
                res = super(CreateRentalProduct, self).default_get(fields_list)
                hw_product_tmpl_ctx = hw_product_tmpl.with_context(display_default_code=False)
                res["name"] = _("Rental of a {}").format(hw_product_tmpl_ctx.display_name)
                if hw_product_tmpl.default_code:
                    res["default_code"] = _("RENT-{}").format(hw_product_tmpl.default_code)
                if hw_product_tmpl.product_variant_ids:
                    res["hw_product_id"] = hw_product_tmpl.product_variant_ids[0].id
                else:
                    for attribute_line in hw_product_tmpl.attribute_line_ids:
                        for ptav in attribute_line.product_template_attribute_value_ids:
                            hw_product = hw_product_tmpl._create_product_variant(ptav)
                            if hw_product:
                                res["hw_product_id"] = hw_product.id
                                break
                        if res.get("hw_product_id"):
                            break
                return res
        return super().default_get(fields_list)


    @api.model
    def _prepare_rental_product(self):
        vals = super()._prepare_rental_product()
        vals["tracking"] = "none"
        return vals


    def create_rental_product(self):
        res = super().create_rental_product()
        rental_product = self.env["product.product"].browse(res["res_id"])
        self._apply_rental_product_translations(rental_product)
        self.hw_product_id.rental_product_tmpl_id = rental_product.product_tmpl_id
        return res

    def _get_rental_prefix(self, lang_code):
        return _("[RENT]")

    def _apply_rental_product_translations(self, rental_product):
        active_langs = self.env["res.lang"].get_installed()
        for lang_code, _lang_name in active_langs:
            new_name = "%s %s" % (self._get_rental_prefix(lang_code), self.hw_product_id.with_context(lang=lang_code).display_name)
            rental_product.with_context(lang=lang_code).write({"name": new_name})

