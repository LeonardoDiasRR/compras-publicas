# Varre classe CATMAT 7060 (placas de vídeo/aceleradores), coleta memórias altas, e busca ARPs vigentes dos códigos >=96GB
import subprocess, json, re

TODAY="2026-09-03"
cmd=["/home/findface/projetos/compras-publicas/MCP_Compras/.venv/bin/compras-mcp"]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
_id=[0]
def call(tool,args):
    _id[0]+=1; i=_id[0]
    p.stdin.write(json.dumps({"jsonrpc":"2.0","id":i,"method":"tools/call","params":{"name":tool,"arguments":args}})+"\n"); p.stdin.flush()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("closed")
        try: d=json.loads(l)
        except ValueError: continue
        if d.get("id")==i:
            c=d.get("result",{}).get("content")
            return json.loads(c[0]["text"]) if c else {"_error":d.get("error")}
p.stdin.write(json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"s","version":"1"}}})+"\n"); p.stdin.flush(); p.stdout.readline()
p.stdin.write(json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"})+"\n"); p.stdin.flush()

# Estágio 1: classe 7060 inteira
placas={}
page=1
while True:
    d=call("compras_catmat_buscar",{"termo":"x","codigo_grupo":70,"codigo_classe":7060,"tamanho_pagina":100,"pagina":page})
    for it in d.get("resultado",[]):
        n=(it.get("descricaoItem") or "").upper()
        if n.startswith("PLACA CONTROLADORA"): placas[it["codigoItem"]]=it["descricaoItem"]
    tp=d.get("_total_paginas") or 1
    if page>=tp: break
    page+=1
print("placas video na classe 7060:",len(placas))

def memgb(desc):
    m=re.search(r"MEM[ÓO]RIA[: ]+(?:SUPERIOR A |MAIOR QUE )?([\d.,]+)\s*(TB|GB)",desc,re.I)
    if not m: return None
    v=float(m.group(1).replace(",","."));  v*=1024 if m.group(2).upper()=="TB" else 1
    sup = "SUPERIOR" in desc.upper() or "MAIOR" in desc.upper()
    return v,sup

alvos={}
for c,n in placas.items():
    r=memgb(n)
    if r and (r[1] or r[0]>=96): alvos[c]=n
print("placas >=96GB ou 'superior a':",len(alvos))
for c,n in alvos.items(): print(c,"|",n[:130])

# Estágio 2: ARPs vigentes p/ esses códigos + os 2 aceleradores conhecidos
alvos.setdefault(464960,"acelerador 24GB (referência)"); alvos.setdefault(637988,"acelerador 48GB (referência)")
ach=[]
for wmin,wmax in [("2025-09-03","2026-09-03"),("2024-09-04","2025-09-02")]:
    for c in alvos:
        d=call("compras_arp_itens_listar",{"data_vigencia_inicial_min":wmin,"data_vigencia_inicial_max":wmax,"codigo_item":c,"tamanho_pagina":500})
        for it in d.get("resultado",[]):
            if (it.get("dataVigenciaFinal") or "")[:10]>=TODAY and not it.get("itemExcluido"):
                it["_catmat"]=alvos[c]; ach.append(it)
json.dump({"placas_gt96gb":alvos,"arps_vigentes":ach},open("/tmp/gpu_gt96.json","w"),ensure_ascii=False,indent=1)
print("FIM itens_vigentes:",len(ach))
p.kill()
