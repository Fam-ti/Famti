# from shutil import move

# from matplotlib.pylab import normal

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo import models
import io
import base64
import xlsxwriter
from datetime import datetime


# class StockLocation(models.Model):
#     _inherit = 'stock.location'

#     serial_prefix = fields.Char(string="Serial Prefix")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_tolling = fields.Boolean(string="Is Tolling")
    logo = fields.Image("Logo", max_width=1920, max_height=1920, default=lambda self: self.env.company.logo)

    so_type = fields.Selection(
        related='sale_id.so_type',
        string="SO Type",
        store=True
    )
    po_type = fields.Selection(
        related='purchase_id.po_type',
        string="PO Type",
        store=True
    )

    parent_location_id = fields.Many2one(
        'stock.location',
        default=lambda self: self.env['stock.location'].search([
            ('complete_name', '=', 'FM/Stock')
        ], limit=1)
    )
    
    def button_validate(self):

        for picking in self:
            for move_line in picking.move_line_ids_without_package:

                if move_line.lot_id:
                    if move_line.lot_id.qc_status != 'passed':
                        raise ValidationError(_(
                            "Lot %s is not QC Passed.\n"
                            "You cannot validate this delivery."
                        ) % (move_line.lot_id.name))

        return super().button_validate()


    def action_dispatched_shipment_excel(self):
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        sheet = workbook.add_worksheet('Dispatch Report')
        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,
            'bg_color': '#FFFF00',
            'border': 1,
        })

        header_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'bg_color': '#FFFF00',
        })

        cell_format = workbook.add_format({
            'border': 1,
            'bg_color': '#DDEBF7',
        })

        number_format = workbook.add_format({
            'border': 1,
            'bg_color': '#DDEBF7',
            'num_format': '#,##0.00',
        })

        date_format = workbook.add_format({
            'border': 1,
            'bg_color': '#DDEBF7',
            'num_format': 'mmm-dd-yyyy',
        })

        grand_total_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'bg_color': '#FFFF00',
            'num_format': '#,##0.00',
        })


        normal_pickings = self.filtered(
            lambda p: p.sale_id.so_type != 'tolling'
        )

        tolling_pickings = self.filtered(
            lambda p: p.sale_id.so_type == 'tolling'
        )


        left_headers = [
            'Customer Name',
            'Sales Order No.',
            'PO #',
            'Weight Lbs',
            '# of pallets',
            'Pick Up Date',
            'Notes'
        ]

        current_month = datetime.today().strftime('%B')
        current_year = datetime.today().strftime('%Y')

        title = f'{current_month} Dispatched Shipments {current_year}'

        sheet.merge_range(
            'A1:G1',
            title,
            title_format
        )

        for col, header in enumerate(left_headers):
            sheet.write(1, col, header, header_format)

        row_left = 2

        grand_weight_left = 0.0
        grand_pallet_left = 0

        for picking in normal_pickings:

            sale = picking.sale_id

            total_weight = 0.0

            for move in picking.move_ids_without_package:
                total_weight += (
                    move.quantity * move.product_id.weight
                )

            pallet_count = len(
                picking.move_line_ids.mapped('result_package_id')
            )

            grand_weight_left += total_weight
            grand_pallet_left += pallet_count

            sheet.write(row_left, 0,picking.partner_id.name or '',cell_format)
            sheet.write(row_left, 1,sale.name or '',cell_format)
            sheet.write(row_left, 2,sale.buyer_po_number or '',)
            sheet.write(row_left, 3,total_weight,number_format)
            sheet.write(row_left, 4,pallet_count,cell_format)

            if picking.scheduled_date:
                sheet.write_datetime(
                    row_left, 5,
                    picking.scheduled_date,
                    date_format
                )

            sheet.write(
                row_left, 6,
                picking.note or '',
                cell_format
            )

            row_left += 1

        sheet.merge_range(row_left, 0,row_left, 2,'Grand Total',grand_total_format)
        sheet.write(row_left, 3,grand_weight_left,grand_total_format)
        sheet.write(row_left, 4,grand_pallet_left,grand_total_format)

        right_headers = [
            'Customer Name',
            'Sales Order No.',
            'PO #',
            'Weight Lbs',
            '# of pallets',
            'Pick Up Date'
        ]

        start_col = 8

        tolling_title = f'{current_month} Toll Slitting {current_year}'

        sheet.merge_range(
            0, start_col,
            0, start_col + 5,
            tolling_title,
            title_format
        )

        for col, header in enumerate(right_headers):
            sheet.write(
                1,
                start_col + col,
                header,
                header_format
            )

        row_right = 2

        grand_weight_right = 0.0
        grand_pallet_right = 0

        for picking in tolling_pickings:

            sale = picking.sale_id

            total_weight = 0.0

            for move in picking.move_ids_without_package:
                total_weight += (
                    move.quantity * move.product_id.weight
                )

            pallet_count = len(
                picking.move_line_ids.mapped('result_package_id')
            )

            grand_weight_right += total_weight
            grand_pallet_right += pallet_count
            sheet.write(row_right, start_col,picking.partner_id.name or '',cell_format)
            sheet.write(row_right, start_col + 1,sale.name or '',cell_format)
            sheet.write(row_right, start_col + 2,sale.buyer_po_number or '',cell_format)
            sheet.write(row_right, start_col + 3,total_weight,number_format)
            sheet.write(row_right, start_col + 4,pallet_count,cell_format)

            if picking.scheduled_date:
                sheet.write_datetime(
                    row_right, start_col + 5,
                    picking.scheduled_date,
                    date_format
                )

            row_right += 1

        sheet.merge_range(row_right, start_col,row_right, start_col + 2,'Grand Total',grand_total_format)
        sheet.write(row_right, start_col + 3,grand_weight_right,grand_total_format)
        sheet.write(row_right, start_col + 4,grand_pallet_right,grand_total_format)

        sheet.set_column('A:A', 35)
        sheet.set_column('B:B', 22)
        sheet.set_column('C:C', 18)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 18)
        sheet.set_column('G:G', 25)

        sheet.set_column('I:I', 35)
        sheet.set_column('J:J', 22)
        sheet.set_column('K:K', 18)
        sheet.set_column('L:L', 15)
        sheet.set_column('M:M', 15)
        sheet.set_column('N:N', 18)

        workbook.close()
        output.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': 'Dispatch_Report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype':
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    
    def action_packing_list_excel(self):

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Packing List')
        header = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        normal = workbook.add_format({
            'border': 1,
        })

        total_fmt = workbook.add_format({
            'bold': True,
            'border': 1,
        })

        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:N', 12)

        picking = self[:1]


        sheet.merge_range('F5:J5', 'PACKING LIST', header)


        sheet.write('A6', 'SUPPLIER: FAM Ti, INC', total_fmt)
        sheet.write('A7', '740 Oval Court')
        sheet.write('A9', 'Burlington, ON L7L 6A9')
    

        sheet.write('A10', f'BUYER : {picking.partner_id.name or ""}', total_fmt)

        address = ', '.join(filter(None, [
            picking.partner_id.street,
            picking.partner_id.city,
            picking.partner_id.zip,
        ]))
        sheet.write('A11', address)


        sheet.write(
            'A14',
            f'Delivery Dated : {picking.scheduled_date.strftime("%d %b %Y") if picking.scheduled_date else ""}'
        )
        sale_order = picking.sale_id
        buyer_po = sale_order.buyer_po_number if sale_order else ''
        sheet.write(
            'A15',
            f'PO Number # {buyer_po or ""}'
        )

        row = 18

        sheet.set_column('A:A', 15) 
        sheet.set_column('B:C', 10) 
        sheet.set_column('D:D', 20) 
        sheet.set_column('E:J', 10)  
        sheet.set_column('K:K', 15) 
        sheet.set_column('L:M', 10)  

        sheet.merge_range(row, 0, row + 1, 0, 'Pallet No', header)
        sheet.merge_range(row, 1, row + 1, 1, 'Roll', header)

        sheet.merge_range(row, 2, row, 3, 'Thickness', header)

        sheet.merge_range(row, 4, row + 1, 4, 'Type', header)

        sheet.merge_range(row, 5, row, 6, 'Width', header)

        sheet.merge_range(row, 7, row, 8, 'Core ID', header)

        sheet.merge_range(row, 9, row, 10, 'Length', header)

        sheet.merge_range(row, 11, row + 1, 11, 'TREATMENT', header)

        sheet.merge_range(row, 12, row, 13, 'Net Wt', header)

        sheet.write(row + 1, 2, 'Mic', header)
        sheet.write(row + 1, 3, 'Guage', header)

        sheet.write(row + 1, 5, 'mm', header)
        sheet.write(row + 1, 6, 'inch', header)

        sheet.write(row + 1, 7, 'mm', header)
        sheet.write(row + 1, 8, 'inch', header)

        sheet.write(row + 1, 9, 'Mtr', header)
        sheet.write(row + 1, 10, 'Feet', header)

        sheet.write(row + 1, 12, 'kgs', header)
        sheet.write(row + 1, 13, 'lbs', header)

        row += 2

        total_kgs = 0
        total_lbs = 0
        for move in picking.move_ids_without_package:
            qty = move.quantity or 0

            lbs = qty * 2.20462
            package_name = ''
            serial_no = ''
            thickness = 0
            gauge = 0
            width_mm = 0
            width_inch = 0
            core_mm = 0
            core_inch = 0
            length_mtr = 0
            length_feet = 0

            if move.move_line_ids:
                move_line = move.move_line_ids[0]

                package_name = move_line.result_package_id.name or ''
                serial_no = move_line.lot_name or ''
            if move.sale_line_id:
                thickness = move.sale_line_id.thickness_val or ''
                gauge = thickness * 4
                width_mm = move.sale_line_id.width_val if move else 0
                width_inch = round(width_mm / 25.4, 2) if width_mm else 0
                core_id = move.sale_line_id.core_id if move else ''
                core_mm = float(core_id) * 25.4 if core_id else 0
                core_inch = core_id or ''
                length_mtr = move.sale_line_id.length_val if move else 0
                length_feet = round(length_mtr * 3.28084, 2) if length_mtr else 0

            elif move.purchase_line_id:
                line = move.purchase_line_id
                thickness = line.thickness_val or 0
                gauge = thickness * 4
                width_mm = line.width_val or 0
                width_inch = round(width_mm / 25.4, 2) if width_mm else 0
                core_id = line.core_id or ''
                core_mm = float(core_id) * 25.4 if core_id else 0
                core_inch = core_id
                length_mtr = line.length_val or 0
                length_feet = round(length_mtr * 3.28084, 2) if length_mtr else 0

            sheet.write(row, 0, package_name, normal)
            sheet.write(row, 1, serial_no, normal)

            sheet.write(row, 2, thickness, normal)
            sheet.write(row, 3, gauge, normal)
            sheet.write(row, 4, move.product_id.name or '', normal)
            sheet.write(row, 5, width_mm, normal)    
            sheet.write(row, 6, width_inch, normal) 

            sheet.write(row, 7, core_mm, normal)    
            sheet.write(row, 8, core_inch, normal)   

            sheet.write(row, 9, length_mtr, normal)      
            sheet.write(row, 10, length_feet, normal)
            sheet.write(row, 11, '', normal)
            sheet.write(row, 12, qty, normal)
            sheet.write(row, 13, lbs, normal)

            total_kgs += qty
            total_lbs += lbs

            row += 1

        sheet.merge_range(row, 0, row, 11, 'TOTAL', total_fmt)
        sheet.write(row, 12, total_kgs, total_fmt)
        sheet.write(row, 13, total_lbs, total_fmt)

        row += 5

        sheet.write(row, 0,
                    'Total Package Weight of Consignment (kg) :',
                    total_fmt)
        sheet.write(row, 4, total_kgs, total_fmt)

        row += 1
        sheet.write(row, 0, 'Total No of Pallet :', total_fmt)
        sheet.write(row, 4, len(picking.move_ids_without_package), total_fmt)

        row += 1
        sheet.write(row, 0, 'Total No of Rolls :', total_fmt)
        sheet.write(row, 4, len(picking.move_ids_without_package), total_fmt)

        row += 1
        sheet.write(row, 0, 'Total Net Weight (lbs) :', total_fmt)
        sheet.write(row, 4, total_lbs, total_fmt)
        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'Packing_List.xlsx',
            'type': 'binary',
            'datas': file_data,
        })


        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
