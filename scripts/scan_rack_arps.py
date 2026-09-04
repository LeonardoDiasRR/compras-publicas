# Varredura completa: CATMAT servidor rack -> itens de ARP vigentes (via MCP compras, sessão única)
import subprocess, json, sys, datetime

TODAY = "2026-09-03"
cmd = ["/home/findface/projetos/compras-publicas/MCP_Compras/.venv/bin/compras-mcp"]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
_id = [0]
def call(tool, args, timeout=90):
    _id[0] += 1
    i = _id[0]
    p.stdin.write(json.dumps({"jsonrpc":"2.0","id":i,"method":"tools/call","params":{"name":tool,"arguments":args}})+"\n")
    p.stdin.flush()
    while True:
        line = p.stdout.readline()
        if not line: raise RuntimeError("server fechou")
        try: d = json.loads(line)
        except ValueError: continue
        if d.get("id") == i:
            c = d.get("result",{}).get("content")
            if not c: return {"_error": d.get("error")}
            try: return json.loads(c[0]["text"])
            except Exception: return {"_raw": c[0].get("text","")}

p.stdin.write(json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"scan","version":"1"}}})+"\n"); p.stdin.flush()
p.stdout.readline()
p.stdin.write(json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"})+"\n"); p.stdin.flush()

# ---- Estágio 1: CATMAT grupo 70, catálogo completo, filtro client-side
rack, gpu = {}, {}
page = 1
while True:
    d = call("compras_catmat_buscar", {"termo":"SERVIDOR","codigo_grupo":70,"tamanho_pagina":100,"pagina":page})
    res = d.get("resultado",[])
    for it in res:
        n = (it.get("descricaoItem") or "").upper()
        if n.startswith("SERVIDOR") and "RACK" in n:
            rack[it["codigoItem"]] = it["descricaoItem"]
        if "GPU" in n or "NVIDIA" in n or "B200" in n or "B300" in n:
            gpu[it["codigoItem"]] = it["descricaoItem"]
    tp = d.get("_total_paginas") or 1
    if page % 20 == 0 or page >= tp: print(f"catmat page {page}/{tp} rack={len(rack)} gpu={len(gpu)}", flush=True)
    if page >= tp: break
    page += 1
    if page > 200: break

json.dump({"rack":rack,"gpu":gpu}, open("/tmp/scan_catmat.json","w"), ensure_ascii=False, indent=1)

# ---- Estágio 2: itens de ARP vigentes por código (janelas de início que ainda estão vigentes)
windows = [("2025-09-03","2026-09-03"), ("2024-09-04","2025-09-02")]
achados = []
codes = sorted(set(list(rack.keys())+list(gpu.keys())))
for n,code in enumerate(codes,1):
    for wmin,wmax in windows:
        d = call("compras_arp_itens_listar", {"data_vigencia_inicial_min":wmin,"data_vigencia_inicial_max":wmax,"codigo_item":code,"tamanho_pagina":500})
        for it in d.get("resultado",[]):
            fv = (it.get("dataVigenciaFinal") or "")[:10]
            if fv >= TODAY and not it.get("itemExcluido"):
                it["_descricaoCatmat"] = rack.get(code) or gpu.get(code)
                achados.append(it)
    if n % 20 == 0: print(f"arp {n}/{len(codes)} achados={len(achados)}", flush=True)

json.dump(achados, open("/tmp/arp_itens_vigentes.json","w"), ensure_ascii=False, indent=1)
print(f"FIM codigos={len(codes)} itens_vigentes={len(achados)}")
p.kill()
