"""
Models for the Results (Output) after running allocation
through the engine.
"""
from django.utils.timezone import timedelta
from allocation.models.core import AllocationIncrease, AllocationRecharge

class InstanceStatusResult():
    status_name = None
    #Burn rate == Time used (After rules applied) per second
    burn_rate = None
    #Clock time == 'Total'Time used (Without rules applied)
    clock_time = None
    #Total time == 'Total'Time used (After rules applied)
    total_time = None


    def __repr__(self):
        return self.__unicode__()
    def __unicode__(self):
        return "<Status:%s Clock Time:%s Total Time:%s Burn Rate:%s/0:00:01>"\
                % (self.status_name, self.clock_time,
                   self.total_time, self.burn_rate)

    def __init__(self, status_name,
            clock_time=None, total_time=None, burn_rate=None):
        if not clock_time:
            clock_time = timedelta(0)
        if not total_time:
            total_time = timedelta(0)
        if not burn_rate:
            burn_rate = timedelta(0)
        self.status_name = status_name
        self.clock_time = clock_time
        self.total_time = total_time
        self.burn_rate = burn_rate

class InstanceResult():
    identifier = None
    status_list = []
    def __init__(self, identifier, status_list):
        self.identifier = identifier
        self.status_list = status_list

    def __repr__(self):
        return self.__unicode__()
    def __unicode__(self):
        return "<InstanceResult: %s Status List:%s>"\
                % (self.identifier,self.status_list)

class TimePeriodResult():
    #Datekeeping
    start_counting_date = None
    stop_counting_date = None
    #Required
    allocation_credit = None
    instance_results = []

    def over_allocation(self):
        """
        Knowing the total allocation, collect total runtime.
        If the difference is LESS THAN//EQUAL to 0, user is OVER Allocation.
        """
        return self.allocation_difference() <= timedelta(0)

    def allocation_difference(self):
        """
        Difference between allocation_credit (Given) and total_runtime (Used)
        """
        total_runtime = self.total_instance_runtime()
        return self.allocation_credit - total_runtime

    def increase_credit(self, credit_amount):
        """
        Increase the current allocation credit by the credit amount.
        Return the new allocation credit total
        """
        self.allocation_credit += credit_amount
        return self.allocation_credit

    def total_instance_runtime(self):
        """
        Count the total_time from each status result, for each instance result.
        """
        total_runtime = timedelta(0)
        for instance_result in self.instance_results:
            for status_result in instance_result.status_list:
                total_runtime += status_result.total_time
        return total_runtime

    def _validate_input(self, start_date, end_date):
        if start_date and not start_date.tzinfo:
            raise Exception("Invalid Start Date: %s Reason: Missing Timezone.")
        if end_date and not end_date.tzinfo:
            raise Exception("Invalid End Date: %s Reason: Missing Timezone.")

    def __init__(self, start_date=None, end_date=None,
            allocation_credit=timedelta(0),
            instance_results=[]):
        self._validate_input(start_date, end_date)
        self.allocation_credit = allocation_credit
        self.instance_results = instance_results
        self.start_counting_date = start_date
        self.stop_counting_date = end_date

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<TimePeriodResult: Starting From: %s To: %s"\
                "Allocation Credit:%s Instance Results:%s>"\
                % (self.start_counting_date, self.stop_counting_date,
                   self.allocation_credit, self.instance_results
                   )

class AllocationResult():
    """
    Purpose: Generalize current method from 'one-month glance' to calculate
    allocations over several months
    """
    allocation = None
    window_start = None
    window_end = None
    time_periods = []
    carry_forward = False
    def __init__(self, allocation, window_start, window_end, time_periods=[],
                 force_interval_every=None, carry_forward=False):
        if not allocation:
            raise Exception("Allocation is a required parameter")

        self.allocation = allocation
        self.window_start = window_start
        self.window_end = window_end
        self.carry_forward = carry_forward
        if time_periods:
            self.time_periods = time_periods
        elif force_interval_every:
            self.time_periods = self._time_periods_by_interval(force_interval_every)
        else:
            self.time_periods = self._time_periods_by_allocation()

    def _time_periods_by_interval(self, tdelta):
        """
        Given a timedelta, evenly divide up your TimePeriod
        """
        time_periods = []
        time_period = TimePeriodResult(self.window_start, None)
        current_date = self.window_start + tdelta
        while current_date <= self.window_end:
            #Finish this interval
            time_period.stop_counting_date = current_date
            time_periods.append(time_period)
            #Start next interval
            time_period = TimePeriodResult(current_date, None)
            current_date += tdelta
        time_period.stop_counting_date = self.window_end
        time_periods.append(time_period)
        self._credit_by_interval(time_periods)
        return time_periods

    def _credit_by_interval(self, time_periods):
        """
        When we create a list by interval, we still need to go through and
        check where AllocationRecharge//AllocationIncrease credits will go.
        """
        #NOTE: This is sorted! We can guarantee order!
        for current_period in time_periods:
            for allocation_credit in sorted(self.allocation.credits,
                key=lambda credit: credit.increase_date):
                inc_date = allocation_credit.increase_date
                #Ignore credits that happened PRIOR to or AT/AFTER
                # your counting dates.
                if inc_date < current_period.start_counting_date or\
                   inc_date >= current_period.stop_counting_date:
                    continue
                #Increase the credit and move along
                current_period.increase_credit(allocation_credit.get_credit())
        return time_periods
    @classmethod
    def _sort_credit_type(cls, credit):
        if credit.__class__ == AllocationRecharge:
            return 0
        else:
            return 1

    def _time_periods_by_allocation(self):
        """
        Given a list of credits to the allocation, logically divide up
        """
        time_periods = []
        current_period = TimePeriodResult(self.window_start, None)

        #NOTE: This is sorted! We can guarantee order!
        for allocation_credit in sorted(self.allocation.credits,
                key=lambda credit: (credit.increase_date,
                                    AllocationResult._sort_credit_type(credit))):
            #Sanity Checks..
            if allocation_credit.increase_date < self.window_start:
                raise ValueError("Bad Allocation Credit:%s requests an increase"
                "PRIOR to the start of accounting [%s]" %
                (allocation_credit, self.window_start))
            elif allocation_credit.increase_date > self.window_end:
                raise ValueError("Bad Allocation Credit:%s requests an increase"
                "AFTER the end of accounting" % (allocation_credit, self.window_end))

            #When NOT to create a new time period:
            if allocation_credit.__class__ == AllocationIncrease:
                #AllocationIncrease at any stage, add it to the current period
                current_period.increase_credit(allocation_credit.get_credit())
                continue
            elif allocation_credit.__class__ != AllocationRecharge:
                raise ValueError("Invalid Object:%s passed in credits"
                                 % allocation_credit)
            #NOTE: ASSERT: Past this line we deal with AllocationRecharge

            if allocation_credit.recharge_date == self.window_start:
                #the increase date conveniently matches the time that we are accounting.
                # Increase time only and move along.
                current_period.increase_credit(allocation_credit.get_credit())
                continue
            #End & start the 'current_period'
            current_period.stop_counting_date = allocation_credit.recharge_date
            time_periods.append(current_period)
            current_period = TimePeriodResult(
                    allocation_credit.recharge_date, None,
                    allocation_credit.get_credit())
        #End the 'final' current_period and return
        current_period.stop_counting_date = self.window_end
        time_periods.append(current_period)
        return time_periods

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<AllocationResult: Time Periods: %s "\
                % (self.time_periods)
    pass
