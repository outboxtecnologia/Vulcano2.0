import sys
import os

filepath = os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "AuditoriaERPView.jsx")
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update fetchTudo declarations
content = content.replace(
    "const virtuaisPorMes = {};\n      const contasGlobais = new Set();",
    "const virtuaisPorMes = {};\n      const legadosPorMes = {};\n      const contasGlobais = new Set();"
)

# 2. Update loop initialization
content = content.replace(
    "const accVirtual = {};",
    "const accVirtual = {};\n        const accLegado = {};"
)

# 3. Update emp.forEach
old_emp = """        (jsonV.data || []).forEach(emp => {
          mergeConta(emp.contas_virtuais, accVirtual);
          
          // Captura também contas do Questor que possuam origem 'VU' mas que não estejam mapeadas no Motor Virtual
          (emp.contas_fisicas || []).forEach(cFisica => {
            const hasVU = (cFisica.detalhes || []).some(d => d.origem === 'VU');
            if (hasVU) {
              contasGlobais.add(cFisica.conta);
            }
          });
        });"""
new_emp = """        (jsonV.data || []).forEach(emp => {
          mergeConta(emp.contas_virtuais, accVirtual);
          mergeConta(emp.contas_legado, accLegado);
          
          (emp.contas_fisicas || []).forEach(cFisica => contasGlobais.add(cFisica.conta));
          (emp.contas_legado || []).forEach(cLegado => contasGlobais.add(cLegado.conta));
        });"""
content = content.replace(old_emp, new_emp)

# 4. Update porMes lists
content = content.replace(
    """        const virtualList = Object.values(accVirtual);
        
        virtualList.forEach(c => contasGlobais.add(c.conta));
        virtuaisPorMes[comp] = virtualList;""",
    """        const virtualList = Object.values(accVirtual);
        const legadoList = Object.values(accLegado);
        
        virtualList.forEach(c => contasGlobais.add(c.conta));
        virtuaisPorMes[comp] = virtualList;
        legadosPorMes[comp] = legadoList;"""
)

# 5. Update novos[comp] assignments
content = content.replace(
    """          novos[comp] = {
            fisico:  fisicoList,
            virtual: virtuaisPorMes[comp],
          };""",
    """          novos[comp] = {
            fisico:  fisicoList,
            virtual: virtuaisPorMes[comp],
            legado:  legadosPorMes[comp],
          };"""
)
content = content.replace(
    """          novos[comp] = { fisico: [], virtual: [] };""",
    """          novos[comp] = { fisico: [], virtual: [], legado: [] };"""
)

# 6. Update contasMap
old_contasmap = """  // ── Contas a exibir: contas com cálculo Vulcano + contas Questor com lançamentos VU ──
  const contasMap = useMemo(() => {
    const m = {};
    Object.values(dadosPorMes).forEach(({ virtual, fisico }) => {
      (virtual || []).forEach(c => {
        if (!m[c.conta]) m[c.conta] = c.nome || `Conta ${c.conta}`;
      });
      (fisico || []).forEach(c => {
        if (!m[c.conta] && (c.detalhes || []).some(d => d.origem === 'VU')) {
          m[c.conta] = c.nome ? `${c.nome} (Sem Mapeamento)` : `Conta ${c.conta} (Extracontábil VU)`;
        }
      });
    });
    return m; // { contaId → nome }
  }, [dadosPorMes]);"""
new_contasmap = """  // ── Contas a exibir: contas com cálculo Vulcano + contas Questor + contas Legado ──
  const contasMap = useMemo(() => {
    const m = {};
    Object.values(dadosPorMes).forEach(({ virtual, fisico, legado }) => {
      (virtual || []).forEach(c => {
        if (!m[c.conta]) m[c.conta] = c.nome || `Conta ${c.conta}`;
      });
      (legado || []).forEach(c => {
        if (!m[c.conta]) m[c.conta] = c.nome ? `${c.nome} (Vulcano 1.0)` : `Conta ${c.conta} (Vulcano 1.0)`;
      });
      (fisico || []).forEach(c => {
        if (!m[c.conta]) m[c.conta] = c.nome || `Conta ${c.conta} (Física Questor)`;
      });
    });
    return m; // { contaId → nome }
  }, [dadosPorMes]);"""
content = content.replace(old_contasmap, new_contasmap)

# 7. Update ContaConfronto
content = content.replace(
    "const fisico   = lista.fisico?.find(r => String(r.conta) === String(contaId));",
    "const fisico   = lista.fisico?.find(r => String(r.conta) === String(contaId));\n    const legado   = lista.legado?.find(r => String(r.conta) === String(contaId));"
)
content = content.replace(
    "detalhesVirtual: virtual?.detalhes || [],",
    "detalhesVirtual: virtual?.detalhes || [],\n      legadoDetalhes:  legado?.detalhes || [],"
)

# 8. Update DetalheOrfaos
content = content.replace(
    "const questorManual = todosFisico.filter(d => d.origem !== 'VU');",
    "const questorManual = todosFisico;"
)
content = content.replace(
    "const vulcano1 = todosFisico.filter(d => d.origem === 'VU');",
    "const vulcano1 = porComp.flatMap(c => c.legadoDetalhes);"
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated AuditoriaERPView.jsx")
