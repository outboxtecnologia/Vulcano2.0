import re

with open(r'D:\vulcano2.0\frontend\src\CustosView.jsx', 'r', encoding='utf-8') as f:
    code = f.read()

# REPLACE NAMES IN DÉBITO AND CRÉDITO
code = code.replace(
    "D É B I T O : {activeEmpData.conta_custo || 'S/ Conta'} (Apropriação Imob.)<br/>",
    "D É B I T O : {activeEmpData.conta_custo || 'S/ Conta'} - {activeEmpData.conta_custo_nome || ''} (Apropriação Imob.)<br/>"
)
code = code.replace(
    "C R É D I T O : {activeEmpData.poc_atual >= 100 ? (activeEmpData.conta_estconc || 'S/ Conta') + ' (Estoque Concluído)' : (activeEmpData.conta_estand || 'S/ Conta') + ' (Estoque em Andamento)'}",
    "C R É D I T O : {activeEmpData.poc_atual >= 100 ? (activeEmpData.conta_estconc || 'S/ Conta') + ' - ' + (activeEmpData.conta_estconc_nome || '') + ' (Estoque Concluído)' : (activeEmpData.conta_estoque || 'S/ Conta') + ' - ' + (activeEmpData.conta_estoque_nome || '') + ' (Estoque em Andamento)'}"
)

# ACCUMULATED HISTORICAL ACCORDION
accum_target = r'<span className="font-bold">{formatCurrency\(\(activeEmpData\.custo_reconhecido_anterior \|\| 0\)\)}</span>'
accum_replacement = '''
<div className="flex flex-col items-end">
    <span className="font-bold cursor-pointer hover:underline flex items-center" 
          onClick={() => document.getElementById("hist-box").classList.toggle("hidden")}
          title="Clique para detalhar o mês-a-mês"
    >
        {formatCurrency((activeEmpData.custo_reconhecido_anterior || 0))} <ChevronDown size={14} className="ml-1"/>
    </span>
</div>
            </div>
            
            <div id="hist-box" className="hidden mt-2 p-2 bg-[#1a1a1a] border border-[#333] rounded text-xs space-y-1">
                <div className="flex justify-between border-b border-[#333] pb-1 text-[#aaa] font-bold">
                    <span>Mês/Ano</span><span>Valor Mensal</span>
                </div>
                {(activeEmpData.historico_anterior || []).length === 0 && <div className="text-center text-[#555] py-2">Sem histórico anterior</div>}
                {(activeEmpData.historico_anterior || []).map((h, idx) => (
                    <div key={idx} className="flex justify-between text-[#888]">
                        <span>{h.periodo}</span>
                        <span>{formatCurrency(h.valor)}</span>
                    </div>
                ))}
            </div>
<div className="hidden">
'''
code = code.replace(accum_target, accum_replacement)

# FIX TWO COLUMNS IN EXTRATO
table_header_target = r'<span className="w-1/2">Ano / Mês</span>\s*<span className="w-1/2 text-right">Custo Acumulado R\$</span>'
table_header_replacement = '''<span className="w-1/3">Ano / Mês</span>
                                                <span className="w-1/3 text-right">Gasto Mensal R$</span>
                                                <span className="w-1/3 text-right">Custo Acumulado R$</span>'''
code = code.replace(table_header_target, table_header_replacement)

table_row_target = r'<span className="w-1/2">\{t.mes\} / \{t.ano\}</span>\s*<span className="w-1/2 text-right">\{formatCurrency\(t.valor\)\}</span>'

# We need to compute cumulative sum on frontend or rewrite timeline rendering
table_render_target = r'''\{timelineElements\.map\(\(t, idx\) => \(\s*<div key=\{idx\} className="flex justify-between items-center py-2 border-b border-\[\#222\]"\>\s*<span className="w-1/2"\>\{t\.ano\} - \{strPad\(t\.mes\)\}</span\>\s*<span className="w-1/2 text-right font-bold text-\[\#ccc\]"\>\s*\{formatCurrency\(t\.valor\)\}\s*</span\>\s*</div\>\s*\)\}'''
table_render_replacement = '''{timelineElements.map((t, idx, arr) => {
                                                // calculate inverted acumulate from the bottom up since it's ordered DESC
                                                let acum = 0;
                                                for(let i = arr.length - 1; i >= idx; i--) {
                                                    acum += arr[i].valor;
                                                }
                                                return (
                                                    <div key={idx} className="flex justify-between items-center py-2 border-b border-[#222]">
                                                        <span className="w-1/3">{t.ano} - {strPad(t.mes)}</span>
                                                        <span className="w-1/3 text-right font-medium text-[#888]">
                                                            {formatCurrency(t.valor)}
                                                        </span>
                                                        <span className="w-1/3 text-right font-bold text-[#ccc]">
                                                            {formatCurrency(acum)}
                                                        </span>
                                                    </div>
                                                );
                                            })}'''

code = code.replace(table_render_target, table_render_replacement)
code = re.sub(r'\{timelineElements\.map\(\(t, idx\).*?</div>\s*\)\}', table_render_replacement, code, flags=re.DOTALL)

with open(r'D:\vulcano2.0\frontend\src\CustosView.jsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("FRONTEND UPDATE OK")
