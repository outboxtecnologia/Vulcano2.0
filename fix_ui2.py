import re

try:
    with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
        text = f.read()

    old_block = r'''                                 <tr key={`u-\$\{j\}`} className="border-b border-\[\#0a0a0a\] bg-\[var\(--v-bg\)\] hover:bg-\[\#111\]">
                                     <td className="p-2 pl-8 border-r border-\[var\(--v-border\)\]">
                                         <div className="flex flex-col min-w-0">
                                            <span className="text-\[var\(--v-accent-5\)\] font-bold text-\[11px\] truncate" title=\{u\.unidade\}>\{u\.unidade\}<\/span>
                                            <span className="text-\[\#a1a1aa\] text-\[10px\] break-all block w-full" title=\{u\.comprador\}>\{u\.comprador \|\| "CLIENTE NÃO INFORMADO"\}<\/span>
                                         </div>
                                     <\/td>
                                     <td className="p-2 text-right">
            <div className="text-\[var\(--v-text-muted\)\] font-bold">\{formatCurrency\(u\.receita_caixa\)\}<\/div>
            <div className="text-\[9px\] text-\[\#888\] uppercase tracking-wider">Acu: \{formatCurrency\(u\.caixa_acumulado \|\| 0\)\}<\/div>
        <\/td>
                                     <td className="p-2 text-right text-\[var\(--v-accent\)\] font-bold text-\[10px\] border-r border-\[var\(--v-border\)\]">
                                         <div className="flex flex-col">
                                            <span>-\{formatCurrency\(u\.tributos_total\)\}<\/span>
                                            <span className="text-\[\#444\]">P:\{formatCurrency\(u\.pis\)\} I:\{formatCurrency\(u\.irpj\)\}<\/span>
                                         </div>
                                     <\/td>
                                     <td className="p-2 text-right text-\[\#444\]">\{u\.poc\.toFixed\(2\)\}%<\/td>
                                     <td className="p-2 text-right">
            <div className="text-\[var\(--v-accent-3\)\] font-bold">\{formatCurrency\(u\.receita_societaria\)\}<\/div>
            <div className="text-\[9px\] text-\[\#888\] uppercase tracking-wider">Acu: \{formatCurrency\(u\.soc_acumulado \|\| 0\)\}<\/div>
        <\/td>
                                     <td className="p-2 text-right text-\[var\(--v-accent\)\] text-\[10px\]">-\{formatCurrency\(u\.tributos_societario\)\}<\/td>
                                     <td className={`p-2 text-right text-\[10px\] font-bold \$\{\(\(u\.caixa_acumulado\|\|0\) - \(u\.soc_acumulado\|\|0\)\) > 0 \? 'text-\[\#007aff\]' : 'text-\[var\(--v-accent\)\]'\} `}>\{formatCurrency\(\(u\.caixa_acumulado\|\|0\) - \(u\.soc_acumulado\|\|0\)\)\}<\/td>
                                 <\/tr>'''

    escaped_old_block = text[text.find('<tr key={`u-${j}`} className="border-b border-[#0a0a0a] bg-[var(--v-bg)] hover:bg-[#111]">') : text.find('</tr>', text.find('<tr key={`u-${j}`} className="border-b border-[#0a0a0a] bg-[var(--v-bg)] hover:bg-[#111]">')) + 5]

    new_block = '''                                 <tr key={`u-${j}`} className="border-b border-[#0a0a0a] bg-[var(--v-bg)] hover:bg-[#111]">
                                     <td className="p-2 pl-8 border-r border-[var(--v-border)]">
                                         <div className="flex flex-col min-w-0">
                                            <span className="text-[var(--v-accent-5)] font-bold text-[11px] truncate" title={u.unidade}>{u.unidade}</span>
                                            <span className="text-[#a1a1aa] text-[10px] break-all block w-full" title={u.comprador}>{u.comprador || "CLIENTE NÃO INFORMADO"}</span>
                                         </div>
                                     </td>
                                     <td className="p-2 text-right">
                                         <div className="text-[var(--v-text-bold)] font-bold">{formatCurrency(u.receita_caixa)}</div>
                                         <div className="text-[9px] text-[var(--v-text-faint)] uppercase tracking-wider">Acu: {formatCurrency(u.caixa_acumulado || 0)}</div>
                                     </td>
                                     <td className="p-2 text-right text-[var(--v-accent)] font-bold text-[10px] border-r border-[var(--v-border)]">
                                         <div className="flex flex-col">
                                            <span>-{formatCurrency(u.tributos_total)}</span>
                                            <span className="text-[#444]">Acu: -{formatCurrency(u.tributos_caixa_acumulado || 0)}</span>
                                         </div>
                                     </td>
                                     <td className="p-2 text-right text-[#444]">{u.poc.toFixed(2)}%</td>
                                     <td className="p-2 text-right">
                                         <div className="text-[var(--v-accent-3)] font-bold">{formatCurrency(u.soc_acumulado || 0)}</div>
                                         <div className="text-[9px] text-[var(--v-text-faint)] uppercase tracking-wider">Mês: {formatCurrency(u.receita_societaria || 0)}</div>
                                     </td>
                                     <td className="p-2 text-right text-[var(--v-accent)] font-bold text-[10px]">
                                         <div className="flex flex-col">
                                            <span>-{formatCurrency(u.tributos_soc_acumulado || 0)}</span>
                                            <span className="text-[#444]">Mês: -{formatCurrency(u.tributos_societario || 0)}</span>
                                         </div>
                                     </td>
                                     <td className={`p-2 text-right text-[10px] font-bold ${((u.caixa_acumulado||0) - (u.soc_acumulado||0)) > 0 ? 'text-[#007aff]' : 'text-[var(--v-accent)]'}`}>
                                         {formatCurrency((u.caixa_acumulado||0) - (u.soc_acumulado||0))}
                                     </td>
                                 </tr>'''

    text = text.replace(escaped_old_block, new_block)

    with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Success")
except Exception as e:
    print(e)
