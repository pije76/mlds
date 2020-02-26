from django.db.models import Q

from scipy.stats import norm    # Using numpy 1.6.0 and scipy 0.9.0

import datetime
import math
import numpy

from .models import *

# This module provides the Python implementation of the Actuarial model.

# Constants

DISCOUNT_RATE = 0.06         # C9
INFLATION = 0.03             # C10
MLB_INFLATION = (414.0/109.0)**(1.0/16.0)-1.0         # C14
ENTRY_SAL_PERCENTILE = 0.25 # C15
ANNUAL_SAL_INCREASE = 0.02   # C16 - %
ADDL_REQ_SCHOOL = 4.0       # C17 - For alternate path
MIN_MLB_SAL = 35000         # C18
MIN_MLB_START = 5           # C19
ASSUME_100 = 3              # C20 - Assume 100% Chance in baseball first this many years

TOTAL_YEARS = 20

MLB_AVERAGE = (4.12,) * 12  # Rounds 1-3, Cells 1-12
MLB_AVERAGE += (3.745,) * 3  # Rounds 4-6, Cells 13-15
MLB_AVERAGE += (3.45,) * 4  # Rounds 7-10, Cells 16-19
MLB_AVERAGE += (3.42,) * 2  # Rounds 11-20, Cells 20-21
MLB_AVERAGE += (3.71,) * 2  # Rounds 21-30, Cells 22-23
MLB_AVERAGE += (4.52,) * 3  # Rounds 30+, Cells 24-26

MiLB_AVERAGE = (4,) * 12  # Rounds 1-3, Cells 1-12
MiLB_AVERAGE += (5,) * 14  # Rounds 1-3, Cells 1-12

R2_POSITION = [0.5225, 0.1909, 0.5877, 0.4806, 0.6212, 0.863, 0.9007, 0.7654, 0]

R2_STATUS = [0.667, 0.8304, 0.7963]

STATUS_CHOICES = (
	(0, 'HS'),
	(1, 'JC'),
	(2, '4YR')
)

TRAVEL_TIME = (
	5.2,  # HS
	4.9,  # JC
	4.07  # 4YR
)   # In the spreadsheet, this is derived from a table listing college years
	# separately. Simplified here.

def norminv(x, mu, sigma):
	"""
	Returns the inverse of the normal cumulative distribution.

	This method is designed to implemnt MS Excel's NORMINV() function.
	
	Arguments:
	x -- probability
	mu -- mean
	sigma -- standard deviation

	"""
	return mu + norm.ppf(x) * sigma

def smoothedPrMajors(status, position, draft_cell):
	"""
	Returns smoothed data indicating the probability a player will play in the Majors.

	Result is an float, 0.0 <= x <= 100.0

	This method emulates the data in the range SupportingStats!B60:AC87 in the prototype spreadsheet.

	Arguments
	status -- zero-based index into django_mlds.acefs.models.STATUS_CHOICES
	position -- zero-based index into django_mlds.acefs.models.POSITION_CHOICES
	draft_cell -- one-based index, 1 <= draft_cell <= len(django_mlds.acefs.models.PICKLIST_THRESHOLDS)

	"""

	try:
		return PrMajorsData.objects.filter(position=position, status=status).order_by('-value')[draft_cell-1].value
	except Exception as e:
		return 0.0

def smoothedMLBData(status, position, year, draft_cell):
	"""
	Returns smoothed information from historical MLB Salary data.

	Result is a float x >= 0.0

	Arguments
	status -- zero-based index into django_mlds.acefs.models.STATUS_CHOICES
	position -- zero-based index into django_mlds.acefs.models.POSITION_CHOICES
	year -- zero-based index starting at current year, 0 <= year <= TOTAL_YEARS
	draft_cell -- one-based index, 1 <= draft_cell <= len(django_mlds.acefs.models.PICKLIST_THRESHOLDS)

	This method emulates the data in the range MLBData!AN40:BQ620 in the prototype spreadsheet.

	"""

	try:
		return MLBData.objects.filter(position=position, status=status, year=year).order_by('-value')[draft_cell-1].value
	except:
		return None

def max_bonus(draft_cell):
	"""
	Returns the maximum bonus for any pick in a given draft cell.

	Argument:
	draft_cell -- one-based index, 1 <= draft_cell <= 15

	"""
	# TODO: Does this break for draft_cell > 15. Is that even possible?
	return SlotBonus.objects.filter(draft_cell=draft_cell).order_by('-amount')[0].amount

def Property(func):
	"""Helper method, shortcut to writing getter and setter methods """
	return property(**func())

class DraftCell(object):
	"""
	Represents a Draft Cell, providing easy access to properties.

	"""

	def __init__(self, index):
		self.index = index # index is Zero-based

	@property
	def cell(self):
		"""
		Read-only Property. One-based index.

		"""
		return self.index + 1

	@property
	def MiLBAverage(self):
		"""
		Read-only Property.

		"""
		return MiLB_AVERAGE[self.index]

	@property
	def MLBAverage(self):
		"""
		Read-only Property.

		"""
		return MLB_AVERAGE[self.index]
		print('test:', MLB_AVERAGE[self.index])

	@property
	def lower(self):
		"""
		Read-only Property. The lowest pick included in this cell.

		"""
		return PICKLIST_THRESHOLDS[self.index]

	@property
	def upper(self):
		"""
		Read-only Property. The highest pick included in this cell.

		"""
		if self.cell < len(PICKLIST_THRESHOLDS):
			return PICKLIST_THRESHOLDS[self.index+1]-1
		else:
			return None

	@property
	def draft_point(self):
		"""
		Read-only Property. A string representign the range of picks in this cell.

		Format examples: "1", "6-10", "1200+"

		"""
		l = self.lower
		u = self.upper
		if u == l:
			return str(l)
		elif u == None:
			return "%d +" % (l,)
		else:
			return "%d - %d" % (l, u)

	def __str__(self):
		return self.draft_point

DRAFT_CELLS = [DraftCell(idx+1) for idx in range (0,26)]
"""Generates a list of draft points usefull for UI (EG: ["1","2",...,"6-10",...,"1201+"] )"""

class Status(object):
	"""
	Represents status (year in school).

	"""

	def __init__(self, index):
		self.index = index

	@property
	def text(self):
		"""
		Read-only Property.

		"""
		return STATUS_CHOICES[self.index][1]

	@property
	def travel_time(self):
		"""
		Read-only Property.

		"""
		return TRAVEL_TIME[self.index]

	def __str__(self):
		return self.text

STATUSES = [Status(x) for x in range(len(STATUS_CHOICES))]

class Position(object):
	"""
	Represents position played.

	"""

	def __init__(self, index):
		self.index = index

	@property
	def text(self):
		"""
		Read-only Property.

		"""
		return POSITION_CHOICES[self.index][1]

	def __str__(self):
		return self.text

POSITIONS = [Position(x) for x in range(len(POSITION_CHOICES))]

class AcefsModel(object):
	"""
	Actuarial Comparison of Expected Future Salaries

	This class implemnts the actuarial model.

	Usage: instantiate the class, passing the appropriate configuration in the constructor or usign the property setter
	methods. The class will automatically recalculte the results when inputs change. Access results using properties
	and getter methods .
	"""

	@Property
	def college():
		"""
		Read/Write Property. The college. Set using id from College.

		"""
		def fget(self):
			return self._college
		def fset(self, college_id):
			self._college = College.objects.get(pk=college_id)
			self._needs_recalc = True
		return locals()

	@Property
	def alt():
		"""
		Read/Write Property. Alternate Career Path, Set using id from DOLSalary

		"""
		def fget(self):
			return self._alt
		def fset(self, alt_id):
			self._alt = DOLSalary.objects.get(pk=alt_id)
			self._needs_recalc = True
		return locals()

	@Property
	def secondary():
		"""
		Read/Write Property. Secondary Career, set using id from DOLSalary

		"""
		def fget(self):
			return self._secondary
		def fset(self, secondary_id):
			self._secondary = DOLSalary.objects.get(pk=secondary_id)
			self._needs_recalc = True
		return locals()

	@Property
	def risk_tolerance():
		"""
		Read/Write Property. Risk Tolereance. Set with float 0.0 <= X <= 100.0

		"""
		def fget(self):
			return self._risk_tolerance
		def fset(self, risk_tolerance):
			self._risk_tolerance = risk_tolerance
			self._needs_recalc = True
		return locals()

	@Property
	def expected_pick():
		"""
		Read/Write Property. Expected pick / draft cell. Set with int 1 <= X <= 26

		"""
		def fget(self):
			return self._expected_pick
		def fset(self, expected_pick):
			self._expected_pick = DraftCell(expected_pick)
			self._needs_recalc = True
		return locals()

	@Property
	def position():
		"""
		Read/Write Property. Position. Set with int 0 <= X <= 8

		"""
		def fget(self):
			return self._position

		def fset(self, position):
			self._position = Position(position)
			self._needs_recalc = True
		return locals()

	@Property
	def status():
		"""
		Read/Write Property. Status. Set with int in [0,1,2]

		"""
		def fget(self):
			return self._status

		def fset(self, status):
			self._status = Status(status)
			self._needs_recalc = True
		return locals()

	def __init__(self, college=None, alt=None, secondary=None, risk_tolerance=0.0, expected_pick=1, position=8, status=0):

		self.college = college
		self.alt = alt
		self.secondary = secondary
		self.risk_tolerance = risk_tolerance
		self.expected_pick = expected_pick
		self.position = position
		self.status = status

		self._needs_recalc = True

		self.recalc()

	def recalc(self):
		"""
		Called automatically on-demand when data has changed. Recalculates model.

		"""

		t_s = datetime.datetime.now()

		# Set this before we start to avoid recursion. GIL will protect us.
		self._needs_recalc = False

		# C26 - Maximum Slotted Bonus
		self._max_slotted_bonus = SigningBonus.objects.filter(draft_cell=self.expected_pick.cell, status=self.status.index).values_list('amount', flat=True).first()

		# C40 Pr(MLB)
		pr_all = smoothedPrMajors(self.status.index, get_idx(POSITION_CHOICES, 'ALL'), self.expected_pick.cell)
		pr_pos = smoothedPrMajors(self.status.index, self.position.index, self.expected_pick.cell)

		self._pr_mlb = (0.2 * pr_all + 0.8 * pr_pos) / 100.0

		self._career_adj_factor = (0.2 * self.college.start_fx + 0.8 * self.college.mid_fx) / 100.0

		# Column F
		self._all_positions = []
		for year in range(0,TOTAL_YEARS):
			ap = smoothedMLBData(self.status.index, get_idx(POSITION_CHOICES, 'ALL'), year, self.expected_pick.cell)
			if ap == None:
				ap = 0
			self._all_positions.append(ap)

		# Column G
		self._selected_position = []
		for year in range(0,TOTAL_YEARS):
			sp = smoothedMLBData(self.status.index, self.position.index, year, self.expected_pick.cell)
			if sp == None:
				sp = 0
			self._selected_position.append(sp)

		# Column H
		self._mlb_sal_shift = []
		for year in range(0,TOTAL_YEARS):
			if year == 0:
				self._mlb_sal_shift.append( 0 )
				
			else:
				if year > self.status.travel_time:
					self._mlb_sal_shift.append( 0.5 * self._all_positions[year] + 0.4 * self._selected_position[year] )
				else:
					self._mlb_sal_shift.append( 0 )

		# Column I
		self._school = []
		for year in range(0,TOTAL_YEARS):
			if year+1 > ADDL_REQ_SCHOOL:
				self._school.append(False)
			else:
				self._school.append(True)


		# Column J
		self._pr_minors = []
		for year in range(0,TOTAL_YEARS):
			if year >= ASSUME_100:
				self._pr_minors.append(math.exp( -1.0 * float(year) / self.expected_pick.MiLBAverage ))
			else:
				self._pr_minors.append(1.0)

		# Column K
		self._pr_out = []
		for year in range(0,TOTAL_YEARS):

			inv_pr_out = 0
			if year <= 18:

				n7 = R2_POSITION[self.position.index]
				o7 = R2_STATUS[self.status.index]

				if self.position.text == 'ALL':
					NX = 0
				else:
					NX = PrOutPosition.objects.filter(position=self.position.index).values_list('value', flat=True).first()

				OX = PrOutStatus.objects.filter(status=self.status.index).values_list('value', flat=True).first()

				inv_pr_out = (NX * n7 + OX * o7) / (n7 + o7)

			self._pr_out.append(1.0 - inv_pr_out)

		# Column L
		self._MiLB_sal = []
		for year in range(0,TOTAL_YEARS):
			self._MiLB_sal.append( 1100 * 12 * self._pr_minors[year] * ( (1 + INFLATION) ** year ))


		# Columns M-AG (AltStart20__)
		mu = self.alt.mean()
		sigma = self.alt.deviation()
		self._alt_start = [] # Outer index is year
		for year in range(0,TOTAL_YEARS):
			row = [] # Inner index is alt_year
			for alt_year in range(0,TOTAL_YEARS):

				if (alt_year > year) or (self._school[year]):
					n = 0
				else:
					sal_percent = ENTRY_SAL_PERCENTILE + (ANNUAL_SAL_INCREASE * max (0, year - alt_year - ADDL_REQ_SCHOOL))
					x = min(0.99, sal_percent)
					n = norminv(x, mu, sigma)

				m = (1 + INFLATION) ** year

				if ((ADDL_REQ_SCHOOL > 0) and (self.status.text == 'HS')) or (self.status.text != 'HS'):
					o = self.career_adj_factor
				else:
					o = 1

				row.append(n * m * o)

			self._alt_start.append(row)


		# Columns AH-BA (SecStart20__)
		mu = self.secondary.mean()
		sigma = self.secondary.deviation()
		self._sec_start = [] # Outer index is year
		for year in range(0,TOTAL_YEARS):
			row = [] # Inner index is sec_year
			for sec_year in range(0,TOTAL_YEARS):

				if sec_year > year:
					n = 0
				else:
					sal_percent = ENTRY_SAL_PERCENTILE + (ANNUAL_SAL_INCREASE  * (year - max(sec_year, 0)))
					x = min(0.99, sal_percent)
					n = norminv(x, mu, sigma)

				m = (1 + INFLATION) ** year

				if self.use_adj_factor:
					o = self._career_adj_factor
				else:
					o = 1

				row.append(n * m * o)

			self._sec_start.append(row)

		# AG2:AZ3
		sum_pr_out = 0
		for p in self._pr_out:
			sum_pr_out += p
		agaz = [pr/sum_pr_out for pr in self._pr_out]   # This is an array of values used to calculage E[MLB],
														# named for the cell range in the spreadsheet

		# Column BB -E [MLB] w/o Min
		self._e_mlb_wo_min = []
		for year in range(0,TOTAL_YEARS):
			x = self._MiLB_sal[year] * self._pr_minors[year]
			y = self._mlb_sal_shift[year] * ((1+MLB_INFLATION)/(1+INFLATION)) ** year
			sumproduct = 0

			for i in range(0,TOTAL_YEARS):
				sumproduct += agaz[i] * self._sec_start[year][i]

			z = (1.0-self._pr_out[year]) * sumproduct

			self._e_mlb_wo_min.append(x+y+z)

		# Column BC - E[MLB]
		self._e_mlb = []
		for year in range(0, TOTAL_YEARS):
			if year == 0:
				self._e_mlb.append( float(self._max_slotted_bonus) )
			elif ( self._e_mlb_wo_min[year] < MIN_MLB_SAL * (1+INFLATION)**year) and (year >= MIN_MLB_START):
				self._e_mlb.append(self._sec_start[year][year])
			else:
				self._e_mlb.append(self._e_mlb_wo_min[year])

		t_e = datetime.datetime.now()
		self.elapsed = t_e - t_s

		# Column BD - E[Alt]
		self._e_alt = [r[0] for r in self._alt_start]

		# BB30:BD30 - Net Present Value
		self._npv_mlb_wo_min = numpy.npv(DISCOUNT_RATE, self._e_mlb_wo_min[1:])
		self._npv_mlb = numpy.npv(DISCOUNT_RATE, self._e_mlb[1:])
		self._npv_alt = numpy.npv(DISCOUNT_RATE, self._e_alt[1:])


	@property
	def bonus_threshold(self):               # B23
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return max(0, self.npv_alt-self.npv_mlb+self.mlb_sal_shift[0])*(1+self.risk_tolerance)

	@property
	def play_ball(self):                              # B29
		"""
		Read-only Property. Return True if Baseball, False if Alternate Path

		"""
		if self._needs_recalc:
			self.recalc()
		return self.npv_mlb >= self.npv_alt


	@property
	def travel_time(self):                              # C37
		"""
		Read-only Property.

		"""
		return self.status.travel_time

	@property
	def MLBAverage(self):                               # C38
		"""
		Read-only Property.

		"""
		return self.expected_pick.MLBAverage
		print('test2:', self.expected_pick.MLBAverage)

	@property
	def MiLBAverage(self):                              # C39
		"""
		Read-only Property.

		"""
		return self.expected_pick.MiLBAverage


	@property
	def pr_mlb(self):                                   # C40
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._pr_mlb


	@property
	def career_adj_factor(self):                        # C43
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._career_adj_factor

	@property
	def use_adj_factor(self):                           # C44
		"""
		Read-only Property.

		"""
		if self.status.text == '4YR':
			return True
		else:
			return False

	@property
	def all_positions(self):                            # Column F
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._all_positions

	@property
	def selected_position(self):                        # Column G
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._selected_position 

	@property
	def mlb_sal_shift(self):                            # Column H
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._mlb_sal_shift

	@property
	def school(self):                                   # Column I
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._school

	@property
	def pr_minors(self):                                # Column J
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._pr_minors

	@property
	def pr_out(self):                                   # Column K
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._pr_out

	@property
	def MiLB_sal(self):                                 # Column L
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._MiLB_sal

	@property
	def alt_start(self):                                # Columns N:AG
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._alt_start

	@property
	def sec_start(self):                                # Columns AH:BA
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._sec_start

	@property
	def e_mlb_wo_min(self):                             # Column BB
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._e_mlb_wo_min

	@property
	def e_mlb(self):                                    # Column BC
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._e_mlb

	@property
	def e_alt(self):                                    # Column BD
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._e_alt

	@property
	def npv_mlb_wo_min(self):                           # BB30
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._npv_mlb_wo_min

	@property
	def npv_mlb(self):                                  # BC30
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._npv_mlb

	@property
	def npv_alt(self):                                  # BD30
		"""
		Read-only Property.

		"""
		if self._needs_recalc:
			self.recalc()
		return self._npv_alt

	@property
	def max_slotted_bonus(self):                        # C26
		"""
		Read-only Property
		"""
		if self._needs_recalc:
			self.recalc()
		return self._max_slotted_bonus

