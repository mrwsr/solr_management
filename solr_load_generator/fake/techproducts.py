"""Generate (probably) unique documents for techproduct example."""
from hypothesis import given, strategies as st

from . import run
from .common import solr_text, lat_long, solr_date


def techproducts_id():
    return st.builds(u'{}-{}-{}'.format,
                     st.integers(min_value=0),
                     solr_text(),
                     st.integers(min_value=0))


@given(id=techproducts_id(),
       name=solr_text(),
       manu=solr_text(),
       manu_id_s=techproducts_id(),
       cat=solr_text(),
       features=solr_text(),
       weight=st.floats(min_value=1, max_value=100),
       price=st.decimals(),
       popularity=st.integers(min_value=1, max_value=10000),
       inStock=st.booleans(),
       store=lat_long(),
       manufacturedate_dt=solr_date())
def generate_documents(use_doc, **kwargs):
    use_doc(kwargs)


def main(*args, **kwargs):
    run.main(generate_documents=generate_documents, *args, **kwargs)


if __name__ == '__main__':
    main()
