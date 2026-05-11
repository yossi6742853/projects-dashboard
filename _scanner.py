"""
דשבורד פרויקטים — סקנר יומי
מעדכן data.json עם סטטוס נוכחי של כל פרויקט
"""
import json, os, subprocess, datetime, urllib.request, urllib.error, socket

BASE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(BASE, "data.json")
HOME = r"C:\Users\יוסף שניידר"

def now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")

def git_last_commit(path):
    try:
        r = subprocess.run(
            ["git", "-C", path, "log", "-1", "--format=%ci|%s"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.strip().split("|", 1)
            return {"date": parts[0][:10], "msg": parts[1][:60] if len(parts) > 1 else ""}
    except Exception:
        pass
    return None

def http_check(url, timeout=6):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BHT-Scanner/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None

def port_check(host, port, timeout=3):
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False

def scan_project(p):
    result = {"id": p["id"], "name": p["name"], "scanned": now_iso()}

    # git last commit
    if p.get("git_path"):
        path = p["git_path"].replace("C:\\", "/mnt/c/").replace("\\", "/")
        commit = git_last_commit(path)
        if commit:
            result["last_commit"] = commit["date"]
            result["last_commit_msg"] = commit["msg"]

    # HTTP liveness check
    if p.get("url"):
        code = http_check(p["url"])
        result["http_status"] = code
        result["http_ok"] = code in (200, 302, 301) if code else False

    # local port check
    if p.get("port"):
        result["port_open"] = port_check("127.0.0.1", p["port"])

    # file freshness (mtime of a key file)
    if p.get("key_file"):
        fpath = p["key_file"].replace("C:\\", "/mnt/c/").replace("\\", "/")
        try:
            mtime = os.path.getmtime(fpath)
            result["file_mtime"] = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
            result["file_size_kb"] = round(os.path.getsize(fpath) / 1024, 1)
        except Exception:
            pass

    return result

PROJECTS = [
    {"id": "bht-sheets",    "name": "BHT Google Sheets",
     "git_path": HOME + r"\בית-התלמוד\sheets",
     "url": "https://script.google.com/macros/s/AKfycbwIFeKofkqY-VRbth-Sja4IDD6vMi-P5L3C9QsI-k3E/exec",
     "key_file": HOME + r"\בית-התלמוד\sheets\v5\Code.gs"},

    {"id": "bht-copy",      "name": "BHT Copy v1",
     "git_path": HOME + r"\עותק-בית-התלמוד\sheets",
     "url": "https://script.google.com/macros/s/AKfycbygxGYY6GgviL_juZt2ej_cYu2Hw6yw8zv8MeTmufGn8W86O80HU5IxgVcexgi6nx-7/exec"},

    {"id": "flask",         "name": "Flask + Access",
     "port": 5050,
     "key_file": HOME + r"\בית-התלמוד\בית_התלמוד.accdb"},

    {"id": "bht-pages",     "name": "BHT GitHub Pages",
     "url": "https://beit-hatalmud.github.io"},

    {"id": "cheder-bht",    "name": "cheder-bht",
     "url": "https://beit-hatalmud.github.io/cheder-bht"},

    {"id": "chaim-katz",    "name": "אתר חיים כץ",
     "git_path": HOME + r"\chaim-katz-site"},

    {"id": "maale-amos",    "name": "אתר מעלה עמוס",
     "git_path": HOME + r"\maale-amos-site"},

    {"id": "cheder-maale",  "name": "cheder-maale-amos",
     "git_path": HOME + r"\חדר-מעלה-עמוס"},

    {"id": "finance",       "name": "כספים",
     "git_path": HOME + r"\כספים"},

    {"id": "ai-email",      "name": "ai-email-agent",
     "git_path": HOME + r"\ai-email-agent",
     "key_file": HOME + r"\ai-email-agent\send_morning_email.py"},

    {"id": "docbuilder",    "name": "DocBuilder Studio",
     "port": 6060},

    {"id": "whatsapp",      "name": "WhatsApp Bridge",
     "port": 3000,
     "key_file": HOME + r"\whatsapp-bridge\state.json"},

    {"id": "yemot",         "name": "קו ימות",
     "url": "https://www.call2all.co.il/ym/api/Login?username=0772251404&password=85478577"},

    {"id": "intercom",      "name": "אינטרקום",
     "port": 47832},

    {"id": "voice-lan",     "name": "סוכן קולי LAN",
     "port": 5060},

    {"id": "video-v8",      "name": "BHT Video Engine v8",
     "key_file": HOME + r"\video_editor_v8.py"},

    {"id": "pregnancy-vid", "name": "pregnancy-videos-haredi",
     "git_path": HOME + r"\pregnancy-videos-haredi"},

    {"id": "vimeo-dl",      "name": "vimeo-downloader",
     "git_path": HOME + r"\vimeo-downloader-work"},

    {"id": "z-sorter",      "name": "סוכן מיון Z:",
     "key_file": HOME + r"\_מיון_רשת\sorter.py"},

    {"id": "dashboard",     "name": "דשבורד פרויקטים",
     "git_path": HOME + r"\projects-dashboard",
     "url": "https://yossi6742853.github.io/projects-dashboard/"},
]

def main():
    print(f"[{now_iso()}] סקנר מתחיל — {len(PROJECTS)} פרויקטים")
    results = []
    for p in PROJECTS:
        try:
            r = scan_project(p)
            results.append(r)
            http = r.get("http_status","")
            port = r.get("port_open","")
            commit = r.get("last_commit","")
            print(f"  {p['name']}: http={http} port={port} commit={commit}")
        except Exception as e:
            results.append({"id": p["id"], "name": p["name"], "error": str(e), "scanned": now_iso()})
            print(f"  {p['name']}: ERROR {e}")

    data = {"generated": now_iso(), "projects": results}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[{now_iso()}] נשמר: {OUT}")

if __name__ == "__main__":
    main()
