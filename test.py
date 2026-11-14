import requests
import urllib3

# Matikan warning SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# GANTI '<NetflixId>' DENGAN NILAI DARI FAIL COOKIE KAU
# Contoh: NetflixId=12345678abcdefg
NETFLIX_ID = "ct=BgjHlOvcAxKQBLWUBZHf76e7gmQNJneKcGI-ZfkBMRir5lZ-ZYUhoHHPQpJq5X1P3avxQNQjDKTxXNVggScWvVquvKUdXHqHovxW_Xk5PsXtwzCyQToIRV133HeOuOtdLlam_xFWKEy5iB1nN61iwBtVRWBt2eCNUPEta0Y6c8VHUajngQAmADUJm2Ta91rxZaliY9I78QOMXiF3gEwx0hZsrEeZUzPdKDcG2gA6oreef8Vf4CPPaAMXOVIwUPasDWHi0QCpRSoIF71Rl_82gvlJntDO9DIcvqhGVSk173aiWjPypl5C-ZLdOrieP27skRckz7mSRuo27alU_H0XM4_qJHHamo4318sInolq_y87Yg6WXsiR3sXw1avgiuL2t74cdlQn9p-3YogwFzqUX72fPuoPRf6JaOyls-gWOgBDTqp2DFAiRWQamrYK6TLIFW2-9YU20WAAn-yNWXERiSDb89U7NRpsEcKSGkNeoMiu9ob2Bq11gdP04MW5sqlSkECVa_nvZmw-8fU6Y06iGUu7PPT79Sm5v3DPhiPwRVpDiJvbcKQD2mAYX-JXQopb5W9UEj0Zn_qBFMs2tfWSj-Qw8iME66QPeUC84UcNQpPQOsejKSOd6gT3PnkIEVW7VNyJEx9yaRb1c0M29xBzkvDKvEAo8z0RgTJ351ao9nVLBgchjuHMTRpZPhpJvdpLiNPLKbxjxse1AhgGIg4KDPIQyBF2dWEghgROZw..&ch=AQEAEAABABS3dFkfBhyOPbbglGp_6fPAY6SW28OWUFM.&v=3&pg=HVN623XYE5BDLL5PXI6DN5PHEI"

url = "https://ios.prod.ftl.netflix.com/iosui/user/15.48"

params = {
    "appVersion": "15.48.1",
    "path": '["account","token","default"]',
    "pathFormat": "graph",
    "responseFormat": "json",
}

headers = {
    "User-Agent": "Argo/15.48.1 (iPhone; iOS 15.8.5; Scale/2.00)",
    "Cookie": f"NetflixId={NETFLIX_ID}"
}

print(f"Testing endpoint: {url}")
r = requests.get(url, params=params, headers=headers, verify=False, timeout=15)

print(f"Status Code: {r.status_code}")
print(f"Response (first 500 chars):")
print(r.text[:500])
