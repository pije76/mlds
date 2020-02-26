from django.contrib.admin.options import ModelAdmin, TabularInline
from .models import College, SlotBonus, MLBData, DOLSalary, PrMajorsData, SigningBonus, Visitor, Scenario, PrOutPosition, PrOutStatus
from django.contrib import admin

class CollegeAdmin(ModelAdmin):
	list_filter = ('type',)
	search_fields = ('school',)
	list_display = ('id', 'school', 'type', 'starting', 'mid_career','start_fx', 'mid_fx')
	ModelAdmin.ordering = ('id', )
admin.site.register(College, CollegeAdmin)

class SlotBonusAdmin(ModelAdmin):
	list_filter = ('draft_cell', )
	list_display = ('id', 'pick', 'amount', 'draft_cell')
	ModelAdmin.ordering = ('id', )
admin.site.register(SlotBonus, SlotBonusAdmin)

class MLBDataAdmin(ModelAdmin):
	list_filter = ('position', 'status', 'draft_cell', 'year')
	list_display = ('id', 'position', 'status', 'draft_cell', 'year', 'value')
	ModelAdmin.ordering = ('id', )
admin.site.register(MLBData, MLBDataAdmin)

class DOLSalaryAdmin(ModelAdmin):
	search_fields = ('occupation',)
	list_display = ('id', 'occupation', 'sal10', 'sal25', 'sal50', 'sal75', 'sal90')
	ModelAdmin.ordering = ('id', )
admin.site.register(DOLSalary, DOLSalaryAdmin)

class PrMajorsDataAdmin(ModelAdmin):
	list_filter = ('position', 'status', 'draft_cell')
	list_display = ('id', 'position', 'status', 'draft_cell', 'value')
	ModelAdmin.ordering = ('id', )
admin.site.register(PrMajorsData, PrMajorsDataAdmin)

class SigningBonusAdmin(ModelAdmin):
	list_filter = ('draft_cell', 'status')
	list_display = ('id', 'draft_cell', 'status', 'amount')
	ModelAdmin.ordering = ('id', )
admin.site.register(SigningBonus, SigningBonusAdmin)

class ScenarioAdmin(ModelAdmin):
	list_filter = ('visitor', 'college')
	list_display = ('id', 'visitor', 'timestamp', 'anonymous', 'college', 'alt', 'sec', 'pick', 'pos', 'status')
	ModelAdmin.ordering = ('id', )
admin.site.register(Scenario, ScenarioAdmin)

class ScenarioInline(TabularInline):
	model = Scenario
	readonly_fields = ('anonymous','college','alt','sec','pick','pos','status')
	extra = 0

class VisitorAdmin(ModelAdmin):
	list_display = ('id', 'username', 'fullname', 'ip')
	readonly_fields = ('modx_id','username','fullname','ip','user_agent')
	inlines = [ScenarioInline,]
	ModelAdmin.ordering = ('id', )
admin.site.register(Visitor, VisitorAdmin)


class PrOutPositionAdmin(ModelAdmin):
	list_filter = ('position', 'year')
	list_display = ('id', 'position', 'year', 'value')
	ModelAdmin.ordering = ('id', )
admin.site.register(PrOutPosition, PrOutPositionAdmin)

class PrOutStatusAdmin(ModelAdmin):
	list_filter = ('status', 'year')
	list_display = ('id', 'status', 'year', 'value')
	ModelAdmin.ordering = ('id', )
admin.site.register(PrOutStatus, PrOutStatusAdmin)
