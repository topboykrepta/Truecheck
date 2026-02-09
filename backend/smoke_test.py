import time
import httpx

BASE = "http://127.0.0.1:8000/api/v1"

def main():
    text = "NASA confirmed water ice exists on the Moon in 2018. The Earth is flat."
    with httpx.Client(timeout=20) as c:
        r = c.post(f"{BASE}/upload/text", data={"payload_text": text})
        r.raise_for_status()
        report_id = r.json()["report_id"]
        print("report_id:", report_id)

        for _ in range(40):
            rr = c.get(f"{BASE}/reports/{report_id}")
            rr.raise_for_status()
            report = rr.json()
            print("status:", report["status"])
            if report["status"] in ("complete", "failed"):
                print("verdict:", report.get("verdict"), "confidence:", report.get("confidence"))
                print("claims:", len(report.get("key_claims") or []))
                print("web_extracts:", len(((report.get("evidence") or {}).get("web_extracts")) or []))
                print("limitations:", report.get("limitations"))
                return
            time.sleep(1.0)

        raise SystemExit("Timed out waiting for report completion")


if __name__ == "__main__":
    main()
