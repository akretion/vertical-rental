# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSaleRentalLot(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rental_prod = cls.env.ref("sale_rental.rent_product_product_25")
        cls.rented_prod = cls.env.ref("product.product_product_25")
        cls.rented_prod.tracking = "serial"

        cls.serial = cls.env["stock.lot"].create(
            {
                "product_id": cls.rented_prod.id,
                "product_uom_id": cls.rented_prod.uom_id.id,
                "company_id": cls.env.ref("base.main_company").id,
            }
        )
        cls.warehouse = cls.env.ref("stock.warehouse0")
        quant = cls.env["stock.quant"].create(
            {
                "product_id": cls.rented_prod.id,
                "location_id": cls.warehouse.lot_stock_id.id,
                "lot_id": cls.serial.id,
                "inventory_quantity": 1,
            }
        )
        quant.action_apply_inventory()

        cls.so = cls.env["sale.order"].create(
            {
                "partner_id": cls.env.ref("base.res_partner_1").id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.rental_prod.id,
                            "start_date": "2049-01-01",
                            "end_date": "2049-01-10",
                            "rental_qty": 1,
                            "rented_lot_id": cls.serial.id,
                        },
                    ),
                ],
            }
        )

        cls.so.action_confirm()

    def test_rented_serial_number(self):
        self.so.picking_ids.action_assign()

        rental = self.env["sale.rental"].search(
            [("start_order_line_id", "=", self.so.order_line[0].id)]
        )
        self.assertEqual(rental.rented_lot_id, self.serial)
        self.assertEqual(self.so.picking_ids.move_ids.restrict_lot_id, self.serial)

    def test_change_rented_serial_number(self):
        company = self.env.ref("base.main_company")
        new_serial = self.env["stock.lot"].create(
            {
                "name": "NewSerial",
                "product_id": self.rented_prod.id,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        line = self.so.order_line[0]
        with self.assertRaises(UserError) as m:
            line.rented_lot_id = new_serial
        self.assertIn("You can't change the lot", m.exception.args[0])

    def test_auto_generated_rented_lot(self):
        self.rented_prod.product_tmpl_id.auto_generate_prodlot = True
        so = self.env["sale.order"].create(
            {
                "partner_id": self.env.ref("base.res_partner_1").id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.rental_prod.id,
                            "start_date": "2049-01-01",
                            "end_date": "2049-01-10",
                            "rental_qty": 1,
                        },
                    ),
                ],
            }
        )
        so.action_confirm()
        rental = self.env["sale.rental"].search(
            [("start_order_line_id", "=", so.order_line.id)]
        )
        self.assertTrue(so.order_line.rented_lot_id)
        self.assertTrue(rental.rented_lot_id)
        self.assertEqual(rental.rented_lot_id.product_id, self.rented_prod)
