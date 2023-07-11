from flask import json
from guidescanpy import config
from urllib.parse import quote


def test_info(app):
    response = app.test_client().get("py/info/supported")
    assert response.mimetype == "application/json"
    data = json.loads(response.data)
    assert "version" in data  # The version of this app
    assert "cli-version" in data  # Guidescan CLI Version
    assert "available" in data  # A list of dicts with enzyme/organism/file keys


def test_query_gene_symbol(app):
    # For the sacCer3 organism and CNE1 gene, find hits for the cas9 enzyme
    # query-text can be a gene symbol, a chromosome region, or an entrez id
    with config({"celery.eager": True}):
        response = app.test_client().get(
            "py/query?organism=sacCer3&enzyme=cas9&query-text=CNE1"
        )
        assert response.mimetype == "application/json"
        data = json.loads(response.data)
        assert (
            len(data["queries"]) == 1
        )  # We passed in a single line in query-text, so we get a single result
        assert len(data["queries"]["CNE1"]["hits"]) == 150


def test_query_entrez_id(app):
    with config({"celery.eager": True}):
        response = app.test_client().get(
            "py/query?organism=sacCer3&enzyme=cas9&query-text=852343"
        )
        assert response.mimetype == "application/json"
        data = json.loads(response.data)
        assert len(data["queries"]) == 1
        assert len(data["queries"]["YRO2"]["hits"]) == 89


def test_query_chr(app):
    with config({"celery.eager": True}):
        response = app.test_client().get(
            "py/query?organism=sacCer3&enzyme=cas9&query-text=chrIX:202200-202300"
        )
        assert response.mimetype == "application/json"
        data = json.loads(response.data)
        assert len(data["queries"]) == 1
        assert len(data["queries"]["chrIX:202200-202300"]["hits"]) == 4


def test_query_chr_bad(app):
    with config({"celery.eager": True}):
        # No such chromosome - chrXX
        response = app.test_client().get(
            "py/query?organism=sacCer3&enzyme=cas9&query-text=chrXX:1000-2000"
        )
        assert response.mimetype == "application/json"
        data = json.loads(response.data)
        assert len(data["queries"]) == 0


def test_query_chr_pos_bad(app):
    with config({"celery.eager": True}):
        # Positions don't exist on chrV, which is length 576874
        response = app.test_client().get(
            "py/query?organism=sacCer3&enzyme=cas9&query-text=chrV:182113225-182113225"
        )
        assert response.mimetype == "application/json"
        data = json.loads(response.data)
        assert len(data["queries"]) == 0


def test_region_exceed_limit(app):
    # RAD51 region is ~1.2K, so the following should fail
    with config({"celery.eager": True, "guidescan.region_size_limit": 1000}):
        query_text = "RAD51"
        encoded_query_text = quote(query_text)
        response = app.test_client().get(
            f"py/query?organism=sacCer3&enzyme=cas9&query-text={encoded_query_text}"
        )
        assert response.status_code == 500
