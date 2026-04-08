import re
try:
    with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
        text = f.read()

    pattern = r'<td className="p-2 text-right">.*?<td className={`p-2 text-right text-\[10px\] font-bold \$\{\(\(u\.caixa_acumulado\|\|0\) - \(u\.soc_acumulado\|\|0\)\) \> 0 \? \'text-\[\#007aff\]\' : \'text-\[var\(--v-accent\)\]\'\}`}>\s*\{formatCurrency\(\(u\.caixa_acumulado\|\|0\) - \(u\.soc_acumulado\|\|0\)\)\}\s*<\/td>'
    
    new_block = '''<td className="p-2 text-right">
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
                                     </td>'''
    
    match = re.search(pattern, text, re.DOTALL)
    if match:
        text = text[:match.start()] + new_block + text[match.end():]
        with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Success")
    else:
        print("Regex not found!")
except Exception as e:
    print(e)
