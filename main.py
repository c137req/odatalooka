import requests, sys
from urllib.parse import urljoin

def IsODataService(baseURL):
    if not baseURL.endswith("/"):
        baseURL += "/"
    
    headers = {"Accept": "application/json, application/xml"}
    
    try:
        resp = requests.get(baseURL, headers=headers, allow_redirects=True)
        if resp.status_code == 200:
            contentType = resp.headers.get("Content-Type", "").lower()
            textLower = resp.text.lower()
            if "application/json" in contentType and "@odata.context" in textLower:
                return True, "Service document"
            if "application/xml" in contentType and ("atom" in textLower or "feed" in textLower):
                return True, "Service document (XML)"
    except Exception:
        pass
    
    try:
        # check $metadata - will double check in ScanHost
        metaURL = urljoin(baseURL, "$metadata")
        resp = requests.get(metaURL, headers=headers, allow_redirects=True)
        if resp.status_code == 200:
            contentType = resp.headers.get("Content-Type", "").lower()
            textLower = resp.text.lower()
            if "application/xml" in contentType and "edmx:edmx" in textLower:
                return True, "$metadata endpoint"
    except Exception:
        pass
    
    return False, ""

def ScanHost(Host):
    # check both http, https, and non-specified urls in-case others are(n't) odata services
    Schemes = ["http://", "https://"] if not Host.startswith(("http://", "https://")) else [""]
    Hosts = [scheme + Host if scheme else Host for scheme in Schemes]

    # references
    # https://docs.getodk.org/central-api-odata-endpoints
    # https://www.odata.org/getting-started/basic-tutorial
    # https://www.odata.org/blog/how-to-use-web-api-odata-to-build-an-odata-v4-service-without-entity-framework
    endpoints = [
        # test for easily forgettable setting-up-from-tutorial-fields
        "",  # service document
        "$metadata",
        "$metadata#?",
        "People",
        "People?$filter=contains(Description,'?')", # malform people description
        "People?$select=ivan",
        "People?$expand=Trips", # worth checking default query from tutorial
        "People?$expand=*",
        "People?$filter=1=1",
        "People?$select=*",
        "People?$filter=Description=%27;DROP%20TABLE%20Users;%27", # sqli test
        "People?$expand=Trips,../../etc/passwd", # path trans test
        "People?$filter=contains(Description,<a id=x tabindex=1 onfocus=alert()></a>)", # not useful for me rn but someone might find it useful
        "People//",
        "People?%24expand=Trips",
        "/V4/(S(flat4rgegiueineatspfdku1))/TripPinServiceRW)",
        "odata",
        "odata/",
        "odata.svc",
        "OData.svc",
        "api",
        "api/",
        "api/odata",
        "api/odata/",
        "api/data",
        "api/data/",
        "data",
        "data/",
        "services",
        "services/",
        "services/odata",
        "services/odata/",
        "_api",
        "_api/",
        "_vti_bin/listdata.svc",
        "sap/opu/odata",
        "sap/opu/odata/",
        "dynamics/api/data",
        "dynamics/api/data/",
        "v1",
        "v1/",
        "v2",
        "v2/",
        "v3",
        "v3/",
        "v4",
        "v4/",
        "odata/v1",
        "odata/v1/",
        "odata/v2",
        "odata/v2/",
        "odata/v3",
        "odata/v3/",
        "odata/v4",
        "odata/v4/",
        "api/v1",
        "api/v1/",
        "api/v2",
        "api/v2/",
        "api/v3",
        "api/v3/",
        "api/v4",
        "api/v4/",
        "serviceRoot",
        "serviceRoot/?",
        "serviceRoot/*",
        "serviceRoot/.",
        "serviceRoot/;;; ls" # attempt at cmd injection
        # lotta endpoints
        ]
    
    Found = []
    for NewHost in Hosts:
        for path in endpoints:
            URL = urljoin(NewHost, path)
            IsOData, EndpointType = IsODataService(URL)
            if IsOData:
                Found.append((URL, EndpointType))
            else:
                try:
                    resp = requests.get(URL, headers={"Accept": "application/json, application/xml"}, allow_redirects=True)
                    status = resp.status_code
                    StatusCode = f"status {status}"
                    if status in [400, 403, 500]:
                        StatusCode += "- possible sanitisation issue"
                    Found.append((URL, f"non-odata res -{StatusCode}"))
                except Exception as e:
                    Found.append((URL, f"req failed: {str(e)}"))
    
    return Found

results = ScanHost(sys.argv[1])
if results:
    for URL, EndpointType in sorted(results, key=lambda x: x[0]):
        print(f"{URL}: {EndpointType}")
else:
    print("no endpoints responded")
