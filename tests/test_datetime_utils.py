import datetime
from blueshed.micro.utils.date_utils import parse_date, json_date
from blueshed.micro.utils.json_utils import loads, dumps


def test_parse_date():
    d1 = datetime.datetime.now()
    assert d1 == parse_date(str(d1))
    assert d1 == parse_date(json_date(d1))

    assert d1 == parse_date(d1)

    d2 = datetime.date.today()
    assert d2 == parse_date(str(d2)).date()
    assert d2 == parse_date(json_date(d2)).date()


class Event(object):
    from_date = datetime.datetime.now()
    to_date = from_date + datetime.timedelta(1)

    def to_json(self):
        ''' called by dumps '''
        return {
            "_type": self.__class__.__name__,
            "from": self.from_date,
            "to": self.to_date
        }


def test_json_utils():
    e = Event()
    s = dumps(e)
    e2 = loads(s)
    assert e.from_date == parse_date(e2["from"])
    assert e.to_date == parse_date(e2["to"])
