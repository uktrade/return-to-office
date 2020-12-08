import csv
import datetime
import io

from django.contrib import admin
from django.contrib.admin.filters import DateFieldListFilter
from django.http import HttpResponse

from .models import DitGroup, Building, Floor, Booking, PRA


def download_bookings_csv(modeladmin, request, queryset):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "booking_date",
            "building",
            "floor",
            "user",
            "directorate",
            "group",
            "business_unit",
            "on_behalf_of_name",
            "on_behalf_of_dit_email",
        ]
    )

    for b in queryset:
        writer.writerow(
            [
                b.booking_date,
                b.building,
                b.floor,
                b.user,
                b.directorate,
                b.group,
                b.business_unit,
                b.on_behalf_of_name,
                b.on_behalf_of_dit_email,
            ]
        )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment;filename=bookings.csv"
    response.write(output.getvalue())

    return response


download_bookings_csv.short_description = "Export as CSV"


class MyDateTimeFilter(DateFieldListFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = datetime.date.today()

        self.links += (
            (
                "Next 7 days",
                {
                    self.lookup_kwarg_since: str(today),
                    self.lookup_kwarg_until: str(today + datetime.timedelta(days=7)),
                },
            ),
        )


class DitGroupAdmin(admin.ModelAdmin):
    ordering = ["name"]


class BuildingAdmin(admin.ModelAdmin):
    ordering = ["name"]


class FloorAdmin(admin.ModelAdmin):
    list_display = ("name", "building")

    list_filter = ["building"]
    ordering = ["building", "name"]


class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "booking_date",
        "building",
        "floor",
        "user",
        "directorate",
        "on_behalf_of_name",
        "on_behalf_of_dit_email",
    )

    list_filter = [
        ("booking_date", MyDateTimeFilter),
        "building",
        "user",
        "on_behalf_of_name",
        "on_behalf_of_dit_email",
    ]
    ordering = ["booking_date", "building"]

    actions = [download_bookings_csv]


class PRAAdmin(admin.ModelAdmin):
    list_display = ("id", "staff_member", "line_manager", "approved_staff_member", "approved_scs")

    search_fields = ["staff_member__email"]

    ordering = ["staff_member"]


admin.site.register(DitGroup, DitGroupAdmin)
admin.site.register(Building, BuildingAdmin)
admin.site.register(Floor, FloorAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(PRA, PRAAdmin)
