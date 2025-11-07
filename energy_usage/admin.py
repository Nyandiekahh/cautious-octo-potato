from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Avg, Max
from django.utils import timezone
from datetime import timedelta
from .models import EnergyReading, UsageSummary


@admin.register(EnergyReading)
class EnergyReadingAdmin(admin.ModelAdmin):
    list_display = ['user', 'timestamp', 'energy_display', 'power_display', 
                    'cost_display', 'battery_display', 'created_at']
    list_filter = ['timestamp', 'battery_status', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__meter_number']
    readonly_fields = ['cost', 'created_at']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Reading Information', {
            'fields': ('timestamp', 'energy_kwh', 'power_kw', 'voltage', 'current', 'cost')
        }),
        ('Battery Information', {
            'fields': ('battery_percentage', 'battery_status'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def energy_display(self, obj):
        """Display energy with formatting"""
        return format_html(
            '<span style="font-weight: bold;">{} kWh</span>',
            f'{float(obj.energy_kwh):.3f}'
        )
    energy_display.short_description = 'Energy Consumed'
    
    def power_display(self, obj):
        """Display power with color coding"""
        power = float(obj.power_kw)
        color = 'red' if power > 3 else 'orange' if power > 2 else 'green'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} kW</span>',
            color, f'{power:.3f}'
        )
    power_display.short_description = 'Power Draw'
    
    def cost_display(self, obj):
        """Display cost with formatting"""
        return format_html(
            '<span style="color: #2E7D32; font-weight: bold;">KES {}</span>',
            f'{float(obj.cost):.2f}'
        )
    cost_display.short_description = 'Cost'
    
    def battery_display(self, obj):
        """Display battery status"""
        if obj.battery_percentage is not None:
            color = 'green' if obj.battery_percentage > 50 else 'orange' if obj.battery_percentage > 20 else 'red'
            return format_html(
                '<span style="color: {};">{}% ({})</span>',
                color, obj.battery_percentage, obj.battery_status or 'N/A'
            )
        return '-'
    battery_display.short_description = 'Battery'
    
    actions = ['export_readings', 'calculate_summary']
    
    def export_readings(self, request, queryset):
        """Export selected readings"""
        count = queryset.count()
        self.message_user(request, f'{count} reading(s) ready for export.')
    export_readings.short_description = "Export selected readings"
    
    def calculate_summary(self, request, queryset):
        """Calculate summary statistics for selected readings"""
        stats = queryset.aggregate(
            total_energy=Sum('energy_kwh'),
            avg_power=Avg('power_kw'),
            max_power=Max('power_kw'),
            total_cost=Sum('cost')
        )
        message = f"Total Energy: {stats['total_energy']:.2f} kWh | " \
                  f"Avg Power: {stats['avg_power']:.2f} kW | " \
                  f"Peak Power: {stats['max_power']:.2f} kW | " \
                  f"Total Cost: KES {stats['total_cost']:.2f}"
        self.message_user(request, message)
    calculate_summary.short_description = "Calculate summary statistics"


@admin.register(UsageSummary)
class UsageSummaryAdmin(admin.ModelAdmin):
    list_display = ['user', 'period_type', 'start_date', 'end_date', 
                    'total_energy_display', 'peak_power_display', 
                    'total_cost_display', 'reading_count']
    list_filter = ['period_type', 'start_date']
    search_fields = ['user__username', 'user__email', 'user__meter_number']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('User & Period', {
            'fields': ('user', 'period_type', 'start_date', 'end_date')
        }),
        ('Usage Metrics', {
            'fields': ('total_energy_kwh', 'average_power_kw', 'peak_power_kw', 
                      'total_cost', 'reading_count')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_energy_display(self, obj):
        """Display total energy with formatting"""
        return format_html(
            '<span style="font-weight: bold;">{} kWh</span>',
            f'{float(obj.total_energy_kwh):.2f}'
        )
    total_energy_display.short_description = 'Total Energy'
    
    def peak_power_display(self, obj):
        """Display peak power with color coding"""
        power = float(obj.peak_power_kw)
        color = 'red' if power > 3 else 'orange' if power > 2 else 'green'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} kW</span>',
            color, f'{power:.2f}'
        )
    peak_power_display.short_description = 'Peak Power'
    
    def total_cost_display(self, obj):
        """Display total cost with formatting"""
        return format_html(
            '<span style="color: #2E7D32; font-weight: bold;">KES {}</span>',
            f'{float(obj.total_cost):.2f}'
        )
    total_cost_display.short_description = 'Total Cost'
    
    actions = ['generate_report']
    
    def generate_report(self, request, queryset):
        """Generate report for selected summaries"""
        count = queryset.count()
        total_energy = queryset.aggregate(Sum('total_energy_kwh'))['total_energy_kwh__sum']
        total_cost = queryset.aggregate(Sum('total_cost'))['total_cost__sum']
        self.message_user(
            request, 
            f'Report for {count} summaries: Total Energy={total_energy:.2f}kWh, Total Cost=KES {total_cost:.2f}'
        )
    generate_report.short_description = "Generate summary report"