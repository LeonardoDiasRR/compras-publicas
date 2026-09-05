# Cliente stdio mínimo do MCP compras (uso fora de sessão Hermes com as tools).
# Uso: python3 mcp_query.py <tool> '<json_args>'   |   python3 mcp_query.py _list
# paths: ajustar BIN se o projeto não estiver em ~/projetos/compras-publicas
import json, subprocess, sys

import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
BIN = os.environ.get("COMPRAS_MCP_BIN") or next(
    (p for p in (os.path.join(_ROOT, "MCP_Compras", ".venv", "Scripts", "compras-mcp.exe"),
                 os.path.join(_ROOT, "MCP_Compras", ".venv", "bin", "compras-mcp"))
     if os.path.exists(p)),
)
tool = sys.argv[1]
_raw = sys.argv[2] if len(sys.argv) > 2 else "{}"
args = json.loads(open(_raw[1:], encoding="utf-8").read() if _raw.startswith("@") else _raw)

p = subprocess.Popen([BIN], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
def send(obj):
    p.stdin.write(json.dumps(obj) + "\n"); p.stdin.flush()
def read():
    while True:
        line = p.stdout.readline()
        if not line: raise RuntimeError("server fechou")
        try: d = json.loads(line)
        except ValueError: continue
        if "id" in d: return d

send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"cli","version":"1"}}})
read()
send({"jsonrpc":"2.0","method":"notifications/initialized"})

if tool == "_list":
    send({"jsonrpc":"2.0","id":2,"method":"tools/list"})
    for t in read()["result"]["tools"]:
        print(t["name"], "|", (t.get("description") or "")[:120].replace("\n", " "))
else:
    send({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":tool,"arguments":args}})
    r = read()
    out = r.get("result", r.get("error"))
    if isinstance(out, dict) and "content" in out:
        for c in out["content"]:
            print(c.get("text", ""))
    else:
        print(json.dumps(out, ensure_ascii=False, indent=2))
p.kill()
