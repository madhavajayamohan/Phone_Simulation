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
import time
import datetime
from typing import Optional
from call import Call
from customer import Customer


class Filter:
    """ A class for filtering customer data on some criterion. A filter is
    applied to a set of calls.

    This is an abstract class. Only subclasses should be instantiated.
    """

    def __init__(self) -> None:
        pass

    def apply(self, customers: list[Customer],
              data: list[Call],
              filter_string: str) \
            -> list[Call]:
        """ Return a list of all calls from <data>, which match the filter
        specified in <filter_string>.

        The <filter_string> is provided by the user through the visual prompt,
        after selecting this filter.
        The <customers> is a list of all customers from the input dataset.

         If the filter has
        no effect or the <filter_string> is invalid then return the same calls
        from the <data> input.

        Note that the order of the output matters, and the output of a filter
        should have calls ordered in the same manner as they were given, except
        for calls which have been removed.

        Precondition:
        - <customers> contains the list of all customers from the input dataset
        - all calls included in <data> are valid calls from the input dataset
        """
        raise NotImplementedError

    def __str__(self) -> str:
        """ Return a description of this filter to be displayed in the UI menu
        """
        raise NotImplementedError


class ResetFilter(Filter):
    """
    A class for resetting all previously applied filters, if any.
    """

    def apply(self, customers: list[Customer],
              data: list[Call],
              filter_string: str) \
            -> list[Call]:
        """ Reset all of the applied filters. Return a List containing all the
        calls corresponding to <customers>.
        The <data> and <filter_string> arguments for this type of filter are
        ignored.

        Precondition:
        - <customers> contains the list of all customers from the input dataset
        """
        filtered_calls = []
        for c in customers:
            customer_history = c.get_history()
            # only take outgoing calls, we don't want to include calls twice
            filtered_calls.extend(customer_history[0])
        return filtered_calls

    def __str__(self) -> str:
        """ Return a description of this filter to be displayed in the UI menu
        """
        return "Reset all of the filters applied so far, if any"


class CustomerFilter(Filter):
    """
    A class for selecting only the calls from a given customer.
    """

    def apply(self, customers: list[Customer],
              data: list[Call],
              filter_string: str) \
            -> list[Call]:
        """ Return a list of all unique calls from <data> made or
        received by the customer with the id specified in <filter_string>.

        The <customers> list contains all customers from the input dataset.

        The filter string is valid if and only if it contains a valid
        customer ID.
        - If the filter string is invalid, return the original list <data>
        - If the filter string is invalid, your code must not crash, as
        specified in the handout.

        Do not mutate any of the function arguments!
        """
        filter_customer = None
        try:
            filter_string = int(filter_string)

            # Checks if the ID in filter string belongs to
            # any customer
            for customer in customers:
                if customer.get_id() == filter_string:
                    filter_customer = customer
                    break
        except ValueError:
            # This will be most likely called in the case
            # when the filter_string cannot be converted to
            # an integer. If so, it is invalid and data is
            # returned
            return data

        # If filter_customer has not been defined, then the
        # Customer ID it describes is not in the given set.
        # Thus, block of code in if statement doesn't run,
        # and data is returned.
        if filter_customer is not None:
            filtered_calls = []

            # Goes through every call in dataset and checks if
            # any of the calls are made or received by the
            # specified customer, and adds it to a list of calls
            # to return
            for call in data:
                if (call.src_number in filter_customer
                        or call.dst_number in filter_customer):
                    filtered_calls.append(call)

            return filtered_calls

        return data

    def __str__(self) -> str:
        """ Return a description of this filter to be displayed in the UI menu
        """
        return "Filter events based on customer ID"


class DurationFilter(Filter):
    """
    A class for selecting only the calls lasting either over or under a
    specified duration.
    """

    def apply(self, customers: list[Customer],
              data: list[Call],
              filter_string: str) \
            -> list[Call]:
        """ Return a list of all unique calls from <data> with a duration
        of under or over the time indicated in the <filter_string>.

        The <customers> list contains all customers from the input dataset.

        The filter string is valid if and only if it contains the following
        input format: either "Lxxx" or "Gxxx", indicating to filter calls less
        than xxx or greater than xxx seconds, respectively.
        - If the filter string is invalid, return the original list <data>
        - If the filter string is invalid, your code must not crash, as
        specified in the handout.

        Do not mutate any of the function arguments!
        """
        try:
            filter_string_valid = (filter_string[0] in "LG"
                                   and 0 <= int(filter_string[1:]) <= 999)
        except (ValueError, IndexError):
            # Should run if filter_string[1:] causes and index error, or if it's
            # impossible to turn filter_string[1:] into an integer
            filter_string_valid = False

        if filter_string_valid:
            filtered_calls = []
            filter_seconds = int(filter_string[1:])

            # Goes through every call in dataset and checks
            # if call duration is smaller than (in if block)
            # or greater than (in else block) than duration
            # specified by filter string. If conditions met,
            # call added to a list that is returned at end
            if filter_string[0] == 'L':
                for call in data:
                    if call.duration < filter_seconds:
                        filtered_calls.append(call)
            else:
                for call in data:
                    if call.duration > filter_seconds:
                        filtered_calls.append(call)

            return filtered_calls

        return data

    def __str__(self) -> str:
        """ Return a description of this filter to be displayed in the UI menu
        """
        return "Filter calls based on duration; " \
               "L### returns calls less than specified length, G### for greater"


def is_loc_filter_str_valid(filter_string: str) -> Optional[list[float]]:
    """
    Checks filter string is valid. If it is valid, returns a list
    of the coordinates in the filter string in the format:
        lowerLong, lowerLat, upperLong, upperLat.

    Otherwise, returns None
    """
    map_coords = (-79.697878, 43.576959, -79.19638, 43.799568)
    filter_coords = [0, 0, 0, 0]
    # Coordinates of filter_coords in order
    # lowerLong, lowerLat, upperLong, upperLat
    index = 0
    sub_str_start = 0

    for i in range(len(filter_string)):
        if filter_string[i] == ',':
            try:
                filter_coords[index] = float(filter_string[sub_str_start:i])
            except (IndexError, ValueError):
                # Called if filter_string[sub_str_start:i]
                # cannot be accessed, or if filter_string[sub_str_start:i]
                # cannot be converted to a float
                return None

            index += 1
            # To indicate next lat/long coordinate is being derived
            sub_str_start = i + 2
            # To bypass space in middle of comma and next number

        if index == 3:
            try:
                filter_coords[index] = float(filter_string[sub_str_start:])
                break
            except (IndexError, ValueError):
                # Called if filter_string[sub_str_start:]
                # cannot be accessed, or if filter_string[sub_str_start:]
                # cannot be converted to a float
                return None

    # Checks if lower bounds are smaller than or equal to
    # upper bounds
    if (filter_coords[0] > filter_coords[2]
            and filter_coords[1] > filter_coords[3]):
        return None

    # Checks if all bounds are within map coordinate ranges
    is_valid = (filter_coords[0] >= map_coords[0]
                and filter_coords[1] >= map_coords[1]
                and filter_coords[2] <= map_coords[2]
                and filter_coords[3] <= map_coords[3])

    if is_valid:
        return filter_coords
    else:
        return None


class LocationFilter(Filter):
    """
    A class for selecting only the calls that took place within a specific area
    """

    def apply(self, customers: list[Customer],
              data: list[Call],
              filter_string: str) \
            -> list[Call]:
        """ Return a list of all unique calls from <data>, which took
        place within a location specified by the <filter_string>
        (at least the source or the destination of the event was
        in the range of coordinates from the <filter_string>).

        The <customers> list contains all customers from the input dataset.

        The filter string is valid if and only if it contains four valid
        coordinates within the map boundaries.
        These coordinates represent the location of the lower left corner
        and the upper right corner of the search location rectangle,
        as 2 pairs of longitude/latitude coordinates, each separated by
        a comma and a space:
          lowerLong, lowerLat, upperLong, upperLat
        Calls that fall exactly on the boundary of this rectangle are
        considered a match as well.
        - If the filter string is invalid, return the original list <data>
        - If the filter string is invalid, your code must not crash, as
        specified in the handout.

        Do not mutate any of the function arguments!
        """
        # Below represents the latitude-longitude range given by
        # the filter string. If the filter string is invalid, it is None
        filt_cord = is_loc_filter_str_valid(filter_string)

        if filt_cord is not None:
            filtered_calls = []

            # For every call, checks if either the source location
            # (where the call was made) or destination location
            # (where the call was received) is in between the given
            # latitude-longitude coordinates in the filter string.
            # If conditions met, added in a list that is returned
            # at end.
            for call in data:
                if (filt_cord[0] <= call.src_loc[0] <= filt_cord[2]
                        and filt_cord[1] <= call.src_loc[1] <= filt_cord[3]):
                    filtered_calls.append(call)
                elif (filt_cord[0] <= call.dst_loc[0] <= filt_cord[2]
                        and filt_cord[1] <= call.dst_loc[1] <= filt_cord[3]):
                    filtered_calls.append(call)

            return filtered_calls

        return data

    def __str__(self) -> str:
        """ Return a description of this filter to be displayed in the UI menu
        """
        return "Filter calls made or received in a given rectangular area. " \
               "Format: \"lowerLong, lowerLat, " \
               "upperLong, upperLat\" (e.g., -79.6, 43.6, -79.3, 43.7)"


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-import-modules': [
            'python_ta', 'typing', 'time', 'datetime', 'call', 'customer'
        ],
        'max-nested-blocks': 4,
        'allowed-io': ['apply', '__str__'],
        'disable': ['W0611', 'W0703'],
        'generated-members': 'pygame.*'
    })
