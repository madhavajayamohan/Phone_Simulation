"""
CSC148, Winter 2023
Assignment 1

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

All of the files in this directory and all subdirectories are:
Copyright (c) 2022 Bogdan Simion, Diane Horton, Jacqueline Smith
"""
import datetime
from math import ceil
from typing import Optional
from bill import Bill
from call import Call


# Constants for the month-to-month contract monthly fee and term deposit
MTM_MONTHLY_FEE = 50.00
TERM_MONTHLY_FEE = 20.00
TERM_DEPOSIT = 300.00

# Constants for the included minutes and SMSs in the term contracts (per month)
TERM_MINS = 100

# Cost per minute and per SMS in the month-to-month contract
MTM_MINS_COST = 0.05

# Cost per minute and per SMS in the term contract
TERM_MINS_COST = 0.1

# Cost per minute and per SMS in the prepaid contract
PREPAID_MINS_COST = 0.025


class Contract:
    """ A contract for a phone line

    This class is not to be changed or instantiated. It is an Abstract Class.

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    """
    start: datetime.date
    bill: Optional[Bill]

    def __init__(self, start: datetime.date) -> None:
        """ Create a new Contract with the <start> date, starts as inactive
        """
        self.start = start
        self.bill = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.

        DO NOT CHANGE THIS METHOD
        """
        raise NotImplementedError

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        self.bill.add_billed_minutes(ceil(call.duration / 60.0))

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        return self.bill.get_cost()


class TermContract(Contract):
    """ A term contract for a phone line.

        === Public Attributes ===
        end:
             The ending month and year for the contract.
    """
    # === Private Attributes ===
    # _num_free_min_used:
    #   Represents the number of free minutes used up in the contract
    #   each month.Resets to zero when the contract advances to
    #   a new month.
    # _curr_date:
    #   A two element tuple that represents the current month and year
    #   the contract is in. The first element represents the year, the
    #   second represents the month

    end: datetime.date
    _curr_date: tuple[int, int]
    _num_free_min_used: int

    def __init__(self, start: datetime.date, end: datetime.date) -> None:
        """ Create a new Contract with the <start> start date and
            <end> ending date, starts as inactive
        """
        Contract.__init__(self, start)
        self._curr_date = (start.year, start.month)
        self.end = end
        self._num_free_min_used = 0

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.
        """
        self._curr_date = (year, month)
        self._num_free_min_used = 0

        if (self.bill is None and self.start.month == month
                and self.start.year == year):
            bill.add_fixed_cost(TERM_DEPOSIT)

        self.bill = bill
        self.bill.set_rates("TERM", TERM_MINS_COST)
        self.bill.add_fixed_cost(TERM_MONTHLY_FEE)

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        duration = ceil(call.duration / 60.0)

        # If the block of code in the if statement runs, then free
        # minutes have been used up. Thus,
        # last free minutes + remaining billed minutes = duration
        # remaining_free is the last free minutes, and
        # billed_mins is the remaining billed minutes
        if self._num_free_min_used + duration > TERM_MINS:
            remaining_free = TERM_MINS - self._num_free_min_used
            billed_mins = duration - remaining_free

            self.bill.add_free_minutes(remaining_free)
            self._num_free_min_used += remaining_free

            self.bill.add_billed_minutes(billed_mins)
        else:  # If else runs, then free minutes are still used up
            self.bill.add_free_minutes(duration)
            self._num_free_min_used += duration

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract, if contract is cancelled before specified end date.
        Otherwise, return the customer the term deposit minus that months cost.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        billed_cost = Contract.cancel_contract(self)

        # To indicate returning the term deposit, billed_cost
        # will be negative. However, this is only if the
        # billed_cost is not greater than the term deposit.
        # If it is greater than the term deposit, then
        # billed_cost will be positive, and the customer
        # will still have to pay some amount to cancel the contract
        if (self._curr_date[0] >= self.end.year
                and self._curr_date[1] >= self.end.month):
            billed_cost -= TERM_DEPOSIT

        self.end = None
        self._curr_date = None

        return billed_cost


class MTMContract(Contract):
    """ A month-to-month contract for a phone line.
        """

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.
        """
        self.bill = bill
        self.bill.set_rates("MTM", MTM_MINS_COST)
        self.bill.add_fixed_cost(MTM_MONTHLY_FEE)


class PrepaidContract(Contract):
    """ A prepaid contract for a phone line.

        === Public Attributes ===
        balance:
         The amount of money the customer owes; a negative value
         indicates customer credit, non-negative values refer to
         how much the customer needs to pay
        """

    balance: float

    def __init__(self, start: datetime.date, balance: float) -> None:
        """ Create a new Contract with the <start> start date and
            <end> ending date, starts as inactive
        """
        Contract.__init__(self, start)
        self.balance = -1 * balance

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.
        """
        if self.bill is not None:
            self.balance = self.bill.get_cost()

        if self.balance > -10:
            self.balance += -25

        self.bill = bill
        self.bill.set_rates("PREPAID", PREPAID_MINS_COST)

        self.bill.add_fixed_cost(self.balance)

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract. If the credit is negative, return 0.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        billed_cost = 0

        if self.balance > 0:
            billed_cost += self.balance

        return billed_cost


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'python_ta', 'typing', 'datetime', 'bill', 'call', 'math'
        ],
        'disable': ['R0902', 'R0913'],
        'generated-members': 'pygame.*'
    })
