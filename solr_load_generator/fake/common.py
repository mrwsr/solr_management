import string
import datetime

import hypothesis.strategies as st


ALPHABET = (string.ascii_uppercase + string.ascii_lowercase).decode('ascii')


def solr_date():

    def timestamp_as_iso_format(s):
        return datetime.datetime.fromtimestamp(s).isoformat() + 'Z'

    return st.floats(min_value=0,
                     max_value=1 << 31).map(timestamp_as_iso_format)
    return st.integers(min_value=1466706406,
                       max_value=1483228800).map(timestamp_as_iso_format)


def solr_text():
    return st.text(alphabet=ALPHABET, min_size=1, max_size=100)


@st.composite
def lat_long(draw):
    return draw(st.just('{},{}'.format(
        draw(st.floats(min_value=-90, max_value=90)),
        draw(st.floats(min_value=-180, max_value=180)))))
