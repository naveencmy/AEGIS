import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import unittest
from fastapi import HTTPException
from backend.app.parsers.nmap_parser import nmap_parser

SAMPLE_VALID_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE nmaprun>
<nmaprun scanner="nmap" args="nmap -sV -oX scan.xml scanme.nmap.org" start="1708272000" version="7.94">
  <host starttime="1708272000" endtime="1708272010">
    <status state="up" reason="echo-reply" reason_ttl="53"/>
    <address addr="45.33.32.156" addrtype="ipv4"/>
    <hostnames>
      <hostname name="scanme.nmap.org" type="user"/>
    </hostnames>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open" reason="syn-ack" reason_ttl="53"/>
        <service name="ssh" product="OpenSSH" version="6.6.1p1" method="probed" conf="10">
          <cpe>cpe:/a:openbsd:openssh:6.6.1p1</cpe>
        </service>
      </port>
      <port protocol="tcp" portid="80">
        <state state="open" reason="syn-ack" reason_ttl="53"/>
        <service name="http" product="Apache httpd" version="2.4.7" method="probed" conf="10">
          <cpe>cpe:/a:apache:http_server:2.4.7</cpe>
        </service>
      </port>
      <port protocol="tcp" portid="9929">
        <state state="closed" reason="reset" reason_ttl="53"/>
        <service name="nping-echo" method="table" conf="3"/>
      </port>
    </ports>
  </host>
</nmaprun>
"""

MALFORMED_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<nmaprun>
  <host>
    <status state="up"/>
    <address addr="192.168.1.1" addrtype="ipv4"/>
    <ports>
      <port portid="80">
        <unclosed_tag>
    </ports>
  </host>
"""

INVALID_ROOT_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<not_nmap>
  <host></host>
</not_nmap>
"""

class TestNmapParser(unittest.TestCase):
    def test_valid_nmap_xml_parsing(self):
        res = nmap_parser.parse_xml_bytes(SAMPLE_VALID_XML, filename="test_scan.xml")
        self.assertEqual(len(res.hosts), 1)
        self.assertIn("45.33.32.156", res.hosts)
        self.assertEqual(res.services_scanned, 2)
        self.assertEqual(len(res.results), 2)
        
        # Verify OpenSSH service
        ssh_svc = next((r for r in res.results if r.port == 22), None)
        self.assertIsNotNone(ssh_svc)
        self.assertEqual(ssh_svc.product, "OpenSSH")
        self.assertEqual(ssh_svc.version, "6.6.1p1")
        
        # Verify Apache service
        http_svc = next((r for r in res.results if r.port == 80), None)
        self.assertIsNotNone(http_svc)
        self.assertEqual(http_svc.product, "Apache httpd")
        self.assertEqual(http_svc.version, "2.4.7")

    def test_malformed_xml_422(self):
        with self.assertRaises(HTTPException) as ctx:
            nmap_parser.parse_xml_bytes(MALFORMED_XML, filename="bad.xml")
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertIn("Invalid or malformed Nmap XML", ctx.exception.detail)

    def test_invalid_root_tag_422(self):
        with self.assertRaises(HTTPException) as ctx:
            nmap_parser.parse_xml_bytes(INVALID_ROOT_XML, filename="invalid_root.xml")
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertIn("Root tag is not <nmaprun>", ctx.exception.detail)

if __name__ == "__main__":
    unittest.main()
