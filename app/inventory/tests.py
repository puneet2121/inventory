from io import BytesIO

import openpyxl
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from app.employee.models import EmployeeProfile
from app.inventory.models import Category, Inventory, Product, InventoryImage


class InventoryImportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='importer', password='pass123')
        EmployeeProfile.objects.create(user=self.user, role='manager', tenant_id=101)
        self.client.force_login(self.user)

    def test_import_inventory_from_xlsx(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Product Name", "Model", "Category", "Cost", "Price", "Description", "Location", "Quantity", "Image URLs"])
        ws.append(["Widget", "W-1", "Tools", "₹12,500.50", "$20,000.75", "Basic widget", "Warehouse A", "1,200", "widget.jpg"])

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        upload = SimpleUploadedFile(
            'inventory.xlsx',
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        response = self.client.post(
            reverse('inventory:import_inventory'),
            data={'file': upload},
            follow=True,
        )

        self.assertRedirects(response, reverse('inventory:item_list'))
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Category.objects.count(), 1)
        inventory = Inventory.objects.get()
        self.assertEqual(inventory.quantity, 1200)
        self.assertEqual(inventory.location, "Warehouse A")

    def test_import_inventory_from_csv(self):
        csv_content = (
            "Product Name,Model,Category,Cost,Price,Description,Location,Quantity,Image URLs\n"
            "Widget CSV,W-2,Hardware,\"₹1,599.00\",\"1,999.95\",CSV widget,Warehouse B,\"3,500\",\n"
        )

        upload = SimpleUploadedFile(
            'inventory.csv',
            csv_content.encode('utf-8'),
            content_type='text/csv'
        )

        response = self.client.post(
            reverse('inventory:import_inventory'),
            data={'file': upload},
            follow=True,
        )

        self.assertRedirects(response, reverse('inventory:item_list'))
        self.assertEqual(Product.objects.count(), 1)
        inventory = Inventory.objects.get()
        self.assertEqual(inventory.quantity, 3500)
        self.assertEqual(inventory.location, "Warehouse B")

    def test_import_defaults_for_missing_location_and_negative_quantity(self):
        csv_content = (
            "Product Name,Model,Category,Cost,Price,Description,Location,Quantity,Image URLs\n"
            "Negative Item,N-1,Test,100,200,Desc,, -5,\n"
        )
        upload = SimpleUploadedFile(
            'neg.csv',
            csv_content.encode('utf-8'),
            content_type='text/csv'
        )

        response = self.client.post(
            reverse('inventory:import_inventory'),
            data={'file': upload},
            follow=True,
        )

        self.assertRedirects(response, reverse('inventory:item_list'))
        inventory = Inventory.objects.get()
        self.assertEqual(inventory.quantity, 0)
        self.assertEqual(inventory.location, "Warehouse")

    @override_settings(PUBLIC_MEDIA_BASE_URL='https://public-bucket.s3.ap-south-1.amazonaws.com/media')
    def test_import_inventory_with_image_urls(self):
        csv_content = (
            "Product Name,Model,Category,Cost,Price,Description,Location,Quantity,Image URLs\n"
            "Image Item,IM-1,Cables,100,150,Desc,Warehouse,10,front.jpg|https://static.example.com/back.png\n"
        )
        upload = SimpleUploadedFile(
            'images.csv',
            csv_content.encode('utf-8'),
            content_type='text/csv'
        )
        response = self.client.post(
            reverse('inventory:import_inventory'),
            data={'file': upload},
            follow=True,
        )
        self.assertRedirects(response, reverse('inventory:item_list'))
        self.assertEqual(InventoryImage.objects.count(), 2)
        urls = set(InventoryImage.objects.values_list('image_url', flat=True))
        self.assertIn('https://public-bucket.s3.ap-south-1.amazonaws.com/media/front.jpg', urls)
        self.assertIn('https://static.example.com/back.png', urls)
