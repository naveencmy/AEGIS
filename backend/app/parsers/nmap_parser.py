import logging
import xml.etree.ElementTree as ET
from typing import Optional, Any
from fastapi import HTTPException

from backend.app.schemas import (
    ScanResult, ServiceScanResult, MatchedCVE, Citation, ScannedHost, ScannedService
)
from backend.app.rag.vectorstore import vector_store
from backend.app.rag.reranker import reranker_service

logger = logging.getLogger("aegis.parsers.nmap")

SEVERITY_COLORS = {
    "CRITICAL": "#ef4444",
    "CRITICAL_EXPLOITED": "#ef4444",
    "HIGH": "#f97316",
    "MEDIUM": "#eab308",
    "LOW": "#3b82f6",
    "UNKNOWN": "#6b7280",
    "NONE": "#6b7280"
}

def get_severity_color(severity: Optional[str]) -> str:
    if not severity:
        return "#6b7280"
    return SEVERITY_COLORS.get(severity.upper().strip(), "#6b7280")

class NmapXMLParser:
    """
    Parses real Nmap XML output (-sV -oX), extracts discovered hosts, ports,
    services, products, and versions, and maps them to verified ChromaDB CVE documents with full provenance citations.
    """
    def __init__(self):
        self.vector_store = vector_store
        self.reranker = reranker_service

    def parse_xml_bytes(self, xml_bytes: bytes, filename: str = "scan.xml") -> ScanResult:
        try:
            xml_text = xml_bytes.decode("utf-8", errors="replace")
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"Malformed Nmap XML uploaded: {e}")
            raise HTTPException(status_code=422, detail=f"Invalid or malformed Nmap XML file: {str(e)}")
        except Exception as e:
            logger.error(f"XML parse failure: {e}")
            raise HTTPException(status_code=422, detail=f"Failed to process Nmap XML payload: {str(e)}")

        if root.tag != "nmaprun":
            raise HTTPException(status_code=422, detail="Invalid XML schema: Root tag is not <nmaprun>")

        hosts_list: list[str] = []
        service_results: list[ServiceScanResult] = []
        total_cves = 0
        total_services = 0
        kev_alerts = 0

        for host_elem in root.findall("host"):
            status_elem = host_elem.find("status")
            if status_elem is not None and status_elem.get("state") != "up":
                continue

            # IP Address
            ip_addr = "unknown"
            for addr in host_elem.findall("address"):
                if addr.get("addrtype") in ["ipv4", "ipv6"]:
                    ip_addr = addr.get("addr", "unknown")
                    break

            if ip_addr not in hosts_list:
                hosts_list.append(ip_addr)

            ports_elem = host_elem.find("ports")
            if ports_elem is not None:
                for port_elem in ports_elem.findall("port"):
                    port_id = int(port_elem.get("portid", "0"))
                    protocol = port_elem.get("protocol", "tcp")
                    state_elem = port_elem.find("state")
                    if state_elem is not None and state_elem.get("state") != "open":
                        continue

                    service_elem = port_elem.find("service")
                    svc_name = "unknown"
                    product = None
                    version = None

                    if service_elem is not None:
                        svc_name = service_elem.get("name", "unknown")
                        product = service_elem.get("product")
                        version = service_elem.get("version")

                    total_services += 1

                    # Build targeted retrieval query
                    query_parts = []
                    if product:
                        query_parts.append(product)
                    if version:
                        query_parts.append(version)
                    if not query_parts:
                        query_parts.append(svc_name)
                    
                    query_text = f"{' '.join(query_parts)} vulnerabilities"

                    # Retrieve matching CVEs from ChromaDB (strictly from cves & kev collections)
                    matched_cves: list[MatchedCVE] = []
                    try:
                        candidates = self.vector_store.query(
                            query_text=query_text,
                            sources=["cves", "kev"],
                            k=6
                        )
                        if candidates:
                            reranked = self.reranker.rerank(query_text, candidates, top_n=3)
                            for doc in reranked:
                                score = doc.get("relevance_score", 0.0)
                                if score >= 0.40:
                                    meta = doc.get("metadata", {})
                                    did = meta.get("doc_id") or doc.get("doc_id", "CVE")
                                    if did.upper().startswith("CVE-"):
                                        cvss_val = None
                                        try:
                                            if meta.get("score"):
                                                cvss_val = float(meta["score"])
                                        except Exception:
                                            pass
                                        
                                        sev_val = meta.get("severity") or "UNKNOWN"
                                        color = get_severity_color(sev_val)
                                        
                                        citation = Citation(
                                            source=meta.get("source", "nvd"),
                                            doc_id=did,
                                            source_url=meta.get("source_url", "https://nvd.nist.gov"),
                                            excerpt=doc.get("content", "")[:280],
                                            fetched_at=meta.get("fetched_at", "")
                                        )

                                        if meta.get("source") == "cisa_kev" or meta.get("date_added"):
                                            kev_alerts += 1

                                        matched_cves.append(MatchedCVE(
                                            cve_id=did,
                                            title=meta.get("title", did),
                                            cvss=cvss_val,
                                            severity=sev_val,
                                            severity_color=color,
                                            citations=[citation]
                                        ))
                    except Exception as e:
                        logger.warning(f"Error querying vector store for service {svc_name}: {e}")

                    total_cves += len(matched_cves)

                    svc_res = ServiceScanResult(
                        host=ip_addr,
                        port=port_id,
                        protocol=protocol,
                        service=svc_name,
                        product=product,
                        version=version,
                        matched_cves=matched_cves
                    )
                    service_results.append(svc_res)

        return ScanResult(
            hosts=hosts_list,
            services_scanned=total_services,
            cves_found=total_cves,
            results=service_results,
            filename=filename,
            hosts_scanned=len(hosts_list),
            services_found=total_services,
            total_cves_matched=total_cves,
            cisa_kev_critical_alerts=kev_alerts
        )

nmap_parser = NmapXMLParser()
