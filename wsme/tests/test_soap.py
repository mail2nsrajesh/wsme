import decimal
import datetime

import wsme.tests.protocol

try:
    import xml.etree.ElementTree as et
except:
    import cElementTree as et

import wsme.soap


def build_soap_message(method, params=""):
    message = """<?xml version="1.0"?>
<soap:Envelope
xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">

  <soap:Body xmlns="http://foo.bar.baz/soap/">
    <%(method)s>
        %(params)s
    </%(method)s>
  </soap:Body>

</soap:Envelope>
""" % dict(method=method, params=params)
    return message


def dumpxml(key, obj):
    el = et.Element(key)
    if isinstance(obj, basestring):
        el.text = obj
    elif type(obj) in (int, float, decimal.Decimal):
        el.text = str(obj)
    elif type(obj) in (datetime.date, datetime.time, datetime.datetime):
        el.text = obj.isoformat()
    elif type(obj) == dict:
        for key, obj in obj.items():
            el.append(dumpxml(key, obj))
    return el


def loadxml(el):
    if len(el):
        d = {}
        for child in el:
            d[child.tag] = loadxml(child)
        return d
    else:
        return el.text


class TestSOAP(wsme.tests.protocol.ProtocolTestCase):
    protocol = 'SOAP'

    def test_simple_call(self):
        message = build_soap_message('Touch')
        print message
        res = self.app.post('/', message,
            headers={
                "Content-Type": "application/soap+xml; charset=utf-8"
        }, expect_errors=True)
        print res.body
        assert res.status.startswith('200')

    def call(self, fpath, **kw):
        # get the actual definition so we can build the adequate request
        
        el = dumpxml('parameters', kw)
        content = et.tostring(el)
        res = self.app.post(
            '/' + fpath,
            content,
            headers={
                'Content-Type': 'text/xml',
            },
            expect_errors=True)
        print "Received:", res.body
        el = et.fromstring(res.body)
        if el.tag == 'error':
            raise wsme.tests.protocol.CallException(
                    el.find('faultcode').text,
                    el.find('faultstring').text,
                    el.find('debuginfo') is not None and
                        el.find('debuginfo').text or None)

        else:
            return loadxml(et.fromstring(res.body))

    def test_wsdl(self):
        res = self.app.get('/api.wsdl')
        print res.body
        assert 'ReturntypesGetunicode' in res.body
