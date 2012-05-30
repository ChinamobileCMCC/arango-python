
from .tests_base import TestsBase

from nose.tools import assert_equal, raises, assert_false

from arango.document import Document, Documents
from arango.utils import json
from arango.exceptions import DocumentAlreadyCreated, \
                               DocumentIncompatibleDataType


__all__ = ("TestDocument", "TestDocumentBase")


class TestDocumentBase(TestsBase):

    def delete_response_mock(self):
        return self.response_mock(
            status_code=200,
            text=json.dumps(dict(
                _rev=30967598,
                _id=1,
                error=False,
                code=204
            )),
            method="delete"
        )

    def create_response_mock(self, _id=None, body=None):
        body = body if body != None else {}
        defaults = dict(
            _rev=_id or 30967598,
            _id=1,
            error=False,
            code=201
        )

        defaults.update(body)

        patcher = self.response_mock(
            status_code=201,
            text=json.dumps(defaults),
            method="post"
        )

        return patcher

    def create_document(self, body, _id=None):
        patcher = self.create_response_mock(_id=_id)
        patcher.start()

        doc = self.c.docs.create(body)
        patcher.stop()

        return doc


class TestDocument(TestDocumentBase):
    def setUp(self):
        super(TestDocument, self).setUp()
        self.c = self.conn.collection.test
        self.d = self.c.docs

    def test_collection_shortcut(self):
        assert_equal(type(self.d), Documents)
        assert_equal(type(self.c.docs), type(self.c.documents))

    def test_document_create(self):
        body = dict(
            key="value",
            num=1
        )

        url = lambda p: "{0}{1}".format(
            self.conn.url,
            self.conn.qs(
                Document.DOCUMENT_PATH,
                **p
            )
        )

        params = dict(
            collection="test"
        )

        doc = self.create_document(body)
        assert_equal(doc.response.url, url(params))
        assert_equal(doc._body, body)

        params.update({
            "createCollection": True
        })

        patcher = self.create_response_mock()
        patcher.start()

        doc = self.c.docs.create(body, createCollection=True)
        assert_equal(doc.response.url, url(params))

        test_args = {"data": json.dumps(body)}
        assert_equal(doc.response.args, test_args)

        patcher.stop()

    @raises(DocumentAlreadyCreated)
    def test_document_create_of_created(self):
        body = {"value": "test"}
        doc = self.c.docs.create(body)

        assert_equal(doc, None)

        # here we modelling properly created document
        doc = Document(collection=self.c)

        doc._body = body
        doc._id = 1
        doc._rev = 1

        doc.create(body)

    def test_document_deletion(self):
        body = {"value": "test"}
        url = "{0}{1}".format(
            self.conn.url,
            Document.DELETE_DOCUMENT_PATH.format("1"),
        )

        doc = self.create_document(body)
        assert_equal(doc._body, body)

        patcher = self.delete_response_mock()
        patcher.start()

        doc._id = 1
        doc._rev = 1
        doc._body = {}

        doc.delete()

        assert_equal(doc.response.url, url)

        assert_equal(doc.id, None)
        assert_equal(doc.rev, None)
        assert_equal(doc.doc, None)

        patcher.stop()

    def test_get_document_fields(self):
        body = {
            "array": [1, 2, 3],
            "options": None,
            "number": 5.5,
            "tree": {
                "sample1": "1",
                "sample2": "2"
            }
        }

        doc = self.create_document(body)

        assert_equal(
            doc.get("array", default=None),
            [1, 2, 3]
        )

        assert_equal(
            doc.get(),
            body
        )

        assert_equal(
            doc["tree"]["sample1"],
            body["tree"]["sample1"]
        )

    def test_get_document_arr(self):
        body = [1, 2, 3]

        doc = self.create_document(body)

        assert_equal(doc.doc, body)
        assert_equal(doc.get(2), body[2])

        # support to getting item by numeric indexes
        # in case we storing plain arrays
        assert_equal(doc[1], body[1])

    def test_document_update_simple(self):
        doc = self.create_document({"value": 1})

        assert_equal(doc["value"], 1)
        doc["value"] = 2

        assert_equal(doc["value"], 2)
        assert_false("name" in doc.doc)
        doc.update({"name": "testing", "value": 3}, save=False)
        assert_equal(doc["name"], "testing")
        assert_equal(doc["value"], 3)

        doc = self.create_document([1, 2, 3])
        assert_equal(len(doc.doc), 3)
        assert_equal(doc.doc[1], 2)

        doc.update([4, 5, 6], save=False)
        assert_equal(len(doc.doc), 6)
        assert_equal(doc.doc[1], 2)
        assert_equal(doc.doc[3], 4)

    def test_document_update_complex(self):
        doc = self.create_document({
            "value": {
                "level1": {
                    "level2": [1, 2, 3]
                }
            }
        })

        doc.doc.get("value").get("level1")["level2"] = [3, 4, 5]

        assert_equal(
            doc.doc.get("value").get("level1").get("level2"),
            [3, 4, 5]
        )

    @raises(DocumentIncompatibleDataType)
    def test_wrong_type_on_update(self):
        doc = self.create_document({})
        doc.update(object())

    @raises(DocumentIncompatibleDataType)
    def test_deleted_doc_update(self):
        doc = self.create_document({})

        patcher = self.delete_response_mock()

        patcher.start()
        doc.delete()
        patcher.stop()

        doc.update({})

    def test_save(self):
        doc = self.create_document({})

        patcher = self.response_mock(
            status_code=201,
            text=json.dumps(dict(
                _rev=30967599,
                _id=1,
                error=False,
                code=201
            )),
            method="put"
        )

        patcher.start()

        test_data = {
            "name": "sample"
        }
        doc.update(test_data)

        url = "{0}{1}".format(
            doc.connection.url,
            doc.UPDATE_DOCUMENT_PATH.format(doc.id)
        )

        assert_equal(doc.rev, 30967599)
        assert_equal(doc.response.url, url)
        assert_equal(
            doc.response.args,
            dict(data=json.dumps(test_data))
        )

        # call manuall save() method
        doc = self.create_document({})

        doc.update(test_data, save=False)
        doc.save()

        assert_equal(doc.rev, 30967599)
        patcher.stop()
