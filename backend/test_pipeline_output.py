import traceback
from core.services.graph_logic_builder import AccountingGraphPipeline

try:
    res = AccountingGraphPipeline.api_contabilizacoes(ano=2025, mes=4, empresa_id=959, empreendimento_id='18')
    vols = [v for v in res if v['empreendimento_nome'].upper().find('STUTTGART') >= 0]
    if vols:
        print("Encontrado. Unidades:", len(vols[0]['contas_virtuais']))
        print([(k['hist']) for k in vols[0]['contas_virtuais'][:3]])
    else:
        print("NOT FOUND")
except Exception as e:
    traceback.print_exc()
