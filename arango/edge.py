import copy
import logging

from .comparsion import ComparsionMixin
from .document import Document
from .exceptions import EdgeAlreadyCreated, EdgeNotYetCreated, \
                        EdgeIncompatibleDataType, \
                        DocumentIncompatibleDataType

logger = logging.getLogger(__name__)


__all__ = ("Edge", "Edges")


class Edges(object):
    """
    Proxy objects between ``Collection`` and ``Edge``.
    Edges in general very related to ``Document``.
    """
    EDGES_PATH = "/_api/edges/{0}"

    def __init__(self, collection=None):
        self.connection = collection.connection
        self.collection = collection

    def __call__(self, *args, **kwargs):
        from .core import Resultset

        return Resultset(self, *args, **kwargs)

    def __repr__(self):
        return "<ArangoDB Edges Proxy Object>"

    def __len__(self):
        return self.count()

    def count(self):
        """Get count of edges within current collection"""
        response = self.connection.get(
            self.EDGES_PATH.format(self.collection.cid)
        )
        return len(response.get("edges", []))

    def prepare_resultset(self, rs, args=None, kwargs=None):
        """This method should be called to prepare results"""

        kwargs = kwargs if kwargs != None else {}

        if not args or not issubclass(type(args[0]), Document):
            raise DocumentIncompatibleDataType(
                "First argument should be VERTEX (eq document)"
            )

        # specify vertex
        kwargs.update({
            "vertex": args[0].id
        })

        response = self.connection.get(
            self.connection.qs(
                self.EDGES_PATH.format(self.collection.cid),
                **kwargs
            )
        )

        edges = response.get("edges", [])[rs._offset:]

        # set up response data
        rs.response = response
        rs.count = len(edges)

        if rs._limit != None:
            edges = edges[:rs._limit]

        rs.data = edges

    def iterate(self, rs):
        """
        Execute to iterate results
        """
        for edge in rs.data:
            yield Edge(
                collection=self.collection,
                **edge
            )

    def create(self, *args, **kwargs):
        """
        Create new Edge
        """
        edge = Edge(collection=self.collection)
        return edge.create(*args, **kwargs)

    def delete(self, ref):
        """
        Delete Edge by reference
        """

        edge = Edge(collection=self.collection, id=ref)
        return edge.delete()

    def update(self, ref, *args, **kwargs):
        """
        Update Edge by reference
        """

        edge = Edge(collection=self.collection, id=ref)
        return edge.update(*args, **kwargs)


class Edge(ComparsionMixin):
    """
    Edge instance object
    """

    EDGE_PATH = "/_api/edge"
    DELETE_EDGE_PATH = "/_api/edge/{0}"
    UPDATE_EDGE_PATH = "/_api/edge/{0}"

    IGNORE_KEYS = set(["_rev", "_id", "_from", "_to"])

    def __init__(self, collection=None,
                 _id=None, _rev=None,
                 _from=None, _to=None, **kwargs):
        self.connection = collection.connection
        self.collection = collection

        self._body = None
        self._id = _id
        self._rev = _rev
        self._from = _from
        self._to = _to

        self._from_document = None
        self._to_document = None

    @property
    def id(self):

        return self._id

    @property
    def rev(self):
        return self._rev

    @property
    def from_document(self):
        """
        From vertex, return instance of ``Document`` or ``None``
        """
        if not self._from:
            return None

        if not self._from_document:
            self._from_document = Document(
                collection=self.collection,
                id=self._from
            )

        return self._from_document

    @property
    def to_document(self):
        """
        To vertex, return instance of ``Document`` or ``None``
        """
        if not self._to:
            return None

        if not self._to_document:
            self._to_document = Document(
                collection=self.collection,
                id=self._to
            )

        return self._to_document

    def __cmp__(self, other):
        """
        Compare two Edges in same way as Document and
        additionally compare FROM and TO documents
        """

        if other == None:
            return -1

        if super(Edge, self).__cmp__(other) != 0:
            return -1

        if self.from_document == other.from_document and \
                self.to_document == other.to_document:
            return 0

        return -1

    def __repr__(self):
        return "<ArangoDB Edge: Id {0}/{1}, From {2} to {3}>".format(
            self._id,
            self._rev,
            self._from,
            self._to
        )

    def __getitem__(self, name):
        """Get element by dict-like key"""
        return self.get(name)

    def __setitem__(self, name, value):
        """Get element by dict-like key"""

        self._body[name] = value

    @property
    def body(self):
        """This property return Edge content"""
        return self.get()

    @property
    def response(self):
        """Property to get latest response"""
        return self._response

    def get(self, name=None, default=None):
        """
        This method very similar to ``dict``'s ``get`` method.
        The difference is that *default* value should be specified
        explicitly.

        To get specific value for specific key in body use and default
        *(fallback)* value ``0``::

            edge.get(name="sample_key", default=0)

        """

        if not self._body:
            return default

        if name == None:
            return self._body

        return self._body.get(name, default)

    def parse_edge_response(self, response):
        """
        Parse Edge details
        """
        self._id = response.get("_id", None)
        self._rev = response.get("_rev", None)
        self._from = response.get("_from", None)
        self._to = response.get("_to", None)
        self._body = response

    def create(self, from_doc, to_doc, body, **kwargs):
        """
        Method to create new edge.
        ``from_doc`` and ``to_doc`` may be both
        **document-handle** or instances of ``Document`` object.

        Possible arguments: :term:`waitForSync`

        Read more about additional arguments  :term:`Edges REST Api`
        """
        if self.id != None:
            raise EdgeAlreadyCreated(
                "This edge already created with id {0}".format(self.id)
            )

        from_doc_id = from_doc
        to_doc_id = to_doc

        if issubclass(type(from_doc), Document):
            from_doc_id = from_doc.id

        if issubclass(type(to_doc), Document):
            to_doc_id = to_doc.id

        params = {
            "collection": self.collection.cid,
            "from": from_doc_id,
            "to": to_doc_id
        }

        params.update(kwargs)

        data = copy.copy(self.body) if self.body else {}
        data.update({
            "_from": from_doc_id,
            "_to": to_doc_id
        })

        response = self.connection.post(
            self.connection.qs(
                self.EDGE_PATH,
                **params
            ),
            data=body
        )

        self._response = response

        # define document ID
        if response.status in [201, 202]:
            self.parse_edge_response(response)

        return self

    def delete(self):
        """
        Method to delete current edge. If edge deleted
        this method return ``True`` and in other case ``False``
        """
        response = self.connection.delete(
            self.DELETE_EDGE_PATH.format(self.id)
        )

        self._response = response

        if response.get("code", 500) == 204:
            self.parse_edge_response({})
            self._body = None
            return True

        return False

    def update(self, body, from_doc=None, to_doc=None, save=True, **kwargs):
        """
        Method to update edge. In case **from_doc** or **do_doc**
        not specified or equal to ``None`` then current
        ``from_document`` and ``to_document`` will be used.

        In case ``save`` argument set to ``False`` edge will not be
        updated until ``save()`` method will be called.
        """
        if not self._id or not self._from or not self._to:
            raise EdgeNotYetCreated(
                "Sorry, you try to update Edge which is not yet created"
            )

        from_doc_id = from_doc or self._from
        to_doc_id = to_doc or self._to

        if issubclass(type(from_doc), Document):
            from_doc_id = from_doc.id

        if issubclass(type(to_doc), Document):
            to_doc_id = to_doc.id

        self._from = from_doc_id
        self._to = to_doc_id

        if not issubclass(type(body), dict) and body != None:
            raise EdgeIncompatibleDataType(
                "Body should be None (empty) or instance or "\
                "subclass of `dict` data type"
            )

        if body != None:
            self.body.update(body)

        if save == True:
            return self.save(**kwargs)

        return True

    def save(self, **kwargs):
        """
        Method to save Edge. This is useful when
        edge udpated several times via ``update``

        Possible arguments: :term:`waitForSync`

        Read more about additional arguments  :term:`Edges REST Api`
        """
        # TODO: research it's possible to change
        # from/to edge properties within this method

        data = copy.copy(self.edge)

        data.update({
            "_from": self._from,
            "_to": self._to
        })

        response = self.connection.put(
            self.UPDATE_EDGE_PATH.format(self.id),
            data=data,
            **kwargs
        )

        self._response = response

        # update revision of the edge
        if response.get("code", 500) in [201, 202]:
            self._rev = response.get("_rev")
            return self

        return None
