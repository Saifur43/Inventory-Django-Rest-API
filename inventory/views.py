# inventory/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from .models import Product, Transaction
from .serializers import ProductSerializer, TransactionSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def stock_in(self, request, pk=None):
        product = self.get_object()
        quantity = request.data.get('quantity', 0)
        
        if quantity > 0:
            product.quantity += quantity
            product.save()
            
            Transaction.objects.create(
                product=product,
                transaction_type='IN',
                quantity=quantity,
                created_by=request.user,
                notes=request.data.get('notes', '')
            )
            
            return Response({'message': 'Stock updated successfully'})
        return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def stock_out(self, request, pk=None):
        product = self.get_object()
        quantity = request.data.get('quantity', 0)
        
        if quantity > 0 and product.quantity >= quantity:
            product.quantity -= quantity
            product.save()
            
            Transaction.objects.create(
                product=product,
                transaction_type='OUT',
                quantity=quantity,
                created_by=request.user,
                notes=request.data.get('notes', '')
            )
            
            return Response({'message': 'Stock updated successfully'})
        return Response({'error': 'Invalid quantity or insufficient stock'}, 
                       status=status.HTTP_400_BAD_REQUEST)

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        # Get total products and current stock value
        total_products = Product.objects.count()
        total_stock_value = Product.objects.annotate(
            value=models.F('quantity') * models.F('unit_price')
        ).aggregate(total=models.Sum('value'))['total'] or 0

        # Get today's transactions
        today = timezone.now().date()
        today_transactions = Transaction.objects.filter(
            transaction_date__date=today
        )

        # Get low stock products (less than 10 items)
        low_stock = Product.objects.filter(quantity__lt=10).count()

        return Response({
            'total_products': total_products,
            'total_stock_value': float(total_stock_value),  # Convert Decimal to float
            'today_stock_in': today_transactions.filter(
                transaction_type='IN'
            ).count(),
            'today_stock_out': today_transactions.filter(
                transaction_type='OUT'
            ).count(),
            'low_stock_alerts': low_stock
        })

class ReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def daily_report(self, request):
        date = request.query_params.get('date', timezone.now().date())
        
        transactions = Transaction.objects.filter(
            transaction_date__date=date
        )
        
        return Response({
            'stock_in': transactions.filter(
                transaction_type='IN'
            ).aggregate(total=Sum('quantity'))['total'] or 0,
            'stock_out': transactions.filter(
                transaction_type='OUT'
            ).aggregate(total=Sum('quantity'))['total'] or 0,
            'transactions': TransactionSerializer(transactions, many=True).data
        })

    @action(detail=False, methods=['get'])
    def monthly_report(self, request):
        today = timezone.now()
        first_day = today.replace(day=1)
        
        transactions = Transaction.objects.filter(
            transaction_date__gte=first_day,
            transaction_date__lte=today
        )
        
        return Response({
            'stock_in': transactions.filter(
                transaction_type='IN'
            ).aggregate(total=Sum('quantity'))['total'] or 0,
            'stock_out': transactions.filter(
                transaction_type='OUT'
            ).aggregate(total=Sum('quantity'))['total'] or 0,
            'transactions': TransactionSerializer(transactions, many=True).data
        })