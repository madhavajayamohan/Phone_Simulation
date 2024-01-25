import datetime

import pytest

from application import create_customers, process_event_history, new_month
from contract import TermContract, MTMContract, PrepaidContract
from customer import Customer
from filter import DurationFilter, CustomerFilter, LocationFilter, ResetFilter
from phoneline import PhoneLine
from call import Call

test_dict = {'events': [
    {"type": "call",
     "src_number": "111-1111",
     "dst_number": "222-2222",
     "time": "2018-01-02 01:01:06",
     "duration": 915,
     "src_loc": [-79.42, 43.64],
     "dst_loc": [-79.52, 43.75]},
    {"type": "sms",
     "src_number": "111-1111",
     "dst_number": "222-2222",
     "time": "2018-01-03 01:01:01",
     "src_loc": [-79.42848154284123, 43.641401675960374],
     "dst_loc": [-79.52745693913239, 43.750338501653374]},
    {"type": "call",
     "src_number": "111-1111",
     "dst_number": "333-3333",
     "time": "2018-01-05 01:01:06",
     "duration": 1975,
     "src_loc": [-79.430, 43.675],
     "dst_loc": [-79.572, 43.782]},
    {"type": "call",
     "src_number": "333-3333",
     "dst_number": "222-2222",
     "time": "2018-01-07 01:01:06",
     "duration": 375,
     "src_loc": [-79.450, 43.663],
     "dst_loc": [-79.276, 43.798]},
    {"type": "call",
     "src_number": "111-1111",
     "dst_number": "222-2222",
     "time": "2018-01-08 01:01:06",
     "duration": 6028,
     "src_loc": [-79.612, 43.595],
     "dst_loc": [-79.437, 43.684]},
    {"type": "call",
     "src_number": "333-3333",
     "dst_number": "111-1111",
     "time": "2018-02-01 01:01:06",
     "duration": 469,
     "src_loc": [-79.353, 43.729],
     "dst_loc": [-79.478, 43.792]},
    {"type": "call",
     "src_number": "222-2222",
     "dst_number": "111-1111",
     "time": "2018-02-03 01:01:06",
     "duration": 248,
     "src_loc": [-79.268, 43.766],
     "dst_loc": [-79.250, 43.679]},
    {"type": "call",
     "src_number": "222-2222",
     "dst_number": "111-1111",
     "time": "2018-02-05 01:01:06",
     "duration": 335,
     "src_loc": [-79.262, 43.673],
     "dst_loc": [-79.477, 43.719]},
    {"type": "call",
     "src_number": "333-3333",
     "dst_number": "111-1111",
     "time": "2018-02-17 01:01:06",
     "duration": 211,
     "src_loc": [-79.660, 43.669],
     "dst_loc": [-79.358, 43.731]},
    {"type": "call",
     "src_number": "222-2222",
     "dst_number": "333-3333",
     "time": "2018-02-18 01:01:06",
     "duration": 884,
     "src_loc": [-79.551, 43.648],
     "dst_loc": [-79.566, 43.688]},
    {"type": "call",
     "src_number": "444-4444",
     "dst_number": "222-2222",
     "time": "2018-03-01 01:01:06",
     "duration": 779,
     "src_loc": [-79.449, 43.594],
     "dst_loc": [-79.278, 43.750]},
    {"type": "call",
     "src_number": "555-5555",
     "dst_number": "111-1111",
     "time": "2018-03-02 01:01:06",
     "duration": 469,
     "src_loc": [-79.340, 43.717],
     "dst_loc": [-79.396, 43.610]},
    {"type": "call",
     "src_number": "111-1111",
     "dst_number": "444-4444",
     "time": "2018-03-03 01:01:06",
     "duration": 317,
     "src_loc": [-79.595, 43.743],
     "dst_loc": [-79.369, 43.709]},
    {"type": "call",
     "src_number": "333-3333",
     "dst_number": "555-5555",
     "time": "2018-03-04 01:01:06",
     "duration": 975,
     "src_loc": [-79.323, 43.769],
     "dst_loc": [-79.249, 43.618]}
],
    'customers': [
        {'lines': [
            {'number': '111-1111',
             'contract': 'term'}
        ],
            'id': 1111},
        {'lines': [
            {'number': '222-2222',
             'contract': 'mtm'}
        ],
            'id': 2222},
        {'lines': [
            {'number': '333-3333',
             'contract': 'prepaid'}
        ],
            'id': 3333},
        {'lines': [
            {'number': '444-4444',
             'contract': 'term'},
            {'number': '555-5555',
             'contract': 'mtm'}
        ],
            'id': 4444}
    ]
}


def process_test_dict() -> list[Customer]:
    customer_list = create_customers(test_dict)
    process_event_history(test_dict, customer_list)
    return customer_list


def get_all_call_history():
    """
    Returns a list of all the calls from test_dict.
    """
    customer_list = process_test_dict()
    all_history = []

    for cust in customer_list:
        hist = cust.get_history()[0]
        all_history.extend(hist)

    return all_history


def test_new_month_and_customer_history() -> None:
    """ Test if new month is called properly. In doing so, also checks:
        - If number of free and billed minutes are counted properly for
          term contracts if free_minute usage is exceeded
        - Check if number of free minutes resets after every month
        - If bills are generated for gap months, and call history is updated
          during gap months
    """
    customer_list = create_customers(test_dict)
    first_month_events = {'events': test_dict["events"][0:5]}
    process_event_history(first_month_events, customer_list)
    new_month(customer_list, 2, 2018)

    # Customer 1 Test
    # Also checks if number of billed minutes and free minutes
    # are correct for bill
    bill = customer_list[0].generate_bill(1, 2018)
    history = customer_list[0].get_history()
    assert bill[0] == 1111
    assert bill[1] == 25
    assert bill[2][0]['total'] == 25
    assert bill[2][0]['free_mins'] == 100
    assert bill[2][0]['billed_mins'] == 50
    assert len(history[0]) == 3
    assert len(history[1]) == 0

    customer_list[0].new_month(2, 2018)
    assert customer_list[0]._phone_lines[0].contract._num_free_min_used == 0

    # Customer 2 Test
    # Also checks for gap months
    bill = customer_list[1].generate_bill(1, 2018)
    history = customer_list[1].get_history()
    assert bill[0] == 2222
    assert bill[1] == 50
    assert bill[2][0]['total'] == 50
    assert bill[2][0]['billed_mins'] == 0
    assert len(history[0]) == 0
    assert len(history[1]) == 3

    # Customer 3 Test
    bill = customer_list[2].generate_bill(1, 2018)
    history = customer_list[2].get_history()
    assert bill[0] == 3333
    assert bill[1] == -99.825
    assert bill[2][0]['total'] == -99.825
    assert bill[2][0]['billed_mins'] == 7
    assert len(history[0]) == 1
    assert len(history[1]) == 1

    # Customer 4 Test
    # Also checks for gap months
    bill = customer_list[3].generate_bill(1, 2018)
    history = customer_list[3].get_history()
    assert bill[0] == 4444
    assert bill[1] == 70
    assert bill[2][0]['total'] == 20
    assert bill[2][0]['free_mins'] == 0
    assert bill[2][0]['billed_mins'] == 0
    assert bill[2][1]['total'] == 50
    assert bill[2][1]['billed_mins'] == 0
    assert len(history[0]) == 0
    assert len(history[1]) == 0


def test_cancellation_payments_1() -> None:
    """
    Tests is bills are cancelled correctly for general cases, like
    when balance < 0 and term contract cancelled before end date
    """
    customer_list = process_test_dict()
    new_month(customer_list, 4, 2018)

    # Term Contract Cancellation
    assert customer_list[0].cancel_phone_line("111-1111") == 20

    # MTM Contract Cancellation
    assert customer_list[1].cancel_phone_line("222-2222") == 50

    # Prepaid Contract Cancellation
    assert customer_list[2].cancel_phone_line("333-3333") == 0


def test_cancellation_payments_2() -> None:
    """
    Tests is bills are cancelled correctly for other cases, like
    when balance > 0 and term contract cancelled after/on end date
    """
    customer_list = process_test_dict()

    date = datetime.datetime.strptime(test_dict['events'][-1]['time'],
                                                "%Y-%m-%d %H:%M:%S")

    customer_list[0]._phone_lines[0].contract.end = date

    new_call = Call("333-3333", "111-1111",
                    date, 360000,
                    (1, 2), (3, 4))
    customer_list[2].make_call(new_call)

    new_month(customer_list, 4, 2018)

    # Term Contract Cancellation

    assert customer_list[0].cancel_phone_line("111-1111") == -280

    # MTM Contract Cancellation
    assert customer_list[1].cancel_phone_line("222-2222") == 50

    # Prepaid Contract Cancellation
    assert customer_list[2].cancel_phone_line("333-3333") == pytest.approx(25.9)


def test_prepaid_correct_bills() -> None:
    """
    Tests if prepaid contract gives correct bills for every month
    """
    customer_list = create_customers(test_dict)

    customer_list[2].new_month(12, 2017)

    process_event_history(test_dict, customer_list)

    customer_list[2].new_month(4, 2018)
    bill_0 = customer_list[2].generate_bill(12, 2017)
    bill_1 = customer_list[2].generate_bill(1, 2018)
    bill_2 = customer_list[2].generate_bill(2, 2018)
    bill_3 = customer_list[2].generate_bill(3, 2018)

    assert bill_0[1] == -100
    assert bill_0[2][0]['billed_mins'] == 0

    assert bill_1[1] == pytest.approx(-99.825)
    assert bill_1[2][0]['billed_mins'] == 7

    assert bill_2[1] == pytest.approx(-99.525)
    assert bill_2[2][0]["billed_mins"] == 12

    assert bill_3[1] == pytest.approx(-99.1)
    assert bill_3[2][0]["billed_mins"] == 17

    customer_list[2].new_month(5, 2018)
    bill_4 = customer_list[2].generate_bill(4, 2018)
    assert bill_4[1] == pytest.approx(-99.1)
    assert bill_4[2][0]["billed_mins"] == 0


def test_mtm_correct_bills() -> None:
    """
    Tests if mtm contract gives correct bills for every month
    """
    customer_list = create_customers(test_dict)

    customer_list[1].new_month(12, 2017)

    process_event_history(test_dict, customer_list)

    customer_list[1].new_month(4, 2018)
    bill_0 = customer_list[1].generate_bill(12, 2017)
    bill_1 = customer_list[1].generate_bill(1, 2018)
    bill_2 = customer_list[1].generate_bill(2, 2018)
    bill_3 = customer_list[1].generate_bill(3, 2018)

    assert bill_0[1] == 50
    assert bill_0[2][0]['billed_mins'] == 0

    assert bill_1[1] == pytest.approx(50)
    assert bill_1[2][0]["billed_mins"] == 0

    assert bill_2[1] == pytest.approx(51.3)
    assert bill_2[2][0]["billed_mins"] == 26

    assert bill_3[1] == pytest.approx(50)
    assert bill_3[2][0]["billed_mins"] == 0


def test_term_correct_bills() -> None:
    """
    Tests if term contract gives correct bills for every month
    """
    customer_list = create_customers(test_dict)

    customer_list[0].new_month(12, 2017)

    process_event_history(test_dict, customer_list)

    customer_list[0].new_month(4, 2018)

    bill_0 = customer_list[0].generate_bill(12, 2017)
    bill_1 = customer_list[0].generate_bill(1, 2018)
    bill_2 = customer_list[0].generate_bill(2, 2018)
    bill_3 = customer_list[0].generate_bill(3, 2018)

    assert bill_0[1] == 320
    assert bill_0[2][0]['free_mins'] == 0
    assert bill_0[2][0]['billed_mins'] == 0

    assert bill_1[1] == pytest.approx(25)
    assert bill_1[2][0]['free_mins'] == 100
    assert bill_1[2][0]["billed_mins"] == 50

    assert bill_2[1] == 20
    assert bill_2[2][0]['free_mins'] == 0
    assert bill_2[2][0]["billed_mins"] == 0

    assert bill_3[1] == 20
    assert bill_3[2][0]['free_mins'] == 6
    assert bill_3[2][0]["billed_mins"] == 0


def test_num_events() -> None:
    """
    Test is process history gets correct number of call events,
    and ignores sms events
    """
    assert len(get_all_call_history()) == 13


def test_num_bills() -> None:
    """
    Test if the correct number of bills are generated for
    each phone line
    """
    customer_list = process_test_dict()
    assert len(customer_list[0]._phone_lines[0].bills) == 3
    assert len(customer_list[1]._phone_lines[0].bills) == 3
    assert len(customer_list[2]._phone_lines[0].bills) == 3
    assert len(customer_list[3]._phone_lines[0].bills) == 3
    assert len(customer_list[3]._phone_lines[1].bills) == 3


def test_proper_customer_filter_str() -> None:
    """
    Test is invalid customer filter strings are properly dealt with
    """
    customer_list = process_test_dict()
    all_history = get_all_call_history()
    assert CustomerFilter().apply(customer_list, all_history, 'a') == all_history
    assert CustomerFilter().apply(customer_list, all_history, 'abcdef') == all_history
    assert CustomerFilter().apply(customer_list, all_history, "12345") == all_history
    assert CustomerFilter().apply(customer_list, all_history, '1111.0') == all_history
    assert CustomerFilter().apply(customer_list, all_history, 'true') == all_history
    assert CustomerFilter().apply(customer_list, all_history, '[56]') == all_history


def test_proper_duration_filter_str() -> None:
    """
    Test is invalid duration filter strings are properly dealt with
    """
    customer_list = process_test_dict()
    all_history = get_all_call_history()
    assert DurationFilter().apply(customer_list, all_history, 'a') == all_history
    assert DurationFilter().apply(customer_list, all_history, 'abcdef') == all_history
    assert DurationFilter().apply(customer_list, all_history, "12345") == all_history
    assert DurationFilter().apply(customer_list, all_history, '1111.0') == all_history
    assert DurationFilter().apply(customer_list, all_history, 'true') == all_history
    assert DurationFilter().apply(customer_list, all_history, '[56]') == all_history

    assert DurationFilter().apply(customer_list, all_history, 'l56') == all_history
    assert DurationFilter().apply(customer_list, all_history, 'g543') == all_history
    assert DurationFilter().apply(customer_list, all_history, 'A56') == all_history
    assert DurationFilter().apply(customer_list, all_history, 'B56') == all_history

    assert DurationFilter().apply(customer_list, all_history, 'L') == all_history
    assert DurationFilter().apply(customer_list, all_history, 'G') == all_history
    assert DurationFilter().apply(customer_list, all_history, 'LARGE') == all_history
    assert DurationFilter().apply(customer_list, all_history, 'GRANDE') == all_history
    assert DurationFilter().apply(customer_list, all_history, 'L1000') == all_history
    assert DurationFilter().apply(customer_list, all_history, 'G-90') == all_history


def test_proper_location_filter_str() -> None:
    """
    Test is invalid location filter strings are properly dealt with
    """
    customer_list = process_test_dict()
    all_history = get_all_call_history()

    assert LocationFilter().apply(customer_list, all_history, 'a') == all_history
    assert LocationFilter().apply(customer_list, all_history, 'abcdef') == all_history
    assert LocationFilter().apply(customer_list, all_history, "12345") == all_history
    assert LocationFilter().apply(customer_list, all_history, '1111.0') == all_history
    assert LocationFilter().apply(customer_list, all_history, 'true') == all_history
    assert LocationFilter().apply(customer_list, all_history, '[56]') == all_history

    assert LocationFilter().apply(customer_list, all_history, 'a, b, c, d') == all_history
    assert LocationFilter().apply(customer_list, all_history, '1, 2, 3, 4') == all_history

    assert (LocationFilter().apply(customer_list, all_history, '-79.543, 43.58, -79.206') ==
            all_history)
    assert (LocationFilter().apply(customer_list, all_history, '-79.543, -79.206, 43.78') ==
            all_history)
    assert (LocationFilter().apply(customer_list, all_history, '15') ==
            all_history)

    assert (LocationFilter().apply(customer_list, all_history, '-79.697879, 43.576959, -79.19638, 43.799568') ==
            all_history)
    assert (LocationFilter().apply(customer_list, all_history, '-79.697878, 43.576958, -79.19638, 43.799568') ==
            all_history)
    assert (LocationFilter().apply(customer_list, all_history, '-79.697878, 43.576959, -79.19637, 43.799568') ==
            all_history)
    assert (LocationFilter().apply(customer_list, all_history, '-79.697878, 43.576959, -79.19638, 43.799569') ==
            all_history)

    assert (LocationFilter().apply(customer_list, all_history, '0, 45, -100, 0') ==
            all_history)


def test_customer_filter() -> None:
    """
    Test if customer filter works properly
    """
    customer_list = process_test_dict()
    all_history = get_all_call_history()

    cust_1_calls = CustomerFilter().apply(customer_list, all_history, '1111')
    assert len(cust_1_calls) == 9
    assert cust_1_calls[0] is all_history[0]
    assert cust_1_calls[1] is all_history[1]
    assert cust_1_calls[2] is all_history[2]
    assert cust_1_calls[3] is all_history[3]
    assert cust_1_calls[4] is all_history[4]
    assert cust_1_calls[5] is all_history[5]
    assert cust_1_calls[6] is all_history[8]
    assert cust_1_calls[7] is all_history[9]
    assert cust_1_calls[8] is all_history[12]

    assert len(CustomerFilter().apply(customer_list, cust_1_calls, '3333')) == 3
    assert len(CustomerFilter().apply(customer_list, cust_1_calls, '2222')) == 4
    assert len(CustomerFilter().apply(customer_list, cust_1_calls, '4444')) == 2

    cust_1_calls = ResetFilter().apply(customer_list, cust_1_calls, '1111')
    assert len(cust_1_calls) == len(all_history)

    for i in range(len(cust_1_calls)):
        assert cust_1_calls[i].src_number == all_history[i].src_number
        assert cust_1_calls[i].dst_number == all_history[i].dst_number
        assert cust_1_calls[i].dst_number == all_history[i].dst_number
        assert cust_1_calls[i].duration == all_history[i].duration
        assert cust_1_calls[i].src_loc == all_history[i].src_loc
        assert cust_1_calls[i].dst_loc == all_history[i].dst_loc

    cust_2_calls = CustomerFilter().apply(customer_list, all_history, '2222')
    assert len(cust_2_calls) == 7
    assert cust_2_calls[0] is all_history[0]
    assert cust_2_calls[1] is all_history[2]
    assert cust_2_calls[2] is all_history[4]
    assert cust_2_calls[3] is all_history[5]
    assert cust_2_calls[4] is all_history[6]
    assert cust_2_calls[5] is all_history[7]
    assert cust_2_calls[6] is all_history[11]

    assert len(CustomerFilter().apply(customer_list, cust_2_calls, '3333')) == 2
    assert len(CustomerFilter().apply(customer_list, cust_2_calls, '1111')) == 4
    assert len(CustomerFilter().apply(customer_list, cust_2_calls, '4444')) == 1

    cust_3_calls = CustomerFilter().apply(customer_list, all_history, '3333')
    assert len(cust_3_calls) == 6
    assert cust_3_calls[0] is all_history[1]
    assert cust_3_calls[1] is all_history[6]
    assert cust_3_calls[2] is all_history[7]
    assert cust_3_calls[3] is all_history[8]
    assert cust_3_calls[4] is all_history[9]
    assert cust_3_calls[5] is all_history[10]

    assert len(CustomerFilter().apply(customer_list, cust_3_calls, '2222')) == 2
    assert len(CustomerFilter().apply(customer_list, cust_3_calls, '1111')) == 3
    assert len(CustomerFilter().apply(customer_list, cust_3_calls, '4444')) == 1

    cust_4_calls = CustomerFilter().apply(customer_list, all_history, '4444')
    assert len(cust_4_calls) == 4
    assert cust_4_calls[0] is all_history[3]
    assert cust_4_calls[1] is all_history[10]
    assert cust_4_calls[2] is all_history[11]
    assert cust_4_calls[3] is all_history[12]

    assert len(CustomerFilter().apply(customer_list, cust_4_calls, '2222')) == 1
    assert len(CustomerFilter().apply(customer_list, cust_4_calls, '1111')) == 2
    assert len(CustomerFilter().apply(customer_list, cust_4_calls, '3333')) == 1


def test_duration_filter() -> None:
    """
    Test if duration filter works properly
    """
    customer_list = process_test_dict()
    all_history = get_all_call_history()
    assert DurationFilter().apply(customer_list, all_history, 'G0') == all_history
    d_list = DurationFilter().apply(customer_list, all_history, 'L999')
    assert len(d_list) == 11
    assert d_list[0] is all_history[0]
    assert d_list[1] is all_history[3]
    assert d_list[2] is all_history[4]
    assert d_list[3] is all_history[5]
    assert d_list[4] is all_history[6]
    assert d_list[5] is all_history[7]
    assert d_list[6] is all_history[8]
    assert d_list[7] is all_history[9]
    assert d_list[8] is all_history[10]
    assert d_list[9] is all_history[11]
    assert d_list[10] is all_history[12]

    d_list = DurationFilter().apply(customer_list, d_list, 'G500')
    assert len(d_list) == 4
    assert d_list[0] is all_history[0]
    assert d_list[1] is all_history[6]
    assert d_list[2] is all_history[10]
    assert d_list[3] is all_history[11]

    d_list = DurationFilter().apply(customer_list, d_list, 'L900')
    assert len(d_list) == 2
    assert d_list[0] is all_history[6]
    assert d_list[1] is all_history[11]

    d_list = ResetFilter().apply(customer_list, all_history, 'L999')

    assert len(d_list) == len(all_history)

    for i in range(len(d_list)):
        assert str(d_list[i]) == str(all_history[i])

    d_list = DurationFilter().apply(customer_list, all_history, 'G300')
    assert d_list[0] is all_history[0]
    assert d_list[1] is all_history[1]
    assert d_list[2] is all_history[2]
    assert d_list[3] is all_history[3]
    assert d_list[4] is all_history[5]
    assert d_list[5] is all_history[6]
    assert d_list[6] is all_history[7]
    assert d_list[7] is all_history[8]
    assert d_list[8] is all_history[10]
    assert d_list[9] is all_history[11]
    assert d_list[10] is all_history[12]

    d_list = DurationFilter().apply(customer_list, all_history, 'L300')
    assert d_list[0] is all_history[4]
    assert d_list[1] is all_history[9]

    d_list = DurationFilter().apply(customer_list, all_history, 'G469')
    assert d_list[0] is all_history[0]
    assert d_list[1] is all_history[1]
    assert d_list[2] is all_history[2]
    assert d_list[3] is all_history[6]
    assert d_list[4] is all_history[10]
    assert d_list[5] is all_history[11]

    d_list = DurationFilter().apply(customer_list, all_history, 'L469')
    assert d_list[0] is all_history[3]
    assert d_list[1] is all_history[4]
    assert d_list[2] is all_history[5]
    assert d_list[3] is all_history[7]
    assert d_list[4] is all_history[9]


def test_location_filter() -> None:
    """
    Test if location filter works properly
    """
    customer_list = process_test_dict()
    all_history = get_all_call_history()

    loc_list = LocationFilter().apply(customer_list, all_history, '-79.6, 43.58, -79.4, 43.72')
    assert len(loc_list) == 7
    assert loc_list[0] is all_history[0]
    assert loc_list[1] is all_history[1]
    assert loc_list[2] is all_history[2]
    assert loc_list[3] is all_history[5]
    assert loc_list[4] is all_history[6]
    assert loc_list[5] is all_history[7]
    assert loc_list[6] is all_history[11]

    loc_list = ResetFilter().apply(customer_list, all_history, '-79.6, 43.58, -79.4, 43.72')
    assert len(loc_list) == len(all_history)

    for i in range(len(loc_list)):
        assert str(loc_list[i]) == str(all_history[i])

    loc_list = LocationFilter().apply(customer_list, all_history, '-79.69, 43.577, -79.2, 43.77')
    assert len(loc_list) == 13

    loc_list = LocationFilter().apply(customer_list, all_history, '-79.69, 43.6, -79.2, 43.7')
    assert len(loc_list) == 10
    assert loc_list[0] is all_history[0]
    assert loc_list[1] is all_history[1]
    assert loc_list[2] is all_history[2]
    assert loc_list[3] is all_history[4]
    assert loc_list[4] is all_history[5]
    assert loc_list[5] is all_history[6]
    assert loc_list[6] is all_history[7]
    assert loc_list[7] is all_history[9]
    assert loc_list[8] is all_history[10]
    assert loc_list[9] is all_history[12]

    loc_list = LocationFilter().apply(customer_list, all_history, '-79.42, 43.6, -79.42, 43.7')
    assert len(loc_list) == 1
    assert loc_list[0] is all_history[0]

    loc_list = LocationFilter().apply(customer_list, all_history, '-79.6, 43.663, -79.2, 43.663')
    assert len(loc_list) == 1
    assert loc_list[0] is all_history[7]


def test_customer_and_duration() -> None:
    """
    Test if customer filter and duration filter applied together
    works properly
    """
    customer_list = process_test_dict()
    all_history = get_all_call_history()

    lst_1 = CustomerFilter().apply(customer_list, all_history, '2222')
    lst_1 = DurationFilter().apply(customer_list, lst_1, 'G300')

    lst_2 = DurationFilter().apply(customer_list, all_history, 'G300')
    lst_2 = CustomerFilter().apply(customer_list, lst_2, '2222')

    assert lst_1 == lst_2

    assert len(lst_1) == 6

    for i in range(6):
        assert lst_1[i] is lst_2[i]

    assert lst_1[0] is all_history[0]
    assert lst_1[1] is all_history[2]
    assert lst_1[2] is all_history[5]
    assert lst_1[3] is all_history[6]
    assert lst_1[4] is all_history[7]
    assert lst_1[5] is all_history[11]


def test_customer_and_location() -> None:
    """
    Test if customer filter and location filter applied together
    works properly
    """
    customer_list = process_test_dict()
    all_history = get_all_call_history()

    lst_1 = CustomerFilter().apply(customer_list, all_history, '2222')
    lst_1 = LocationFilter().apply(customer_list, lst_1, '-79.6, 43.58, -79.4, 43.72')

    lst_2 = LocationFilter().apply(customer_list, all_history, '-79.6, 43.58, -79.4, 43.72')
    lst_2 = CustomerFilter().apply(customer_list, lst_2, '2222')

    assert lst_1 == lst_2

    assert len(lst_1) == 6

    assert lst_1[0] is all_history[0]
    assert lst_1[1] is all_history[2]
    assert lst_1[2] is all_history[5]
    assert lst_1[3] is all_history[6]
    assert lst_1[4] is all_history[7]
    assert lst_1[5] is all_history[11]


def test_duration_and_location() -> None:
    """
    Test if duration filter and location filter applied together
    works properly
    """
    customer_list = process_test_dict()
    all_history = get_all_call_history()

    lst_1 = DurationFilter().apply(customer_list, all_history, 'G500')
    lst_1 = LocationFilter().apply(customer_list, lst_1, '-79.6, 43.58, -79.4, 43.72')

    lst_2 = LocationFilter().apply(customer_list, all_history, '-79.6, 43.58, -79.4, 43.72')
    lst_2 = DurationFilter().apply(customer_list, lst_2, 'G500')

    for i in range(5):
        assert lst_1[i] is lst_2[i]

    assert lst_1 == lst_2

    assert len(lst_1) == 5

    assert lst_1[0] is all_history[0]
    assert lst_1[1] is all_history[1]
    assert lst_1[2] is all_history[2]
    assert lst_1[3] is all_history[6]
    assert lst_1[4] is all_history[11]

    lst_3 = DurationFilter().apply(customer_list, all_history, 'L0')
    lst_3 = LocationFilter().apply(customer_list, lst_3, '-79.6, 43.58, -79.4, 43.72')

    lst_4 = LocationFilter().apply(customer_list, all_history, '-79.6, 43.58, -79.4, 43.72')
    lst_4 = DurationFilter().apply(customer_list, lst_4, 'L0')

    assert len(lst_3) == 0
    assert len(lst_4) == 0


if __name__ == '__main__':
    pytest.main(['a1_my_tests.py'])
