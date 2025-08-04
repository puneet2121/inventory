from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from .models import SalesOrder, Invoice, Payment
from app.customers.models import Customer
from app.employee.models import EmployeeProfile
from app.inventory.models import Product, Category


class RefundTestCase(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test customer
        self.customer = Customer.objects.create(
            name='Test Customer',
            city='Test City',
            customer_type='C',
            contact='1234567890'
        )
        
        # Create test employee
        self.employee = EmployeeProfile.objects.create(
            user=self.user,
            employee_id='EMP001',
            department='Sales'
        )
        
        # Create test category and product
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            cost=Decimal('10.00'),
            price=Decimal('20.00'),
            description='Test product description',
            barcode='123456789',
            model='Test Model'
        )
        
        # Create test sales order
        self.sales_order = SalesOrder.objects.create(
            customer=self.customer,
            employee=self.employee,
            status='completed',
            order_number='SO-00001',
            cached_total=Decimal('100.00')
        )
        
        # Create test invoice
        self.invoice = Invoice.objects.create(
            sales_order=self.sales_order,
            payment_status='paid',
            invoice_number='INV-00001',
            total_invoice_amount=Decimal('100.00'),
            cached_paid_amount=Decimal('100.00'),
            created_by=self.user
        )
        
        # Create test payment
        self.payment = Payment.objects.create(
            invoice=self.invoice,
            amount=Decimal('100.00'),
            payment_method='cash',
            type='payment',
            received_by=self.user
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_refund_form_access(self):
        """Test that refund form is accessible for paid invoices"""
        url = reverse('point_of_sale:process_refund', args=[self.invoice.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Process Refund')

    def test_refund_processing(self):
        """Test that refund can be processed successfully"""
        url = reverse('point_of_sale:process_refund', args=[self.invoice.id])
        data = {
            'amount': '50.00',
            'payment_method': 'cash',
            'reference': 'Test refund',
            'type': 'refund'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check that refund was created
        refund = Payment.objects.filter(type='refund').first()
        self.assertIsNotNone(refund)
        self.assertEqual(refund.amount, Decimal('50.00'))
        self.assertEqual(refund.payment_method, 'cash')
        self.assertEqual(refund.reference, 'Test refund')

    def test_refund_amount_validation(self):
        """Test that refund amount cannot exceed paid amount"""
        url = reverse('point_of_sale:process_refund', args=[self.invoice.id])
        data = {
            'amount': '150.00',  # More than paid amount
            'payment_method': 'cash',
            'reference': 'Test refund',
            'type': 'refund'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Form errors, not redirect
        self.assertContains(response, 'Refund amount cannot exceed')

    def test_invoice_detail_shows_refunds(self):
        """Test that invoice detail page shows refund information"""
        # Create a refund first
        refund = Payment.objects.create(
            invoice=self.invoice,
            amount=Decimal('30.00'),
            payment_method='cash',
            type='refund',
            received_by=self.user
        )
        
        url = reverse('point_of_sale:invoice_detail', args=[self.invoice.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Refund')
        self.assertContains(response, '30.00')

    def test_refund_form_validation(self):
        """Test that refund form validation works correctly"""
        from .forms import RefundForm
        
        # Test form with valid data
        form_data = {
            'amount': '50.00',
            'payment_method': 'cash',
            'reference': 'Test refund'
        }
        
        form = RefundForm(data=form_data, invoice=self.invoice)
        self.assertTrue(form.is_valid(), f"Form should be valid but got errors: {form.errors}")
        
        # Test form with invalid amount (too high)
        form_data_invalid = {
            'amount': '150.00',  # More than paid amount
            'payment_method': 'cash',
            'reference': 'Test refund'
        }
        
        form_invalid = RefundForm(data=form_data_invalid, invoice=self.invoice)
        self.assertFalse(form_invalid.is_valid())
        self.assertIn('amount', form_invalid.errors)

    def test_refund_form_initialization(self):
        """Test that refund form initializes correctly"""
        from .forms import RefundForm
        
        form = RefundForm(invoice=self.invoice)
        self.assertIsNotNone(form)
        self.assertIn('amount', form.fields)
        self.assertIn('payment_method', form.fields)
        self.assertIn('reference', form.fields)
