import sys
import os

filepath = os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "AuditoriaERPView.jsx")
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: Stop reading all physical accounts into contasGlobais
old_emp = """        (jsonV.data || []).forEach(emp => {
          mergeConta(emp.contas_virtuais, accVirtual);
          mergeConta(emp.contas_legado, accLegado);
          
          (emp.contas_fisicas || []).forEach(cFisica => contasGlobais.add(cFisica.conta));
          (emp.contas_legado || []).forEach(cLegado => contasGlobais.add(cLegado.conta));
        });"""

new_emp = """        (jsonV.data || []).forEach(emp => {
          mergeConta(emp.contas_virtuais, accVirtual);
          mergeConta(emp.contas_legado, accLegado);
          
          (emp.contas_virtuais || []).forEach(c => contasGlobais.add(c.conta));
          (emp.contas_legado || []).forEach(c => contasGlobais.add(c.conta));
        });"""
content = content.replace(old_emp, new_emp)

# Fix 2: Stop forcing m[c.conta] using fisico in contasMap
old_contasmap = """  // ── Contas a exibir: contas com cálculo Vulcano + contas Questor + contas Legado ──
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

new_contasmap = """  // ── Contas a exibir: contas com cálculo Vulcano + contas Legado ──
  const contasMap = useMemo(() => {
    const m = {};
    Object.values(dadosPorMes).forEach(({ virtual, legado }) => {
      // 1. Contas Virtuais
      (virtual || []).forEach(c => {
        if (!m[c.conta]) m[c.conta] = c.nome || `Conta ${c.conta}`;
      });
      // 2. Contas Legado
      (legado || []).forEach(c => {
        if (!m[c.conta]) m[c.conta] = c.nome ? `${c.nome} (Vulcano 1.0)` : `Conta ${c.conta} (Vulcano 1.0)`;
      });
    });
    return m; // { contaId → nome }
  }, [dadosPorMes]);"""
content = content.replace(old_contasmap, new_contasmap)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated AuditoriaERPView.jsx")
