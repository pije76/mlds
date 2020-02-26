from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

PR_MAJORS = 4

PICKLIST_THRESHOLDS = (1, 2, 3, 4, 5, 6, 11, 16, 21, 31, 46, 61, 91, 121, 151, 181, 211, 241, 271, 301, 451, 601, 751, 901, 1051, 1201)  # Lower Bounds

PICK_CHOICES = (
    (1, '1st Overall'),
    (2, '2nd Overall'),
    (3, '3rd Overall'),
    (4, '4th Overall'),
    (5, '5th Overall'),
    (6, '6th - 10th Overall'),
    (7, '11th - 15th Overall'),
    (8, '16th - 20th Overall'),
    (9, 'End of 1st Round'),
    (10, 'Beg of 2nd Round'),
    (11, 'End of 2nd Round'),
    (12, '3rd Round '),
    (13, '4th Round '),
    (14, '5th Round '),
    (15, '6th Round '),
    (16, '7th Round '),
    (17, '8th Round '),
    (18, '9th Round '),
    (19, '10th Round'),
    (20, '11th - 15th Round '),
    (21, '16th - 20th Round '),
    (22, '21st - 25th Round '),
    (23, '26th - 30th Round '),
    (24, '31st - 35th Round '),
    (25, '36th - 40th Round '),
    (26, '41st Round +')
)

POSITION_CHOICES = (
    (0, 'C'),
    (1, '1B-DH'),
    (2, '2B'),
    (3, '3B'),
    (4, 'SS'),
    (5, 'OF'),
    (6, 'LHP'),
    (7, 'RHP'),
    (8, 'ALL')
)

STATUS_CHOICES = (
    (0, 'HS'),
    (1, 'JC'),
    (2, '4YR')
)

def get_idx(choices, string):
    """Given a string, finds the corresponding int index in a *_CHOICES list"""
    for pair in choices:
        if pair[1] == string.strip():
            return pair[0]

class College(models.Model):
    school = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    starting = models.IntegerField()
    mid_career = models.IntegerField()
    start_fx = models.FloatField()
    mid_fx = models.FloatField()

    class Meta:
        verbose_name_plural = "Colleges"

    def __str__(self):
        return self.school

class DOLSalary(models.Model):
    occupation = models.CharField(max_length=255)
    sal10 = models.IntegerField()
    sal25 = models.IntegerField()
    sal50 = models.IntegerField()
    sal75 = models.IntegerField()
    sal90 = models.IntegerField()

    class Meta:
        verbose_name_plural = "DOLSalaries"

    def __str__(self):
        return self.occupation

    def mean(self):
        return self.sal50

    def deviation(self):
        return (1.1 * self.sal90 - self.sal50) / 2

class SlotBonus(models.Model):
    pick = models.IntegerField()
    amount = models.IntegerField()
    draft_cell = models.IntegerField(validators = [MinValueValidator(0), MaxValueValidator(26)])

    class Meta:
        verbose_name_plural = "SlotBonuses"

    def __str__(self):
        return "Pick %d ($%d, cell %d) " % (self.pick, self.amount, self.draft_cell)

class SigningBonus(models.Model):
    draft_cell = models.IntegerField(validators = [MinValueValidator(0), MaxValueValidator(26)])
    status = models.IntegerField(choices=STATUS_CHOICES, validators = [MinValueValidator(0), MaxValueValidator(2)])
    amount = models.IntegerField()
        
    class Meta:
        verbose_name_plural = "SigningBonuses"

    def __str__(self):
        return ("Cell %d, status %s: $%d" % (self.draft_cell, self.status, self.amount))

class MLBData(models.Model):
    position = models.IntegerField(choices=POSITION_CHOICES, validators = [MinValueValidator(0), MaxValueValidator(8)])
    status = models.IntegerField(choices=STATUS_CHOICES, validators = [MinValueValidator(0), MaxValueValidator(2)])
    draft_cell = models.IntegerField(validators = [MinValueValidator(0), MaxValueValidator(26)])
    year = models.IntegerField(validators = [MinValueValidator(0), MaxValueValidator(19)])
    value = models.FloatField(validators = [MinValueValidator(0.0), MaxValueValidator(100.0)], null=True)

    class Meta:
        verbose_name_plural = "MLBData"

    def __str__(self):
        return ("%s %s cell %d year %d: %s" % (self.position, self.status, self.draft_cell, self.year, self.value))

class PrMajorsData(models.Model):
    position = models.IntegerField(choices=POSITION_CHOICES, validators = [MinValueValidator(0), MaxValueValidator(8)])
    status = models.IntegerField(choices=STATUS_CHOICES,validators = [MinValueValidator(0),MaxValueValidator(2)])
    draft_cell = models.IntegerField(validators = [MinValueValidator(0), MaxValueValidator(26)])
    value = models.FloatField(validators = [MinValueValidator(0.0), MaxValueValidator(100.0)])

    class Meta:
        verbose_name_plural = "PrMajorsData"

    def __str__(self):
        return ("%s %s cell %d: %d" % (self.position, self.status, self.draft_cell, self.value))

class PrOutPosition(models.Model):
    position = models.IntegerField(choices=POSITION_CHOICES, validators = [MinValueValidator(0), MaxValueValidator(8)])
    year = models.IntegerField(validators = [MinValueValidator(0), MaxValueValidator(18)])
    value = models.FloatField(validators = [MinValueValidator(0.0), MaxValueValidator(1.0)], null=True)

    class Meta:
        verbose_name_plural = "PrOutPositions"

    def __str__(self):
        return ("Position %s, year %d: %s" % (self.position, self.year, self.value))

class PrOutStatus(models.Model):
    status = models.IntegerField(choices=STATUS_CHOICES, validators = [MinValueValidator(0), MaxValueValidator(2)])
    year = models.IntegerField(validators = [MinValueValidator(0), MaxValueValidator(18)])
    value = models.FloatField(validators = [MinValueValidator(0.0), MaxValueValidator(1.0)], null=True)

    class Meta:
        verbose_name_plural = "PrOutStatuses"

    def __str__(self):
        return "Status %s, year %d: %s" % (self.status, self.year, self.value)

class Visitor(models.Model):
    modx_id = models.IntegerField(null=True, blank=True)
    username = models.CharField(max_length=64, null=True, blank=True)
    fullname = models.CharField(max_length=64, null=True, blank=True)

    ip = models.CharField(max_length=15)
    user_agent = models.CharField(max_length=255)

    # Reverse: scenarios

    def __str__(self):
        if self.fullname:
            return self.fullname
        else:
            return '(%s)' % (self.ip, )

class Scenario(models.Model):
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    anonymous = models.BooleanField(default=True)
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    alt = models.ForeignKey(DOLSalary, related_name="alt_scenario_set", on_delete=models.CASCADE)
    sec = models.ForeignKey(DOLSalary, related_name="sec_scenario_set", on_delete=models.CASCADE)
    pick = models.IntegerField()
    pos = models.IntegerField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)

    def get_draft_cell(self):
        from .acefs import DraftCell
        return DraftCell(self.pick)

    def get_position(self):
        from .acefs import Position
        return Position(self.pos)

    def get_status(self):
        from .acefs import Status
        return Status(self.status)

    def get_modx_url(self):
        return 'http://example.com'

    def __str__(self):
        fullname = self.visitor.fullname
        if not fullname:
            fullname = '(Anonymous)'
        return "%s %s" % (fullname, self.timestamp)

        